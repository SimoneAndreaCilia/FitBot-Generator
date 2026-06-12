"""Workout regeneration confirmation and cancel command."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from wod.bot.locales import get_text


async def regen_callback(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the regenerate workout confirmation."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None

    choice = query.data.split(":")[1]
    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"

    if choice == "yes":
        await query.edit_message_text(get_text(lang, "regen_yes"))
    else:
        await query.edit_message_text(get_text(lang, "regen_no"))

    return ConversationHandler.END


async def edit_cancel_command(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel the edit conversation."""
    assert update.message is not None
    lang = _context.user_data.get("lang", "it") if _context.user_data else "it"
    await update.message.reply_text(get_text(lang, "edit_cancel"))
    return ConversationHandler.END
