"""Exercise filtering engine.

Selects exercises from the catalogue that are compatible with a user's
available equipment.
"""

from __future__ import annotations

from wod.core.types import MuscleGroup
from wod.db.models import Equipment, Exercise


def filter_exercises_by_equipment(
    exercises: list[Exercise],
    user_equipment: list[Equipment],
) -> list[Exercise]:
    """Return only exercises whose required equipment is a subset of the user's gear.

    An exercise is valid if **every** piece of equipment it requires is
    present in the user's home-gym inventory.

    Args:
        exercises: Full catalogue of exercises.
        user_equipment: Equipment the user owns.

    Returns:
        Filtered list of exercises the user can perform.
    """
    owned_ids = {eq.id for eq in user_equipment}
    return [
        ex for ex in exercises if {eq.id for eq in ex.equipment}.issubset(owned_ids)
    ]


def filter_exercises_by_muscle_groups(
    exercises: list[Exercise],
    target_groups: list[MuscleGroup],
) -> list[Exercise]:
    """Return exercises targeting any of the specified muscle groups.

    Args:
        exercises: Pre-filtered exercise list.
        target_groups: Muscle groups to train on a given day.

    Returns:
        Exercises matching the target muscle groups.
    """
    group_set = set(target_groups)
    return [ex for ex in exercises if ex.muscle_group in group_set]
