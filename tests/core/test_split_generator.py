"""Tests for the weekly split generator."""

from __future__ import annotations

import pytest

from wod.core.split_generator import TrainingDay, generate_weekly_split
from wod.core.types import MuscleGroup, SplitType


class TestGenerateWeeklySplit:
    """Verifies the split generator produces correct training plans."""

    # --- Full Body ---

    def test_full_body_3_days(self) -> None:
        """3-day Full Body should produce 3 identical days."""
        days = generate_weekly_split(SplitType.FULL_BODY, 3)
        assert len(days) == 3
        for i, day in enumerate(days, start=1):
            assert day.day_number == i
            assert "Full Body" in day.label
            assert len(day.muscle_groups) == 6  # all muscle groups

    def test_full_body_single_day(self) -> None:
        """1-day Full Body should still hit all groups."""
        days = generate_weekly_split(SplitType.FULL_BODY, 1)
        assert len(days) == 1
        assert set(days[0].muscle_groups) == set(MuscleGroup)

    # --- Upper/Lower ---

    def test_upper_lower_4_days(self) -> None:
        """4-day Upper/Lower should alternate: U, L, U, L."""
        days = generate_weekly_split(SplitType.UPPER_LOWER, 4)
        assert len(days) == 4
        assert "Upper" in days[0].label
        assert "Lower" in days[1].label
        assert "Upper" in days[2].label
        assert "Lower" in days[3].label

    def test_upper_lower_muscle_groups(self) -> None:
        """Upper days should not include LEGS; Lower days should."""
        days = generate_weekly_split(SplitType.UPPER_LOWER, 2)
        upper_day = days[0]
        lower_day = days[1]
        assert MuscleGroup.LEGS not in upper_day.muscle_groups
        assert MuscleGroup.CHEST not in lower_day.muscle_groups
        assert MuscleGroup.LEGS in lower_day.muscle_groups

    # --- Push/Pull/Legs ---

    def test_ppl_6_days(self) -> None:
        """6-day PPL should cycle twice: Push, Pull, Legs, Push, Pull, Legs."""
        days = generate_weekly_split(SplitType.PUSH_PULL_LEGS, 6)
        assert len(days) == 6
        expected_labels = ["Push", "Pull", "Legs", "Push", "Pull", "Legs"]
        for day, expected in zip(days, expected_labels):
            assert expected in day.label

    def test_ppl_3_days(self) -> None:
        """3-day PPL should cover Push, Pull, Legs once."""
        days = generate_weekly_split(SplitType.PUSH_PULL_LEGS, 3)
        assert len(days) == 3
        assert "Push" in days[0].label
        assert "Pull" in days[1].label
        assert "Legs" in days[2].label

    def test_ppl_push_day_groups(self) -> None:
        """Push day should target CHEST and SHOULDERS."""
        days = generate_weekly_split(SplitType.PUSH_PULL_LEGS, 3)
        push_day = days[0]
        assert MuscleGroup.CHEST in push_day.muscle_groups
        assert MuscleGroup.SHOULDERS in push_day.muscle_groups
        assert MuscleGroup.BACK not in push_day.muscle_groups

    # --- Day numbering ---

    def test_day_numbers_are_sequential(self) -> None:
        """Day numbers should be 1-indexed and sequential."""
        days = generate_weekly_split(SplitType.UPPER_LOWER, 5)
        for i, day in enumerate(days, start=1):
            assert day.day_number == i

    # --- Edge cases ---

    def test_frequency_7_days(self) -> None:
        """Maximum frequency (7 days) should work for any split."""
        for split_type in SplitType:
            days = generate_weekly_split(split_type, 7)
            assert len(days) == 7

    def test_invalid_frequency_zero(self) -> None:
        """Frequency 0 should raise ValueError."""
        with pytest.raises(ValueError, match="1-7"):
            generate_weekly_split(SplitType.FULL_BODY, 0)

    def test_invalid_frequency_eight(self) -> None:
        """Frequency 8 should raise ValueError."""
        with pytest.raises(ValueError, match="1-7"):
            generate_weekly_split(SplitType.FULL_BODY, 8)

    def test_invalid_frequency_negative(self) -> None:
        """Negative frequency should raise ValueError."""
        with pytest.raises(ValueError, match="1-7"):
            generate_weekly_split(SplitType.FULL_BODY, -1)

    # --- TrainingDay dataclass ---

    def test_training_day_is_frozen(self) -> None:
        """TrainingDay should be immutable."""
        day = TrainingDay(
            day_number=1,
            label="Test",
            muscle_groups=[MuscleGroup.CHEST],
        )
        with pytest.raises(AttributeError):
            day.day_number = 2  # type: ignore[misc]
