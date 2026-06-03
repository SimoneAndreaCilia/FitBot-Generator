"""Tests for the WOD command handler."""

# pylint: disable=too-many-arguments

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import CommandHandler

from wod.bot.handlers.wod import (
    _prescribe_exercises,
    _select_exercises,
    build_wod_handler,
    wod_command,
)
from wod.core.types import EffortType, ExperienceLevel, MuscleGroup, SplitType
from wod.db.models import Exercise, GeneratedWorkout, User


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user.id = 123
    update.message = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    return MagicMock()


class TestWodCommand:
    @pytest.mark.asyncio
    @patch("wod.bot.handlers.wod.get_session_factory")
    @patch("wod.bot.handlers.wod.get_or_create_user")
    async def test_incomplete_profile(
        self, mock_get_user, mock_session_factory, mock_update, mock_context
    ):
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        user = User(id=1, experience_level=None)
        mock_get_user.return_value = user

        await wod_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "non è completo" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.wod.get_session_factory")
    @patch("wod.bot.handlers.wod.get_or_create_user")
    @patch("wod.bot.handlers.wod.get_all_exercises")
    async def test_no_equipment(
        self,
        mock_get_exercises,
        mock_get_user,
        mock_session_factory,
        mock_update,
        mock_context,
    ):
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        user = User(
            id=1,
            experience_level=ExperienceLevel.BEGINNER,
            training_frequency=3,
            preferred_split=SplitType.FULL_BODY,
            equipment=[],
        )
        mock_get_user.return_value = user
        mock_get_exercises.return_value = []

        await wod_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert (
            "Non hai selezionato nessuna attrezzatura"
            in mock_update.message.reply_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.wod.get_session_factory")
    @patch("wod.bot.handlers.wod.get_or_create_user")
    @patch("wod.bot.handlers.wod.get_all_exercises")
    @patch("wod.bot.handlers.wod.filter_exercises_by_equipment")
    async def test_no_compatible_exercises(
        self,
        mock_filter_eq,
        mock_get_exercises,
        mock_get_user,
        mock_session_factory,
        mock_update,
        mock_context,
    ):
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        user = User(
            id=1,
            experience_level=ExperienceLevel.BEGINNER,
            training_frequency=3,
            preferred_split=SplitType.FULL_BODY,
            equipment=[MagicMock(id=1)],
        )
        mock_get_user.return_value = user
        mock_get_exercises.return_value = [MagicMock()]
        mock_filter_eq.return_value = []

        await wod_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert (
            "Non ho trovato esercizi compatibili"
            in mock_update.message.reply_text.call_args[0][0]
        )

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.wod.send_workout_text")
    @patch("wod.bot.handlers.wod.save_workout")
    @patch("wod.bot.handlers.wod.get_session_factory")
    @patch("wod.bot.handlers.wod.get_or_create_user")
    @patch("wod.bot.handlers.wod.get_all_exercises")
    @patch("wod.bot.handlers.wod.filter_exercises_by_equipment")
    @patch("wod.bot.handlers.wod.generate_weekly_split")
    @patch("wod.bot.handlers.wod.filter_exercises_by_muscle_groups")
    @patch("wod.bot.handlers.wod._select_exercises")
    @patch("wod.bot.handlers.wod._prescribe_exercises")
    async def test_successful_generation(
        self,
        mock_prescribe,
        mock_select,
        mock_filter_muscle,
        mock_gen_split,
        mock_filter_eq,
        mock_get_exercises,
        mock_get_user,
        mock_session_factory,
        mock_save_workout,
        mock_send_workout,
        mock_update,
        mock_context,
    ):
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        user = User(
            id=1,
            experience_level=ExperienceLevel.BEGINNER,
            training_frequency=3,
            preferred_split=SplitType.FULL_BODY,
            equipment=[MagicMock(id=1)],
        )
        mock_get_user.return_value = user
        mock_get_exercises.return_value = [MagicMock()]
        mock_filter_eq.return_value = [MagicMock()]

        training_day = MagicMock()
        training_day.muscle_groups = [MuscleGroup.CHEST]
        training_day.label = "Day 1"
        mock_gen_split.return_value = [training_day]
        mock_filter_muscle.return_value = [MagicMock()]
        mock_select.return_value = [MagicMock()]

        formatted_ex = MagicMock()
        formatted_ex.name = "Push Up"
        formatted_ex.sets = 3
        formatted_ex.reps = "10"
        formatted_ex.notes = "Do it right"
        formatted_ex.day_label = "Day 1"
        formatted_ex.order = 1
        formatted_ex.intensity = "RIR 1"
        mock_prescribe.return_value = [formatted_ex]

        workout = GeneratedWorkout(id=10)
        mock_save_workout.return_value = workout

        await wod_command(mock_update, mock_context)

        mock_save_workout.assert_called_once()
        mock_send_workout.assert_called_once()

    @pytest.mark.asyncio
    @patch("wod.bot.handlers.wod.get_session_factory")
    @patch("wod.bot.handlers.wod.get_or_create_user")
    @patch("wod.bot.handlers.wod.get_all_exercises")
    @patch("wod.bot.handlers.wod.filter_exercises_by_equipment")
    @patch("wod.bot.handlers.wod.generate_weekly_split")
    @patch("wod.bot.handlers.wod.filter_exercises_by_muscle_groups")
    @patch("wod.bot.handlers.wod._select_exercises")
    @patch("wod.bot.handlers.wod._prescribe_exercises")
    async def test_no_prescribed_exercises(
        self,
        mock_prescribe,
        mock_select,
        mock_filter_muscle,
        mock_gen_split,
        mock_filter_eq,
        mock_get_exercises,
        mock_get_user,
        mock_session_factory,
        mock_update,
        mock_context,
    ):
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = MagicMock(return_value=session_mock)

        user = User(
            id=1,
            experience_level=ExperienceLevel.BEGINNER,
            training_frequency=3,
            preferred_split=SplitType.FULL_BODY,
            equipment=[MagicMock(id=1)],
        )
        mock_get_user.return_value = user
        mock_get_exercises.return_value = [MagicMock()]
        mock_filter_eq.return_value = [MagicMock()]

        training_day = MagicMock()
        training_day.muscle_groups = [MuscleGroup.CHEST]
        training_day.label = "Day 1"
        mock_gen_split.return_value = [training_day]
        mock_filter_muscle.return_value = [MagicMock()]
        mock_select.return_value = []
        mock_prescribe.return_value = []

        await wod_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert (
            "Non ho trovato esercizi sufficienti"
            in mock_update.message.reply_text.call_args[0][0]
        )


class TestSelectExercises:
    def test_select_exercises_arms(self):
        training_day = MagicMock()
        training_day.muscle_groups = [MuscleGroup.BICEPS]

        ex1 = Exercise(
            muscle_group=MuscleGroup.BICEPS, weight=1, effort_type=EffortType.COMPOUND
        )
        ex2 = Exercise(
            muscle_group=MuscleGroup.BICEPS, weight=2, effort_type=EffortType.ISOLATION
        )

        selected = _select_exercises([ex1, ex2], training_day)

        # Biceps should select only 1, preferring weight=2
        assert len(selected) == 1
        assert selected[0].weight == 2

    def test_select_exercises_other_groups(self):
        training_day = MagicMock()
        training_day.muscle_groups = [MuscleGroup.CHEST]

        ex1 = Exercise(
            muscle_group=MuscleGroup.CHEST, weight=1, effort_type=EffortType.COMPOUND
        )
        ex2 = Exercise(
            muscle_group=MuscleGroup.CHEST, weight=2, effort_type=EffortType.ISOLATION
        )

        selected = _select_exercises([ex1, ex2], training_day)

        # Other groups select 1 weight 1 and 1 weight 2
        assert len(selected) == 2
        weights = [e.weight for e in selected]
        assert 1 in weights
        assert 2 in weights


class TestPrescribeExercises:
    def test_prescribe_exercises(self):
        ex = Exercise(name="Push Up", effort_type=EffortType.ISOLATION)
        result = _prescribe_exercises([ex], ExperienceLevel.BEGINNER, "Day 1", 1)

        assert len(result) == 1
        assert result[0].name == "Push Up"
        assert result[0].day_label == "Day 1"
        assert result[0].order == 1


class TestBuildWodHandler:
    def test_build(self):
        handler = build_wod_handler()
        assert isinstance(handler, CommandHandler)
