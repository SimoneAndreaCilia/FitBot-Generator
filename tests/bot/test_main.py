"""Tests for the bot main module (application wiring)."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler

from wod.bot.main import (
    _ensure_user_profile_columns,
    create_application,
    error_handler,
    initialize_database,
    main,
)


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


class TestErrorHandler:
    """Verify that the global error handler functions correctly."""

    @pytest.mark.asyncio
    async def test_error_handler_with_message(self) -> None:
        update = MagicMock(spec=Update)
        update.effective_message = AsyncMock()
        update.callback_query = None

        context = MagicMock()
        context.error = ValueError("Test error")

        await error_handler(update, context)

        update.effective_message.reply_text.assert_called_once_with(
            "⚠️ Si è verificato un errore imprevisto "
            "durante l'elaborazione del comando. "
            "Riprova più tardi."
        )

    @pytest.mark.asyncio
    async def test_error_handler_with_callback(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.message = AsyncMock()
        update.callback_query = query
        update.effective_message = query.message
        update.effective_chat = None

        context = MagicMock()
        context.error = ValueError("Test callback error")

        await error_handler(update, context)

        query.answer.assert_called_once()
        query.message.reply_text.assert_called_once_with(
            "⚠️ Si è verificato un errore imprevisto "
            "durante l'elaborazione del comando. "
            "Riprova più tardi."
        )

    @pytest.mark.asyncio
    async def test_error_handler_fallback_to_chat(self) -> None:
        update = MagicMock(spec=Update)
        update.effective_message = None
        update.callback_query = None
        chat = MagicMock()
        chat.id = 12345
        update.effective_chat = chat

        context = MagicMock()
        context.bot.send_message = AsyncMock()
        context.error = ValueError("Test fallback error")

        await error_handler(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="⚠️ Si è verificato un errore imprevisto "
            "durante l'elaborazione del comando. "
            "Riprova più tardi.",
        )

    @pytest.mark.asyncio
    async def test_error_handler_non_update(self) -> None:
        # Non-Update object should not raise exceptions but just log
        context = MagicMock()
        context.error = ValueError("Test non-update error")

        # Calling with an arbitrary object should not crash
        await error_handler(object(), context)


class TestDatabaseInitialization:
    @pytest.mark.asyncio
    @patch("wod.bot.main.get_engine")
    async def test_ensure_user_profile_columns(self, mock_engine):
        mock_conn = AsyncMock()
        # Mock pragma result
        mock_conn.exec_driver_sql.return_value = [("0", "id")]

        mock_engine.return_value.connect.return_value.__aenter__.return_value = (
            mock_conn
        )

        await _ensure_user_profile_columns()

        assert mock_conn.exec_driver_sql.call_count == 6  # 1 for PRAGMA, 5 for columns
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("wod.bot.main.get_engine")
    @patch("wod.bot.main._ensure_user_profile_columns")
    @patch("wod.bot.main.auto_seed_if_empty")
    async def test_initialize_database(self, mock_seed, mock_ensure, mock_engine):
        mock_conn = AsyncMock()
        mock_engine.return_value.begin.return_value.__aenter__.return_value = mock_conn

        await initialize_database(MagicMock())

        mock_conn.run_sync.assert_called_once()
        mock_ensure.assert_called_once()
        mock_seed.assert_called_once()


class TestMain:
    @patch("wod.bot.main.create_application")
    def test_main(self, mock_create):
        mock_app = MagicMock()
        mock_create.return_value = mock_app

        main()

        mock_app.run_polling.assert_called_once_with(drop_pending_updates=True)
