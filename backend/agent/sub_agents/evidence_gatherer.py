"""Evidence Gatherer Sub-Agent — Collects all relevant investigation data from MongoDB."""

from google.adk.agents import LlmAgent
from agent.tools.mongodb_tools import (
    get_account_transactions,
    get_customer_profile,
    get_entity_network,
    get_transaction_velocity,
    get_linked_accounts_by_device,
    get_linked_accounts_by_ip,
    search_fraud_history,
    get_alert_details,
)
from agent.prompts.system_prompts import EVIDENCE_GATHERER_PROMPT
from agent.config import settings

evidence_gatherer_agent = LlmAgent(
    name="evidence_gatherer",
    model=settings.gemini_model,
    instruction=EVIDENCE_GATHERER_PROMPT,
    description="Collects and organizes evidence for fraud investigations by querying the MongoDB database for transactions, customer profiles, device fingerprints, and entity networks.",
    tools=[
        get_account_transactions,
        get_customer_profile,
        get_entity_network,
        get_transaction_velocity,
        get_linked_accounts_by_device,
        get_linked_accounts_by_ip,
        search_fraud_history,
        get_alert_details,
    ],
)
