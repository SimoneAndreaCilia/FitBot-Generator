"""Tests for the 'crea scheda con profilo esistente' conversation flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, MessageHandler

from wod.bot.handlers.menu import (
    CREA_FREQ,
    CREA_SPLIT,
    _crea_freq_callback,
    _crea_split_callback,
    build_crea_scheda_existing_handler,
    build_menu_handlers,
    build_wod_navigation_handler,
    handle_altro,
    handle_crea_scheda,
    handle_crea_scheda_existing,
    handle_preferiti,
    handle_profilo,
    handle_storico,
    handle_wod_giorno,
    handle_wod_navigation,
)
from wod.core.types import SplitType
from wod.db.models import GeneratedWorkout


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


class TestMenuHandlers:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.menu.get_session_factory")
    @patch("wod.bot.handlers.menu.get_user_with_equipment")
    async def test_handle_crea_scheda_complete_profile(
        self, mock_get_user, mock_session_factory
    ):
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        user = MagicMock()
        user.experience_level = "beginner"
        user.training_frequency = 3
        user.preferred_split = "full_body"
        user.equipment = [MagicMock()]
        mock_get_user.return_value = user

        await handle_crea_scheda(update, context)

        update.message.reply_text.assert_called_once()
        assert (
            "Hai già un profilo configurato!"
            in update.message.reply_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.menu.get_session_factory")
    @patch("wod.bot.handlers.menu.get_user_with_equipment")
    async def test_handle_crea_scheda_incomplete_profile(
        self, mock_get_user, mock_session_factory
    ):
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        mock_get_user.return_value = None

        await handle_crea_scheda(update, context)

        update.message.reply_text.assert_called_once()
        assert (
            "Non hai ancora un profilo completo"
            in update.message.reply_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    async def test_handle_altro(self):
        update = MagicMock()
        update.message = AsyncMock()
        await handle_altro(update, MagicMock())
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.profile.profile_command")
    async def test_handle_profilo(self, mock_cmd):
        update, context = MagicMock(), MagicMock()
        await handle_profilo(update, context)
        mock_cmd.assert_called_once_with(update, context)

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.history.history_command")
    async def test_handle_storico(self, mock_cmd):
        update, context = MagicMock(), MagicMock()
        await handle_storico(update, context)
        mock_cmd.assert_called_once_with(update, context)

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.favorites.favorites_command")
    async def test_handle_preferiti(self, mock_cmd):
        update, context = MagicMock(), MagicMock()
        await handle_preferiti(update, context)
        mock_cmd.assert_called_once_with(update, context)

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.menu.get_session_factory")
    @patch("wod.bot.handlers.menu.get_or_create_user")
    @patch("wod.bot.handlers.menu.get_user_workouts")
    async def test_handle_wod_giorno_no_workouts(
        self, mock_get_workouts, _mock_get_user, mock_session_factory
    ):
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        mock_get_workouts.return_value = []

        await handle_wod_giorno(update, context)

        update.message.reply_text.assert_called_once()
        assert (
            "Non hai ancora generato nessuna scheda"
            in update.message.reply_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.menu.get_session_factory")
    @patch("wod.bot.handlers.menu.get_or_create_user")
    @patch("wod.bot.handlers.menu.get_user_workouts")
    async def test_handle_wod_giorno_with_workouts(
        self, mock_get_workouts, _mock_get_user, mock_session_factory
    ):
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        workout = GeneratedWorkout(
            id=1,
            content_json=(
                '{"exercises": [{"day_label": "Day 1", '
                '"name": "Squat", "sets": 3, "reps": "10"}]}'
            ),
        )
        mock_get_workouts.return_value = [workout]

        await handle_wod_giorno(update, context)

        update.message.reply_text.assert_called_once()
        assert context.user_data["wod_workout_id"] == 1
        assert context.user_data["wod_current_day"] == 0

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.menu.get_session_factory")
    @patch("wod.bot.handlers.menu.get_or_create_user")
    @patch("wod.bot.handlers.menu.get_user_workouts")
    async def test_handle_wod_giorno_no_days(
        self, mock_get_workouts, _mock_get_user, mock_session_factory
    ):
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        workout = GeneratedWorkout(id=1, content_json='{"exercises": []}')
        mock_get_workouts.return_value = [workout]

        await handle_wod_giorno(update, context)

        update.message.reply_text.assert_called_once()
        assert (
            "La scheda non contiene giornate"
            in update.message.reply_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    async def test_handle_wod_navigation(self):
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "wodday:1"
        update.callback_query = query
        context = MagicMock()
        context.user_data = {
            "wod_days": [
                {"label": "Day 1", "exercises": []},
                {"label": "Day 2", "exercises": []},
            ],
            "wod_workout_id": 1,
        }

        await handle_wod_navigation(update, context)

        assert context.user_data["wod_current_day"] == 1
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_wod_navigation_noop(self):
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "wodday:noop"
        update.callback_query = query
        context = MagicMock()

        await handle_wod_navigation(update, context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_wod_navigation_invalid(self):
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "wodday:99"
        update.callback_query = query
        context = MagicMock()
        context.user_data = {
            "wod_days": [{"label": "Day 1", "exercises": []}],
            "wod_workout_id": 1,
        }

        await handle_wod_navigation(update, context)
        query.answer.assert_called_with("⚠️ Giornata non disponibile.", show_alert=True)


class TestBuilders:
    def test_build_menu_handlers(self):
        handlers = build_menu_handlers()
        assert len(handlers) == 6
        for h in handlers:
            assert isinstance(h, MessageHandler)

    def test_build_wod_navigation_handler(self):
        handler = build_wod_navigation_handler()
        assert isinstance(handler, CallbackQueryHandler)
