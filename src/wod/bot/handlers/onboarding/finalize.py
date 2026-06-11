"""Onboarding finalization — persist data and cancel command."""

from __future__ import annotations

from typing import cast

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes, ConversationHandler

from wod.bot.handlers.onboarding.constants import BODY_TYPE_LABELS
from wod.bot.keyboards import expanded_menu_keyboard
from wod.core.types import BodyType
from wod.db.repositories import (
    get_or_create_user,
    set_user_equipment,
    update_user_profile,
)
from wod.db.session import get_session_factory


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
            name=context.user_data.get("name"),
            height_cm=context.user_data.get("height_cm"),
            weight_kg=context.user_data.get("weight_kg"),
            body_type=context.user_data.get("body_type"),
            experience_level=context.user_data["experience_level"],
            training_frequency=context.user_data["training_frequency"],
            preferred_split=context.user_data["preferred_split"],
        )
        selected_ids = list(context.user_data.get("selected_equipment", set()))
        if selected_ids:
            await set_user_equipment(session, user, selected_ids)
        await session.commit()

    name = context.user_data.get("name", "—")
    height = context.user_data.get("height_cm", 0)
    weight = context.user_data.get("weight_kg", 0)
    bmi_value = context.user_data.get("bmi_value", "—")
    bmi_cat = context.user_data.get("bmi_category", "")
    # pyrefly: ignore [no-matching-overload]
    body_label = BODY_TYPE_LABELS.get(
        cast(BodyType, context.user_data.get("body_type")), "—"
    )
    level = context.user_data["experience_level"].value.title()
    freq = context.user_data["training_frequency"]
    split_label = context.user_data["preferred_split"].value.replace("_", " ").title()
    eq_count = len(context.user_data.get("selected_equipment", set()))

    await query.edit_message_text(
        "🎉 *Profilo configurato!*\n\n"
        f"📛 Nome: {name}\n"
        f"📏 Altezza: {height:.0f} cm\n"
        f"⚖️ Peso: {weight:.1f} kg\n"
        f"📊 BMI: {bmi_value} ({bmi_cat})\n"
        f"🦴 Corporatura: {body_label}\n"
        f"• Livello: {level}\n"
        f"• Frequenza: {freq} giorni/settimana\n"
        f"• Split: {split_label}\n"
        f"• Attrezzatura: {eq_count} elementi\n\n"
        "⏳ *Generazione della scheda in corso...*",
        parse_mode="Markdown",
    )

    # Re-show the main menu keyboard
    assert query.message is not None
    from telegram import Message  # pylint: disable=import-outside-toplevel

    if isinstance(query.message, Message):
        try:
            update_id = int(query.id)
        except (ValueError, TypeError):
            update_id = 0

        # Delegate to wod_command to generate a workout for the new profile
        fake_update = Update(
            update_id=update_id,
            message=query.message,
        )
        # Set effective_user manually
        # pylint: disable=protected-access
        fake_update._effective_user = query.from_user
        # pylint: enable=protected-access

        # pylint: disable=import-outside-toplevel
        from wod.bot.handlers.wod import wod_command

        await wod_command(fake_update, context)

        # Show the expanded menu keyboard so they have options ready
        await query.message.reply_text(
            "📋 *Menu completo:*",
            parse_mode="Markdown",
            reply_markup=expanded_menu_keyboard(),
        )
    return ConversationHandler.END


async def cancel_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the onboarding conversation."""
    assert update.message is not None
    await update.message.reply_text(
        "❌ Configurazione annullata. Usa /start per ricominciare."
    )
    return ConversationHandler.END
