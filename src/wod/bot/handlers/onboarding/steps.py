"""Onboarding steps — name, height, weight, body type, BMI, experience, frequency."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from wod.bot.handlers.onboarding.constants import (
    BMI_DISPLAY,
    BODY_TYPE,
    EQUIPMENT,
    EXPERIENCE,
    FREQUENCY,
    HEIGHT,
    NAME,
    SPLIT,
    WEIGHT,
)
from wod.bot.keyboards import (
    bmi_continue_keyboard,
    body_type_keyboard,
    equipment_keyboard,
    experience_keyboard,
    frequency_keyboard,
    split_keyboard,
)
from wod.bot.locales import get_text
from wod.core.bmi import calculate_bmi
from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.repositories import get_all_equipment, get_or_create_user
from wod.db.session import get_session_factory

# ---------------------------------------------------------------------------
# Onboarding entry point (triggered via menu, not /start)
# ---------------------------------------------------------------------------


async def begin_onboarding(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Begin the onboarding flow — ask for the user's name.

    Triggered by the 'crea:new' callback from the menu choice keyboard.
    """
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert update.effective_user is not None
    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        lang = user.language or "it"

    assert _context.user_data is not None
    _context.user_data["lang"] = lang

    await query.edit_message_text(
        get_text(lang, "onb_begin"),
        parse_mode="Markdown",
    )
    return NAME


# ---------------------------------------------------------------------------
# Step 1 — Name (free text)
# ---------------------------------------------------------------------------


async def name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's name input."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    lang = context.user_data.get("lang", "it")
    name = update.message.text.strip()
    if not name or len(name) > 128:
        await update.message.reply_text(get_text(lang, "onb_name_err"))
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        get_text(lang, "onb_name_ok", name=name),
        parse_mode="Markdown",
    )
    return HEIGHT


# ---------------------------------------------------------------------------
# Step 2 — Height (free text, numeric)
# ---------------------------------------------------------------------------


async def height_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's height input."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    lang = context.user_data.get("lang", "it")
    try:
        height = float(update.message.text.strip().replace(",", "."))
        if height < 50 or height > 300:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(get_text(lang, "onb_height_err"))
        return HEIGHT

    context.user_data["height_cm"] = height

    await update.message.reply_text(
        get_text(lang, "onb_height_ok", height=f"{height:.0f}"),
        parse_mode="Markdown",
    )
    return WEIGHT


# ---------------------------------------------------------------------------
# Step 3 — Weight (free text, numeric)
# ---------------------------------------------------------------------------


async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's weight input."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    lang = context.user_data.get("lang", "it")
    try:
        weight = float(update.message.text.strip().replace(",", "."))
        if weight < 20 or weight > 500:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(get_text(lang, "onb_weight_err"))
        return WEIGHT

    context.user_data["weight_kg"] = weight

    await update.message.reply_text(
        get_text(lang, "onb_weight_ok", weight=f"{weight:.1f}"),
        parse_mode="Markdown",
        reply_markup=body_type_keyboard(lang),
    )
    return BODY_TYPE


# ---------------------------------------------------------------------------
# Step 4 — Body Type (inline keyboard)
# ---------------------------------------------------------------------------


async def body_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle body type selection and show BMI."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    assert context.user_data is not None

    body_str = query.data.split(":")[1]
    body = BodyType(body_str)
    context.user_data["body_type"] = body

    lang = context.user_data.get("lang", "it")

    # Calculate BMI
    height_cm = context.user_data["height_cm"]
    weight_kg = context.user_data["weight_kg"]
    bmi_value, bmi_category_key = calculate_bmi(weight_kg, height_cm)
    bmi_category = get_text(lang, bmi_category_key)
    context.user_data["bmi_value"] = bmi_value
    context.user_data["bmi_category"] = bmi_category

    body_label = get_text(lang, f"lbl_{body.value}")

    await query.edit_message_text(
        get_text(
            lang,
            "onb_body_ok",
            body=body_label,
            bmi_value=bmi_value,
            bmi_category=bmi_category,
        ),
        parse_mode="Markdown",
        reply_markup=bmi_continue_keyboard(lang),
    )
    return BMI_DISPLAY


# ---------------------------------------------------------------------------
# Step 5 — BMI Display → Continue to Experience
# ---------------------------------------------------------------------------


async def bmi_continue_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle BMI continue button — move to experience selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    await query.edit_message_text(
        get_text(lang, "onb_exp_prompt"),
        reply_markup=experience_keyboard(lang),
    )
    return EXPERIENCE


# ---------------------------------------------------------------------------
# Step 6 — Experience Level (inline keyboard)
# ---------------------------------------------------------------------------


async def experience_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle experience level selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    level_str = query.data.split(":")[1]
    level = ExperienceLevel(level_str)

    # Store in user_data for the session
    assert context.user_data is not None
    context.user_data["experience_level"] = level

    lang = context.user_data.get("lang", "it")
    await query.edit_message_text(
        get_text(lang, "onb_exp_ok", level=get_text(lang, f"lbl_{level.value}")),
        parse_mode="Markdown",
        reply_markup=frequency_keyboard(lang),
    )
    return FREQUENCY


# ---------------------------------------------------------------------------
# Step 7 — Training Frequency (inline keyboard)
# ---------------------------------------------------------------------------


async def frequency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle training frequency selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    freq = int(query.data.split(":")[1])
    assert context.user_data is not None
    context.user_data["training_frequency"] = freq

    lang = context.user_data.get("lang", "it")
    await query.edit_message_text(
        get_text(lang, "onb_freq_ok", freq=freq),
        parse_mode="Markdown",
        reply_markup=split_keyboard(lang, frequency=freq),
    )
    return SPLIT


# ---------------------------------------------------------------------------
# Step 8 — Split Type (inline keyboard)
# ---------------------------------------------------------------------------


async def split_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle split type selection, then show equipment selector."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    split_str = query.data.split(":")[1]
    split_type = SplitType(split_str)
    assert context.user_data is not None
    context.user_data["preferred_split"] = split_type

    # Load equipment from DB
    async with get_session_factory()() as session:
        all_eq = await get_all_equipment(session)
        eq_list = [(eq.id, eq.name) for eq in all_eq]

    context.user_data["equipment_list"] = eq_list
    context.user_data["selected_equipment"] = set()

    lang = context.user_data.get("lang", "it")
    split_label = get_text(lang, f"lbl_{split_type.value}")
    await query.edit_message_text(
        get_text(lang, "onb_split_ok", split=split_label),
        parse_mode="Markdown",
        reply_markup=equipment_keyboard(lang, eq_list, set()),
    )
    return EQUIPMENT
