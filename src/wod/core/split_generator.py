"""Split generator — organizes the weekly training plan.

Given a user's preferred split type and training frequency, this module
distributes muscle groups across the training days following established
bodybuilding / strength-training conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from wod.core.types import SPLIT_TEMPLATES, MuscleGroup, SplitType


@dataclass(frozen=True)
class TrainingDay:
    """A single day in the weekly plan."""

    day_number: int
    label: str
    muscle_groups: list[MuscleGroup] = field(default_factory=list)


def generate_weekly_split(
    split_type: SplitType,
    frequency: int,
) -> list[TrainingDay]:
    """Generate a list of training days for the week.

    The template for each ``split_type`` defines a repeating cycle of
    muscle-group groupings.  This function distributes ``frequency`` days
    across that cycle, wrapping around as needed.

    Args:
        split_type: The chosen split strategy.
        frequency: How many days per week the user trains (1-7).

    Returns:
        A list of ``TrainingDay`` objects, one per training day.

    Raises:
        ValueError: If ``frequency`` is not between 1 and 7.
    """
    if not 1 <= frequency <= 7:
        raise ValueError(f"Frequency must be 1-7, got {frequency}")

    template = SPLIT_TEMPLATES[split_type]
    days: list[TrainingDay] = []

    label_map = {
        SplitType.FULL_BODY: "Full Body",
        SplitType.UPPER_LOWER: ["Upper Body", "Lower Body"],
        SplitType.PUSH_PULL_LEGS: ["Push", "Pull", "Legs"],
    }

    for i in range(frequency):
        cycle_index = i % len(template)
        muscle_groups = template[cycle_index]

        raw_label = label_map[split_type]
        if isinstance(raw_label, list):
            label = raw_label[cycle_index]
        else:
            label = raw_label

        days.append(
            TrainingDay(
                day_number=i + 1,
                label=f"{label} — Day {i + 1}",
                muscle_groups=list(muscle_groups),
            )
        )

    return days
