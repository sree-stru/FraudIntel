"""Compliance Sub-Agent — Evaluates regulatory requirements and drafts SARs."""

from google.adk.agents import LlmAgent
from agent.tools.investigation_tools import generate_sar_narrative
from agent.tools.mongodb_tools import save_investigation, append_audit_trail
from agent.prompts.system_prompts import COMPLIANCE_AGENT_PROMPT
from agent.config import settings

compliance_agent = LlmAgent(
    name="compliance",
    model=settings.gemini_model,
    instruction=COMPLIANCE_AGENT_PROMPT,
    description="Evaluates investigation findings against BSA/AML and FinCEN regulatory requirements, and automatically generates Suspicious Activity Report (SAR) drafts when thresholds are met.",
    tools=[
        generate_sar_narrative,
        save_investigation,
        append_audit_trail,
    ],
)
