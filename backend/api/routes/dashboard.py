"""Dashboard-specific API routes for FraudIntel.

Provides aggregate statistics and recent-activity feeds for the
investigation dashboard UI.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from agent.database import get_database
from agent.tools.mongodb_tools import _serialize
from api.models.schemas import DashboardStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ---------------------------------------------------------------------------
# A) GET /api/dashboard/stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats() -> DashboardStats:
    """Return aggregate investigation and alert statistics for the dashboard."""
    try:
        db = get_database()
        inv = db["investigations"]
        alerts = db["alerts"]

        total_cases = await inv.count_documents({})
        active_investigations = await inv.count_documents({"status": "under_investigation"})
        pending_alerts = await alerts.count_documents({"status": "new"})
        high_risk_cases = await inv.count_documents({"fraud_score": {"$gte": 70}})
        resolved_cases = await inv.count_documents({"status": "resolved"})

        # Average fraud score
        avg_pipeline = [
            {"$match": {"fraud_score": {"$exists": True}}},
            {"$group": {"_id": None, "avg": {"$avg": "$fraud_score"}}},
        ]
        avg_result = await inv.aggregate(avg_pipeline).to_list(length=None)
        avg_fraud_score = round(avg_result[0]["avg"], 1) if avg_result else 0.0

        # Cases created today
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0,
        ).isoformat()
        cases_today = await inv.count_documents({"created_at": {"$gte": today_start}})

        return DashboardStats(
            total_cases=total_cases,
            active_investigations=active_investigations,
            pending_alerts=pending_alerts,
            high_risk_cases=high_risk_cases,
            resolved_cases=resolved_cases,
            avg_fraud_score=avg_fraud_score,
            cases_today=cases_today,
        )
    except Exception as exc:
        logger.error("GET /api/dashboard/stats failed: %s", exc)
        return DashboardStats()


# ---------------------------------------------------------------------------
# B) GET /api/dashboard/recent-activity
# ---------------------------------------------------------------------------

@router.get("/recent-activity", response_model=list[dict])
async def get_recent_activity() -> list[dict]:
    """Return the 20 most recent alerts and investigation updates merged chronologically."""
    try:
        activity: list[dict] = []
        db = get_database()

        # Recent alerts
        alert_cursor = (
            db["alerts"]
            .find()
            .sort("created_at", -1)
            .limit(10)
        )
        alert_docs = await alert_cursor.to_list(length=10)
        for doc in alert_docs:
            doc = _serialize(doc)
            activity.append({
                "type": "alert",
                "timestamp": doc.get("created_at", ""),
                "description": (
                    f"{doc.get('severity', 'unknown').upper()} alert: "
                    f"{doc.get('trigger_rule', 'unknown')} — "
                    f"{', '.join(doc.get('related_entities', []))}"
                ),
                "severity": doc.get("severity", "info"),
                "id": doc.get("alert_id", ""),
            })

        # Recent investigation updates
        inv_cursor = (
            db["investigations"]
            .find()
            .sort("updated_at", -1)
            .limit(10)
        )
        inv_docs = await inv_cursor.to_list(length=10)
        for doc in inv_docs:
            doc = _serialize(doc)
            score = doc.get("fraud_score", 0)
            if score is None:
                score = 0

            if score >= 76:
                severity = "critical"
            elif score >= 51:
                severity = "high"
            elif score >= 26:
                severity = "medium"
            else:
                severity = "low"

            activity.append({
                "type": "investigation",
                "timestamp": doc.get("updated_at", doc.get("created_at", "")),
                "description": (
                    f"Case {doc.get('case_id', 'N/A')}: "
                    f"{doc.get('title', doc.get('status', 'unknown'))} "
                    f"(score: {score})"
                ),
                "severity": severity,
                "id": doc.get("case_id", ""),
            })

        # Sort merged list by timestamp desc and return top 20
        activity.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
        return activity[:20]

    except Exception as exc:
        logger.error("GET /api/dashboard/recent-activity failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
