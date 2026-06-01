"""BMI calculator — computes Body Mass Index from weight and height.

Categories follow the WHO classification:
- Sottopeso: BMI < 18.5
- Normopeso: 18.5 ≤ BMI < 25
- Sovrappeso: 25 ≤ BMI < 30
- Obeso: BMI ≥ 30
"""

from __future__ import annotations


def calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float, str]:
    """Return ``(bmi_value, category)`` for the given body measurements.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.

    Returns:
        A tuple of (rounded BMI value, Italian category label).

    Raises:
        ValueError: If weight or height are non-positive.
    """
    if weight_kg <= 0:
        raise ValueError("Il peso deve essere un valore positivo.")
    if height_cm <= 0:
        raise ValueError("L'altezza deve essere un valore positivo.")

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m**2)
    bmi = round(bmi, 1)

    if bmi < 18.5:
        category = "Sottopeso"
    elif bmi < 25:
        category = "Normopeso"
    elif bmi < 30:
        category = "Sovrappeso"
    else:
        category = "Obeso"

    return bmi, category
