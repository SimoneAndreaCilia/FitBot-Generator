"""Profile field editing — text inputs and inline keyboard callbacks."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from wod.bot.handlers.profile.constants import (
    BODY_TYPE_LABELS,
    CHOOSE_FIELD,
    EDIT_BODY_TYPE,
    EDIT_EQUIPMENT,
    EDIT_EXPERIENCE,
    EDIT_FREQUENCY,
    EDIT_HEIGHT,
    EDIT_NAME,
    EDIT_SPLIT,
    EDIT_WEIGHT,
    EXPERIENCE_LABELS,
    REGEN_CONFIRM,
    SPLIT_LABELS,
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

    await query.edit_message_text(
        "✏️ *Cosa vuoi modificare?*",
        parse_mode="Markdown",
        reply_markup=edit_field_keyboard(),
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

    field = query.data.split(":")[1]

    if field == "cancel":
        await query.edit_message_text("❌ Modifica annullata.")
        return ConversationHandler.END

    if field == "name":
        await query.edit_message_text("📛 Inserisci il tuo nuovo nome:")
        return EDIT_NAME

    if field == "height":
        await query.edit_message_text(
            "📏 Inserisci la tua nuova altezza in *cm*:\n_(es: 175)_",
            parse_mode="Markdown",
        )
        return EDIT_HEIGHT

    if field == "weight":
        await query.edit_message_text(
            "⚖️ Inserisci il tuo nuovo peso in *kg*:\n_(es: 72.5)_",
            parse_mode="Markdown",
        )
        return EDIT_WEIGHT

    if field == "body_type":
        await query.edit_message_text(
            "🦴 Seleziona il tuo tipo di corporatura:",
            reply_markup=body_type_keyboard(),
        )
        return EDIT_BODY_TYPE

    if field == "experience":
        await query.edit_message_text(
            "📊 Seleziona il tuo livello di esperienza:",
            reply_markup=experience_keyboard(),
        )
        return EDIT_EXPERIENCE

    if field == "frequency":
        await query.edit_message_text(
            "📅 Quanti giorni a settimana vuoi allenarti?",
            reply_markup=frequency_keyboard(),
        )
        return EDIT_FREQUENCY

    if field == "split":
        # Fetch user's current frequency to filter compatible splits
        assert query.from_user is not None
        async with get_session_factory()() as session:
            user = await get_or_create_user(session, telegram_id=query.from_user.id)
            user_freq = user.training_frequency

        await query.edit_message_text(
            "🔀 Scegli il tipo di split settimanale:",
            reply_markup=split_keyboard(frequency=user_freq),
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
            "🔧 Modifica la tua attrezzatura.\n"
            "Tocca per selezionare/deselezionare, poi conferma:",
            reply_markup=equipment_keyboard(eq_list, current_ids),
        )
        return EDIT_EQUIPMENT

    # Fallback
    await query.edit_message_text("⚠️ Campo non riconosciuto.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Edit handlers — text inputs
# ---------------------------------------------------------------------------


async def edit_name_input(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new name input during profile editing."""
    assert update.message is not None
    assert update.message.text is not None
    assert update.effective_user is not None

    name = update.message.text.strip()
    if not name or len(name) > 128:
        await update.message.reply_text(
            "⚠️ Inserisci un nome valido (max 128 caratteri):"
        )
        return EDIT_NAME

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, name=name)
        await session.commit()

    await update.message.reply_text(
        f"✅ Nome aggiornato a: *{name}*\n\n"
        "Usa /profilo per vedere il profilo aggiornato.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_height_input(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new height input during profile editing."""
    assert update.message is not None
    assert update.message.text is not None
    assert update.effective_user is not None

    try:
        height = float(update.message.text.strip().replace(",", "."))
        if height < 50 or height > 300:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Inserisci un'altezza valida in cm (es: 175):"
        )
        return EDIT_HEIGHT

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, height_cm=height)
        await session.commit()
        if user.weight_kg and user.height_cm:
            bmi_val, bmi_cat = calculate_bmi(user.weight_kg, user.height_cm)
            bmi_msg = f"\n📊 Nuovo BMI: *{bmi_val}* — _{bmi_cat}_\n"
        else:
            bmi_msg = ""

    await update.message.reply_text(
        f"✅ Altezza aggiornata a: *{height:.0f} cm*\n{bmi_msg}\n"
        "Usa /profilo per vedere il profilo aggiornato.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_weight_input(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new weight input during profile editing."""
    assert update.message is not None
    assert update.message.text is not None
    assert update.effective_user is not None

    try:
        weight = float(update.message.text.strip().replace(",", "."))
        if weight < 20 or weight > 500:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text("⚠️ Inserisci un peso valido in kg (es: 72.5):")
        return EDIT_WEIGHT

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, weight_kg=weight)
        await session.commit()
        if user.weight_kg and user.height_cm:
            bmi_val, bmi_cat = calculate_bmi(user.weight_kg, user.height_cm)
            bmi_msg = f"\n📊 Nuovo BMI: *{bmi_val}* — _{bmi_cat}_\n"
        else:
            bmi_msg = ""

    await update.message.reply_text(
        f"✅ Peso aggiornato a: *{weight:.1f} kg*\n{bmi_msg}\n"
        "Usa /profilo per vedere il profilo aggiornato.",
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

    label = BODY_TYPE_LABELS[body]
    await query.edit_message_text(
        f"✅ Corporatura aggiornata a: *{label}*\n\n"
        "Usa /profilo per vedere il profilo aggiornato.",
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

    label = EXPERIENCE_LABELS[level]
    await query.edit_message_text(
        f"✅ Livello aggiornato a: *{label}*\n\n"
        "Usa /profilo per vedere il profilo aggiornato.",
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

    # Check if the current split is still compatible with the new frequency
    if current_split is not None and freq < split_min_days.get(current_split, 1):
        await query.edit_message_text(
            f"✅ Frequenza aggiornata a: *{freq} giorni/settimana*\n\n"
            "⚠️ Lo split attuale non è compatibile con la nuova frequenza.\n"
            "Scegli un nuovo tipo di split:",
            parse_mode="Markdown",
            reply_markup=split_keyboard(frequency=freq),
        )
        return EDIT_SPLIT

    await query.edit_message_text(
        f"✅ Frequenza aggiornata a: *{freq} giorni/settimana*\n\n"
        "Vuoi rigenerare la scheda di allenamento con i nuovi dati?",
        parse_mode="Markdown",
        reply_markup=regenerate_keyboard(),
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

    label = SPLIT_LABELS[split]
    await query.edit_message_text(
        f"✅ Split aggiornato a: *{label}*\n\n"
        "Vuoi rigenerare la scheda di allenamento con i nuovi dati?",
        parse_mode="Markdown",
        reply_markup=regenerate_keyboard(),
    )
    return REGEN_CONFIRM
