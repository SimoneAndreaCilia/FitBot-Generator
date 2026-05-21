"""Onboarding handler — /start conversation flow.

Guides a new user through:
1. Experience level selection
2. Training frequency selection
3. Preferred split selection
4. Equipment selection (toggle-based)

Uses ``ConversationHandler`` with inline-keyboard callbacks.
"""

from __future__ import annotations

import logging

from telegram import CallbackQuery, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from wod.bot.keyboards import (
    equipment_keyboard,
    experience_keyboard,
    frequency_keyboard,
    split_keyboard,
)
from wod.core.types import ExperienceLevel, SplitType
from wod.db.models import Base
from wod.db.repositories import (
    get_all_equipment,
    get_or_create_user,
    set_user_equipment,
    update_user_profile,
)
from wod.db.session import get_engine, get_session_factory

logger = logging.getLogger(__name__)

# Conversation states
EXPERIENCE, FREQUENCY, SPLIT, EQUIPMENT = range(4)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: /start — greet and ask for experience level."""
    assert update.effective_user is not None
    assert update.message is not None

    # Ensure tables exist
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_factory()() as session:
        await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
        )
        await session.commit()

    await update.message.reply_text(
        "🏋️ *Benvenuto nel WOD Bot!*\n\n"
        "Configuriamo il tuo profilo di allenamento.\n\n"
        "Qual è il tuo livello di esperienza?",
        parse_mode="Markdown",
        reply_markup=experience_keyboard(),
    )
    return EXPERIENCE


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
        reply_markup=split_keyboard(),
    )
    return SPLIT


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


async def equipment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """Handle equipment toggle or confirmation."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert context.user_data is not None

    data = query.data.split(":")[1]

    if data == "done":
        # Save everything to DB
        return await _finalize_onboarding(query, context)

    # Toggle equipment selection
    eq_id = int(data)
    selected: set[int] = context.user_data["selected_equipment"]
    if eq_id in selected:
        selected.discard(eq_id)
    else:
        selected.add(eq_id)
    context.user_data["selected_equipment"] = selected

    eq_list = context.user_data["equipment_list"]
    await query.edit_message_text(
        "Seleziona l'attrezzatura disponibile nella tua Home Gym.\n"
        "Tocca per selezionare/deselezionare, poi conferma:",
        reply_markup=equipment_keyboard(eq_list, selected),
    )
    return EQUIPMENT


async def _finalize_onboarding(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Persist all onboarding data and end the conversation."""
    assert query.from_user is not None
    assert context.user_data is not None

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(
            session,
            user,
            experience_level=context.user_data["experience_level"],
            training_frequency=context.user_data["training_frequency"],
            preferred_split=context.user_data["preferred_split"],
        )
        selected_ids = list(context.user_data.get("selected_equipment", set()))
        if selected_ids:
            await set_user_equipment(session, user, selected_ids)
        await session.commit()

    level = context.user_data["experience_level"].value.title()
    freq = context.user_data["training_frequency"]
    split_label = context.user_data["preferred_split"].value.replace("_", " ").title()
    eq_count = len(context.user_data.get("selected_equipment", set()))

    await query.edit_message_text(
        "🎉 *Profilo configurato!*\n\n"
        f"• Livello: {level}\n"
        f"• Frequenza: {freq} giorni/settimana\n"
        f"• Split: {split_label}\n"
        f"• Attrezzatura: {eq_count} elementi\n\n"
        "Usa /wod per generare il tuo allenamento del giorno!\n"
        "Usa /history per vedere le schede passate.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the onboarding conversation."""
    assert update.message is not None
    await update.message.reply_text(
        "❌ Configurazione annullata. Usa /start per ricominciare."
    )
    return ConversationHandler.END


def build_onboarding_handler() -> ConversationHandler[ContextTypes.DEFAULT_TYPE]:
    """Build and return the ConversationHandler for onboarding."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            EXPERIENCE: [CallbackQueryHandler(experience_callback, pattern=r"^exp:")],
            FREQUENCY: [CallbackQueryHandler(frequency_callback, pattern=r"^freq:")],
            SPLIT: [CallbackQueryHandler(split_callback, pattern=r"^split:")],
            EQUIPMENT: [CallbackQueryHandler(equipment_callback, pattern=r"^equip:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        per_message=False,
    )
