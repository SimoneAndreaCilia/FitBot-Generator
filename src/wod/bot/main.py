"""Bot entry point — assembles all handlers and starts polling."""

from __future__ import annotations

import logging
from typing import Any

from telegram.ext import Application

from wod.bot.handlers.favorites import (
    build_favorite_callback_handler,
    build_favorites_command_handler,
)
from wod.bot.handlers.history import (
    build_download_pdf_handler,
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
    application: Application[Any, Any, Any, Any, Any, Any]
) -> None:
    """Initialize and seed database if it is empty."""
    await auto_seed_if_empty()


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
    app.add_handler(build_favorite_callback_handler())

    return app


def main() -> None:
    """Start the bot in long-polling mode."""
    logger.info("Starting WOD Telegram Bot...")
    app = create_application()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
