"""Tests for wod.core.bmi — BMI calculator."""

from __future__ import annotations

import pytest

from wod.core.bmi import calculate_bmi


class TestCalculateBmi:
    """Verify BMI calculation and categorisation."""

    def test_normopeso(self) -> None:
        bmi, cat = calculate_bmi(70, 175)
        assert cat == "bmi_normal"
        assert bmi == 22.9

    def test_sottopeso(self) -> None:
        bmi, cat = calculate_bmi(50, 180)
        assert cat == "bmi_underweight"
        assert bmi < 18.5

    def test_sovrappeso(self) -> None:
        bmi, cat = calculate_bmi(85, 175)
        assert cat == "bmi_overweight"
        assert 25 <= bmi < 30

    def test_obeso(self) -> None:
        bmi, cat = calculate_bmi(120, 170)
        assert cat == "bmi_obese"
        assert bmi >= 30

    def test_boundary_normopeso_lower(self) -> None:
        """BMI exactly 18.5 should be 'Normopeso'."""
        # height=100cm, weight=18.5kg → BMI = 18.5
        bmi, cat = calculate_bmi(18.5, 100)
        assert cat == "bmi_normal"
        assert bmi == 18.5

    def test_boundary_sovrappeso_lower(self) -> None:
        """BMI exactly 25.0 should be 'Sovrappeso'."""
        # height=100cm, weight=25kg → BMI = 25.0
        bmi, cat = calculate_bmi(25, 100)
        assert cat == "bmi_overweight"
        assert bmi == 25.0

    def test_boundary_obeso_lower(self) -> None:
        """BMI exactly 30.0 should be 'Obeso'."""
        # height=100cm, weight=30kg → BMI = 30.0
        bmi, cat = calculate_bmi(30, 100)
        assert cat == "bmi_obese"
        assert bmi == 30.0

    def test_rounding(self) -> None:
        bmi, _ = calculate_bmi(70, 175)
        # 70 / 1.75^2 = 22.857... → rounded to 22.9
        assert bmi == 22.9

    def test_invalid_weight_zero(self) -> None:
        with pytest.raises(ValueError, match="peso"):
            calculate_bmi(0, 175)

    def test_invalid_weight_negative(self) -> None:
        with pytest.raises(ValueError, match="peso"):
            calculate_bmi(-5, 175)

    def test_invalid_height_zero(self) -> None:
        with pytest.raises(ValueError, match="altezza"):
            calculate_bmi(70, 0)

    def test_invalid_height_negative(self) -> None:
        with pytest.raises(ValueError, match="altezza"):
            calculate_bmi(70, -10)
