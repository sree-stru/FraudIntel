"""Report Generator Sub-Agent — Compiles final intelligence reports."""

from google.adk.agents import LlmAgent
from agent.tools.investigation_tools import (
    build_investigation_timeline,
    build_network_graph,
    format_investigation_report,
    generate_case_id,
)
from agent.tools.mongodb_tools import save_investigation, append_audit_trail
from agent.prompts.system_prompts import REPORT_GENERATOR_PROMPT
from agent.config import settings

report_generator_agent = LlmAgent(
    name="report_generator",
    model=settings.gemini_model,
    instruction=REPORT_GENERATOR_PROMPT,
    description="Compiles all investigation findings into a final, structured JSON report including timelines, network graphs, and risk assessments.",
    tools=[
        build_investigation_timeline,
        build_network_graph,
        format_investigation_report,
        generate_case_id,
        save_investigation,
        append_audit_trail,
    ],
)
