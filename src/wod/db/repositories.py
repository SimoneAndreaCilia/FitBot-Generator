"""Data-access repositories — async CRUD operations for all models."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.models import (
    Equipment,
    Exercise,
    FavoriteWorkout,
    GeneratedWorkout,
    SetLog,
    User,
    UserEquipment,
    WorkoutExercise,
    WorkoutSession,
)

# ---------------------------------------------------------------------------
# User repository
# ---------------------------------------------------------------------------


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
) -> User:
    """Fetch an existing user by Telegram ID, or create a new one."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
    return user


async def get_user_with_equipment(
    session: AsyncSession,
    telegram_id: int,
) -> Optional[User]:
    """Fetch a user with equipment eagerly loaded.

    Returns:
        The ``User`` instance or ``None`` if the user does not exist.
    """
    stmt = (
        select(User)
        .options(selectinload(User.equipment))
        .where(User.telegram_id == telegram_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def update_user_profile(
    session: AsyncSession,
    user: User,
    *,
    name: Optional[str] = None,
    height_cm: Optional[float] = None,
    weight_kg: Optional[float] = None,
    body_type: Optional[BodyType] = None,
    experience_level: Optional[ExperienceLevel] = None,
    training_frequency: Optional[int] = None,
    preferred_split: Optional[SplitType] = None,
) -> User:
    """Update a user's profile and training preferences."""
    if name is not None:
        user.name = name
    if height_cm is not None:
        user.height_cm = height_cm
    if weight_kg is not None:
        user.weight_kg = weight_kg
    if body_type is not None:
        user.body_type = body_type
    if experience_level is not None:
        user.experience_level = experience_level
    if training_frequency is not None:
        user.training_frequency = training_frequency
    if preferred_split is not None:
        user.preferred_split = preferred_split
    await session.flush()
    return user


async def set_user_equipment(
    session: AsyncSession,
    user: User,
    equipment_ids: list[int],
) -> None:
    """Replace a user's equipment set with the given IDs."""
    # Remove existing associations
    stmt = select(UserEquipment).where(UserEquipment.user_id == user.id)
    result = await session.execute(stmt)
    for row in result.scalars():
        await session.delete(row)

    # Add new associations
    for eq_id in equipment_ids:
        session.add(UserEquipment(user_id=user.id, equipment_id=eq_id))
    await session.flush()


# ---------------------------------------------------------------------------
# Equipment repository
# ---------------------------------------------------------------------------


async def get_all_equipment(session: AsyncSession) -> Sequence[Equipment]:
    """Return all equipment in the catalogue."""
    result = await session.execute(select(Equipment).order_by(Equipment.name))
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Exercise repository
# ---------------------------------------------------------------------------


async def get_all_exercises(session: AsyncSession) -> Sequence[Exercise]:
    """Return all exercises with their equipment eagerly loaded."""
    stmt = (
        select(Exercise)
        .options(selectinload(Exercise.equipment))
        .order_by(Exercise.name)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Workout repository
# ---------------------------------------------------------------------------


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def save_workout(
    session: AsyncSession,
    user: User,
    title: str,
    content_json: str,
    content_text: str,
    exercise_entries: list[dict[str, Any]],
) -> GeneratedWorkout:
    """Persist a newly generated workout with its exercise entries.

    Args:
        session: Active database session.
        user: The user this workout belongs to.
        title: Human-readable workout title.
        content_json: JSON-serialized workout data.
        content_text: Plain-text rendering.
        exercise_entries: List of dicts with keys:
            exercise_id, sets, reps, order_index, notes.

    Returns:
        The saved ``GeneratedWorkout`` instance.
    """
    workout = GeneratedWorkout(
        user_id=user.id,
        title=title,
        content_json=content_json,
        content_text=content_text,
    )
    session.add(workout)
    await session.flush()  # get workout.id

    for entry in exercise_entries:
        we = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=entry["exercise_id"],
            sets=entry["sets"],
            reps=entry["reps"],
            order_index=entry["order_index"],
            notes=entry.get("notes"),
            day_label=entry.get("day_label"),
        )
        session.add(we)

    await session.flush()
    return workout


async def get_user_workouts(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> Sequence[GeneratedWorkout]:
    """Return the most recent workouts for a user."""
    stmt = (
        select(GeneratedWorkout)
        .where(GeneratedWorkout.user_id == user_id)
        .order_by(GeneratedWorkout.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_workout_by_id(
    session: AsyncSession,
    workout_id: int,
) -> Optional[GeneratedWorkout]:
    """Return a single workout by primary key."""
    stmt = (
        select(GeneratedWorkout)
        .options(selectinload(GeneratedWorkout.exercises))
        .where(GeneratedWorkout.id == workout_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Favorites repository
# ---------------------------------------------------------------------------


async def toggle_favorite(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
) -> bool:
    """Toggle the favorite status of a workout.

    Returns:
        ``True`` if the workout was added to favorites,
        ``False`` if it was removed.
    """
    stmt = select(FavoriteWorkout).where(
        FavoriteWorkout.user_id == user_id,
        FavoriteWorkout.workout_id == workout_id,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        await session.delete(existing)
        await session.flush()
        return False

    fav = FavoriteWorkout(user_id=user_id, workout_id=workout_id)
    session.add(fav)
    await session.flush()
    return True


async def get_user_favorites(
    session: AsyncSession,
    user_id: int,
) -> Sequence[FavoriteWorkout]:
    """Return all favorites for a user, ordered by creation date."""
    stmt = (
        select(FavoriteWorkout)
        .options(selectinload(FavoriteWorkout.workout))
        .where(FavoriteWorkout.user_id == user_id)
        .order_by(FavoriteWorkout.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Live workout session repository
# ---------------------------------------------------------------------------


async def create_workout_session(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
) -> WorkoutSession:
    """Create a new live workout session."""
    ws = WorkoutSession(
        user_id=user_id,
        workout_id=workout_id,
        status="in_progress",
    )
    session.add(ws)
    await session.flush()
    return ws


async def complete_workout_session(
    session: AsyncSession,
    session_id: int,
    status: str = "completed",
) -> Optional[WorkoutSession]:
    """Mark a workout session as completed or abandoned."""
    stmt = select(WorkoutSession).where(WorkoutSession.id == session_id)
    result = await session.execute(stmt)
    ws = result.scalar_one_or_none()
    if ws:
        ws.status = status
        from sqlalchemy.sql import func

        ws.completed_at = func.now()  # pylint: disable=not-callable
        await session.flush()
    return ws


async def log_set(
    session: AsyncSession,
    session_id: int,
    workout_exercise_id: int,
    set_number: int,
    weight_kg: Optional[float] = None,
    reps_done: Optional[int] = None,
    skipped: bool = False,
) -> SetLog:
    """Log a single set for a workout session."""
    log = SetLog(
        session_id=session_id,
        workout_exercise_id=workout_exercise_id,
        set_number=set_number,
        weight_kg=weight_kg,
        reps_done=reps_done,
        skipped=skipped,
    )
    session.add(log)
    await session.flush()
    return log


async def get_session_logs(
    session: AsyncSession,
    session_id: int,
) -> Sequence[SetLog]:
    """Return all set logs for a session, ordered by time."""
    stmt = (
        select(SetLog)
        .options(selectinload(SetLog.workout_exercise))
        .where(SetLog.session_id == session_id)
        .order_by(SetLog.logged_at)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_latest_completed_session(
    session: AsyncSession,
    workout_id: int,
) -> Optional[WorkoutSession]:
    """Return the most recently completed session for a workout."""
    stmt = (
        select(WorkoutSession)
        .where(
            WorkoutSession.workout_id == workout_id,
            WorkoutSession.status.in_(["completed", "abandoned"]),
        )
        .order_by(WorkoutSession.completed_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
