"""Tests for the WOD handler's pure helper functions."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest

from wod.bot.formatters import FormattedExercise
from wod.bot.handlers.wod import (
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
            id=1,
            name="Push-Up",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
            weight=1,
            tier="C",
            equipment=[bodyweight_eq],
        ),
        Exercise(
            id=2,
            name="Chest Fly BW",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.ISOLATION,
            weight=2,
            tier="B",
            equipment=[bodyweight_eq],
        ),
        Exercise(
            id=3,
            name="Extra Chest",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
            weight=1,
            tier="A",
            equipment=[bodyweight_eq],
        ),
        Exercise(
            id=4,
            name="Squat",
            muscle_group=MuscleGroup.QUADS,
            effort_type=EffortType.COMPOUND,
            weight=1,
            tier="A",
            equipment=[bodyweight_eq],
        ),
        Exercise(
            id=5,
            name="Plank",
            muscle_group=MuscleGroup.CORE,
            effort_type=EffortType.ISOLATION,
            weight=2,
            tier="A",
            equipment=[bodyweight_eq],
        ),
    ]


class TestSelectExercises:
    """Tests for _select_exercises."""

    def test_limits_per_muscle_group(self, mixed_exercises: list[Exercise]) -> None:
        day = TrainingDay(
            day_number=1,
            label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        selected = _select_exercises(mixed_exercises, day)
        # Should pick at most 2 exercises for chest (one w=1, one w=2)
        assert len(selected) <= 2

    def test_compounds_preferred(self, mixed_exercises: list[Exercise]) -> None:
        day = TrainingDay(
            day_number=1,
            label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        selected = _select_exercises(mixed_exercises, day)
        # One of them must be compound (w=1) and should pick Tier A first (Extra Chest)
        assert any(ex.effort_type == EffortType.COMPOUND for ex in selected)
        assert any(ex.name == "Extra Chest" for ex in selected)

    def test_multiple_muscle_groups(self, mixed_exercises: list[Exercise]) -> None:
        day = TrainingDay(
            day_number=1,
            label="Test",
            muscle_groups=[MuscleGroup.CHEST, MuscleGroup.QUADS, MuscleGroup.CORE],
        )
        selected = _select_exercises(mixed_exercises, day)
        groups = {ex.muscle_group for ex in selected}
        assert MuscleGroup.CHEST in groups
        assert MuscleGroup.QUADS in groups
        assert MuscleGroup.CORE in groups

    def test_empty_exercises(self) -> None:
        day = TrainingDay(
            day_number=1,
            label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        selected = _select_exercises([], day)
        assert selected == []


class TestPrescribeExercises:
    """Tests for _prescribe_exercises."""

    def test_returns_formatted_exercises(self, mixed_exercises: list[Exercise]) -> None:
        result = _prescribe_exercises(mixed_exercises[:2], ExperienceLevel.BEGINNER, "Day 1")
        assert len(result) == 2
        assert all(isinstance(ex, FormattedExercise) for ex in result)

    def test_order_is_sequential(self, mixed_exercises: list[Exercise]) -> None:
        result = _prescribe_exercises(mixed_exercises[:3], ExperienceLevel.INTERMEDIATE, "Day 1")
        for i, ex in enumerate(result, start=1):
            assert ex.order == i

    def test_empty_list(self) -> None:
        result = _prescribe_exercises([], ExperienceLevel.BEGINNER, "Day 1")
        assert result == []

