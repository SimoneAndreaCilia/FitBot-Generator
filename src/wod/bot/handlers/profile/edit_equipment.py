"""Equipment editing during profile modification."""

from __future__ import annotations

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from wod.bot.handlers.profile.constants import EDIT_EQUIPMENT, REGEN_CONFIRM
from wod.bot.keyboards import equipment_keyboard, regenerate_keyboard
from wod.bot.locales import get_text
from wod.bot.utils import handle_equipment_toggle
from wod.db.repositories import get_or_create_user, set_user_equipment
from wod.db.session import get_session_factory


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
    lang = context.user_data.get("lang", "it") if context.user_data else "it"

    if data == "done":
        selected_ids = list(context.user_data.get("selected_equipment", set()))
        if not selected_ids:
            await query.answer(
                text=get_text(lang, "edit_eq_err"),
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
            get_text(lang, "edit_eq_ok", eq_count=eq_count),
            parse_mode="Markdown",
            reply_markup=regenerate_keyboard(lang),
        )
        return REGEN_CONFIRM

    await query.answer()
    eq_list = context.user_data["equipment_list"]
    handle_equipment_toggle(context.user_data, data)
    selected_set = context.user_data["selected_equipment"]
    try:
        await query.edit_message_text(
            get_text(lang, "edit_eq_prompt"),
            reply_markup=equipment_keyboard(lang, eq_list, selected_set),
        )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise

    return EDIT_EQUIPMENT
