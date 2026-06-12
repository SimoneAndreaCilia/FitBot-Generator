"""/start command handler — greeting and menu."""

from __future__ import annotations

from typing import Any

from telegram import (
    BotCommand,
    BotCommandScopeChat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import CallbackQueryHandler, ContextTypes

from wod.bot.keyboards import main_menu_keyboard
from wod.bot.locales import get_text
from wod.db.models import Base
from wod.db.repositories import get_or_create_user, update_user_profile
from wod.db.session import get_engine, get_session_factory


async def start_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — ask for language or greet user and show main menu."""
    assert update.effective_user is not None
    assert update.message is not None

    # Ensure tables exist
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_factory()() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
        )
        await session.commit()
        language = user.language

    # If the user has no language preference, prompt for it
    if not language:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang:it"),
                    InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
                ]
            ]
        )
        await update.message.reply_text(
            get_text("it", "choose_language"),
            reply_markup=keyboard,
        )
        return

    # Language is set, proceed with translated welcome message
    first_name = update.effective_user.first_name or "atleta"
    lang = user.language or "it"
    welcome_msg = get_text(lang, "welcome", name=first_name)

    await update.message.reply_text(
        welcome_msg,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def handle_language_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle the language selection from the inline keyboard."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    lang_code = query.data.split(":")[1]

    assert update.effective_user is not None

    # Save language to the database
    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        await update_user_profile(session, user, language=lang_code)
        await session.commit()

    # Set user-scoped bot commands based on the selected language
    commands = [
        BotCommand("start", get_text(lang_code, "cmd_start")),
    ]
    assert update.effective_chat is not None
    await context.bot.set_my_commands(
        commands, scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )

    # Delete the inline keyboard message and send the welcome message
    first_name = update.effective_user.first_name or "atleta"
    welcome_msg = get_text(lang_code, "welcome", name=first_name)
    language_set_msg = get_text(lang_code, "language_set")

    await query.edit_message_text(
        f"{language_set_msg}\n\n{welcome_msg}", parse_mode="Markdown"
    )

    # We also send the main menu keyboard using a new message because
    # edit_message_text cannot easily add a ReplyKeyboardMarkup
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👇",
        reply_markup=main_menu_keyboard(lang_code),
    )


def build_language_handlers() -> list[CallbackQueryHandler[Any, Any]]:
    """Build the callback handler for language selection."""
    return [
        CallbackQueryHandler(handle_language_selection, pattern=r"^lang:"),
    ]
