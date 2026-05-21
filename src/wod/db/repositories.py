"""Data-access repositories — async CRUD operations for all models."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wod.core.types import ExperienceLevel, SplitType
from wod.db.models import (
    Equipment,
    Exercise,
    FavoriteWorkout,
    GeneratedWorkout,
    User,
    UserEquipment,
    WorkoutExercise,
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


async def update_user_profile(
    session: AsyncSession,
    user: User,
    *,
    experience_level: Optional[ExperienceLevel] = None,
    training_frequency: Optional[int] = None,
    preferred_split: Optional[SplitType] = None,
) -> User:
    """Update a user's training preferences."""
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
