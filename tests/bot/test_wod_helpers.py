"""Tests for the WOD handler's pure helper functions."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest

from wod.bot.formatters import FormattedExercise
from wod.bot.handlers.wod import (
    MAX_EXERCISES_PER_GROUP,
    _pick_today_training_day,
    _prescribe_exercises,
    _select_exercises,
)
from wod.core.split_generator import TrainingDay
from wod.core.types import EffortType, ExperienceLevel, MuscleGroup, SplitType
from wod.db.models import Equipment, Exercise


@pytest.fixture()
def bodyweight_eq() -> Equipment:
    return Equipment(id=1, name="bodyweight")


@pytest.fixture()
def mixed_exercises(bodyweight_eq: Equipment) -> list[Exercise]:
    return [
        Exercise(
            id=1, name="Push-Up", muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND, equipment=[bodyweight_eq],
        ),
        Exercise(
            id=2, name="Chest Fly BW", muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.ISOLATION, equipment=[bodyweight_eq],
        ),
        Exercise(
            id=3, name="Extra Chest", muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND, equipment=[bodyweight_eq],
        ),
        Exercise(
            id=4, name="Squat", muscle_group=MuscleGroup.LEGS,
            effort_type=EffortType.COMPOUND, equipment=[bodyweight_eq],
        ),
        Exercise(
            id=5, name="Plank", muscle_group=MuscleGroup.CORE,
            effort_type=EffortType.ISOLATION, equipment=[bodyweight_eq],
        ),
    ]


class TestPickTodayTrainingDay:
    """Tests for _pick_today_training_day."""

    def test_returns_training_day(self) -> None:
        day = _pick_today_training_day(SplitType.FULL_BODY, 3)
        assert isinstance(day, TrainingDay)

    def test_cycles_based_on_weekday(self) -> None:
        # Monday = isoweekday 1, index 0
        with patch("wod.bot.handlers.wod.datetime") as mock_dt:
            mock_dt.date.today.return_value = datetime.date(2025, 6, 16)  # Monday
            mock_dt.datetime = datetime.datetime
            mock_dt.timezone = datetime.timezone
            day = _pick_today_training_day(SplitType.UPPER_LOWER, 2)
            # Monday → index 0 → Upper
            assert "Upper" in day.label

    def test_full_body_always_same(self) -> None:
        day1 = _pick_today_training_day(SplitType.FULL_BODY, 1)
        assert "Full Body" in day1.label


class TestSelectExercises:
    """Tests for _select_exercises."""

    def test_limits_per_muscle_group(self, mixed_exercises: list[Exercise]) -> None:
        day = TrainingDay(
            day_number=1, label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        selected = _select_exercises(mixed_exercises, day)
        # Should pick at most MAX_EXERCISES_PER_GROUP for chest
        assert len(selected) <= MAX_EXERCISES_PER_GROUP

    def test_compounds_preferred(self, mixed_exercises: list[Exercise]) -> None:
        day = TrainingDay(
            day_number=1, label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        # Run multiple times — compounds should always be first
        for _ in range(10):
            selected = _select_exercises(mixed_exercises, day)
            if len(selected) == MAX_EXERCISES_PER_GROUP:
                assert selected[0].effort_type == EffortType.COMPOUND

    def test_multiple_muscle_groups(self, mixed_exercises: list[Exercise]) -> None:
        day = TrainingDay(
            day_number=1, label="Test",
            muscle_groups=[MuscleGroup.CHEST, MuscleGroup.LEGS, MuscleGroup.CORE],
        )
        selected = _select_exercises(mixed_exercises, day)
        groups = {ex.muscle_group for ex in selected}
        assert MuscleGroup.CHEST in groups
        assert MuscleGroup.LEGS in groups
        assert MuscleGroup.CORE in groups

    def test_empty_exercises(self) -> None:
        day = TrainingDay(
            day_number=1, label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        selected = _select_exercises([], day)
        assert selected == []


class TestPrescribeExercises:
    """Tests for _prescribe_exercises."""

    def test_returns_formatted_exercises(self, mixed_exercises: list[Exercise]) -> None:
        result = _prescribe_exercises(
            mixed_exercises[:2], ExperienceLevel.BEGINNER
        )
        assert len(result) == 2
        assert all(isinstance(ex, FormattedExercise) for ex in result)

    def test_order_is_sequential(self, mixed_exercises: list[Exercise]) -> None:
        result = _prescribe_exercises(
            mixed_exercises[:3], ExperienceLevel.INTERMEDIATE
        )
        for i, ex in enumerate(result, start=1):
            assert ex.order == i

    def test_beginner_compound_prescription(self, bodyweight_eq: Equipment) -> None:
        exercises = [
            Exercise(
                id=1, name="Push-Up", muscle_group=MuscleGroup.CHEST,
                effort_type=EffortType.COMPOUND, equipment=[bodyweight_eq],
            )
        ]
        result = _prescribe_exercises(exercises, ExperienceLevel.BEGINNER)
        assert result[0].sets == 3
        assert result[0].reps == 12

    def test_advanced_isolation_prescription(self, bodyweight_eq: Equipment) -> None:
        exercises = [
            Exercise(
                id=1, name="Plank", muscle_group=MuscleGroup.CORE,
                effort_type=EffortType.ISOLATION, equipment=[bodyweight_eq],
            )
        ]
        result = _prescribe_exercises(exercises, ExperienceLevel.ADVANCED)
        assert result[0].sets == 4
        assert result[0].reps == 10

    def test_empty_list(self) -> None:
        result = _prescribe_exercises([], ExperienceLevel.BEGINNER)
        assert result == []
