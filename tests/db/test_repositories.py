"""Tests for the data-access repositories (async, in-memory SQLite)."""

from __future__ import annotations

import pytest

from wod.core.types import ExperienceLevel, SplitType
from wod.db.models import Equipment, Exercise, GeneratedWorkout, User
from wod.db.repositories import (
    get_all_equipment,
    get_all_exercises,
    get_or_create_user,
    get_user_favorites,
    get_user_workouts,
    get_workout_by_id,
    save_workout,
    set_user_equipment,
    toggle_favorite,
    update_user_profile,
)

# ---------------------------------------------------------------------------
# User repository
# ---------------------------------------------------------------------------


class TestUserRepository:
    """Tests for user CRUD operations."""

    async def test_create_new_user(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=111, username="alice")
        assert user.id is not None
        assert user.telegram_id == 111
        assert user.username == "alice"

    async def test_get_existing_user(self, db_session) -> None:
        user1 = await get_or_create_user(db_session, telegram_id=222)
        user2 = await get_or_create_user(db_session, telegram_id=222)
        assert user1.id == user2.id

    async def test_update_profile(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=333)
        updated = await update_user_profile(
            db_session,
            user,
            experience_level=ExperienceLevel.ADVANCED,
            training_frequency=5,
            preferred_split=SplitType.PUSH_PULL_LEGS,
        )
        assert updated.experience_level == ExperienceLevel.ADVANCED
        assert updated.training_frequency == 5
        assert updated.preferred_split == SplitType.PUSH_PULL_LEGS

    async def test_partial_update(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=444)
        await update_user_profile(
            db_session,
            user,
            experience_level=ExperienceLevel.BEGINNER,
        )
        assert user.experience_level == ExperienceLevel.BEGINNER
        assert user.training_frequency is None  # untouched


# ---------------------------------------------------------------------------
# Equipment repository
# ---------------------------------------------------------------------------


class TestEquipmentRepository:
    """Tests for equipment operations."""

    async def test_get_all_equipment_empty(self, db_session) -> None:
        result = await get_all_equipment(db_session)
        assert len(result) == 0

    async def test_get_all_equipment(self, db_session, sample_equipment) -> None:
        for eq in sample_equipment:
            db_session.add(eq)
        await db_session.flush()

        result = await get_all_equipment(db_session)
        assert len(result) == len(sample_equipment)

    async def test_set_user_equipment(self, db_session, sample_equipment) -> None:
        for eq in sample_equipment:
            db_session.add(eq)
        await db_session.flush()

        user = await get_or_create_user(db_session, telegram_id=555)
        eq_ids = [sample_equipment[0].id, sample_equipment[1].id]
        await set_user_equipment(db_session, user, eq_ids)

        # Refresh to see relationship
        await db_session.refresh(user, ["equipment"])
        assert len(user.equipment) == 2

    async def test_replace_user_equipment(self, db_session, sample_equipment) -> None:
        for eq in sample_equipment:
            db_session.add(eq)
        await db_session.flush()

        user = await get_or_create_user(db_session, telegram_id=666)
        await set_user_equipment(
            db_session, user, [sample_equipment[0].id, sample_equipment[1].id]
        )
        # Replace with different set
        await set_user_equipment(db_session, user, [sample_equipment[2].id])
        await db_session.refresh(user, ["equipment"])
        assert len(user.equipment) == 1
        assert user.equipment[0].id == sample_equipment[2].id


# ---------------------------------------------------------------------------
# Exercise repository
# ---------------------------------------------------------------------------


class TestExerciseRepository:
    """Tests for exercise operations."""

    async def test_get_all_exercises_empty(self, db_session) -> None:
        result = await get_all_exercises(db_session)
        assert len(result) == 0

    async def test_get_all_exercises_with_equipment(
        self, db_session, sample_equipment, sample_exercises
    ) -> None:
        for eq in sample_equipment:
            db_session.add(eq)
        await db_session.flush()
        for ex in sample_exercises:
            db_session.add(ex)
        await db_session.flush()

        result = await get_all_exercises(db_session)
        assert len(result) == len(sample_exercises)
        # Verify equipment is eagerly loaded
        for exercise in result:
            assert exercise.equipment is not None


# ---------------------------------------------------------------------------
# Workout repository
# ---------------------------------------------------------------------------


class TestWorkoutRepository:
    """Tests for workout CRUD operations."""

    async def _create_user_and_workout(self, db_session):
        """Helper: create a user and save one workout."""
        user = await get_or_create_user(db_session, telegram_id=777)
        workout = await save_workout(
            db_session,
            user=user,
            title="Test Workout",
            content_json='{"exercises": []}',
            content_text="Push-Up 3x12",
            exercise_entries=[
                {
                    "exercise_id": None,
                    "sets": 3,
                    "reps": 12,
                    "order_index": 0,
                    "notes": "Slow tempo",
                },
            ],
        )
        return user, workout

    async def test_save_workout(self, db_session) -> None:
        user, workout = await self._create_user_and_workout(db_session)
        assert workout.id is not None
        assert workout.user_id == user.id
        assert workout.title == "Test Workout"

    async def test_workout_exercises_saved(self, db_session) -> None:
        _, workout = await self._create_user_and_workout(db_session)
        # Re-fetch with eager loading to access exercises
        fetched = await get_workout_by_id(db_session, workout.id)
        assert fetched is not None
        assert len(fetched.exercises) == 1
        assert fetched.exercises[0].sets == 3
        assert fetched.exercises[0].reps == 12
        assert fetched.exercises[0].notes == "Slow tempo"

    async def test_get_user_workouts(self, db_session) -> None:
        user, _ = await self._create_user_and_workout(db_session)
        # Save another workout
        await save_workout(
            db_session,
            user=user,
            title="Second Workout",
            content_json="{}",
            content_text="Squat 4x10",
            exercise_entries=[],
        )

        workouts = await get_user_workouts(db_session, user.id, limit=10)
        assert len(workouts) == 2

    async def test_get_user_workouts_limit(self, db_session) -> None:
        user, _ = await self._create_user_and_workout(db_session)
        await save_workout(
            db_session,
            user=user,
            title="Second",
            content_json="{}",
            content_text="",
            exercise_entries=[],
        )

        workouts = await get_user_workouts(db_session, user.id, limit=1)
        assert len(workouts) == 1

    async def test_get_workout_by_id(self, db_session) -> None:
        _, workout = await self._create_user_and_workout(db_session)
        fetched = await get_workout_by_id(db_session, workout.id)
        assert fetched is not None
        assert fetched.id == workout.id

    async def test_get_workout_by_id_not_found(self, db_session) -> None:
        result = await get_workout_by_id(db_session, 99999)
        assert result is None


# ---------------------------------------------------------------------------
# Favorites repository
# ---------------------------------------------------------------------------


class TestFavoritesRepository:
    """Tests for the favorites toggle mechanism."""

    async def test_toggle_on(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=888)
        workout = await save_workout(
            db_session,
            user=user,
            title="Fav Workout",
            content_json="{}",
            content_text="",
            exercise_entries=[],
        )

        added = await toggle_favorite(db_session, user.id, workout.id)
        assert added is True

    async def test_toggle_off(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=999)
        workout = await save_workout(
            db_session,
            user=user,
            title="Fav Workout",
            content_json="{}",
            content_text="",
            exercise_entries=[],
        )

        await toggle_favorite(db_session, user.id, workout.id)
        removed = await toggle_favorite(db_session, user.id, workout.id)
        assert removed is False

    async def test_get_user_favorites(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=1010)
        w1 = await save_workout(
            db_session,
            user=user,
            title="W1",
            content_json="{}",
            content_text="",
            exercise_entries=[],
        )
        w2 = await save_workout(
            db_session,
            user=user,
            title="W2",
            content_json="{}",
            content_text="",
            exercise_entries=[],
        )

        await toggle_favorite(db_session, user.id, w1.id)
        await toggle_favorite(db_session, user.id, w2.id)

        favs = await get_user_favorites(db_session, user.id)
        assert len(favs) == 2

    async def test_favorites_empty(self, db_session) -> None:
        user = await get_or_create_user(db_session, telegram_id=1111)
        favs = await get_user_favorites(db_session, user.id)
        assert len(favs) == 0
