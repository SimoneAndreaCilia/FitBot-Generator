"""Tests for onboarding handler."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import ConversationHandler

from wod.bot.handlers.onboarding import (
    EQUIPMENT,
    equipment_callback,
)
from wod.core.types import ExperienceLevel, SplitType


# pylint: disable=too-many-instance-attributes
class MockUser:
    def __init__(self, **kwargs: Any) -> None:
        self.name = kwargs.get("name", "Alice")
        self.height_cm = kwargs.get("height_cm", 180)
        self.weight_kg = kwargs.get("weight_kg", 72)
        self.body_type = kwargs.get("body_type", None)
        self.experience_level = kwargs.get("experience_level", None)
        self.training_frequency = kwargs.get("training_frequency", None)
        self.preferred_split = kwargs.get("preferred_split", None)
        self.equipment = kwargs.get("equipment", [])


class TestOnboardingEquipmentCallback:
    """Verify onboarding equipment selection callback."""

    @pytest.mark.asyncio
    async def test_equipment_done_empty(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "equip:done"
        update.callback_query = query

        context = MagicMock()
        context.user_data = {"selected_equipment": set()}

        next_state = await equipment_callback(update, context)

        assert next_state == EQUIPMENT
        query.answer.assert_called_once_with(
            text="⚠️ Seleziona almeno un attrezzo per procedere!",
            show_alert=True,
        )

    @pytest.mark.asyncio
    async def test_equipment_done_valid(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "equip:done"
        query.from_user.id = 123
        update.callback_query = query

        context = MagicMock()
        context.user_data = {
            "selected_equipment": {1},
            "name": "Alice",
            "height_cm": 180.0,
            "weight_kg": 72.0,
            "body_type": None,
            "experience_level": ExperienceLevel.BEGINNER,
            "training_frequency": 3,
            "preferred_split": SplitType.FULL_BODY,
            "bmi_value": "22.2",
            "bmi_category": "Normal",
        }

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.onboarding.finalize.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch(
                "wod.bot.handlers.onboarding.finalize.get_or_create_user",
                return_value=user,
            ),
            patch("wod.bot.handlers.onboarding.finalize.update_user_profile"),
            patch(
                "wod.bot.handlers.onboarding.finalize.set_user_equipment"
            ) as set_eq_mock,
            patch("wod.bot.handlers.wod.wod_command"),
        ):
            next_state = await equipment_callback(update, context)

        assert next_state == ConversationHandler.END
        set_eq_mock.assert_called_once_with(session_mock, user, [1])
        query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_equipment_toggle(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "equip:1"
        update.callback_query = query

        context = MagicMock()
        context.user_data = {
            "equipment_list": [(1, "barbell"), (2, "bench")],
            "selected_equipment": {1},
        }

        # Toggle equipment (1 will be discarded)
        next_state = await equipment_callback(update, context)
        assert next_state == EQUIPMENT
        assert context.user_data["selected_equipment"] == set()
        query.edit_message_text.assert_called_once()
        query.answer.assert_called_once()
