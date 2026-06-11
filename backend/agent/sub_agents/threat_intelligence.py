"""Threat Intelligence Sub-Agent — Detects emerging fraud campaigns across cases."""

from google.adk.agents import LlmAgent
from agent.tools.mongodb_tools import (
    get_account_transactions,
    get_entity_network,
    search_fraud_history,
)
from agent.prompts.system_prompts import THREAT_INTELLIGENCE_PROMPT
from agent.config import settings

threat_intelligence_agent = LlmAgent(
    name="threat_intelligence",
    model=settings.gemini_model,
    instruction=THREAT_INTELLIGENCE_PROMPT,
    description=(
        "Analyzes investigation results to detect emerging fraud campaigns "
        "by cross-referencing patterns across recent cases, identifying shared "
        "merchants, devices, IPs, and transaction patterns."
    ),
    tools=[
        get_account_transactions,
        get_entity_network,
        search_fraud_history,
    ],
)
