"""Onboarding steps — name, height, weight, body type, BMI, experience, frequency."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from wod.bot.handlers.onboarding.constants import (
    BMI_DISPLAY,
    BODY_TYPE,
    BODY_TYPE_LABELS,
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
from wod.core.bmi import calculate_bmi
from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.repositories import get_all_equipment
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

    await query.edit_message_text(
        "🏋️ *Configuriamo il tuo profilo di allenamento!*\n\nCome ti chiami?",
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

    name = update.message.text.strip()
    if not name or len(name) > 128:
        await update.message.reply_text(
            "⚠️ Inserisci un nome valido (max 128 caratteri):"
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        f"✅ Nome: *{name}*\n\n" "📏 Qual è la tua altezza in *cm*?\n" "_(es: 175)_",
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

    try:
        height = float(update.message.text.strip().replace(",", "."))
        if height < 50 or height > 300:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Inserisci un'altezza valida in cm (es: 175):"
        )
        return HEIGHT

    context.user_data["height_cm"] = height

    await update.message.reply_text(
        f"✅ Altezza: *{height:.0f} cm*\n\n"
        "⚖️ Qual è il tuo peso in *kg*?\n"
        "_(es: 72.5)_",
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

    try:
        weight = float(update.message.text.strip().replace(",", "."))
        if weight < 20 or weight > 500:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text("⚠️ Inserisci un peso valido in kg (es: 72.5):")
        return WEIGHT

    context.user_data["weight_kg"] = weight

    await update.message.reply_text(
        f"✅ Peso: *{weight:.1f} kg*\n\n" "Qual è il tuo tipo di corporatura?",
        parse_mode="Markdown",
        reply_markup=body_type_keyboard(),
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

    # Calculate BMI
    height_cm = context.user_data["height_cm"]
    weight_kg = context.user_data["weight_kg"]
    bmi_value, bmi_category = calculate_bmi(weight_kg, height_cm)
    context.user_data["bmi_value"] = bmi_value
    context.user_data["bmi_category"] = bmi_category

    body_label = BODY_TYPE_LABELS[body]
    await query.edit_message_text(
        f"✅ Corporatura: *{body_label}*\n\n"
        f"📊 *Il tuo BMI: {bmi_value}* — _{bmi_category}_\n\n"
        "Ora configuriamo il tuo allenamento!",
        parse_mode="Markdown",
        reply_markup=bmi_continue_keyboard(),
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

    await query.edit_message_text(
        "Qual è il tuo livello di esperienza?",
        reply_markup=experience_keyboard(),
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

    await query.edit_message_text(
        f"✅ Livello: *{level.value.title()}*\n\n"
        "Quanti giorni a settimana vuoi allenarti?",
        parse_mode="Markdown",
        reply_markup=frequency_keyboard(),
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

    await query.edit_message_text(
        f"✅ Frequenza: *{freq} giorni/settimana*\n\n"
        "Scegli il tipo di split settimanale:",
        parse_mode="Markdown",
        reply_markup=split_keyboard(frequency=freq),
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

    split_label = split_type.value.replace("_", " ").title()
    await query.edit_message_text(
        f"✅ Split: *{split_label}*\n\n"
        "Seleziona l'attrezzatura disponibile nella tua Home Gym.\n"
        "Tocca per selezionare/deselezionare, poi conferma:",
        parse_mode="Markdown",
        reply_markup=equipment_keyboard(eq_list, set()),
    )
    return EQUIPMENT
