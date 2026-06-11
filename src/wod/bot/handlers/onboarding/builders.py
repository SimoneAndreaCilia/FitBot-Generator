"""Handler builders for the onboarding module."""

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
from wod.bot.handlers.onboarding.finalize import cancel_command
from wod.bot.handlers.onboarding.start import start_command
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


def build_start_handler() -> CommandHandler[Any, Any]:
    """Build the /start command handler (greeting + menu)."""
    return CommandHandler("start", start_command)


def build_onboarding_handler() -> ConversationHandler[ContextTypes.DEFAULT_TYPE]:
    """Build and return the ConversationHandler for onboarding.

    Entry point is the ``crea:new`` callback from the menu choice keyboard.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(begin_onboarding, pattern=r"^crea:new$"),
        ],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    name_input,
                )
            ],
            HEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    height_input,
                )
            ],
            WEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    weight_input,
                )
            ],
            BODY_TYPE: [CallbackQueryHandler(body_type_callback, pattern=r"^body:")],
            BMI_DISPLAY: [
                CallbackQueryHandler(bmi_continue_callback, pattern=r"^bmi:")
            ],
            EXPERIENCE: [CallbackQueryHandler(experience_callback, pattern=r"^exp:")],
            FREQUENCY: [CallbackQueryHandler(frequency_callback, pattern=r"^freq:")],
            SPLIT: [CallbackQueryHandler(split_callback, pattern=r"^split:")],
            EQUIPMENT: [CallbackQueryHandler(equipment_callback, pattern=r"^equip:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        per_message=False,
    )
