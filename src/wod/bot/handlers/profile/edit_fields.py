"""Profile field editing — text inputs and inline keyboard callbacks."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from wod.bot.handlers.profile.constants import (
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
)
from wod.bot.keyboards import (
    body_type_keyboard,
    edit_field_keyboard,
    equipment_keyboard,
    experience_keyboard,
    frequency_keyboard,
    regenerate_keyboard,
    split_keyboard,
)
from wod.bot.locales import get_text
from wod.core.bmi import calculate_bmi
from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.repositories import (
    get_all_equipment,
    get_or_create_user,
    get_user_with_equipment,
    update_user_profile,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entry point (callback from profile message)
# ---------------------------------------------------------------------------


async def edit_profile_entry(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the 'Modifica profilo' button — show field selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    await query.edit_message_text(
        get_text(lang, "edit_choose"),
        parse_mode="Markdown",
        reply_markup=edit_field_keyboard(lang),
    )
    return CHOOSE_FIELD


# ---------------------------------------------------------------------------
# Field selection
# ---------------------------------------------------------------------------


# pylint: disable=too-many-return-statements
async def field_selection_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the field selection for profile editing."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert context.user_data is not None

    lang = context.user_data.get("lang", "it")
    field = query.data.split(":")[1]

    if field == "cancel":
        await query.edit_message_text(get_text(lang, "edit_cancel"))
        return ConversationHandler.END

    if field == "name":
        await query.edit_message_text(get_text(lang, "edit_name_prompt"))
        return EDIT_NAME

    if field == "height":
        await query.edit_message_text(
            get_text(lang, "edit_height_prompt"),
            parse_mode="Markdown",
        )
        return EDIT_HEIGHT

    if field == "weight":
        await query.edit_message_text(
            get_text(lang, "edit_weight_prompt"),
            parse_mode="Markdown",
        )
        return EDIT_WEIGHT

    if field == "body_type":
        await query.edit_message_text(
            get_text(lang, "edit_body_prompt"),
            reply_markup=body_type_keyboard(lang),
        )
        return EDIT_BODY_TYPE

    if field == "experience":
        await query.edit_message_text(
            get_text(lang, "edit_exp_prompt"),
            reply_markup=experience_keyboard(lang),
        )
        return EDIT_EXPERIENCE

    if field == "frequency":
        await query.edit_message_text(
            get_text(lang, "edit_freq_prompt"),
            reply_markup=frequency_keyboard(lang),
        )
        return EDIT_FREQUENCY

    if field == "split":
        # Fetch user's current frequency to filter compatible splits
        assert query.from_user is not None
        async with get_session_factory()() as session:
            user = await get_or_create_user(session, telegram_id=query.from_user.id)
            user_freq = user.training_frequency

        await query.edit_message_text(
            get_text(lang, "edit_split_prompt"),
            reply_markup=split_keyboard(lang, frequency=user_freq),
        )
        return EDIT_SPLIT

    if field == "equipment":
        # Load equipment from DB
        async with get_session_factory()() as session:
            all_eq = await get_all_equipment(session)
            eq_list = [(eq.id, eq.name) for eq in all_eq]

            # Load current user equipment
            assert query.from_user is not None
            user_with_eq = await get_user_with_equipment(session, query.from_user.id)
            assert user_with_eq is not None
            current_ids = {eq.id for eq in user_with_eq.equipment}

        context.user_data["equipment_list"] = eq_list
        context.user_data["selected_equipment"] = current_ids

        await query.edit_message_text(
            get_text(lang, "edit_eq_prompt"),
            reply_markup=equipment_keyboard(lang, eq_list, current_ids),
        )
        return EDIT_EQUIPMENT

    # Fallback
    await query.edit_message_text(get_text(lang, "edit_unrecognized"))
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Edit handlers — text inputs
# ---------------------------------------------------------------------------


async def edit_name_input(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new name input during profile editing."""
    assert update.message is not None
    assert update.message.text is not None
    assert update.effective_user is not None

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    name = update.message.text.strip()
    if not name or len(name) > 128:
        await update.message.reply_text(get_text(lang, "onb_name_err"))
        return EDIT_NAME

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, name=name)
        await session.commit()

    await update.message.reply_text(
        get_text(lang, "edit_name_ok", name=name),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_height_input(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new height input during profile editing."""
    assert update.message is not None
    assert update.message.text is not None
    assert update.effective_user is not None

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    try:
        height = float(update.message.text.strip().replace(",", "."))
        if height < 50 or height > 300:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(get_text(lang, "onb_height_err"))
        return EDIT_HEIGHT

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, height_cm=height)
        await session.commit()
        if user.weight_kg and user.height_cm:
            bmi_val, bmi_cat_key = calculate_bmi(user.weight_kg, user.height_cm)
            bmi_cat = get_text(lang, bmi_cat_key)
            bmi_msg = get_text(lang, "edit_bmi_msg", bmi_val=bmi_val, bmi_cat=bmi_cat)
        else:
            bmi_msg = ""

    await update.message.reply_text(
        get_text(lang, "edit_height_ok", height=f"{height:.0f}", bmi_msg=bmi_msg),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_weight_input(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new weight input during profile editing."""
    assert update.message is not None
    assert update.message.text is not None
    assert update.effective_user is not None

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    try:
        weight = float(update.message.text.strip().replace(",", "."))
        if weight < 20 or weight > 500:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(get_text(lang, "onb_weight_err"))
        return EDIT_WEIGHT

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, weight_kg=weight)
        await session.commit()
        if user.weight_kg and user.height_cm:
            bmi_val, bmi_cat_key = calculate_bmi(user.weight_kg, user.height_cm)
            bmi_cat = get_text(lang, bmi_cat_key)
            bmi_msg = get_text(lang, "edit_bmi_msg", bmi_val=bmi_val, bmi_cat=bmi_cat)
        else:
            bmi_msg = ""

    await update.message.reply_text(
        get_text(lang, "edit_weight_ok", weight=f"{weight:.1f}", bmi_msg=bmi_msg),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Edit handlers — inline keyboard selections
# ---------------------------------------------------------------------------


async def edit_body_type_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle body type edit selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    body = BodyType(query.data.split(":")[1])

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(session, user, body_type=body)
        await session.commit()

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    label = get_text(lang, f"lbl_{body.value}")
    await query.edit_message_text(
        get_text(lang, "edit_body_ok", body=label),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_experience_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle experience level edit selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    level = ExperienceLevel(query.data.split(":")[1])

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(session, user, experience_level=level)
        await session.commit()

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    label = get_text(lang, f"lbl_{level.value}")
    await query.edit_message_text(
        get_text(lang, "edit_exp_ok", level=label),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_frequency_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle training frequency edit selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    freq = int(query.data.split(":")[1])

    # Minimum days required for each split type
    split_min_days = {
        SplitType.FULL_BODY: 1,
        SplitType.UPPER_LOWER: 2,
        SplitType.PUSH_PULL_LEGS: 3,
    }

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(session, user, training_frequency=freq)
        await session.commit()
        current_split = user.preferred_split

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"

    # Check if the current split is still compatible with the new frequency
    if current_split is not None and freq < split_min_days.get(current_split, 1):
        await query.edit_message_text(
            get_text(lang, "edit_freq_incompat", freq=freq),
            parse_mode="Markdown",
            reply_markup=split_keyboard(lang, frequency=freq),
        )
        return EDIT_SPLIT

    await query.edit_message_text(
        get_text(lang, "edit_freq_ok", freq=freq),
        parse_mode="Markdown",
        reply_markup=regenerate_keyboard(lang),
    )
    return REGEN_CONFIRM


async def edit_split_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle split type edit selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    split = SplitType(query.data.split(":")[1])

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(session, user, preferred_split=split)
        await session.commit()

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    label = get_text(lang, f"lbl_{split.value}")
    await query.edit_message_text(
        get_text(lang, "edit_split_ok", split=label),
        parse_mode="Markdown",
        reply_markup=regenerate_keyboard(lang),
    )
    return REGEN_CONFIRM
