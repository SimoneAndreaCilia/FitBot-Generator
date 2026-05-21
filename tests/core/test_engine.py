"""Tests for the exercise filtering engine."""

from __future__ import annotations

import pytest

from wod.core.engine import (
    filter_exercises_by_equipment,
    filter_exercises_by_muscle_groups,
)
from wod.core.types import EffortType, MuscleGroup
from wod.db.models import Equipment, Exercise

# ---------------------------------------------------------------------------
# Fixtures (lightweight, no DB)
# ---------------------------------------------------------------------------


@pytest.fixture()
def equipment_catalog() -> dict[str, Equipment]:
    """Named equipment with fake IDs for pure-logic tests."""
    items = {
        "barbell": Equipment(id=1, name="barbell"),
        "dumbbell": Equipment(id=2, name="dumbbell"),
        "pull_up_bar": Equipment(id=3, name="pull_up_bar"),
        "bench": Equipment(id=4, name="bench"),
        "kettlebell": Equipment(id=5, name="kettlebell"),
        "bodyweight": Equipment(id=6, name="bodyweight"),
    }
    return items


@pytest.fixture()
def exercise_catalog(equipment_catalog: dict[str, Equipment]) -> list[Exercise]:
    """Exercises with equipment relationships set in-memory."""
    eq = equipment_catalog
    exercises = [
        Exercise(
            id=1,
            name="Barbell Bench Press",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
            equipment=[eq["barbell"], eq["bench"]],
        ),
        Exercise(
            id=2,
            name="Dumbbell Row",
            muscle_group=MuscleGroup.BACK,
            effort_type=EffortType.COMPOUND,
            equipment=[eq["dumbbell"], eq["bench"]],
        ),
        Exercise(
            id=3,
            name="Pull-Up",
            muscle_group=MuscleGroup.BACK,
            effort_type=EffortType.COMPOUND,
            equipment=[eq["pull_up_bar"]],
        ),
        Exercise(
            id=4,
            name="Push-Up",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
            equipment=[eq["bodyweight"]],
        ),
        Exercise(
            id=5,
            name="Bodyweight Squat",
            muscle_group=MuscleGroup.LEGS,
            effort_type=EffortType.COMPOUND,
            equipment=[eq["bodyweight"]],
        ),
        Exercise(
            id=6,
            name="Overhead Press",
            muscle_group=MuscleGroup.SHOULDERS,
            effort_type=EffortType.COMPOUND,
            equipment=[eq["barbell"]],
        ),
        Exercise(
            id=7,
            name="Bicep Curl",
            muscle_group=MuscleGroup.ARMS,
            effort_type=EffortType.ISOLATION,
            equipment=[eq["dumbbell"]],
        ),
        Exercise(
            id=8,
            name="Plank",
            muscle_group=MuscleGroup.CORE,
            effort_type=EffortType.ISOLATION,
            equipment=[eq["bodyweight"]],
        ),
    ]
    return exercises


# ---------------------------------------------------------------------------
# filter_exercises_by_equipment
# ---------------------------------------------------------------------------


class TestFilterByEquipment:
    """Verifies that exercises are correctly filtered by available equipment."""

    def test_all_equipment_available(
        self,
        exercise_catalog: list[Exercise],
        equipment_catalog: dict[str, Equipment],
    ) -> None:
        """When the user owns everything, all exercises should be returned."""
        user_eq = list(equipment_catalog.values())
        result = filter_exercises_by_equipment(exercise_catalog, user_eq)
        assert len(result) == len(exercise_catalog)

    def test_bodyweight_only(
        self,
        exercise_catalog: list[Exercise],
        equipment_catalog: dict[str, Equipment],
    ) -> None:
        """Bodyweight-only user should see Push-Up, Squat, Plank."""
        user_eq = [equipment_catalog["bodyweight"]]
        result = filter_exercises_by_equipment(exercise_catalog, user_eq)
        names = {ex.name for ex in result}
        assert names == {"Push-Up", "Bodyweight Squat", "Plank"}

    def test_partial_equipment(
        self,
        exercise_catalog: list[Exercise],
        equipment_catalog: dict[str, Equipment],
    ) -> None:
        """User with dumbbell + bench + bodyweight should see matching exercises."""
        user_eq = [
            equipment_catalog["dumbbell"],
            equipment_catalog["bench"],
            equipment_catalog["bodyweight"],
        ]
        result = filter_exercises_by_equipment(exercise_catalog, user_eq)
        names = {ex.name for ex in result}
        # dumbbell+bench → Dumbbell Row; dumbbell → Bicep Curl;
        # bodyweight → Push-Up, Squat, Plank
        assert names == {
            "Dumbbell Row",
            "Bicep Curl",
            "Push-Up",
            "Bodyweight Squat",
            "Plank",
        }

    def test_no_equipment(
        self,
        exercise_catalog: list[Exercise],
    ) -> None:
        """No equipment means no exercises available."""
        result = filter_exercises_by_equipment(exercise_catalog, [])
        assert result == []

    def test_empty_catalog(
        self,
        equipment_catalog: dict[str, Equipment],
    ) -> None:
        """Empty exercise catalogue should return empty list."""
        result = filter_exercises_by_equipment([], list(equipment_catalog.values()))
        assert result == []


# ---------------------------------------------------------------------------
# filter_exercises_by_muscle_groups
# ---------------------------------------------------------------------------


class TestFilterByMuscleGroups:
    """Verifies muscle-group filtering."""

    def test_single_group(self, exercise_catalog: list[Exercise]) -> None:
        """Filter for CHEST should return only chest exercises."""
        result = filter_exercises_by_muscle_groups(
            exercise_catalog, [MuscleGroup.CHEST]
        )
        assert all(ex.muscle_group == MuscleGroup.CHEST for ex in result)
        assert len(result) == 2  # Bench Press + Push-Up

    def test_multiple_groups(self, exercise_catalog: list[Exercise]) -> None:
        """Filter for BACK + ARMS should return matching exercises."""
        result = filter_exercises_by_muscle_groups(
            exercise_catalog, [MuscleGroup.BACK, MuscleGroup.ARMS]
        )
        names = {ex.name for ex in result}
        assert names == {"Dumbbell Row", "Pull-Up", "Bicep Curl"}

    def test_all_groups(self, exercise_catalog: list[Exercise]) -> None:
        """Filtering for all groups returns everything."""
        all_groups = list(MuscleGroup)
        result = filter_exercises_by_muscle_groups(exercise_catalog, all_groups)
        assert len(result) == len(exercise_catalog)

    def test_no_groups(self, exercise_catalog: list[Exercise]) -> None:
        """Empty target groups returns nothing."""
        result = filter_exercises_by_muscle_groups(exercise_catalog, [])
        assert result == []

    def test_nonexistent_group_match(self, exercise_catalog: list[Exercise]) -> None:
        """Filter for a group with no exercises returns empty list."""
        # All exercises have at least one group, but CORE only has Plank
        result = filter_exercises_by_muscle_groups(exercise_catalog, [MuscleGroup.CORE])
        assert len(result) == 1
        assert result[0].name == "Plank"
