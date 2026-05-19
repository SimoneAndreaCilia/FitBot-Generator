"""Tests for the intensity calculator."""

from __future__ import annotations

import pytest

from wod.core.intensity import SetRepPrescription, calculate_intensity
from wod.core.types import EffortType, ExperienceLevel


class TestCalculateIntensity:
    """Verifies that the set/rep prescription matches expected guidelines."""

    # --- Beginners ---

    def test_beginner_compound(self) -> None:
        result = calculate_intensity(ExperienceLevel.BEGINNER, EffortType.COMPOUND)
        assert result.sets == 3
        assert result.reps == 12

    def test_beginner_isolation(self) -> None:
        result = calculate_intensity(ExperienceLevel.BEGINNER, EffortType.ISOLATION)
        assert result.sets == 2
        assert result.reps == 15

    # --- Intermediate ---

    def test_intermediate_compound(self) -> None:
        result = calculate_intensity(
            ExperienceLevel.INTERMEDIATE, EffortType.COMPOUND
        )
        assert result.sets == 4
        assert result.reps == 10

    def test_intermediate_isolation(self) -> None:
        result = calculate_intensity(
            ExperienceLevel.INTERMEDIATE, EffortType.ISOLATION
        )
        assert result.sets == 3
        assert result.reps == 12

    # --- Advanced ---

    def test_advanced_compound(self) -> None:
        result = calculate_intensity(ExperienceLevel.ADVANCED, EffortType.COMPOUND)
        assert result.sets == 5
        assert result.reps == 8

    def test_advanced_isolation(self) -> None:
        result = calculate_intensity(ExperienceLevel.ADVANCED, EffortType.ISOLATION)
        assert result.sets == 4
        assert result.reps == 10

    # --- Volume progression ---

    def test_compound_volume_increases_with_experience(self) -> None:
        """Total volume (sets * reps) should generally increase with level."""
        beginner = calculate_intensity(ExperienceLevel.BEGINNER, EffortType.COMPOUND)
        intermediate = calculate_intensity(
            ExperienceLevel.INTERMEDIATE, EffortType.COMPOUND
        )
        advanced = calculate_intensity(ExperienceLevel.ADVANCED, EffortType.COMPOUND)

        vol_b = beginner.sets * beginner.reps
        vol_i = intermediate.sets * intermediate.reps
        vol_a = advanced.sets * advanced.reps

        assert vol_b <= vol_i <= vol_a

    def test_sets_increase_with_experience(self) -> None:
        """Sets should increase as experience grows (for compound)."""
        beginner = calculate_intensity(ExperienceLevel.BEGINNER, EffortType.COMPOUND)
        intermediate = calculate_intensity(
            ExperienceLevel.INTERMEDIATE, EffortType.COMPOUND
        )
        advanced = calculate_intensity(ExperienceLevel.ADVANCED, EffortType.COMPOUND)

        assert beginner.sets <= intermediate.sets <= advanced.sets

    # --- All combinations covered ---

    def test_all_combinations_exist(self) -> None:
        """Every (experience, effort_type) combination should return a result."""
        for level in ExperienceLevel:
            for effort in EffortType:
                result = calculate_intensity(level, effort)
                assert isinstance(result, SetRepPrescription)
                assert result.sets > 0
                assert result.reps > 0


class TestSetRepPrescription:
    """Tests for the SetRepPrescription dataclass."""

    def test_str_representation(self) -> None:
        p = SetRepPrescription(sets=4, reps=10)
        assert str(p) == "4×10"

    def test_frozen(self) -> None:
        p = SetRepPrescription(sets=3, reps=12)
        with pytest.raises(AttributeError):
            p.sets = 5  # type: ignore[misc]

    def test_equality(self) -> None:
        a = SetRepPrescription(sets=3, reps=12)
        b = SetRepPrescription(sets=3, reps=12)
        assert a == b

    def test_inequality(self) -> None:
        a = SetRepPrescription(sets=3, reps=12)
        b = SetRepPrescription(sets=4, reps=10)
        assert a != b
