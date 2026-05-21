"""Favorites handler — toggle and list favorite workouts."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from wod.bot.keyboards import history_keyboard, workout_actions_keyboard
from wod.db.repositories import (
    get_or_create_user,
    get_user_favorites,
    get_workout_by_id,
    toggle_favorite,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def favorite_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle fav:<id> — toggle favorite status."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None and query.from_user is not None

    workout_id = int(query.data.split(":")[1])

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        is_now_fav = await toggle_favorite(session, user.id, workout_id)
        workout = await get_workout_by_id(session, workout_id)
        await session.commit()

    if workout is None:
        await query.edit_message_text("Scheda non trovata.")
        return

    status = "Aggiunta ai preferiti!" if is_now_fav else "Rimossa dai preferiti."
    await query.answer(status, show_alert=True)
    await query.edit_message_text(
        f"```\n{workout.content_text}\n```",
        parse_mode="Markdown",
        reply_markup=workout_actions_keyboard(workout_id, is_now_fav),
    )


async def favorites_command(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /favorites — list bookmarked workouts."""
    assert update.effective_user is not None and update.message is not None

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        favorites = await get_user_favorites(session, user.id)

    if not favorites:
        await update.message.reply_text(
            "Non hai ancora nessuna scheda nei preferiti.\nUsa /wod e aggiungila!"
        )
        return

    tuples = [
        (
            f.workout.id,
            f.workout.title,
            f.workout.created_at.strftime("%d/%m/%Y %H:%M"),
            True,
        )
        for f in favorites
        if f.workout is not None
    ]
    await update.message.reply_text(
        "*I tuoi preferiti:*\nTocca per visualizzare:",
        parse_mode="Markdown",
        reply_markup=history_keyboard(tuples),
    )


def build_favorite_callback_handler() -> (
    CallbackQueryHandler[ContextTypes.DEFAULT_TYPE, None]
):
    """Build the callback handler for toggling favorites."""
    return CallbackQueryHandler(favorite_callback, pattern=r"^fav:")


def build_favorites_command_handler() -> (
    CommandHandler[ContextTypes.DEFAULT_TYPE, None]
):
    """Build the /favorites command handler."""
    return CommandHandler("favorites", favorites_command)
