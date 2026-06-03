"""Tests for the 'crea scheda con profilo esistente' conversation flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import ConversationHandler

from wod.bot.handlers.menu import (
    CREA_FREQ,
    CREA_SPLIT,
    _crea_freq_callback,
    _crea_split_callback,
    build_crea_scheda_existing_handler,
    handle_crea_scheda_existing,
)
from wod.core.types import SplitType


class TestHandleCreaSchedaExisting:
    """Verify entry point shows frequency selection."""

    @pytest.mark.asyncio
    async def test_shows_frequency_keyboard(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        next_state = await handle_crea_scheda_existing(update, context)

        assert next_state == CREA_FREQ
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        call_text = query.edit_message_text.call_args[0][0]
        assert "giorni" in call_text.lower()


class TestCreaFreqCallback:
    """Verify frequency selection stores freq and shows split keyboard."""

    @pytest.mark.asyncio
    async def test_stores_frequency_and_shows_split(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "freq:4"
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        next_state = await _crea_freq_callback(update, context)

        assert next_state == CREA_SPLIT
        assert context.user_data["crea_frequency"] == 4
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        call_text = query.edit_message_text.call_args[0][0]
        assert "4 giorni/settimana" in call_text


class TestCreaSplitCallback:
    """Verify split selection updates profile and generates workout."""

    @pytest.mark.asyncio
    async def test_updates_profile_and_generates(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "split:full_body"
        query.from_user.id = 123

        # query.message must be a real Message for isinstance() check
        from telegram import Message  # pylint: disable=import-outside-toplevel

        query.message = MagicMock(spec=Message)
        update.callback_query = query
        update.update_id = 42

        context = MagicMock()
        context.user_data = {"crea_frequency": 3}

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        class MockUser:
            pass

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.menu.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch(
                "wod.bot.handlers.menu.get_or_create_user",
                return_value=user,
            ),
            patch(
                "wod.bot.handlers.menu.update_user_profile",
            ) as update_profile_mock,
            patch(
                "wod.bot.handlers.wod.wod_command", new_callable=AsyncMock
            ) as wod_mock,
        ):
            next_state = await _crea_split_callback(update, context)

        assert next_state == ConversationHandler.END
        update_profile_mock.assert_called_once_with(
            session_mock,
            user,
            training_frequency=3,
            preferred_split=SplitType.FULL_BODY,
        )
        wod_mock.assert_called_once()
        query.answer.assert_called_once()


class TestBuildCreaSchedaExistingHandler:
    """Verify builder returns a ConversationHandler."""

    def test_returns_conversation_handler(self) -> None:
        handler = build_crea_scheda_existing_handler()
        assert isinstance(handler, ConversationHandler)
