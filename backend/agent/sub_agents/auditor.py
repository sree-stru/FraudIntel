"""Auditor Sub-Agent — Reviews investigations for contradictions and missing evidence."""

from google.adk.agents import LlmAgent
from agent.tools.mongodb_tools import (
    get_account_transactions,
    get_customer_profile,
    search_fraud_history,
)
from agent.prompts.system_prompts import AUDITOR_PROMPT
from agent.config import settings

auditor_agent = LlmAgent(
    name="auditor",
    model=settings.gemini_model,
    instruction=AUDITOR_PROMPT,
    description=(
        "Challenges investigation findings, searches for contradictory "
        "evidence, identifies logical gaps, and provides an independent "
        "confidence rating of the investigation."
    ),
    tools=[
        get_account_transactions,
        get_customer_profile,
        search_fraud_history,
    ],
)
