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
    reps: str
    intensity: str

    def __str__(self) -> str:
        return f"{self.sets}×{self.reps} ({self.intensity})"


# Prescription tables keyed by (experience_level, effort_type)
_PRESCRIPTIONS: dict[tuple[ExperienceLevel, EffortType], SetRepPrescription] = {
    # Beginners: not to failure, buffer 1
    (ExperienceLevel.BEGINNER, EffortType.COMPOUND): SetRepPrescription(
        sets=3, reps="8-12", intensity="Buffer 1"
    ),
    (ExperienceLevel.BEGINNER, EffortType.ISOLATION): SetRepPrescription(
        sets=2, reps="12-15", intensity="Buffer 1"
    ),
    # Intermediate: technical failure
    (ExperienceLevel.INTERMEDIATE, EffortType.COMPOUND): SetRepPrescription(
        sets=2, reps="6-10", intensity="Cedimento tecnico"
    ),
    (ExperienceLevel.INTERMEDIATE, EffortType.ISOLATION): SetRepPrescription(
        sets=2, reps="10-12", intensity="Cedimento tecnico"
    ),
    # Advanced: technical failure
    (ExperienceLevel.ADVANCED, EffortType.COMPOUND): SetRepPrescription(
        sets=2, reps="4-8", intensity="Cedimento tecnico"
    ),
    (ExperienceLevel.ADVANCED, EffortType.ISOLATION): SetRepPrescription(
        sets=2, reps="8-12", intensity="Cedimento tecnico"
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
