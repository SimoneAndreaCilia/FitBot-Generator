"""/start command handler — greeting and menu."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from wod.bot.keyboards import main_menu_keyboard
from wod.db.models import Base
from wod.db.repositories import get_or_create_user
from wod.db.session import get_engine, get_session_factory


async def start_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — greet user by Telegram name and show the main menu."""
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

    first_name = update.effective_user.first_name or "atleta"

    await update.message.reply_text(
        f"Ciao {first_name}! 👋\n\n"
        "Sono *FitBot* 🏋️, il tuo assistente personale di allenamento!\n\n"
        "Ecco cosa posso fare per te:\n"
        "• 🏋️ *Nuova scheda* — crea la tua scheda personalizzata\n"
        "• 👤 *Profilo* — visualizza e modifica il tuo profilo\n"
        "• 🔥 *WOD del giorno* — consulta il tuo allenamento quotidiano\n"
        "• 📜 *Storico* — rivedi le schede passate\n"
        "• ⭐ *Preferiti* — accedi alle schede salvate\n\n"
        "Usa i pulsanti qui sotto per iniziare! 👇",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
