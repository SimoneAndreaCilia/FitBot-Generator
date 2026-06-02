import asyncio
from wod.db.session import get_session_factory
from wod.db.repositories import get_latest_completed_session, get_session_logs
from wod.db.models import GeneratedWorkout, WorkoutSession
from sqlalchemy import select

async def main():
    async with get_session_factory()() as session:
        # Find any completed session
        stmt = select(WorkoutSession).where(WorkoutSession.status.in_(["completed", "abandoned"])).order_by(WorkoutSession.id.desc()).limit(1)
        result = await session.execute(stmt)
        ws = result.scalar_one_or_none()
        
        if not ws:
            print("No completed sessions found.")
            return
            
        print(f"Found completed session {ws.id} for workout {ws.workout_id}")
        
        # Now try to run the logic from history.py
        from wod.bot.handlers.history import download_pdf_callback
        # We can't easily mock the context and update here without more code.
        # But we can extract the exact logic:
        
        workout_id = ws.workout_id
        
        from wod.db.repositories import get_workout_by_id, get_user_with_equipment
        workout = await get_workout_by_id(session, workout_id)
        # Assuming user_id
        user = await get_user_with_equipment(session, telegram_id=workout.user.telegram_id)
        
        from wod.core.intensity import calculate_intensity
        from wod.core.types import EffortType
        from wod.bot.formatters import SessionSummary, SessionLogRow, UserProfile, session_summary_to_pdf
        
        logs = await get_session_logs(session, ws.id)
        session_rows = []
        
        ex_by_id = {we.id: we for we in workout.exercises}
        
        for log in logs:
            we = ex_by_id.get(log.workout_exercise_id)
            if not we: continue
            
            exercise_name = we.exercise.name if we.exercise else f"Esercizio #{we.order_index + 1}"
            
            intensity = "-"
            rest = "-"
            if we.exercise and user and user.experience_level:
                try:
                    prescription = calculate_intensity(user.experience_level, we.exercise.effort_type)
                    intensity = prescription.intensity
                    rest = "120s" if we.exercise.effort_type == EffortType.COMPOUND else "60s"
                except KeyError:
                    pass
                    
            weight_str = f"{log.weight_kg:g}" if log.weight_kg is not None else "0"
            
            session_rows.append(
                SessionLogRow(
                    order=we.order_index + 1,
                    exercise_name=exercise_name,
                    set_number=log.set_number,
                    kg=weight_str,
                    reps=str(log.reps_done) if log.reps_done is not None else "0",
                    rest=rest,
                    intensity=intensity,
                    skipped=log.skipped,
                )
            )
            
        summary = SessionSummary(
            title=workout.title,
            date=ws.completed_at or ws.started_at or workout.created_at,
            rows=session_rows,
            user_profile=UserProfile(name="Test")
        )
        try:
            pdf_bytes = session_summary_to_pdf(summary)
            print("Successfully generated PDF! Size:", len(pdf_bytes))
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
