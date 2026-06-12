# pylint: disable=too-many-positional-arguments
"""Tests for the live workout session handler."""

# pylint: disable=too-many-arguments, redefined-outer-name

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import ConversationHandler

from wod.bot.handlers.live_workout import (
    SELECT_DAY,
    WAIT_SET_INPUT,
    _advance_state_and_rest,
    _ask_current_set,
    _finish_workout,
    _start_session_for_day,
    build_live_workout_handler,
    cancel_live_workout,
    handle_live_set_action,
    handle_set_input,
    select_day_callback,
    start_live_workout,
)
from wod.db.models import Exercise, GeneratedWorkout, WorkoutExercise


@pytest.fixture
def mock_update() -> Any:
    update = MagicMock(spec=Update)
    update.effective_user.id = 123
    update.effective_chat.id = 456

    query = AsyncMock()
    query.data = "startw:1"
    update.callback_query = query

    message = AsyncMock()
    message.text = "60 10"
    update.message = message
    return update


@pytest.fixture
def mock_context() -> Any:
    context = MagicMock()
    context.user_data = {}
    context.bot.send_message = AsyncMock()
    return context


@pytest.fixture
def mock_workout() -> Any:
    workout = MagicMock(spec=GeneratedWorkout)
    workout.id = 1
    workout.title = "Test Workout"

    ex1 = MagicMock(spec=WorkoutExercise)
    ex1.id = 10
    ex1.day_label = "Giorno 1"
    ex1.sets = 3
    ex1.reps = "10"
    ex1.notes = "Note"
    ex1.exercise = MagicMock(spec=Exercise, name="Squat")
    ex1.exercise.name = "Squat"

    ex2 = MagicMock(spec=WorkoutExercise)
    ex2.id = 11
    ex2.day_label = "Giorno 2"
    ex2.sets = 3
    ex2.reps = "12"
    ex2.notes = None
    ex2.exercise = MagicMock(spec=Exercise, name="Bench")
    ex2.exercise.name = "Bench Press"

    workout.exercises = [ex1, ex2]
    return workout


class TestStartLiveWorkout:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_workout_by_id")
    @patch("wod.bot.handlers.live_workout.get_or_create_user")
    async def test_start_workout_no_workout(
        self,
        mock_get_user: Any,
        mock_get_workout: Any,
        mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_get_workout.return_value = None
        mock_user = MagicMock()
        mock_user.language = "it"
        mock_get_user.return_value = mock_user

        result = await start_live_workout(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_update.callback_query.edit_message_text.assert_called_once_with(
            "⚠️ Impossibile caricare la scheda."
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_workout_by_id")
    @patch("wod.bot.handlers.live_workout.get_or_create_user")
    async def test_start_workout_multiple_days(
        self,
        mock_get_user: Any,
        mock_get_workout: Any,
        mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_get_workout.return_value = mock_workout
        mock_user = MagicMock()
        mock_user.language = "it"
        mock_get_user.return_value = mock_user

        result = await start_live_workout(mock_update, mock_context)

        assert result == SELECT_DAY
        assert mock_context.user_data["live_workout_id"] == 1
        mock_update.callback_query.edit_message_text.assert_called_once()
        assert (
            "Quale giorno"
            in mock_update.callback_query.edit_message_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._start_session_for_day")
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_workout_by_id")
    @patch("wod.bot.handlers.live_workout.get_or_create_user")
    async def test_start_workout_with_day_index(
        self,
        mock_get_user: Any,
        mock_get_workout: Any,
        mock_session_factory: Any,
        mock_start_session: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_get_workout.return_value = mock_workout
        mock_start_session.return_value = WAIT_SET_INPUT
        mock_user = MagicMock()
        mock_user.language = "it"
        mock_get_user.return_value = mock_user

        mock_update.callback_query.data = "startw:1:0"

        result = await start_live_workout(mock_update, mock_context)

        assert result == WAIT_SET_INPUT
        mock_start_session.assert_called_once_with(
            mock_update, mock_context, mock_workout, "Giorno 1"
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._start_session_for_day")
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_workout_by_id")
    @patch("wod.bot.handlers.live_workout.get_or_create_user")
    async def test_start_workout_single_day(
        self,
        mock_get_user: Any,
        mock_get_workout: Any,
        mock_session_factory: Any,
        mock_start_session: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        # Modify workout to have only 1 day
        mock_workout.exercises = [mock_workout.exercises[0]]
        mock_get_workout.return_value = mock_workout
        mock_start_session.return_value = WAIT_SET_INPUT
        mock_user = MagicMock()
        mock_user.language = "it"
        mock_get_user.return_value = mock_user

        mock_update.callback_query.data = "startw:1"

        result = await start_live_workout(mock_update, mock_context)

        assert result == WAIT_SET_INPUT
        mock_start_session.assert_called_once_with(
            mock_update, mock_context, mock_workout, "Giorno 1"
        )


class TestSelectDayCallback:
    @pytest.mark.asyncio
    async def test_select_day_cancel(self, mock_update: Any, mock_context: Any) -> None:
        mock_update.callback_query.data = "selday:cancel"

        result = await select_day_callback(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_update.callback_query.edit_message_text.assert_called_once_with(
            "❌ Allenamento annullato."
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._start_session_for_day")
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_workout_by_id")
    async def test_select_day_valid(
        self,
        mock_get_workout: Any,
        mock_session_factory: Any,
        mock_start_session: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_get_workout.return_value = mock_workout
        mock_start_session.return_value = WAIT_SET_INPUT
        mock_context.user_data["live_workout_id"] = 1
        mock_update.callback_query.data = "selday:Giorno 1"

        result = await select_day_callback(mock_update, mock_context)

        assert result == WAIT_SET_INPUT
        mock_start_session.assert_called_once_with(
            mock_update, mock_context, mock_workout, "Giorno 1"
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_workout_by_id")
    async def test_select_day_not_found(
        self,
        mock_get_workout: Any,
        mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_get_workout.return_value = None
        mock_context.user_data["live_workout_id"] = 1
        mock_update.callback_query.data = "selday:Giorno 1"

        result = await select_day_callback(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_update.callback_query.edit_message_text.assert_called_once_with(
            "⚠️ Errore nel caricamento della scheda."
        )


class TestStartSessionForDay:
    @pytest.mark.asyncio
    async def test_start_session_no_exercises(
        self, mock_update: Any, mock_context: Any, mock_workout: Any
    ) -> None:
        result = await _start_session_for_day(
            mock_update, mock_context, mock_workout, "Non Existent Day"
        )
        assert result == ConversationHandler.END
        mock_update.callback_query.edit_message_text.assert_called_once_with(
            "⚠️ Nessun esercizio trovato per questo giorno."
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._ask_current_set")
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.get_or_create_user")
    @patch("wod.bot.handlers.live_workout.create_workout_session")
    async def test_start_session_valid(
        self,
        mock_create_ws: Any,
        mock_get_user: Any,
        mock_session_factory: Any,
        mock_ask: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_user = MagicMock(id=1)
        mock_get_user.return_value = mock_user
        mock_ws = MagicMock(id=99)
        mock_create_ws.return_value = mock_ws
        mock_ask.return_value = WAIT_SET_INPUT

        result = await _start_session_for_day(
            mock_update, mock_context, mock_workout, "Giorno 1"
        )

        assert result == WAIT_SET_INPUT
        assert mock_context.user_data["live_session_id"] == 99
        assert len(mock_context.user_data["live_exercises"]) == 1
        assert mock_context.user_data["live_ex_index"] == 0
        assert mock_context.user_data["live_set_number"] == 1


class TestAskCurrentSet:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._finish_workout")
    async def test_ask_current_set_finished(
        self, mock_finish: Any, mock_update: Any, mock_context: Any, mock_workout: Any
    ) -> None:
        mock_finish.return_value = ConversationHandler.END
        mock_context.user_data = {
            "live_exercises": [mock_workout.exercises[0]],
            "live_ex_index": 1,
            "live_set_number": 1,
        }

        result = await _ask_current_set(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_finish.assert_called_once()

    @pytest.mark.asyncio
    async def test_ask_current_set_active(
        self, mock_update: Any, mock_context: Any, mock_workout: Any
    ) -> None:
        mock_context.user_data = {
            "live_exercises": [mock_workout.exercises[0]],
            "live_ex_index": 0,
            "live_set_number": 1,
        }

        result = await _ask_current_set(mock_update, mock_context)

        assert result == WAIT_SET_INPUT
        mock_context.bot.send_message.assert_called_once()
        assert "Squat" in mock_context.bot.send_message.call_args[1]["text"]


class TestHandleSetInput:
    @pytest.mark.asyncio
    async def test_invalid_format(self, mock_update: Any, mock_context: Any) -> None:
        mock_update.message.text = "invalid format string"
        result = await handle_set_input(mock_update, mock_context)
        assert result == WAIT_SET_INPUT
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_values(self, mock_update: Any, mock_context: Any) -> None:
        mock_update.message.text = "aa bb"
        result = await handle_set_input(mock_update, mock_context)
        assert result == WAIT_SET_INPUT
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._advance_state_and_rest")
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.log_set")
    async def test_valid_input(
        self,
        mock_log_set: Any,
        mock_session_factory: Any,
        mock_advance: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_update.message.text = "60.5 10"
        mock_context.user_data = {
            "live_session_id": 99,
            "live_exercises": [mock_workout.exercises[0]],
            "live_ex_index": 0,
            "live_set_number": 1,
        }
        mock_advance.return_value = WAIT_SET_INPUT

        result = await handle_set_input(mock_update, mock_context)

        assert result == WAIT_SET_INPUT
        mock_log_set.assert_called_once_with(
            mock_session_factory.return_value.return_value,
            session_id=99,
            workout_exercise_id=10,
            set_number=1,
            weight_kg=60.5,
            reps_done=10,
            skipped=False,
        )


class TestHandleLiveSetAction:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.complete_workout_session")
    async def test_abort(
        self,
        mock_complete: Any,
        mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_update.callback_query.data = "liveset:abort"
        mock_context.user_data["live_session_id"] = 99

        result = await handle_live_set_action(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_complete.assert_called_once_with(
            mock_session_factory.return_value.return_value, 99, status="abandoned"
        )
        assert "live_session_id" not in mock_context.user_data

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._ask_current_set")
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.log_set")
    async def test_skip(
        self,
        mock_log_set: Any,
        mock_session_factory: Any,
        mock_ask: Any,
        mock_update: Any,
        mock_context: Any,
        mock_workout: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_update.callback_query.data = "liveset:skip"
        mock_context.user_data = {
            "live_session_id": 99,
            "live_exercises": [mock_workout.exercises[0]],
            "live_ex_index": 0,
            "live_set_number": 1,
        }
        mock_ask.return_value = WAIT_SET_INPUT

        result = await handle_live_set_action(mock_update, mock_context)

        assert result == WAIT_SET_INPUT
        mock_log_set.assert_called_once_with(
            mock_session_factory.return_value.return_value,
            session_id=99,
            workout_exercise_id=10,
            set_number=1,
            weight_kg=0,
            reps_done=0,
            skipped=True,
        )
        assert mock_context.user_data["live_set_number"] == 2

    @pytest.mark.asyncio
    async def test_invalid_action(self, mock_update: Any, mock_context: Any) -> None:
        mock_update.callback_query.data = "liveset:other"
        result = await handle_live_set_action(mock_update, mock_context)
        assert result == WAIT_SET_INPUT


class TestAdvanceStateAndRest:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._ask_current_set")
    async def test_advance_next_set(
        self, mock_ask: Any, mock_update: Any, mock_context: Any, mock_workout: Any
    ) -> None:
        mock_context.user_data = {
            "live_exercises": [mock_workout.exercises[0]],
            "live_ex_index": 0,
            "live_set_number": 1,
        }
        mock_ask.return_value = WAIT_SET_INPUT
        result = await _advance_state_and_rest(mock_update, mock_context)
        assert result == WAIT_SET_INPUT
        assert mock_context.user_data["live_set_number"] == 2

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout._finish_workout")
    async def test_advance_finish(
        self, mock_finish: Any, mock_update: Any, mock_context: Any, mock_workout: Any
    ) -> None:
        mock_context.user_data = {
            "live_exercises": [mock_workout.exercises[0]],
            "live_ex_index": 0,
            "live_set_number": 3,
        }
        mock_finish.return_value = ConversationHandler.END
        result = await _advance_state_and_rest(mock_update, mock_context)
        assert result == ConversationHandler.END


class TestFinishWorkout:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.complete_workout_session")
    @patch("wod.bot.handlers.live_workout.get_session_logs")
    async def test_finish_workout(
        self,
        mock_get_logs: Any,
        mock_complete: Any,
        mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        mock_ws = MagicMock()
        mock_ws.started_at = datetime.datetime.now() - datetime.timedelta(minutes=45)
        mock_ws.completed_at = datetime.datetime.now()
        mock_complete.return_value = mock_ws

        mock_log = MagicMock()
        mock_log.workout_exercise_id = 10
        mock_log.skipped = False
        mock_log.set_number = 1
        mock_log.weight_kg = 60.5
        mock_log.reps_done = 10
        mock_log.workout_exercise.exercise.name = "Squat"
        mock_get_logs.return_value = [mock_log]

        mock_context.user_data = {"live_session_id": 99, "live_exercises": []}

        result = await _finish_workout(mock_update, mock_context)

        assert result == ConversationHandler.END
        assert "live_session_id" not in mock_context.user_data
        mock_context.bot.send_message.assert_called_once()
        assert (
            "Allenamento Completato"
            in mock_context.bot.send_message.call_args[1]["text"]
        )


class TestCancelLiveWorkout:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.complete_workout_session")
    async def test_cancel_active(
        self,
        mock_complete: Any,
        mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
    ) -> None:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)
        mock_context.user_data["live_session_id"] = 99

        result = await cancel_live_workout(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_complete.assert_called_once()
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.live_workout.get_session_factory")
    @patch("wod.bot.handlers.live_workout.complete_workout_session")
    async def test_cancel_inactive(
        self,
        mock_complete: Any,
        _mock_session_factory: Any,
        mock_update: Any,
        mock_context: Any,
    ) -> None:
        result = await cancel_live_workout(mock_update, mock_context)
        assert result == ConversationHandler.END
        mock_complete.assert_not_called()


class TestBuildLiveWorkoutHandler:
    def test_build(self) -> None:
        handler = build_live_workout_handler()
        assert isinstance(handler, ConversationHandler)
