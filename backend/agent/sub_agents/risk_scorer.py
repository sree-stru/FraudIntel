"""Risk Scorer Sub-Agent — Analyzes evidence and calculates composite fraud risk scores."""

from google.adk.agents import LlmAgent
from agent.tools.scoring_tools import (
    calculate_fraud_risk_score,
    classify_fraud_typology,
    generate_risk_summary,
)
from agent.tools.mongodb_tools import search_similar_fraud_patterns
from agent.prompts.system_prompts import RISK_SCORER_PROMPT
from agent.config import settings

risk_scorer_agent = LlmAgent(
    name="risk_scorer",
    model=settings.gemini_model,
    instruction=RISK_SCORER_PROMPT,
    description="Analyzes gathered evidence and calculates a detailed fraud risk score (0-100) using deterministic scoring rules and identifies the specific fraud typology.",
    tools=[
        calculate_fraud_risk_score,
        classify_fraud_typology,
        search_similar_fraud_patterns,
        generate_risk_summary,
    ],
)
