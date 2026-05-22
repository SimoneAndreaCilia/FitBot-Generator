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
        assert result.reps == "8-12"
        assert result.intensity == "Buffer 1"

    def test_beginner_isolation(self) -> None:
        result = calculate_intensity(ExperienceLevel.BEGINNER, EffortType.ISOLATION)
        assert result.sets == 2
        assert result.reps == "12-15"
        assert result.intensity == "Buffer 1"

    # --- Intermediate ---

    def test_intermediate_compound(self) -> None:
        result = calculate_intensity(ExperienceLevel.INTERMEDIATE, EffortType.COMPOUND)
        assert result.sets == 2
        assert result.reps == "6-10"
        assert result.intensity == "Cedimento tecnico"

    def test_intermediate_isolation(self) -> None:
        result = calculate_intensity(ExperienceLevel.INTERMEDIATE, EffortType.ISOLATION)
        assert result.sets == 2
        assert result.reps == "10-12"
        assert result.intensity == "Cedimento tecnico"

    # --- Advanced ---

    def test_advanced_compound(self) -> None:
        result = calculate_intensity(ExperienceLevel.ADVANCED, EffortType.COMPOUND)
        assert result.sets == 2
        assert result.reps == "4-8"
        assert result.intensity == "Cedimento tecnico"

    def test_advanced_isolation(self) -> None:
        result = calculate_intensity(ExperienceLevel.ADVANCED, EffortType.ISOLATION)
        assert result.sets == 2
        assert result.reps == "8-12"
        assert result.intensity == "Cedimento tecnico"

    # --- All combinations covered ---

    def test_all_combinations_exist(self) -> None:
        """Every (experience, effort_type) combination should return a result."""
        for level in ExperienceLevel:
            for effort in EffortType:
                result = calculate_intensity(level, effort)
                assert isinstance(result, SetRepPrescription)
                assert result.sets > 0
                assert isinstance(result.reps, str)
                assert isinstance(result.intensity, str)


class TestSetRepPrescription:
    """Tests for the SetRepPrescription dataclass."""

    def test_str_representation(self) -> None:
        p = SetRepPrescription(sets=4, reps="10-12", intensity="Cedimento")
        assert str(p) == "4×10-12 (Cedimento)"

    def test_frozen(self) -> None:
        p = SetRepPrescription(sets=3, reps="12", intensity="Buffer 1")
        with pytest.raises(AttributeError):
            p.sets = 5  # type: ignore[misc]

    def test_equality(self) -> None:
        a = SetRepPrescription(sets=3, reps="12", intensity="Buffer 1")
        b = SetRepPrescription(sets=3, reps="12", intensity="Buffer 1")
        assert a == b

    def test_inequality(self) -> None:
        a = SetRepPrescription(sets=3, reps="12", intensity="Buffer 1")
        b = SetRepPrescription(sets=4, reps="10-12", intensity="Cedimento")
        assert a != b
