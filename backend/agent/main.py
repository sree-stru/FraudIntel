"""FraudIntel CLI — Interactive fraud investigation agent.

Usage::

    python -m agent.main
"""

import asyncio
import logging
import sys

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.config import settings
from agent.database import check_connection, get_collection_stats
from agent.orchestrator import get_agent

logger = logging.getLogger(__name__)


async def main() -> None:
    """Launch the interactive FraudIntel investigation session."""

    # Logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    # Banner
    print()
    print("╔═══════════════════════════════════════════╗")
    print("║  🛡️  FraudIntel Investigation Agent        ║")
    print("║  AI-Powered Fraud Investigation System     ║")
    print("╚═══════════════════════════════════════════╝")
    print()
    print(f"  Model:    {settings.gemini_model}")
    print(f"  Database: {settings.mongodb_database}")
    print()

    # MongoDB health check
    print("  Checking MongoDB connection...")
    connected = await check_connection()
    if not connected:
        print("  ❌ Could not connect to MongoDB. Exiting.")
        sys.exit(1)
    print("  ✅ MongoDB connected")
    print()

    # Collection stats
    stats = await get_collection_stats()
    print("  📊 Collection Stats:")
    for name, count in stats.items():
        print(f"      {name:<25} {count:>6} docs")
    print()

    # ADK session & runner
    session_service = InMemorySessionService()
    agent = get_agent()
    runner = Runner(
        agent=agent,
        app_name="fraudintel",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="fraudintel",
        user_id="investigator",
    )

    print("  Ready! Type your investigation request. Type 'quit' to exit.")
    print("  Example: Investigate account ACC-001 for suspicious activity")
    print()

    # Interactive loop
    while True:
        try:
            user_input = input("\n🔍 Investigator > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("👋 FraudIntel shutting down.")
                break

            content = types.Content(
                role="user",
                parts=[types.Part(text=user_input)],
            )
            print("\n⏳ Investigating...")

            async for event in runner.run_async(
                user_id="investigator",
                session_id=session.id,
                new_message=content,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                print(f"\n🛡️ FraudIntel:\n{part.text}")

        except KeyboardInterrupt:
            print("\n👋 Investigation interrupted.")
            break
        except Exception as exc:
            logger.error("Error during investigation: %s", exc)
            print(f"\n❌ Error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
