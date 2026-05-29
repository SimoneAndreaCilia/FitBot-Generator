"""Domain types — enums and value objects used across the application."""

from enum import Enum


class ExperienceLevel(str, Enum):
    """User's training experience level."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MuscleGroup(str, Enum):
    """Primary muscle groups targeted by exercises."""

    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    CALVES = "calves"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CORE = "core"


class EffortType(str, Enum):
    """Classification of exercise effort type."""

    COMPOUND = "compound"
    ISOLATION = "isolation"


class SplitType(str, Enum):
    """Weekly training split strategy."""

    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"


# Mapping from split type to the muscle groups trained each day
SPLIT_TEMPLATES: dict[SplitType, list[list[MuscleGroup]]] = {
    SplitType.FULL_BODY: [
        [
            MuscleGroup.CHEST,
            MuscleGroup.BACK,
            MuscleGroup.SHOULDERS,
            MuscleGroup.BICEPS,
            MuscleGroup.TRICEPS,
            MuscleGroup.QUADS,
            MuscleGroup.HAMSTRINGS,
            MuscleGroup.CALVES,
            MuscleGroup.CORE,
        ],
    ],
    SplitType.UPPER_LOWER: [
        # Upper day
        [
            MuscleGroup.CHEST,
            MuscleGroup.BACK,
            MuscleGroup.SHOULDERS,
            MuscleGroup.BICEPS,
            MuscleGroup.TRICEPS,
        ],
        # Lower day
        [
            MuscleGroup.QUADS,
            MuscleGroup.HAMSTRINGS,
            MuscleGroup.CALVES,
            MuscleGroup.CORE,
        ],
    ],
    SplitType.PUSH_PULL_LEGS: [
        # Push day
        [MuscleGroup.CHEST, MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS],
        # Pull day
        [MuscleGroup.BACK, MuscleGroup.BICEPS],
        # Legs day
        [
            MuscleGroup.QUADS,
            MuscleGroup.HAMSTRINGS,
            MuscleGroup.CALVES,
            MuscleGroup.CORE,
        ],
    ],
}
