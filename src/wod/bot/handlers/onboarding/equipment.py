"""Equipment selection during onboarding."""

from __future__ import annotations

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from wod.bot.handlers.onboarding.constants import EQUIPMENT
from wod.bot.handlers.onboarding.finalize import _finalize_onboarding
from wod.bot.keyboards import equipment_keyboard
from wod.bot.utils import handle_equipment_toggle


async def equipment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """Handle equipment toggle or confirmation."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None
    assert context.user_data is not None

    data = query.data.split(":")[1]

    if data == "done":
        selected = context.user_data.get("selected_equipment", set())
        if not selected:
            await query.answer(
                text="⚠️ Seleziona almeno un attrezzo per procedere!",
                show_alert=True,
            )
            return EQUIPMENT
        await query.answer()
        # Save everything to DB
        return await _finalize_onboarding(query, context)

    await query.answer()
    handle_equipment_toggle(context.user_data, data)

    selected = context.user_data["selected_equipment"]
    eq_list = context.user_data["equipment_list"]
    try:
        await query.edit_message_text(
            "Seleziona l'attrezzatura disponibile nella tua Home Gym.\n"
            "Tocca per selezionare/deselezionare, poi conferma:",
            reply_markup=equipment_keyboard(eq_list, selected),
        )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise

    return EQUIPMENT
