"""Handler builders for the profile module."""

from __future__ import annotations

from typing import Any

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
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
from wod.bot.handlers.profile.display import profile_command
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


def build_profile_command_handler() -> CommandHandler[Any, Any]:
    """Build the /profilo command handler."""
    return CommandHandler("profilo", profile_command)


def build_edit_profile_handler() -> ConversationHandler[ContextTypes.DEFAULT_TYPE]:
    """Build the ConversationHandler for profile editing.

    Entry point is the ``edit_profile`` callback from the profile message.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_profile_entry, pattern=r"^edit_profile$"),
        ],
        states={
            CHOOSE_FIELD: [
                CallbackQueryHandler(field_selection_callback, pattern=r"^editf:"),
            ],
            EDIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name_input),
            ],
            EDIT_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_height_input),
            ],
            EDIT_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_weight_input),
            ],
            EDIT_BODY_TYPE: [
                CallbackQueryHandler(edit_body_type_callback, pattern=r"^body:"),
            ],
            EDIT_EXPERIENCE: [
                CallbackQueryHandler(edit_experience_callback, pattern=r"^exp:"),
            ],
            EDIT_FREQUENCY: [
                CallbackQueryHandler(edit_frequency_callback, pattern=r"^freq:"),
            ],
            EDIT_SPLIT: [
                CallbackQueryHandler(edit_split_callback, pattern=r"^split:"),
            ],
            EDIT_EQUIPMENT: [
                CallbackQueryHandler(edit_equipment_callback, pattern=r"^equip:"),
            ],
            REGEN_CONFIRM: [
                CallbackQueryHandler(regen_callback, pattern=r"^regen:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel_command)],
        per_message=False,
    )
