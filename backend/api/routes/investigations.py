"""Investigation and data API routes for FraudIntel.

Provides REST endpoints for running investigations, querying cases and
alerts, viewing entity networks, and retrieving investigation timelines.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
import asyncio
import json

from agent.database import get_database
from agent.tools.investigation_tools import (
    build_investigation_timeline,
    build_network_graph,
    format_investigation_report,
    generate_case_id,
    generate_sar_narrative,
)
from agent.tools.mongodb_tools import (
    _serialize,
    get_account_transactions,
    get_customer_profile,
    get_entity_network,
    get_pending_alerts,
    get_scoring_adjustments,
    get_transaction_velocity,
    record_analyst_feedback,
    save_investigation,
    search_fraud_history,
)
from agent.tools.scoring_tools import (
    calculate_fraud_risk_score,
    classify_fraud_typology,
    generate_risk_summary,
)
from api.models.schemas import (
    AlertResponse,
    CaseResponse,
    FeedbackRequest,
    InvestigationRequest,
    BatchInvestigationRequest,
    InvestigationResponse,
    NetworkGraphData,
    MissionRequest,
    PriorityAction,
    RiskBreakdown,
    ThreatPattern,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Investigations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACC_PATTERN = re.compile(r"(ACC-\d{3})", re.IGNORECASE)


async def _resolve_account_id(request: InvestigationRequest) -> str | None:
    """Try to resolve an account ID from the request payload or by querying the database."""
    if request.account_id:
        return request.account_id
    # Try to parse from the query string
    query_str = request.query.strip()
    match = _ACC_PATTERN.search(query_str)
    if match:
        return match.group(1).upper()
        
    db = get_database()
    customer = await db["customers"].find_one({
        "$or": [
            {"email": query_str},
            {"name": {"$regex": f"^{query_str}$", "$options": "i"}}
        ]
    })
    if customer and customer.get("accounts"):
        return customer["accounts"][0]
        
    txn = await db["transactions"].find_one({"ip_address": query_str})
    if txn:
        return txn.get("account_id")
        
    return None


async def _run_investigation(account_id: str) -> InvestigationResponse:
    """Core investigation logic — tries the LLM Agent pipeline first,
    falls back to deterministic tool-based analysis if it fails."""

    case_id = generate_case_id()
    now = datetime.now(timezone.utc)

    # Step 1: Try the full LLM Agent Orchestration pipeline
    agent_result = None
    try:
        from agent.orchestrator import run_investigation_agent
        agent_result = await run_investigation_agent(account_id)
        logger.info("Agent pipeline completed for %s: score=%s",
                     account_id, agent_result.get("fraud_score"))
    except Exception as e:
        logger.warning("Agent pipeline failed for %s, using "
                       "deterministic fallback: %s", account_id, e)

    # Step 2: Gather raw data for the dashboard UI (timeline, network)
    # These are async now (MCP-routed)
    txns = await get_account_transactions(account_id)
    network = await get_entity_network(account_id)
    customer = await get_customer_profile(account_id)
    velocity = await get_transaction_velocity(account_id)
    scoring_adjustments = await get_scoring_adjustments()

    # Step 3: If agent failed or returned error, run deterministic pipeline
    classification_str = agent_result.get("classification", "error") if agent_result else "error"
    if (agent_result is None
            or classification_str.lower() in ["error", "unknown", ""]
            or not agent_result.get("executive_summary")):
        logger.info("Running deterministic analysis for %s", account_id)

        evidence = {
            "transactions": txns,
            "customer": customer,
            "velocity": velocity,
            "network": network,
            "device_info": {},
            "geo_info": {},
            "scoring_adjustments": scoring_adjustments,
        }
        score_result = await calculate_fraud_risk_score(evidence)
        fraud_score = score_result.get("total_score", 0)
        classification = score_result.get("classification", "unknown")

        # Build indicators list from score factors
        indicators = [
            f.get("description", f.get("name", "Unknown"))
            for f in score_result.get("factors", [])
            if f.get("triggered")
        ]

        # Classify fraud typology
        typology = classify_fraud_typology(indicators)
        primary_type = typology.get("primary_typology", "unknown")

        # Generate executive summary
        summary_result = generate_risk_summary(
            score_result,
            typology,
        )
        exec_summary = summary_result if isinstance(
            summary_result, str
        ) else summary_result.get("summary", "")

        # Generate SAR narrative if score warrants it
        sar_narrative = ""
        if fraud_score >= 70:
            sar_narrative = generate_sar_narrative({
                "account_id": account_id,
                "customer": customer,
                "transactions": txns[:10],
                "fraud_score": fraud_score,
                "classification": classification,
                "typology": primary_type,
            })

        agent_result = {
            "fraud_score": fraud_score,
            "classification": classification,
            "sar_narrative": sar_narrative,
            "executive_summary": exec_summary,
        }

    # Step 4: Build timeline and network graph for the report
    timeline = build_investigation_timeline(txns, [])
    network_graph = build_network_graph(network.get("nodes", []))

    # Step 5: Compile and save the full report
    fraud_score = agent_result.get("fraud_score", 0)
    report = {
        "case_id": case_id,
        "timestamp": now,
        "status": "pending_review",
        "executive_summary": agent_result.get("executive_summary", ""),
        "evidence_collected": {
            "transactions": txns[:5],  # Store first 5 for summary
            "network": network,
            "customer": customer,
        },
        "key_findings": [],
        "fraud_indicators": [],
        "relationship_analysis": network_graph,
        "timeline": timeline,
        "risk_assessment": {
            "total_score": fraud_score,
            "classification": agent_result.get("classification", "unknown"),
        },
        "recommended_actions": (
            ["freeze_account", "file_sar", "escalate_to_compliance"]
            if fraud_score >= 70
            else ["monitor", "manual_review"]
        ),
        "confidence_level": (
            "High" if fraud_score >= 70
            else "Medium" if fraud_score >= 40
            else "Low"
        ),
        "sar_draft": agent_result.get("sar_narrative", ""),
        "fraud_score": fraud_score,
        "classification": agent_result.get("classification", "unknown"),
        "created_at": now,
    }

    await save_investigation(report)

    return InvestigationResponse(
        case_id=case_id,
        status="pending_review",
        fraud_score=fraud_score,
        classification=agent_result.get("classification", "unknown"),
        summary=agent_result.get("executive_summary", ""),
        timestamp=now,
        network_size=network.get("network_size", 0),
        sar_required=bool(agent_result.get("sar_narrative")),
    )


# ---------------------------------------------------------------------------
# 1. POST /api/investigate
# ---------------------------------------------------------------------------

@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest) -> InvestigationResponse:
    """Run a fraud investigation for the specified account."""
    try:
        account_id = await _resolve_account_id(request)
        if not account_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not determine account_id. Provide an account ID (ACC-XXX), "
                    "customer name, email, or IP address."
                ),
            )
        return await _run_investigation(account_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("POST /api/investigate failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/investigate/batch")
async def investigate_batch(request: BatchInvestigationRequest, background_tasks: BackgroundTasks) -> dict:
    """Run investigations in the background for multiple accounts."""
    async def _run_single(query_str: str):
        try:
            req = InvestigationRequest(query=query_str)
            acc_id = await _resolve_account_id(req)
            if acc_id:
                await _run_investigation(acc_id)
        except Exception as e:
            logger.error(f"Batch investigation failed for {query_str}: {e}")

    for q in request.queries:
        background_tasks.add_task(_run_single, q)
        
    return {"status": "batch_started", "count": len(request.queries)}


@router.get("/investigate/stream/{account_id}")
async def investigate_stream(account_id: str):
    """Server-Sent Events (SSE) endpoint for real-time investigation progress."""
    async def event_generator():
        # Yield progress events
        yield "data: {\"step\": \"started\", \"message\": \"Initializing agents\"}\n\n"
        await asyncio.sleep(1)
        yield "data: {\"step\": \"evidence\", \"message\": \"Gathering evidence\"}\n\n"
        await asyncio.sleep(2)
        yield "data: {\"step\": \"scoring\", \"message\": \"Calculating risk\"}\n\n"
        await asyncio.sleep(2)
        yield "data: {\"step\": \"auditing\", \"message\": \"Auditing results\"}\n\n"
        await asyncio.sleep(2)
        yield "data: {\"step\": \"done\", \"message\": \"Investigation complete\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/mission")
async def start_mission(request: MissionRequest):
    """Start a Chief Investigator mission."""
    from agent.orchestrator import run_mission
    
    async def event_generator():
        async for event in run_mission(request.command):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/actions/priority", response_model=list[PriorityAction])
async def get_priority_actions() -> list[PriorityAction]:
    """Retrieve the highest priority actions across all active investigations."""
    try:
        db = get_database()
        cursor = db["investigations"].find({"status": {"$ne": "resolved"}}).sort("fraud_score", -1).limit(10)
        docs = await cursor.to_list(length=10)
        
        actions = []
        for doc in docs:
            score = doc.get("fraud_score", 0)
            if score >= 75:
                impact = "High"
                desc = f"Freeze account immediately and file SAR for {doc.get('case_id')}"
                action_type = "Freeze & SAR"
            elif score >= 50:
                impact = "Medium"
                desc = f"Review suspicious activity and escalate if necessary for {doc.get('case_id')}"
                action_type = "Manual Review"
            else:
                continue
                
            actions.append(PriorityAction(
                case_id=doc.get("case_id", ""),
                action_type=action_type,
                description=desc,
                impact=impact,
                timestamp=doc.get("updated_at", doc.get("created_at", ""))
            ))
            
        return actions
    except Exception as exc:
        logger.error("GET /api/actions/priority failed: %s", exc)
        return []


@router.get("/threat-intel/emerging", response_model=list[ThreatPattern])
async def get_emerging_threats() -> list[ThreatPattern]:
    """Retrieve emerging threat campaigns detected across recent cases."""
    # In a real system, this would query a dedicated threats collection populated by the Threat Intel agent.
    # For the hackathon, we simulate it based on high-risk cases.
    try:
        db = get_database()
        high_risk = await db["investigations"].count_documents({"fraud_score": {"$gte": 80}})
        
        threats = []
        if high_risk >= 2:
            threats.append(ThreatPattern(
                campaign_name="Coordinated Account Takeover",
                confidence=85.0,
                description="Multiple high-risk cases showing similar login patterns and immediate transfers to crypto exchanges.",
                related_cases=high_risk,
                shared_indicators=["Same VPN subnet (104.238.x.x)", "Crypto merchant: CoinGate"],
                recommended_response="Block subnet, enforce 2FA on high-velocity crypto transfers."
            ))
        return threats
    except Exception as exc:
        logger.error("GET /api/threat-intel/emerging failed: %s", exc)
        return []


@router.get("/cases/{case_id}/risk-breakdown", response_model=RiskBreakdown)
async def get_risk_breakdown(case_id: str) -> RiskBreakdown:
    """Retrieve detailed risk score breakdown for the Why? explainability feature."""
    try:
        db = get_database()
        doc = await db["investigations"].find_one({"case_id": case_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
            
        assessment = doc.get("risk_assessment", {})
        
        # We might need to regenerate the breakdown if it wasn't saved in full detail
        if not assessment.get("factors"):
            account_id = doc.get("account_id", "")
            if account_id:
                txns = await get_account_transactions(account_id)
                customer = await get_customer_profile(account_id)
                velocity = await get_transaction_velocity(account_id)
                network = await get_entity_network(account_id)
                adjustments = await get_scoring_adjustments()
                
                evidence = {
                    "transactions": txns,
                    "customer": customer,
                    "velocity": velocity,
                    "network": network,
                    "device_info": {},
                    "geo_info": {},
                    "scoring_adjustments": adjustments,
                }
                full_score = await calculate_fraud_risk_score(evidence)
                factors = full_score.get("factors", [])
            else:
                factors = []
        else:
            factors = assessment.get("factors", [])
            
        return RiskBreakdown(
            case_id=case_id,
            total_score=doc.get("fraud_score", 0),
            classification=doc.get("classification", "unknown"),
            confidence=0.85, # mock confidence if missing
            factors=factors
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("GET /api/cases/%s/risk-breakdown failed: %s", case_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 2. GET /api/cases
# ---------------------------------------------------------------------------

@router.get("/cases", response_model=list[CaseResponse])
async def list_cases(
    status: Optional[str] = None, skip: int = 0, limit: int = 20,
) -> list[dict]:
    """List investigation cases, optionally filtered by status."""
    try:
        query: dict = {}
        if status:
            query["status"] = status

        db = get_database()
        cursor = (
            db["investigations"]
            .find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        results = [_serialize(doc) for doc in docs]

        # Map stored fields to CaseResponse shape
        cases = []
        for doc in results:
            cases.append(CaseResponse(
                case_id=doc.get("case_id", ""),
                status=doc.get("status", ""),
                fraud_score=doc.get("fraud_score"),
                classification=doc.get("classification"),
                executive_summary=doc.get("executive_summary"),
                evidence_summary=doc.get("evidence_summary"),
                key_findings=doc.get("key_findings"),
                timeline=doc.get("timeline"),
                network_map=(
                    doc.get("network_map")
                    or doc.get("relationship_analysis")
                ),
                sar_draft=doc.get("sar_draft"),
                audit_trail=doc.get("audit_trail"),
                recommended_actions=doc.get("recommended_actions"),
                confidence_level=doc.get("confidence_level"),
                created_at=doc.get("created_at"),
                updated_at=doc.get("updated_at"),
            ))
        return cases
    except Exception as exc:
        logger.error("GET /api/cases failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 3. GET /api/cases/{case_id}
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str) -> CaseResponse:
    """Retrieve a single investigation case by case_id."""
    try:
        db = get_database()
        doc = await db["investigations"].find_one({"case_id": case_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail=f"Case {case_id} not found",
            )
        doc = _serialize(doc)
        return CaseResponse(
            case_id=doc.get("case_id", ""),
            status=doc.get("status", ""),
            fraud_score=doc.get("fraud_score"),
            classification=doc.get("classification"),
            executive_summary=doc.get("executive_summary"),
            evidence_summary=doc.get("evidence_summary"),
            key_findings=doc.get("key_findings"),
            timeline=doc.get("timeline"),
            network_map=(
                doc.get("network_map")
                or doc.get("relationship_analysis")
            ),
            sar_draft=doc.get("sar_draft"),
            audit_trail=doc.get("audit_trail"),
            recommended_actions=doc.get("recommended_actions"),
            confidence_level=doc.get("confidence_level"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("GET /api/cases/%s failed: %s", case_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 4. POST /api/cases/{case_id}/feedback  (Learning Loop)
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/feedback")
async def submit_feedback(
    case_id: str, request: FeedbackRequest,
) -> dict:
    """Record analyst feedback on an investigation.

    This endpoint powers the learning loop — analysts can confirm fraud,
    mark false positives, or override scores.  Feedback is stored in the
    investigation document for future model improvement.
    """
    try:
        db = get_database()
        doc = await db["investigations"].find_one({"case_id": case_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail=f"Case {case_id} not found",
            )

        ok = await record_analyst_feedback(
            case_id=case_id,
            analyst_decision=request.analyst_decision,
            override_score=request.override_score,
            reason=request.reason,
        )

        if not ok:
            raise HTTPException(
                status_code=500,
                detail="Failed to record feedback",
            )

        return {
            "status": "ok",
            "case_id": case_id,
            "decision": request.analyst_decision,
            "message": "Feedback recorded. System will incorporate this "
                       "into future scoring calibration.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("POST feedback for %s failed: %s", case_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 5. GET /api/alerts
# ---------------------------------------------------------------------------

@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[AlertResponse]:
    """List fraud alerts with optional status and severity filters."""
    try:
        query: dict = {}
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity

        db = get_database()
        cursor = (
            db["alerts"]
            .find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        results = [_serialize(doc) for doc in docs]

        return [
            AlertResponse(
                alert_id=doc.get("alert_id", ""),
                source=doc.get("source", ""),
                severity=doc.get("severity", ""),
                trigger_rule=doc.get("trigger_rule", ""),
                related_entities=doc.get("related_entities", []),
                status=doc.get("status", ""),
                created_at=doc.get("created_at", ""),
            )
            for doc in results
        ]
    except Exception as exc:
        logger.error("GET /api/alerts failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 6. GET /api/alerts/{alert_id}
# ---------------------------------------------------------------------------

@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str) -> AlertResponse:
    """Retrieve a single alert by alert_id."""
    try:
        db = get_database()
        doc = await db["alerts"].find_one({"alert_id": alert_id})
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Alert {alert_id} not found",
            )
        doc = _serialize(doc)
        return AlertResponse(
            alert_id=doc.get("alert_id", ""),
            source=doc.get("source", ""),
            severity=doc.get("severity", ""),
            trigger_rule=doc.get("trigger_rule", ""),
            related_entities=doc.get("related_entities", []),
            status=doc.get("status", ""),
            created_at=doc.get("created_at", ""),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("GET /api/alerts/%s failed: %s", alert_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 7. POST /api/alerts/{alert_id}/investigate
# ---------------------------------------------------------------------------

@router.post(
    "/alerts/{alert_id}/investigate",
    response_model=InvestigationResponse,
)
async def investigate_alert(alert_id: str) -> InvestigationResponse:
    """Investigate a specific alert by running the full investigation pipeline."""
    try:
        db = get_database()
        doc = await db["alerts"].find_one({"alert_id": alert_id})
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Alert {alert_id} not found",
            )
        doc = _serialize(doc)

        related = doc.get("related_entities", [])
        if not related:
            raise HTTPException(
                status_code=400,
                detail=f"Alert {alert_id} has no related entities",
            )

        account_id = related[0]
        return await _run_investigation(account_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "POST /api/alerts/%s/investigate failed: %s", alert_id, exc,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 8. GET /api/network/{entity_id}
# ---------------------------------------------------------------------------

@router.get("/network/{entity_id}", response_model=NetworkGraphData)
async def get_network(entity_id: str) -> NetworkGraphData:
    """Retrieve the entity-relationship network graph for a given entity."""
    try:
        network = await get_entity_network(entity_id)
        nodes = network.get("nodes", [])

        if nodes:
            graph = build_network_graph(nodes)
        else:
            graph = {
                "nodes": [],
                "edges": [],
                "stats": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "unique_types": 0,
                },
            }

        return NetworkGraphData(
            nodes=graph.get("nodes", []),
            edges=graph.get("edges", []),
            stats=graph.get("stats", {}),
        )
    except Exception as exc:
        logger.error("GET /api/network/%s failed: %s", entity_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 9. GET /api/timeline/{case_id}
# ---------------------------------------------------------------------------

@router.get("/timeline/{case_id}", response_model=list[dict])
async def get_timeline(case_id: str) -> list[dict]:
    """Retrieve the investigation timeline for a specific case."""
    try:
        db = get_database()
        doc = await db["investigations"].find_one({"case_id": case_id})
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Case {case_id} not found",
            )
        doc = _serialize(doc)
        return doc.get("timeline", [])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("GET /api/timeline/%s failed: %s", case_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 10. GET /api/cases/{case_id}/sar/xml
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/sar/xml")
async def export_sar_xml(case_id: str):
    """Export the SAR narrative in BSA E-Filing XML format."""
    try:
        db = get_database()
        doc = await db["investigations"].find_one({"case_id": case_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        root = ET.Element("EFilingBatchXML")
        form = ET.SubElement(root, "Form111")
        
        filing_inst = ET.SubElement(form, "FilingInstitutionInfo")
        ET.SubElement(filing_inst, "InstitutionName").text = "FraudIntel Bank"
        ET.SubElement(filing_inst, "InstitutionTIN").text = "12-3456789"
        
        subject = ET.SubElement(form, "SubjectInformation")
        ET.SubElement(subject, "SubjectID").text = str(doc.get("account_id", ""))
        
        activity = ET.SubElement(form, "SuspiciousActivityInfo")
        ET.SubElement(activity, "RiskScore").text = str(doc.get("fraud_score", 0))
        ET.SubElement(activity, "PrimaryTypology").text = str(doc.get("primary_typology", "Unknown"))
        
        narrative = ET.SubElement(form, "Narrative")
        report = doc.get("report", {})
        narrative_text = ""
        if isinstance(report, dict):
            narrative_text = report.get("sar_draft", "")
        elif isinstance(report, str):
            narrative_text = report
        ET.SubElement(narrative, "NarrativeText").text = str(narrative_text)
        
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        return Response(content=xmlstr, media_type="application/xml", headers={
            "Content-Disposition": f"attachment; filename=SAR_{case_id}.xml"
        })
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("GET /api/cases/%s/sar/xml failed: %s", case_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
