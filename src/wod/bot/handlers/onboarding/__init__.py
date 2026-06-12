"""Onboarding handler — /start greeting and profile creation flow.

``/start`` greets the user by name and shows the main menu.
The onboarding profile creation flow is triggered separately
via the "Creati una scheda" → "Crea nuovo profilo" menu path.

This package re-exports all public symbols so that existing imports
like ``from wod.bot.handlers.onboarding import build_start_handler``
keep working.
"""

from wod.bot.handlers.onboarding.builders import (
    build_onboarding_handler,
    build_start_handler,
)
from wod.bot.handlers.onboarding.constants import (
    BMI_DISPLAY,
    BODY_TYPE,
    EQUIPMENT,
    EXPERIENCE,
    FREQUENCY,
    HEIGHT,
    NAME,
    SPLIT,
    WEIGHT,
)
from wod.bot.handlers.onboarding.equipment import equipment_callback
from wod.bot.handlers.onboarding.finalize import _finalize_onboarding, cancel_command
from wod.bot.handlers.onboarding.start import build_language_handlers, start_command
from wod.bot.handlers.onboarding.steps import (
    begin_onboarding,
    bmi_continue_callback,
    body_type_callback,
    experience_callback,
    frequency_callback,
    height_input,
    name_input,
    split_callback,
    weight_input,
)

__all__ = [
    "BMI_DISPLAY",
    "BODY_TYPE",
    "EQUIPMENT",
    "EXPERIENCE",
    "FREQUENCY",
    "HEIGHT",
    "NAME",
    "SPLIT",
    "WEIGHT",
    "_finalize_onboarding",
    "begin_onboarding",
    "bmi_continue_callback",
    "body_type_callback",
    "build_language_handlers",
    "build_onboarding_handler",
    "build_start_handler",
    "cancel_command",
    "equipment_callback",
    "experience_callback",
    "frequency_callback",
    "height_input",
    "name_input",
    "split_callback",
    "start_command",
    "weight_input",
]
