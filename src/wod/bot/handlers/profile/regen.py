"""Workout regeneration confirmation and cancel command."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


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


async def edit_cancel_command(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel the edit conversation."""
    assert update.message is not None
    await update.message.reply_text("❌ Modifica annullata.")
    return ConversationHandler.END
