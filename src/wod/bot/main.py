"""Bot entry point — assembles all handlers and starts polling."""

from __future__ import annotations

import logging
import traceback
from typing import Any

from telegram import Update
from telegram.ext import Application, ContextTypes

from wod.bot.handlers.favorites import (
    build_favorite_callback_handler,
    build_favorites_command_handler,
)
from wod.bot.handlers.history import (
    build_download_pdf_handler,
    build_download_txt_handler,
    build_history_handler,
    build_view_callback_handler,
)
from wod.bot.handlers.live_workout import build_live_workout_handler
from wod.bot.handlers.menu import (
    build_crea_scheda_existing_handler,
    build_menu_handlers,
    build_wod_navigation_handler,
)
from wod.bot.handlers.onboarding import build_onboarding_handler, build_start_handler
from wod.bot.handlers.profile import (
    build_edit_profile_handler,
    build_profile_command_handler,
)
from wod.bot.handlers.wod import build_wod_handler
from wod.config import get_settings
from wod.db.seeding import auto_seed_if_empty

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _ensure_user_profile_columns() -> None:
    """Add profile columns to the users table if they don't exist yet.

    ``create_all()`` won't alter existing tables, so we manually
    check for and add missing columns for SQLite backwards-compatibility.
    """
    from wod.db.session import get_engine  # pylint: disable=import-outside-toplevel

    new_columns = {
        "name": "VARCHAR(128)",
        "height_cm": "FLOAT",
        "weight_kg": "FLOAT",
        "body_type": "VARCHAR(10)",
    }

    async with get_engine().connect() as conn:
        # Get existing column names
        result = await conn.exec_driver_sql("PRAGMA table_info(users)")
        existing = {row[1] for row in result}

        for col_name, col_type in new_columns.items():
            if col_name not in existing:
                await conn.exec_driver_sql(
                    f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                )
                logger.info("Added column 'users.%s'.", col_name)
        await conn.commit()


async def initialize_database(
    application: Application[Any, Any, Any, Any, Any, Any],
) -> None:
    """Initialize and seed database if it is empty."""
    from wod.db.models import Base
    from wod.db.session import get_engine
    
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await _ensure_user_profile_columns()
    await auto_seed_if_empty()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a friendly warning to the user if possible."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if context.error:
        tb_list = traceback.format_exception(
            None, context.error, context.error.__traceback__
        )
        tb_string = "".join(tb_list)
        logger.debug("Detailed traceback:\n%s", tb_string)

    error_msg = (
        "⚠️ Si è verificato un errore imprevisto durante l'elaborazione del comando. "
        "Riprova più tardi."
    )

    if isinstance(update, Update):
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        if update.effective_message:
            try:
                await update.effective_message.reply_text(error_msg)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Failed to notify user about error", exc_info=True)
        elif update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=error_msg
                )
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Failed to notify user about error", exc_info=True)


def create_application() -> Application[Any, Any, Any, Any, Any, Any]:
    """Build the Telegram Application with all handlers registered."""
    settings = get_settings()
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(initialize_database)
        .build()
    )

    # /start command (greeting + menu, not a ConversationHandler)
    app.add_handler(build_start_handler())

    # Conversation handlers (must be added first — they consume updates)
    app.add_handler(build_live_workout_handler())
    app.add_handler(build_onboarding_handler())
    app.add_handler(build_edit_profile_handler())

    # Command handlers
    app.add_handler(build_profile_command_handler())
    app.add_handler(build_wod_handler())
    app.add_handler(build_history_handler())
    app.add_handler(build_favorites_command_handler())

    # Menu button handlers (ReplyKeyboard text messages)
    for handler in build_menu_handlers():
        app.add_handler(handler)

    # Callback query handlers
    app.add_handler(build_crea_scheda_existing_handler())
    app.add_handler(build_wod_navigation_handler())
    app.add_handler(build_view_callback_handler())
    app.add_handler(build_download_pdf_handler())
    app.add_handler(build_download_txt_handler())
    app.add_handler(build_favorite_callback_handler())

    # Global error handler
    app.add_error_handler(error_handler)

    return app


def main() -> None:
    """Start the bot in long-polling mode."""
    logger.info("Starting WOD Telegram Bot...")
    app = create_application()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
