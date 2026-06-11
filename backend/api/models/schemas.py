"""Pydantic v2 data models for the FraudIntel REST API."""

from typing import Optional

from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    """Payload for initiating a new fraud investigation."""

    alert_id: Optional[str] = None
    account_id: Optional[str] = None
    query: str = Field(
        ...,
        description=(
            "Natural language investigation request or account ID to investigate"
        ),
    )


class BatchInvestigationRequest(BaseModel):
    """Payload for initiating multiple fraud investigations in batch."""
    queries: list[str] = Field(
        ...,
        description="A list of investigation queries or account IDs"
    )


class MissionRequest(BaseModel):
    """Payload for starting a Chief Investigator mission."""
    command: str = Field(..., description="Natural language mission command")


class MissionEvent(BaseModel):
    """SSE event yielded during a mission."""
    status: str
    agent: str
    message: str
    timestamp: str
    result: Optional[dict] = None


class InvestigationResponse(BaseModel):
    """Summary returned after an investigation is executed."""

    case_id: str
    status: str
    fraud_score: Optional[int] = None
    classification: Optional[str] = None
    summary: str
    timestamp: str
    network_size: Optional[int] = None
    sar_required: Optional[bool] = None


class FeedbackRequest(BaseModel):
    """Analyst feedback on an investigation for the learning loop."""

    analyst_decision: str = Field(
        ...,
        description=(
            "The analyst's final decision: confirmed_fraud, "
            "false_positive, needs_more_info, or escalated"
        ),
    )
    override_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Optional corrected fraud score (0-100)",
    )
    reason: str = Field(
        "",
        description="Free-text justification for the decision",
    )


class AlertResponse(BaseModel):
    """Representation of a single fraud alert."""

    alert_id: str
    source: str
    severity: str
    trigger_rule: str
    related_entities: list[str] = []
    status: str
    created_at: str


class CaseResponse(BaseModel):
    """Full investigation case with all associated data."""

    case_id: str
    status: str
    fraud_score: Optional[int] = None
    classification: Optional[str] = None
    executive_summary: Optional[str] = None
    evidence_summary: Optional[str] = None
    key_findings: Optional[list[str]] = None
    timeline: Optional[list[dict]] = None
    network_map: Optional[dict] = None
    sar_draft: Optional[str] = None
    audit_trail: Optional[list[dict]] = None
    recommended_actions: Optional[list[str]] = None
    confidence_level: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DashboardStats(BaseModel):
    """Aggregate statistics for the investigation dashboard."""

    total_cases: int = 0
    active_investigations: int = 0
    pending_alerts: int = 0
    high_risk_cases: int = 0
    resolved_cases: int = 0
    avg_fraud_score: float = 0.0
    cases_today: int = 0


class NetworkGraphData(BaseModel):
    """Entity-relationship graph data for D3.js visualization."""

    nodes: list[dict] = []
    edges: list[dict] = []
    stats: dict = {}


class PriorityAction(BaseModel):
    """A recommended priority action across cases."""
    case_id: str
    action_type: str
    description: str
    impact: str
    timestamp: str


class RiskBreakdown(BaseModel):
    """Detailed explanation of a risk score."""
    case_id: str
    total_score: int
    classification: str
    confidence: float
    factors: list[dict] = []


class ThreatPattern(BaseModel):
    """An emerging threat campaign detected across cases."""
    campaign_name: str
    confidence: float
    description: str
    related_cases: int
    shared_indicators: list[str] = []
    recommended_response: str


class HealthResponse(BaseModel):
    """System health-check response."""

    status: str
    mongodb_connected: bool
    collections: dict = {}
    version: str = "1.0.0"
