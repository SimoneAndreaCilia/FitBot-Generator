"""Tests for the bot main module (application wiring)."""

from __future__ import annotations

import os
from unittest.mock import patch

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
            assert len(app.handlers[0]) >= 7
