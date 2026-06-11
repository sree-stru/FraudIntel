"""Investigation utility functions for FraudIntel ADK agents.

Provides timeline construction, network-graph building, FinCEN SAR
narrative generation, case-ID minting, and final report formatting.
All functions are pure computation with no database side-effects.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ts(value: Any) -> str:
    """Normalise a timestamp value to an ISO-8601 string."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return ""


# ---------------------------------------------------------------------------
# 1. build_investigation_timeline
# ---------------------------------------------------------------------------

def build_investigation_timeline(
    transactions: object,
    alerts: object,
    logins: object = None,
) -> object:
    """Build a unified, chronological investigation timeline from multiple data sources.

    Merges transactions, alerts, and login events into a single sorted
    timeline with severity classifications.  This is the primary tool
    for reconstructing the sequence of events during an investigation.

    Args:
        transactions: List of transaction dicts (must contain
            ``timestamp``, ``type``, ``amount``, ``direction``).
        alerts: List of alert dicts (must contain ``created_at``,
            ``trigger_rule``, ``severity``).
        logins: Optional list of login event dicts (must contain
            ``timestamp``).

    Returns:
        A list of timeline-entry dicts sorted by timestamp ascending.
        Each entry has ``timestamp``, ``event_type``, ``description``,
        ``severity``, and ``details``.
    """
    try:
        entries: list[dict] = []

        # --- Transactions ---
        for txn in transactions or []:
            amount = txn.get("amount", 0) or 0
            txn_type = txn.get("type", "unknown")
            direction = txn.get("direction", "unknown")

            if amount > 10000:
                severity = "critical"
            elif amount > 5000:
                severity = "warning"
            else:
                severity = "info"

            entries.append({
                "timestamp": _ts(txn.get("timestamp")),
                "event_type": "transaction",
                "description": f"{txn_type} of ${amount:,.2f} ({direction})",
                "severity": severity,
                "details": {
                    "transaction_id": txn.get("transaction_id"),
                    "account_id": txn.get("account_id"),
                    "amount": amount,
                    "type": txn_type,
                    "direction": direction,
                    "merchant_category": txn.get("merchant_category"),
                    "ip_address": txn.get("ip_address"),
                    "device_fingerprint": txn.get("device_fingerprint"),
                },
            })

        # --- Alerts ---
        for alert in alerts or []:
            trigger = alert.get("trigger_rule", "unknown")
            sev = alert.get("severity", "info")

            entries.append({
                "timestamp": _ts(alert.get("created_at")),
                "event_type": "alert",
                "description": f"Alert: {trigger} - {sev}",
                "severity": sev,
                "details": {
                    "alert_id": alert.get("alert_id"),
                    "source": alert.get("source"),
                    "trigger_rule": trigger,
                    "related_entities": alert.get("related_entities", []),
                    "status": alert.get("status"),
                },
            })

        # --- Logins ---
        for login in logins or []:
            entries.append({
                "timestamp": _ts(login.get("timestamp")),
                "event_type": "login",
                "description": (
                    f"Login from {login.get('ip_address', 'unknown IP')} "
                    f"via {login.get('device', 'unknown device')}"
                ),
                "severity": "info",
                "details": {
                    "ip_address": login.get("ip_address"),
                    "device": login.get("device"),
                    "location": login.get("location"),
                    "success": login.get("success", True),
                },
            })

        # Sort chronologically
        entries.sort(key=lambda e: e.get("timestamp", ""))

        return entries

    except Exception as exc:
        logger.error("build_investigation_timeline failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# 2. build_network_graph
# ---------------------------------------------------------------------------

def build_network_graph(relationships: object) -> object:
    """Transform raw entity relationship data into a graph structure suitable
    for D3.js force-directed visualization.

    Creates deduplicated nodes and directional edges with visual
    properties.  Use this to power network-graph rendering in the
    investigation dashboard.

    Args:
        relationships: List of entity-relationship dicts, each
            containing ``entity_id``, ``entity_type``,
            ``linked_entity_id``, ``linked_entity_type``,
            ``relationship_type``, and ``strength``.

    Returns:
        A dict with ``nodes`` (list), ``edges`` (list), and ``stats``
        (total_nodes, total_edges, unique_types).
    """
    try:
        node_map: dict[str, dict] = {}
        edges: list[dict] = []

        for rel in relationships or []:
            # Source node
            eid = rel.get("entity_id", "")
            etype = rel.get("entity_type", "unknown")
            if eid and eid not in node_map:
                node_map[eid] = {
                    "id": eid,
                    "type": etype,
                    "label": eid,
                    "risk_level": "clean",
                }

            # Target node
            lid = rel.get("linked_entity_id", "")
            ltype = rel.get("linked_entity_type", "unknown")
            if lid and lid not in node_map:
                node_map[lid] = {
                    "id": lid,
                    "type": ltype,
                    "label": lid,
                    "risk_level": "clean",
                }

            # Edge
            if eid and lid:
                edges.append({
                    "source": eid,
                    "target": lid,
                    "relationship": rel.get("relationship_type", "related"),
                    "strength": rel.get("strength", 0.5),
                })

        nodes = list(node_map.values())
        
        # --- Graph Analytics: Connected Components & Degree Centrality ---
        adj = {n["id"]: [] for n in nodes}
        for e in edges:
            adj[e["source"]].append(e["target"])
            adj[e["target"]].append(e["source"])
            
        visited = set()
        components = []
        for n in nodes:
            if n["id"] not in visited:
                comp = []
                queue = [n["id"]]
                visited.add(n["id"])
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)
                
        for i, comp in enumerate(components):
            for nid in comp:
                node_map[nid]["community"] = i
                
        for n in nodes:
            n["degree"] = len(adj[n["id"]])
        # -----------------------------------------------------------------

        unique_types = {n["type"] for n in nodes}

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "unique_types": len(unique_types),
            },
        }

    except Exception as exc:
        logger.error("build_network_graph failed: %s", exc)
        return {"nodes": [], "edges": [], "stats": {"total_nodes": 0, "total_edges": 0, "unique_types": 0}}


# ---------------------------------------------------------------------------
# 3. generate_sar_narrative
# ---------------------------------------------------------------------------

def generate_sar_narrative(investigation: object) -> str:
    """Generate a FinCEN-compliant Suspicious Activity Report (SAR) draft
    narrative from investigation findings.

    **This is a DRAFT** that requires human analyst review and approval
    before submission to FinCEN.  It follows the standard five-paragraph
    SAR narrative structure used by US financial institutions.

    Args:
        investigation: A dict containing investigation data such as
            ``case_id``, ``fraud_type``, ``related_accounts``,
            ``evidence``, ``fraud_score``, ``timeline``,
            ``network_map``, and ``status``.

    Returns:
        A formatted multi-paragraph SAR narrative string.
    """
    try:
        case_id = investigation.get("case_id", "UNKNOWN")
        fraud_type = investigation.get("fraud_type", "suspicious financial activity")
        accounts = investigation.get("related_accounts", [])
        evidence = investigation.get("evidence", {})
        score = investigation.get("fraud_score", 0)
        timeline = investigation.get("timeline", [])
        network = investigation.get("network_map", {})
        status = investigation.get("status", "under_investigation")
        title = investigation.get("title", "Fraud Investigation")
        created_at = investigation.get("created_at", datetime.now(timezone.utc).isoformat())

        customer = investigation.get("customer", {})
        transactions = investigation.get("transactions", [])
        total_amount = sum((t.get("amount", 0) for t in transactions if isinstance(t.get("amount"), (int, float))))

        # Subject line
        subject_name = customer.get("name", "Unknown Subject")
        subject = f"{subject_name} ({', '.join(accounts[:3]) if accounts else investigation.get('account_id', 'unknown account')})"

        fincen_header = (
            "FINCEN REPORT DATA (PARTS I, II & III)\n"
            f"Subject Name: {subject_name}\n"
            f"Subject IDs: {subject}\n"
            f"Typology/Category: {fraud_type.upper()}\n"
            f"Total Suspicious Amount: ${total_amount:,.2f}\n"
            "---\n"
        )

        # Paragraph 1 — Opening
        p1 = (
            f"This SAR is being filed to report suspected {fraud_type} "
            f"involving {subject}. The activity was identified on "
            f"{created_at[:10]} through automated transaction monitoring "
            f"and AI-assisted investigation (Case ID: {case_id})."
        )

        # Paragraph 2 — Activity Summary
        txns_analyzed = evidence.get("transactions_analyzed", 0)
        accts_reviewed = evidence.get("accounts_reviewed", 0)
        p2 = (
            f"Investigation '{title}' reviewed {accts_reviewed} account(s) "
            f"and analyzed {txns_analyzed} transaction(s). "
        )
        if timeline:
            first_event = timeline[0] if isinstance(timeline[0], dict) else {}
            last_event = timeline[-1] if isinstance(timeline[-1], dict) else {}
            first_ts = first_event.get("timestamp", first_event.get("event", ""))[:10]
            last_ts = last_event.get("timestamp", last_event.get("event", ""))[:10]
            p2 += (
                f"The suspicious activity spans from approximately "
                f"{first_ts} to {last_ts}. "
            )
        else:
            p2 += "Timeline details are pending further analysis. "

        # Paragraph 3 — Indicators
        indicators = investigation.get("indicators", [])
        sar_draft = investigation.get("sar_draft")
        if indicators:
            indicator_list = "; ".join(indicators[:5])
            p3 = (
                f"The following fraud indicators were detected: "
                f"{indicator_list}."
            )
        elif sar_draft and isinstance(sar_draft, str):
            p3 = sar_draft
        else:
            p3 = (
                f"Multiple indicators consistent with {fraud_type} "
                f"were identified during the investigation."
            )

        # Paragraph 4 — Network
        nodes = network.get("nodes", [])
        edges = network.get("edges", [])
        if nodes:
            node_count = len(nodes)
            edge_count = len(edges)
            entity_types = {n.get("type", "unknown") for n in nodes if isinstance(n, dict)}
            type_list = ", ".join(sorted(entity_types))
            p4 = (
                f"Network analysis identified {node_count} connected "
                f"entities across {edge_count} relationships, involving "
                f"the following entity types: {type_list}. "
                f"These connections may indicate coordinated activity "
                f"warranting further scrutiny."
            )
        else:
            p4 = (
                "Network analysis did not reveal additional connected "
                "entities beyond the primary subject(s)."
            )

        # Paragraph 5 — Conclusion
        if score >= 76:
            risk_label = "critical"
            action = "immediate account freeze and escalation to law enforcement"
        elif score >= 51:
            risk_label = "high"
            action = "escalation to senior compliance and potential SAR filing"
        elif score >= 26:
            risk_label = "medium"
            action = "enhanced monitoring and periodic review"
        else:
            risk_label = "low"
            action = "continued monitoring with standard controls"

        p5 = (
            f"Based on the investigation, the activity presents a "
            f"{risk_label} risk with a composite score of {score}/100. "
            f"Recommended action: {action}."
        )

        # Footer
        footer = (
            "---\n"
            "STATUS: DRAFT — Requires human analyst review before "
            "submission to FinCEN.\n"
            "Generated by FraudIntel AI Investigation Agent."
        )

        narrative = "\n\n".join([fincen_header.strip(), p1, p2, p3, p4, p5, footer])
        return narrative

    except Exception as exc:
        logger.error("generate_sar_narrative failed: %s", exc)
        return (
            "SAR NARRATIVE GENERATION FAILED\n\n"
            "Unable to generate SAR narrative due to an internal error. "
            "Manual narrative preparation is required.\n\n"
            "---\n"
            "STATUS: ERROR — Requires manual preparation.\n"
            "Generated by FraudIntel AI Investigation Agent."
        )


# ---------------------------------------------------------------------------
# 4. generate_case_id
# ---------------------------------------------------------------------------

def generate_case_id() -> str:
    """Generate a unique investigation case ID in the format ``INV-2026-XXXX``.

    Uses a UUID suffix to guarantee uniqueness.

    Returns:
        A case ID string such as ``"INV-2026-A1B2C3D4"``.
    """
    import uuid
    try:
        return f"INV-2026-{uuid.uuid4().hex[:8].upper()}"
    except Exception as exc:
        logger.error("generate_case_id failed: %s", exc)
        return f"INV-2026-0000"


# ---------------------------------------------------------------------------
# 5. format_investigation_report
# ---------------------------------------------------------------------------

def format_investigation_report(
    case_id: str,
    evidence: object,
    risk_score: object,
    timeline: object,
    network: object,
    sar_narrative: str | None = None,
) -> object:
    """Compile all investigation components into a structured investigation
    report document.

    Returns a complete report ready for storage in MongoDB and display
    on the investigation dashboard.

    Args:
        case_id: The investigation case identifier.
        evidence: Collected evidence dict (transactions, customer data, etc.).
        risk_score: The dict returned by
            :func:`~agent.tools.scoring_tools.calculate_fraud_risk_score`.
        timeline: The list returned by :func:`build_investigation_timeline`.
        network: The dict returned by :func:`build_network_graph`.
        sar_narrative: Optional SAR draft string from
            :func:`generate_sar_narrative`.

    Returns:
        A comprehensive report dict with executive summary, key findings,
        risk assessment, timeline, network analysis, and optional SAR.
    """
    try:
        total_score = risk_score.get("total_score", 0)
        classification = risk_score.get("classification", "unknown")
        confidence = risk_score.get("confidence", 0.0)
        action = risk_score.get("recommended_action", "investigate")
        factors = risk_score.get("factors", [])

        # Executive summary
        class_display = classification.replace("_", " ")
        executive_summary = (
            f"Investigation {case_id} concluded with a {class_display} "
            f"determination and a composite fraud score of {total_score}/100. "
            f"The analysis evaluated {len(factors)} risk factors with "
            f"{confidence * 100:.0f}% confidence. "
            f"Recommended action: {action}."
        )

        # Key findings — triggered positive factors
        key_findings: list[str] = []
        for f in factors:
            if f.get("triggered") and f.get("points", 0) > 0:
                key_findings.append(
                    f"{f['name'].replace('_', ' ').title()}: {f.get('reason', '')}"
                )

        # Fraud indicators — same as key findings for report purposes
        fraud_indicators: list[str] = [
            f.get("reason", f.get("name", ""))
            for f in factors
            if f.get("triggered") and f.get("points", 0) > 0
        ]

        # Confidence label
        if confidence > 0.8:
            confidence_level = "High"
        elif confidence > 0.6:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"

        report: dict = {
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "pending_review",
            "executive_summary": executive_summary,
            "evidence_collected": evidence,
            "key_findings": key_findings,
            "fraud_indicators": fraud_indicators,
            "relationship_analysis": network,
            "timeline": timeline,
            "risk_assessment": risk_score,
            "recommended_actions": [action],
            "confidence_level": confidence_level,
            "sar_draft": sar_narrative,
            "fraud_score": total_score,
            "classification": classification,
        }

        return report

    except Exception as exc:
        logger.error("format_investigation_report failed: %s", exc)
        return {
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "executive_summary": "Report generation failed due to an internal error.",
            "evidence_collected": evidence,
            "key_findings": [],
            "fraud_indicators": [],
            "relationship_analysis": {},
            "timeline": [],
            "risk_assessment": {},
            "recommended_actions": ["manual_review"],
            "confidence_level": "Low",
            "sar_draft": None,
            "fraud_score": 0,
            "classification": "unknown",
        }
