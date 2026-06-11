"""FraudIntel Orchestrator — Manages the multi-agent investigation lifecycle.

Uses Google ADK to coordinate five specialized sub-agents
(Evidence Gatherer, Risk Scorer, Auditor, Compliance, Report Generator)
through a Gemini-powered orchestrator agent.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
import re

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.config import settings
from agent.prompts.system_prompts import ORCHESTRATOR_PROMPT
from agent.sub_agents.evidence_gatherer import evidence_gatherer_agent
from agent.sub_agents.risk_scorer import risk_scorer_agent
from agent.sub_agents.auditor import auditor_agent
from agent.sub_agents.compliance import compliance_agent
from agent.sub_agents.report_generator import report_generator_agent
from agent.sub_agents.threat_intelligence import threat_intelligence_agent

logger = logging.getLogger(__name__)

from agent.database import get_database

# ---------------------------------------------------------------------------
# Persistent Session service (shared across sub-agent delegations within a run)
# ---------------------------------------------------------------------------

class MongoSessionService(InMemorySessionService):
    """ADK Session service that persists to MongoDB."""
    async def create_session(self, *args, **kwargs):
        session = await super().create_session(*args, **kwargs)
        try:
            db = get_database()
            doc = session.model_dump()
            doc["_id"] = doc["id"]
            await db["adk_sessions"].insert_one(doc)
        except Exception as e:
            logger.warning("Failed to persist session creation: %s", e)
        return session

    async def append_event(self, session, event):
        result = await super().append_event(session, event)
        try:
            db = get_database()
            await db["adk_sessions"].update_one(
                {"_id": session.id},
                {"$set": session.model_dump()},
                upsert=True
            )
        except Exception as e:
            logger.warning("Failed to persist session event: %s", e)
        return result

_session_service = MongoSessionService()


# ---------------------------------------------------------------------------
# Async delegation tools for the orchestrator agent
# ---------------------------------------------------------------------------

async def async_delegate_to_evidence_gatherer(prompt: str) -> str:
    """Delegate a task to the Evidence Gatherer agent.

    The Evidence Gatherer collects all relevant investigation data from
    the MongoDB database, including transactions, customer profiles,
    device fingerprints, and entity networks.
    """
    return await _run_sub_agent(evidence_gatherer_agent, prompt)


async def async_delegate_to_risk_scorer(prompt: str) -> str:
    """Delegate a task to the Risk Scorer agent.

    The Risk Scorer analyzes collected evidence and calculates a composite
    fraud risk score (0-100) using deterministic scoring rules and pattern
    matching.
    """
    return await _run_sub_agent(risk_scorer_agent, prompt)


async def async_delegate_to_auditor(prompt: str) -> str:
    """Delegate a task to the Auditor agent.

    The Auditor challenges the investigation findings, searches for
    contradictory evidence, identifies logical gaps, and provides an
    independent confidence rating.
    """
    return await _run_sub_agent(auditor_agent, prompt)


async def async_delegate_to_compliance(prompt: str) -> str:
    """Delegate a task to the Compliance agent.

    The Compliance agent evaluates findings against BSA/AML and FinCEN
    regulations, and drafts Suspicious Activity Reports (SARs) when
    warranted.
    """
    return await _run_sub_agent(compliance_agent, prompt)


async def async_delegate_to_report_generator(prompt: str) -> str:
    """Delegate a task to the Report Generator agent.

    The Report Generator compiles all investigation findings into a
    structured JSON report with timelines, network graphs, and risk
    assessments.
    """
    return await _run_sub_agent(report_generator_agent, prompt)


async def async_delegate_to_threat_intelligence(prompt: str) -> str:
    """Delegate a task to the Threat Intelligence agent.

    The Threat Intelligence agent analyzes investigation results to detect
    emerging fraud campaigns across recent cases.
    """
    return await _run_sub_agent(threat_intelligence_agent, prompt)


async def _run_sub_agent(agent: LlmAgent, prompt: str) -> str:
    """Run a sub-agent and collect its final response."""
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    user_id = "orchestrator"

    runner = Runner(
        agent=agent,
        app_name="fraudintel",
        session_service=_session_service,
    )
    session = await _session_service.create_session(
        app_name="fraudintel",
        user_id=user_id,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        if (event.is_final_response()
                and event.content
                and event.content.parts):
            for part in event.content.parts:
                if part.text:
                    final_text += part.text

    return final_text if final_text else "No response from sub-agent."


# ---------------------------------------------------------------------------
# Orchestrator Agent
# ---------------------------------------------------------------------------

fraudintel_agent = LlmAgent(
    name="orchestrator",
    model=settings.gemini_model,
    instruction=ORCHESTRATOR_PROMPT,
    description=(
        "The lead investigator that coordinates all sub-agents to "
        "complete a full fraud investigation."
    ),
    tools=[
        async_delegate_to_evidence_gatherer,
        async_delegate_to_risk_scorer,
        async_delegate_to_auditor,
        async_delegate_to_compliance,
        async_delegate_to_report_generator,
        async_delegate_to_threat_intelligence,
    ],
)


def get_agent():
    return fraudintel_agent


async def run_investigation_agent(account_id: str) -> dict:
    """Run the Multi-Agent Pipeline via the ADK Orchestrator.

    The orchestrator uses Gemini to dynamically coordinate sub-agents
    and return a structured investigation result.

    Returns:
        A dict with keys: fraud_score, classification, sar_narrative,
        executive_summary.
    """
    logger.info("🔍 Starting agent investigation for account: %s",
                account_id)

    try:
        prompt = f"""
        Please conduct a full fraud investigation for account: {account_id}.

        You must coordinate with your sub-agents in this order:
        1. Have the evidence_gatherer collect data.
        2. Have the risk_scorer analyze it.
        3. Have the auditor review it.
        4. Have the compliance agent check regulations.
        5. Have the report_generator create the final report.

        Return ONLY the final JSON payload matching this structure:
        {{
          "fraud_score": <int 0-100>,
          "classification": "<string>",
          "sar_narrative": "<string or empty>",
          "executive_summary": "<string>"
        }}
        """

        runner = Runner(
            agent=fraudintel_agent,
            app_name="fraudintel",
            session_service=_session_service,
        )
        session = await _session_service.create_session(
            app_name="fraudintel",
            user_id="api",
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        async def _consume_agent() -> str:
            text = ""
            async for event in runner.run_async(
                user_id="api",
                session_id=session.id,
                new_message=content,
            ):
                if (event.is_final_response()
                        and event.content
                        and event.content.parts):
                    for part in event.content.parts:
                        if part.text:
                            text += part.text
            return text

        try:
            final_text = await asyncio.wait_for(_consume_agent(), timeout=settings.agent_timeout_seconds)
        except asyncio.TimeoutError:
            logger.error("Agent pipeline timed out for %s", account_id)
            return {
                "fraud_score": 0,
                "classification": "error",
                "sar_narrative": "",
                "executive_summary": (
                    f"Agent pipeline timed out after {settings.agent_timeout_seconds} seconds. "
                    f"Manual investigation required."
                ),
            }

        # Try to extract JSON block if wrapped in markdown
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", final_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(1)
        else:
            # Fallback: extract everything from first { to last }
            start = final_text.find('{')
            end = final_text.rfind('}')
            if start != -1 and end != -1:
                clean_text = final_text[start:end+1]
            else:
                clean_text = final_text.strip()

        return json.loads(clean_text)

    except json.JSONDecodeError as e:
        logger.error("Agent returned non-JSON response: %s", e)
        return {
            "fraud_score": 0,
            "classification": "error",
            "sar_narrative": "",
            "executive_summary": (
                f"Agent completed but returned non-parseable response "
                f"for {account_id}. Manual investigation required."
            ),
        }
    except Exception as e:
        logger.error("Agent Pipeline Failed for %s: %s", account_id, e)
        return {
            "fraud_score": 0,
            "classification": "error",
            "sar_narrative": "",
            "executive_summary": (
                f"Multi-agent pipeline error for {account_id}: {e}. "
                f"Falling back to deterministic analysis."
            ),
        }


async def run_mission(mission_query: str):
    """Run a Chief Investigator mission and yield progress events.
    
    This is an async generator that yields status updates as the 
    orchestrator works through the mission and delegates to sub-agents.
    """
    logger.info("🚀 Starting mission: %s", mission_query)
    
    # 1. Initial acknowledgment
    yield {
        "status": "in_progress",
        "agent": "orchestrator",
        "message": f"Mission received. Formulating investigation plan.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        runner = Runner(
            agent=fraudintel_agent,
            app_name="fraudintel",
            session_service=_session_service,
        )
        
        session = await _session_service.create_session(
            app_name="fraudintel",
            user_id="mission_api",
        )
            # await _session_service.append_event(session, types.Content(role="system", parts=[types.Part(text="Session initialized.")]))
        
        # We need a prompt that forces JSON output + step-by-step 
        prompt = f"""
        Execute this mission: "{mission_query}"
        
        You must coordinate with your sub-agents. 
        As you work, output your progress.
        
        Return ONLY a final JSON payload matching this structure:
        {{
          "response_message": "Your conversational reply to the user's mission or question",
          "target_account": "<account_id if identified, else null>",
          "case_id": "<case_id if generated by report_generator, otherwise null>",
          "fraud_score": <int 0-100 or null>,
          "classification": "<string or null>",
          "executive_summary": "<string or null>",
          "recommended_actions": ["<action 1>", "<action 2>"],
          "threat_campaign_detected": <bool or null>
        }}
        """

        content = types.Content(role="user", parts=[types.Part(text=prompt)])
        
        # To simulate real-time streaming, we will yield intermediate steps
        # This uses the orchestrator's event stream
        async for event in runner.run_async(
            user_id="mission_api",
            session_id=session.id,
            new_message=content,
        ):
            # Intercept tool calls to yield progress events
            model_calls = getattr(event, "model_calls", None)
            if model_calls:
                for call in model_calls:
                    if hasattr(call, 'function_call') and call.function_call:
                        func_name = call.function_call.name
                        agent_name = func_name.replace("async_delegate_to_", "")
                        
                        yield {
                            "status": "in_progress",
                            "agent": agent_name,
                            "message": f"Delegating task to {agent_name.replace('_', ' ').title()}",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
            
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(part.text for part in event.content.parts if part.text)
                
                # Robust JSON extraction
                json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", final_text, re.DOTALL)
                if json_match:
                    clean_text = json_match.group(1)
                else:
                    start = final_text.find('{')
                    end = final_text.rfind('}')
                    if start != -1 and end != -1:
                        clean_text = final_text[start:end+1]
                    else:
                        clean_text = final_text.strip()

                try:
                    result = json.loads(clean_text)
                    yield {
                        "status": "completed",
                        "agent": "orchestrator",
                        "message": "Mission accomplished.",
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                except json.JSONDecodeError:
                    # If it's not JSON, just return it as a conversational message
                    yield {
                        "status": "completed",
                        "agent": "orchestrator",
                        "message": "Mission accomplished.",
                        "result": {"response_message": final_text.strip()},
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
    except Exception as e:
        logger.error("Mission failed: %s", e)
        yield {
            "status": "error",
            "agent": "orchestrator",
            "message": f"Mission failed due to internal error: {e}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
