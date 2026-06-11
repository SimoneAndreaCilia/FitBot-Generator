"""Profile display — /profilo command and profile text formatting."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from wod.bot.handlers.profile.constants import (
    BODY_TYPE_LABELS,
    EXPERIENCE_LABELS,
    SPLIT_LABELS,
)
from wod.bot.keyboards import profile_keyboard
from wod.core.bmi import calculate_bmi
from wod.db.repositories import get_user_with_equipment
from wod.db.session import get_session_factory


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

    body = BODY_TYPE_LABELS.get(user.body_type, "—")
    level = EXPERIENCE_LABELS.get(user.experience_level, "—")
    freq = (
        f"{user.training_frequency} giorni/settimana"
        if user.training_frequency
        else "—"
    )
    split = SPLIT_LABELS.get(user.preferred_split, "—")

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
