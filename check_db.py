import asyncio
from wod.db.session import get_session_factory
from wod.db.repositories import get_session_logs, get_latest_completed_session

async def main():
    async with get_session_factory()() as session:
        # Assuming workout_id 1
        ws = await get_latest_completed_session(session, 1)
        if ws:
            logs = await get_session_logs(session, ws.id)
            for log in logs:
                print(f"Ex ID: {log.workout_exercise_id}, Set: {log.set_number}, Skipped: {log.skipped}, Reps: {log.reps_done}")
        else:
            print("No session found")

if __name__ == "__main__":
    asyncio.run(main())
