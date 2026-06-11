import asyncio
from agent.orchestrator import run_mission

async def main():
    try:
        async for ev in run_mission('test'):
            print(ev)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
