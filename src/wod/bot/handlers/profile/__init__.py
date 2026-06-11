"""Profile handler — /profilo command and profile editing.

Provides:
* ``/profilo`` — Display the user's complete profile with a "Modifica" button.
* Edit conversation — Pick a field to modify, update it, and optionally
  regenerate the workout when equipment changes.

This package re-exports all public symbols so that existing imports
like ``from wod.bot.handlers.profile import build_edit_profile_handler``
keep working.
"""

from wod.bot.handlers.profile.builders import (
    build_edit_profile_handler,
    build_profile_command_handler,
)
from wod.bot.handlers.profile.constants import (
    CHOOSE_FIELD,
    EDIT_BODY_TYPE,
    EDIT_EQUIPMENT,
    EDIT_EXPERIENCE,
    EDIT_FREQUENCY,
    EDIT_HEIGHT,
    EDIT_NAME,
    EDIT_SPLIT,
    EDIT_WEIGHT,
    REGEN_CONFIRM,
)
from wod.bot.handlers.profile.display import _format_profile_text, profile_command
from wod.bot.handlers.profile.edit_equipment import edit_equipment_callback
from wod.bot.handlers.profile.edit_fields import (
    edit_body_type_callback,
    edit_experience_callback,
    edit_frequency_callback,
    edit_height_input,
    edit_name_input,
    edit_profile_entry,
    edit_split_callback,
    edit_weight_input,
    field_selection_callback,
)
from wod.bot.handlers.profile.regen import edit_cancel_command, regen_callback

__all__ = [
    "CHOOSE_FIELD",
    "EDIT_BODY_TYPE",
    "EDIT_EQUIPMENT",
    "EDIT_EXPERIENCE",
    "EDIT_FREQUENCY",
    "EDIT_HEIGHT",
    "EDIT_NAME",
    "EDIT_SPLIT",
    "EDIT_WEIGHT",
    "REGEN_CONFIRM",
    "_format_profile_text",
    "build_edit_profile_handler",
    "build_profile_command_handler",
    "edit_body_type_callback",
    "edit_cancel_command",
    "edit_equipment_callback",
    "edit_experience_callback",
    "edit_frequency_callback",
    "edit_height_input",
    "edit_name_input",
    "edit_profile_entry",
    "edit_split_callback",
    "edit_weight_input",
    "field_selection_callback",
    "profile_command",
    "regen_callback",
]
