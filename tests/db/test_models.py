"""Tests for SQLAlchemy model __repr__ methods and basic model creation."""

from __future__ import annotations

from wod.core.types import EffortType, ExperienceLevel, MuscleGroup
from wod.db.models import (
    Equipment,
    Exercise,
    FavoriteWorkout,
    GeneratedWorkout,
    User,
    WorkoutExercise,
)


class TestModelRepr:
    """Verify __repr__ strings for all models."""

    def test_user_repr(self) -> None:
        user = User(
            id=1,
            telegram_id=12345,
            experience_level=ExperienceLevel.BEGINNER,
        )
        r = repr(user)
        assert "User" in r
        assert "12345" in r
        assert "BEGINNER" in r

    def test_equipment_repr(self) -> None:
        eq = Equipment(id=1, name="barbell")
        r = repr(eq)
        assert "Equipment" in r
        assert "barbell" in r

    def test_exercise_repr(self) -> None:
        ex = Exercise(
            id=1,
            name="Bench Press",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
        )
        r = repr(ex)
        assert "Exercise" in r
        assert "Bench Press" in r
        assert "chest" in r

    def test_generated_workout_repr(self) -> None:
        w = GeneratedWorkout(
            id=1,
            user_id=1,
            title="Upper Body",
            content_json="{}",
            content_text="text",
        )
        r = repr(w)
        assert "GeneratedWorkout" in r
        assert "Upper Body" in r

    def test_workout_exercise_repr(self) -> None:
        we = WorkoutExercise(
            workout_id=1,
            exercise_id=2,
            sets=4,
            reps=10,
            order_index=0,
        )
        r = repr(we)
        assert "WorkoutExercise" in r
        assert "4x10" in r

    def test_favorite_workout_repr(self) -> None:
        fav = FavoriteWorkout(
            user_id=1,
            workout_id=2,
        )
        r = repr(fav)
        assert "FavoriteWorkout" in r
        assert "1" in r
        assert "2" in r
