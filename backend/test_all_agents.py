import asyncio
import sys
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.sub_agents.auditor import auditor_agent
from agent.sub_agents.compliance import compliance_agent
from agent.sub_agents.evidence_gatherer import evidence_gatherer_agent
from agent.sub_agents.report_generator import report_generator_agent
from agent.sub_agents.risk_scorer import risk_scorer_agent

agents_to_test = [
    ("Auditor Agent", auditor_agent, "Review this investigation for missing evidence."),
    ("Compliance Agent", compliance_agent, "Check if freezing account 'fraud_user_123' violates any regulations."),
    ("Evidence Gatherer Agent", evidence_gatherer_agent, "Gather transaction data for account 'fraud_user_123'."),
    ("Report Generator Agent", report_generator_agent, "Generate a summary report for account 'fraud_user_123' investigation."),
    ("Risk Scorer Agent", risk_scorer_agent, "Calculate the risk score for account 'fraud_user_123' based on their recent transactions."),
]

async def test_agent(name, agent, prompt):
    print(f"\n--- Testing {name} ---")
    print(f"Prompt: {prompt}")
    try:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="test_app",
            session_service=session_service,
        )
        session = await session_service.create_session(
            app_name="test_app",
            user_id="test_user",
        )
        
        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )
        
        final_text = ""
        async for event in runner.run_async(
            user_id="test_user", 
            session_id=session.id, 
            new_message=content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
                        
        print(f"Response: {final_text[:200]}...")
        if final_text:
            print(f"✅ {name} works properly!")
            return True
        else:
            print(f"❌ {name} returned empty response.")
            return False
    except Exception as e:
        print(f"❌ {name} failed with error: {e}")
        return False

async def main():
    success_count = 0
    for name, agent, prompt in agents_to_test:
        success = await test_agent(name, agent, prompt)
        if success:
            success_count += 1
            
    print(f"\nTested {len(agents_to_test)} agents. {success_count} succeeded.")
    
if __name__ == "__main__":
    # Force UTF-8 encoding for standard output
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(main())
