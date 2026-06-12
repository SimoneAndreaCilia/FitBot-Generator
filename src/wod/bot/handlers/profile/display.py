"""Profile display — /profilo command and profile text formatting."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from wod.bot.keyboards import profile_keyboard
from wod.bot.locales import get_text
from wod.core.bmi import calculate_bmi
from wod.db.repositories import get_user_with_equipment
from wod.db.session import get_session_factory


def _format_profile_text(lang: str, user) -> str:  # type: ignore[no-untyped-def]
    """Build the profile display text from a User model instance."""
    name = user.name or "—"
    height = f"{user.height_cm:.0f} cm" if user.height_cm else "—"
    weight = f"{user.weight_kg:.1f} kg" if user.weight_kg else "—"

    if user.height_cm and user.weight_kg:
        bmi_val, bmi_cat_key = calculate_bmi(user.weight_kg, user.height_cm)
        bmi_cat = get_text(lang, bmi_cat_key)
        bmi_str = f"{bmi_val} ({bmi_cat})"
    else:
        bmi_str = "—"

    body = get_text(lang, f"lbl_{user.body_type.value}") if user.body_type else "—"
    level = (
        get_text(lang, f"lbl_{user.experience_level.value}")
        if user.experience_level
        else "—"
    )
    freq = (
        get_text(lang, "prof_freq_val", freq=user.training_frequency)
        if user.training_frequency
        else "—"
    )
    split = (
        get_text(lang, f"lbl_{user.preferred_split.value}")
        if user.preferred_split
        else "—"
    )

    eq_names = sorted(eq.name.replace("_", " ").title() for eq in user.equipment)
    eq_str = ", ".join(eq_names) if eq_names else get_text(lang, "prof_eq_none")

    return get_text(
        lang,
        "prof_display",
        name=name,
        height=height,
        weight=weight,
        bmi_str=bmi_str,
        body=body,
        level=level,
        freq=freq,
        split=split,
        eq_str=eq_str,
    )


async def profile_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /profilo — display the user's profile."""
    assert update.effective_user is not None
    assert update.message is not None

    async with get_session_factory()() as session:
        user = await get_user_with_equipment(session, update.effective_user.id)
        # Note: if user is None, we don't have their DB language, fallback to 'it'
        lang = user.language if user and user.language else "it"

    if user is None:
        await update.message.reply_text(get_text(lang, "prof_no_profile"))
        return

    if _context.user_data is not None:
        _context.user_data["lang"] = lang

    text = _format_profile_text(lang, user)
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=profile_keyboard(lang),
    )
