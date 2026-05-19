"""Intensity calculator — determines sets and reps based on experience level.

The prescription tables are derived from widely-accepted strength training
guidelines (NSCA, ACSM).
"""

from __future__ import annotations

from dataclasses import dataclass

from wod.core.types import EffortType, ExperienceLevel


@dataclass(frozen=True)
class SetRepPrescription:
    """Prescribed sets × reps for a single exercise."""

    sets: int
    reps: int

    def __str__(self) -> str:
        return f"{self.sets}×{self.reps}"


# Prescription tables keyed by (experience_level, effort_type)
_PRESCRIPTIONS: dict[
    tuple[ExperienceLevel, EffortType], SetRepPrescription
] = {
    # Beginners: moderate volume, higher reps for motor-pattern learning
    (ExperienceLevel.BEGINNER, EffortType.COMPOUND): SetRepPrescription(
        sets=3, reps=12
    ),
    (ExperienceLevel.BEGINNER, EffortType.ISOLATION): SetRepPrescription(
        sets=2, reps=15
    ),
    # Intermediate: increased volume, moderate rep range
    (ExperienceLevel.INTERMEDIATE, EffortType.COMPOUND): SetRepPrescription(
        sets=4, reps=10
    ),
    (ExperienceLevel.INTERMEDIATE, EffortType.ISOLATION): SetRepPrescription(
        sets=3, reps=12
    ),
    # Advanced: high volume, varied rep range
    (ExperienceLevel.ADVANCED, EffortType.COMPOUND): SetRepPrescription(
        sets=5, reps=8
    ),
    (ExperienceLevel.ADVANCED, EffortType.ISOLATION): SetRepPrescription(
        sets=4, reps=10
    ),
}


def calculate_intensity(
    experience: ExperienceLevel,
    effort_type: EffortType,
) -> SetRepPrescription:
    """Return the recommended sets × reps for the given parameters.

    Args:
        experience: User's training experience level.
        effort_type: Whether the exercise is compound or isolation.

    Returns:
        A ``SetRepPrescription`` with ``sets`` and ``reps`` attributes.

    Raises:
        KeyError: If the combination is not found (should never happen
            with the current enum values).
    """
    return _PRESCRIPTIONS[(experience, effort_type)]
