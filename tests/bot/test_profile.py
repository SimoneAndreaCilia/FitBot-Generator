"""Tests for profile handler — /profilo command and editing."""

# pylint: disable=import-error

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import ConversationHandler

from wod.bot.handlers.profile import (
    CHOOSE_FIELD,
    EDIT_BODY_TYPE,
    EDIT_EQUIPMENT,
    EDIT_EXPERIENCE,
    EDIT_FREQUENCY,
    EDIT_HEIGHT,
    EDIT_NAME,
    EDIT_SPLIT,
    EDIT_WEIGHT,
    REGEN_CONFIRM,
    _format_profile_text,
    build_edit_profile_handler,
    build_profile_command_handler,
    edit_body_type_callback,
    edit_cancel_command,
    edit_equipment_callback,
    edit_experience_callback,
    edit_frequency_callback,
    edit_height_input,
    edit_name_input,
    edit_profile_entry,
    edit_split_callback,
    edit_weight_input,
    field_selection_callback,
    profile_command,
    regen_callback,
)
from wod.core.types import BodyType, ExperienceLevel, SplitType


class MockEquipment:
    def __init__(self, id_val: int, name: str):
        self.id = id_val
        self.name = name


# pylint: disable=too-many-instance-attributes
class MockUser:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", None)
        self.height_cm = kwargs.get("height_cm", None)
        self.weight_kg = kwargs.get("weight_kg", None)
        self.body_type = kwargs.get("body_type", None)
        self.experience_level = kwargs.get("experience_level", None)
        self.training_frequency = kwargs.get("training_frequency", None)
        self.preferred_split = kwargs.get("preferred_split", None)
        self.equipment = kwargs.get("equipment", [])


class TestFormatProfileText:
    """Verify profile text formatting."""

    def test_format_profile_text_empty(self) -> None:
        user = MockUser()
        text = _format_profile_text(user)
        assert "Nome: —" in text
        assert "Altezza: —" in text
        assert "Peso: —" in text
        assert "BMI: —" in text
        assert "Corporatura: —" in text
        assert "Livello: —" in text
        assert "Frequenza: —" in text
        assert "Split: —" in text
        assert "Attrezzatura: Nessuna" in text

    def test_format_profile_text_full(self) -> None:
        eq1 = MockEquipment(1, "barbell")
        eq2 = MockEquipment(2, "bench_press")
        user = MockUser(
            name="Alice",
            height_cm=180,
            weight_kg=72.5,
            body_type=BodyType.MESOMORPH,
            experience_level=ExperienceLevel.ADVANCED,
            training_frequency=4,
            preferred_split=SplitType.UPPER_LOWER,
            equipment=[eq1, eq2],
        )
        text = _format_profile_text(user)
        assert "Nome: Alice" in text
        assert "Altezza: 180 cm" in text
        assert "Peso: 72.5 kg" in text
        assert "BMI: 22.4" in text
        assert "Corporatura: Mesomorfo" in text
        assert "Livello: Avanzato" in text
        assert "Frequenza: 4 giorni/settimana" in text
        assert "Split: Upper/Lower" in text
        assert "Attrezzatura: Barbell, Bench Press" in text


class TestProfileCommand:
    """Verify /profilo command."""

    @pytest.mark.asyncio
    async def test_profile_command_user_not_found(self) -> None:
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch(
                "wod.bot.handlers.profile.get_user_with_equipment", return_value=None
            ),
        ):
            await profile_command(update, context)

        update.message.reply_text.assert_called_once_with(
            "⚠️ Non hai ancora un profilo. Usa /start per configurarlo."
        )

    @pytest.mark.asyncio
    async def test_profile_command_success(self) -> None:
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        update.message = AsyncMock()
        context = MagicMock()

        user = MockUser(name="Bob")

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch(
                "wod.bot.handlers.profile.get_user_with_equipment", return_value=user
            ),
        ):
            await profile_command(update, context)

        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        assert "Nome: Bob" in args[0]
        assert kwargs["parse_mode"] == "Markdown"


class TestEditProfileEntry:
    """Verify edit profile entry point."""

    @pytest.mark.asyncio
    async def test_edit_profile_entry(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        next_state = await edit_profile_entry(update, context)

        assert next_state == CHOOSE_FIELD
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()


class TestFieldSelectionCallback:
    """Verify field selection callback."""

    @pytest.mark.asyncio
    async def test_cancel(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "editf:cancel"
        update.callback_query = query
        context = MagicMock()

        next_state = await field_selection_callback(update, context)
        assert next_state == ConversationHandler.END
        query.edit_message_text.assert_called_once_with("❌ Modifica annullata.")

    @pytest.mark.asyncio
    async def test_fields(self) -> None:
        context = MagicMock()
        context.user_data = {}

        fields = [
            ("name", EDIT_NAME),
            ("height", EDIT_HEIGHT),
            ("weight", EDIT_WEIGHT),
            ("body_type", EDIT_BODY_TYPE),
            ("experience", EDIT_EXPERIENCE),
            ("frequency", EDIT_FREQUENCY),
            ("split", EDIT_SPLIT),
        ]

        for field_name, expected_state in fields:
            update = MagicMock(spec=Update)
            query = AsyncMock()
            query.data = f"editf:{field_name}"
            update.callback_query = query

            next_state = await field_selection_callback(update, context)
            assert next_state == expected_state
            query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_equipment_loading(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "editf:equipment"
        query.from_user.id = 123
        update.callback_query = query
        context = MagicMock()
        context.user_data = {}

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        eq1 = MockEquipment(1, "barbell")
        user = MockUser(equipment=[eq1])

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_all_equipment", return_value=[eq1]),
            patch(
                "wod.bot.handlers.profile.get_user_with_equipment", return_value=user
            ),
        ):
            next_state = await field_selection_callback(update, context)

        assert next_state == EDIT_EQUIPMENT
        assert context.user_data["selected_equipment"] == {1}
        query.edit_message_text.assert_called_once()


class TestTextInputs:
    """Verify name, height, and weight inputs."""

    @pytest.mark.asyncio
    async def test_edit_name_valid(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        update.message.text = "  Alice  "
        update.effective_user.id = 123
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_name_input(update, context)

        assert next_state == ConversationHandler.END
        update_mock.assert_called_once_with(session_mock, user, name="Alice")
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_name_invalid(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        update.message.text = ""
        context = MagicMock()

        next_state = await edit_name_input(update, context)
        assert next_state == EDIT_NAME
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_height_valid(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        update.message.text = "175.5"
        update.effective_user.id = 123
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser(weight_kg=70.0, height_cm=175.5)

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_height_input(update, context)

        assert next_state == ConversationHandler.END
        update_mock.assert_called_once_with(session_mock, user, height_cm=175.5)
        update.message.reply_text.assert_called_once()
        assert "Nuovo BMI:" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_edit_height_invalid(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        update.message.text = "abc"
        context = MagicMock()

        next_state = await edit_height_input(update, context)
        assert next_state == EDIT_HEIGHT
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_weight_valid(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        update.message.text = "72,5"
        update.effective_user.id = 123
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser(height_cm=180.0, weight_kg=72.5)

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_weight_input(update, context)

        assert next_state == ConversationHandler.END
        update_mock.assert_called_once_with(session_mock, user, weight_kg=72.5)
        update.message.reply_text.assert_called_once()
        assert "Nuovo BMI:" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_edit_weight_invalid(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        update.message.text = "550"  # out of range
        context = MagicMock()

        next_state = await edit_weight_input(update, context)
        assert next_state == EDIT_WEIGHT
        update.message.reply_text.assert_called_once()


class TestSelectionCallbacks:
    """Verify inline button selection callbacks."""

    @pytest.mark.asyncio
    async def test_edit_body_type(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "body:ectomorph"
        query.from_user.id = 123
        update.callback_query = query
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_body_type_callback(update, context)

        assert next_state == ConversationHandler.END
        update_mock.assert_called_once_with(
            session_mock, user, body_type=BodyType.ECTOMORPH
        )
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_experience(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "exp:advanced"
        query.from_user.id = 123
        update.callback_query = query
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_experience_callback(update, context)

        assert next_state == ConversationHandler.END
        update_mock.assert_called_once_with(
            session_mock, user, experience_level=ExperienceLevel.ADVANCED
        )
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_frequency(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "freq:4"
        query.from_user.id = 123
        update.callback_query = query
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_frequency_callback(update, context)

        assert next_state == REGEN_CONFIRM
        update_mock.assert_called_once_with(session_mock, user, training_frequency=4)
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_split(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "split:upper_lower"
        query.from_user.id = 123
        update.callback_query = query
        context = MagicMock()

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch(
                "wod.bot.handlers.profile.update_user_profile", return_value=user
            ) as update_mock,
        ):
            next_state = await edit_split_callback(update, context)

        assert next_state == REGEN_CONFIRM
        update_mock.assert_called_once_with(
            session_mock, user, preferred_split=SplitType.UPPER_LOWER
        )
        query.edit_message_text.assert_called_once()


class TestEditEquipmentCallback:
    """Verify equipment edit selection callback."""

    @pytest.mark.asyncio
    async def test_edit_equipment_done(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "equip:done"
        query.from_user.id = 123
        update.callback_query = query

        context = MagicMock()
        context.user_data = {"selected_equipment": {1, 2}}

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock()

        user = MockUser()

        with (
            patch(
                "wod.bot.handlers.profile.get_session_factory",
                return_value=MagicMock(return_value=session_mock),
            ),
            patch("wod.bot.handlers.profile.get_or_create_user", return_value=user),
            patch("wod.bot.handlers.profile.set_user_equipment") as set_eq_mock,
        ):
            next_state = await edit_equipment_callback(update, context)

        assert next_state == REGEN_CONFIRM
        set_eq_mock.assert_called_once_with(session_mock, user, [1, 2])
        query.edit_message_text.assert_called_once()
        query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_equipment_done_empty(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "equip:done"
        query.from_user.id = 123
        update.callback_query = query

        context = MagicMock()
        context.user_data = {"selected_equipment": set()}

        next_state = await edit_equipment_callback(update, context)

        assert next_state == EDIT_EQUIPMENT
        query.answer.assert_called_once_with(
            text="⚠️ Seleziona almeno un attrezzo per confermare!",
            show_alert=True,
        )

    @pytest.mark.asyncio
    async def test_edit_equipment_toggle(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "equip:1"
        query.from_user.id = 123
        update.callback_query = query

        context = MagicMock()
        context.user_data = {
            "equipment_list": [(1, "barbell"), (2, "bench")],
            "selected_equipment": {1},
        }

        # Toggle equipment (1 will be discarded)
        next_state = await edit_equipment_callback(update, context)
        assert next_state == EDIT_EQUIPMENT
        assert context.user_data["selected_equipment"] == set()
        query.edit_message_text.assert_called_once()


class TestRegenCallback:
    """Verify regeneration choice callback."""

    @pytest.mark.asyncio
    async def test_regen_yes(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "regen:yes"
        update.callback_query = query
        context = MagicMock()

        next_state = await regen_callback(update, context)
        assert next_state == ConversationHandler.END
        query.edit_message_text.assert_called_once()
        assert "generare una nuova scheda" in query.edit_message_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_regen_no(self) -> None:
        update = MagicMock(spec=Update)
        query = AsyncMock()
        query.data = "regen:no"
        update.callback_query = query
        context = MagicMock()

        next_state = await regen_callback(update, context)
        assert next_state == ConversationHandler.END
        query.edit_message_text.assert_called_once()
        assert "Perfetto!" in query.edit_message_text.call_args[0][0]


class TestCancelCommand:
    """Verify cancel command."""

    @pytest.mark.asyncio
    async def test_edit_cancel_command(self) -> None:
        update = MagicMock(spec=Update)
        update.message = AsyncMock()
        context = MagicMock()

        next_state = await edit_cancel_command(update, context)
        assert next_state == ConversationHandler.END
        update.message.reply_text.assert_called_once()


def test_builders() -> None:
    """Verify command and conversation builders return proper types."""
    cmd_handler = build_profile_command_handler()
    assert isinstance(cmd_handler, MagicMock) or cmd_handler is not None

    conv_handler = build_edit_profile_handler()
    assert isinstance(conv_handler, ConversationHandler)
