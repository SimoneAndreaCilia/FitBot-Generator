"""Tests for the bot main module (application wiring)."""

from __future__ import annotations

import os
from unittest.mock import patch

from telegram.ext import CallbackQueryHandler, CommandHandler

from wod.bot.main import create_application


class TestCreateApplication:
    """Verify that the bot application can be built."""

    def test_creates_application(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "test-token-fake-123"}
        with patch.dict(os.environ, env, clear=True):
            app = create_application()
            assert app is not None

    def test_registers_handlers(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "test-token-fake-123"}
        with patch.dict(os.environ, env, clear=True):
            app = create_application()
            # Should have at least: onboarding conversation, wod, history,
            # favorites command, view/download/fav callbacks
            assert len(app.handlers[0]) >= 8

            history_handler = next(
                (
                    h
                    for h in app.handlers[0]
                    if isinstance(h, CommandHandler) and "history" in h.commands
                ),
                None,
            )
            assert history_handler is not None
            assert "mie_schede" in history_handler.commands

            txt_handler = next(
                (
                    h
                    for h in app.handlers[0]
                    if isinstance(h, CallbackQueryHandler)
                    and h.pattern is not None
                    and getattr(h.pattern, "pattern", "").startswith("^dl_txt")
                ),
                None,
            )
            assert txt_handler is not None
