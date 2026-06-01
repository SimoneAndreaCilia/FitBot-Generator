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
from wod.bot.handlers.onboarding import build_onboarding_handler
from wod.bot.handlers.wod import build_wod_handler
from wod.config import get_settings
from wod.db.seeding import auto_seed_if_empty

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def initialize_database(
    application: Application[Any, Any, Any, Any, Any, Any],
) -> None:
    """Initialize and seed database if it is empty."""
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

    # Conversation handler (must be added first — it consumes updates)
    app.add_handler(build_onboarding_handler())

    # Command handlers
    app.add_handler(build_wod_handler())
    app.add_handler(build_history_handler())
    app.add_handler(build_favorites_command_handler())

    # Callback query handlers
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
