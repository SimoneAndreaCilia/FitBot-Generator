"""Profile handler — /profilo command and profile editing.

Provides:
* ``/profilo`` — Display the user's complete profile with a "Modifica" button.
* Edit conversation — Pick a field to modify, update it, and optionally
  regenerate the workout when equipment changes.
"""

from __future__ import annotations

import logging
from typing import Any

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from wod.bot.keyboards import (
    body_type_keyboard,
    edit_field_keyboard,
    equipment_keyboard,
    experience_keyboard,
    frequency_keyboard,
    profile_keyboard,
    regenerate_keyboard,
    split_keyboard,
)
from wod.bot.utils import handle_equipment_toggle
from wod.core.bmi import calculate_bmi
from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.repositories import (
    get_all_equipment,
    get_or_create_user,
    get_user_with_equipment,
    set_user_equipment,
    update_user_profile,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)

# Body type display labels
_BODY_TYPE_LABELS = {
    BodyType.ECTOMORPH: "Ectomorfo",
    BodyType.MESOMORPH: "Mesomorfo",
    BodyType.ENDOMORPH: "Endomorfo",
}

# Experience level display labels
_EXPERIENCE_LABELS = {
    ExperienceLevel.BEGINNER: "Principiante",
    ExperienceLevel.INTERMEDIATE: "Intermedio",
    ExperienceLevel.ADVANCED: "Avanzato",
}

# Split type display labels
_SPLIT_LABELS = {
    SplitType.FULL_BODY: "Full Body",
    SplitType.UPPER_LOWER: "Upper/Lower",
    SplitType.PUSH_PULL_LEGS: "Push/Pull/Legs",
}

# ---------------------------------------------------------------------------
# Edit conversation states
# ---------------------------------------------------------------------------

(
    CHOOSE_FIELD,
    EDIT_NAME,
    EDIT_HEIGHT,
    EDIT_WEIGHT,
    EDIT_BODY_TYPE,
    EDIT_EXPERIENCE,
    EDIT_FREQUENCY,
    EDIT_SPLIT,
    EDIT_EQUIPMENT,
    REGEN_CONFIRM,
) = range(10)


# ---------------------------------------------------------------------------
# /profilo command
# ---------------------------------------------------------------------------


def _format_profile_text(user) -> str:  # type: ignore[no-untyped-def]
    """Build the profile display text from a User model instance."""
    name = user.name or "—"
    height = f"{user.height_cm:.0f} cm" if user.height_cm else "—"
    weight = f"{user.weight_kg:.1f} kg" if user.weight_kg else "—"

    if user.height_cm and user.weight_kg:
        bmi_val, bmi_cat = calculate_bmi(user.weight_kg, user.height_cm)
        bmi_str = f"{bmi_val} ({bmi_cat})"
    else:
        bmi_str = "—"

    body = _BODY_TYPE_LABELS.get(user.body_type, "—")
    level = _EXPERIENCE_LABELS.get(user.experience_level, "—")
    freq = (
        f"{user.training_frequency} giorni/settimana"
        if user.training_frequency
        else "—"
    )
    split = _SPLIT_LABELS.get(user.preferred_split, "—")

    eq_names = sorted(eq.name.replace("_", " ").title() for eq in user.equipment)
    eq_str = ", ".join(eq_names) if eq_names else "Nessuna"

    return (
        "👤 *Il tuo profilo*\n\n"
        f"📛 Nome: {name}\n"
        f"📏 Altezza: {height}\n"
        f"⚖️ Peso: {weight}\n"
        f"📊 BMI: {bmi_str}\n"
        f"🦴 Corporatura: {body}\n"
        f"📊 Livello: {level}\n"
        f"📅 Frequenza: {freq}\n"
        f"🔀 Split: {split}\n"
        f"🔧 Attrezzatura: {eq_str}"
    )


async def profile_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /profilo — display the user's profile."""
    assert update.effective_user is not None
    assert update.message is not None

    async with get_session_factory()() as session:
        user = await get_user_with_equipment(session, update.effective_user.id)

    if user is None:
        await update.message.reply_text(
            "⚠️ Non hai ancora un profilo. Usa /start per configurarlo."
        )
        return

    text = _format_profile_text(user)
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=profile_keyboard(),
    )


# ---------------------------------------------------------------------------
# Edit profile — entry point (callback from profile message)
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

    label = _BODY_TYPE_LABELS[body]
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

    label = _EXPERIENCE_LABELS[level]
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

    label = _SPLIT_LABELS[split]
    await query.edit_message_text(
        f"✅ Split aggiornato a: *{label}*\n\n"
        "Vuoi rigenerare la scheda di allenamento con i nuovi dati?",
        parse_mode="Markdown",
        reply_markup=regenerate_keyboard(),
    )
    return REGEN_CONFIRM


# ---------------------------------------------------------------------------
# Edit equipment (toggle-based, with regenerate offer)
# ---------------------------------------------------------------------------


async def edit_equipment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle equipment toggle or confirmation during profile editing."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None
    assert context.user_data is not None
    assert query.from_user is not None

    data = query.data.split(":")[1]

    if data == "done":
        selected_ids = list(context.user_data.get("selected_equipment", set()))
        if not selected_ids:
            await query.answer(
                text="⚠️ Seleziona almeno un attrezzo per confermare!",
                show_alert=True,
            )
            return EDIT_EQUIPMENT

        await query.answer()
        # Save equipment to DB
        async with get_session_factory()() as session:
            user = await get_or_create_user(session, telegram_id=query.from_user.id)
            await set_user_equipment(session, user, selected_ids)
            await session.commit()

        eq_count = len(selected_ids)
        await query.edit_message_text(
            f"✅ Attrezzatura aggiornata: *{eq_count} elementi*\n\n"
            "Vuoi rigenerare la scheda di allenamento con la nuova attrezzatura?",
            parse_mode="Markdown",
            reply_markup=regenerate_keyboard(),
        )
        return REGEN_CONFIRM

    await query.answer()
    eq_list = context.user_data["equipment_list"]
    handle_equipment_toggle(context.user_data, data)
    selected_set = context.user_data["selected_equipment"]
    try:
        await query.edit_message_text(
            "🔧 Modifica la tua attrezzatura.\n"
            "Tocca per selezionare/deselezionare, poi conferma:",
            reply_markup=equipment_keyboard(eq_list, selected_set),
        )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise

    return EDIT_EQUIPMENT


# ---------------------------------------------------------------------------
# Regenerate workout confirmation
# ---------------------------------------------------------------------------


async def regen_callback(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the regenerate workout confirmation."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None

    choice = query.data.split(":")[1]

    if choice == "yes":
        await query.edit_message_text(
            "🔄 Usa il comando /wod per generare una nuova scheda "
            "con i tuoi dati aggiornati!"
        )
    else:
        await query.edit_message_text(
            "👍 Perfetto! Usa /profilo per rivedere il tuo profilo."
        )

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


async def edit_cancel_command(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel the edit conversation."""
    assert update.message is not None
    await update.message.reply_text("❌ Modifica annullata.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# ConversationHandler builders
# ---------------------------------------------------------------------------


def build_profile_command_handler() -> CommandHandler[Any, Any]:
    """Build the /profilo command handler."""
    return CommandHandler("profilo", profile_command)


def build_edit_profile_handler() -> ConversationHandler[ContextTypes.DEFAULT_TYPE]:
    """Build the ConversationHandler for profile editing.

    Entry point is the ``edit_profile`` callback from the profile message.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_profile_entry, pattern=r"^edit_profile$"),
        ],
        states={
            CHOOSE_FIELD: [
                CallbackQueryHandler(field_selection_callback, pattern=r"^editf:"),
            ],
            EDIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name_input),
            ],
            EDIT_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_height_input),
            ],
            EDIT_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_weight_input),
            ],
            EDIT_BODY_TYPE: [
                CallbackQueryHandler(edit_body_type_callback, pattern=r"^body:"),
            ],
            EDIT_EXPERIENCE: [
                CallbackQueryHandler(edit_experience_callback, pattern=r"^exp:"),
            ],
            EDIT_FREQUENCY: [
                CallbackQueryHandler(edit_frequency_callback, pattern=r"^freq:"),
            ],
            EDIT_SPLIT: [
                CallbackQueryHandler(edit_split_callback, pattern=r"^split:"),
            ],
            EDIT_EQUIPMENT: [
                CallbackQueryHandler(edit_equipment_callback, pattern=r"^equip:"),
            ],
            REGEN_CONFIRM: [
                CallbackQueryHandler(regen_callback, pattern=r"^regen:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel_command)],
        per_message=False,
    )
