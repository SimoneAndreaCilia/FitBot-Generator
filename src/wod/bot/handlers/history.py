"""History handler — /history command and workout viewing.

Shows the user's last N generated workouts with inline buttons
to view details, download as .txt or .pdf, and toggle favorites.
"""

from __future__ import annotations

import io
import logging

from telegram import Message, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from wod.bot.formatters import (
    FormattedExercise,
    FormattedWorkout,
    UserProfile,
    workout_to_pdf,
)
from wod.bot.keyboards import history_keyboard, workout_actions_keyboard
from wod.bot.utils import send_workout_text
from wod.config import get_settings
from wod.db.repositories import (
    get_or_create_user,
    get_user_favorites,
    get_user_with_equipment,
    get_user_workouts,
    get_workout_by_id,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def history_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history — list recent workouts."""
    assert update.effective_user is not None
    assert update.message is not None

    settings = get_settings()

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        workouts = await get_user_workouts(
            session, user.id, limit=settings.max_history_items
        )
        favorites = await get_user_favorites(session, user.id)
        fav_workout_ids = {fav.workout_id for fav in favorites}

    if not workouts:
        await update.message.reply_text(
            "📋 Non hai ancora generato nessuna scheda.\n"
            "Usa /wod per creare il tuo primo allenamento!"
        )
        return

    workout_tuples = [
        (
            w.id,
            w.title,
            w.created_at.strftime("%d/%m/%Y %H:%M"),
            w.id in fav_workout_ids,
        )
        for w in workouts
    ]

    await update.message.reply_text(
        "📋 *Le tue ultime schede:*\n\nTocca per visualizzare:",
        parse_mode="Markdown",
        reply_markup=history_keyboard(workout_tuples),
    )


async def view_workout_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle view:<id> — display a specific workout."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    workout_id = int(query.data.split(":")[1])

    async with get_session_factory()() as session:
        workout = await get_workout_by_id(session, workout_id)
        if workout is None:
            await query.edit_message_text("❌ Scheda non trovata.")
            return

        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        favorites = await get_user_favorites(session, user.id)
        is_fav = any(f.workout_id == workout_id for f in favorites)

    await send_workout_text(
        update,
        workout.content_text,
        reply_markup=workout_actions_keyboard(workout_id, is_fav),
        parse_mode="Markdown",
    )


async def download_pdf_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle dl_pdf:<id> — send workout as .pdf file."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    workout_id = int(query.data.split(":")[1])

    async with get_session_factory()() as session:
        workout = await get_workout_by_id(session, workout_id)
        if workout is None:
            await query.edit_message_text("❌ Scheda non trovata.")
            return

        # Load user profile with equipment for the PDF
        user = await get_user_with_equipment(
            session, telegram_id=query.from_user.id
        )

    # Build user profile for the PDF (if available)
    user_profile = None
    if user is not None:
        user_profile = UserProfile(
            name=user.name,
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            body_type=user.body_type.value if user.body_type else None,
            experience_level=(
                user.experience_level.value if user.experience_level else None
            ),
            training_frequency=user.training_frequency,
            preferred_split=(
                user.preferred_split.value if user.preferred_split else None
            ),
            equipment=[eq.name for eq in user.equipment],
        )

    # Build FormattedWorkout from stored data
    formatted = FormattedWorkout(
        title=workout.title,
        date=workout.created_at,
        exercises=[
            FormattedExercise(
                order=we.order_index + 1,
                name=(
                    we.exercise.name
                    if we.exercise
                    else f"Esercizio #{we.order_index + 1}"
                ),
                sets=we.sets,
                reps=we.reps,
                notes=we.notes,
                day_label=we.day_label,
            )
            for we in workout.exercises
        ],
        user_profile=user_profile,
    )

    pdf_bytes = workout_to_pdf(formatted)
    date_str = workout.created_at.strftime("%Y%m%d")
    title_slug = workout.title.replace(" ", "_")
    filename = f"WOD_{title_slug}_{date_str}.pdf"

    assert query.message is not None
    msg: Message = query.message  # type: ignore[assignment]
    await msg.reply_document(
        document=io.BytesIO(pdf_bytes),
        filename=filename,
        caption=f"📕 {workout.title}",
    )


async def download_txt_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle dl_txt:<id> — send workout as .txt file."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None

    workout_id = int(query.data.split(":")[1])

    async with get_session_factory()() as session:
        workout = await get_workout_by_id(session, workout_id)
        if workout is None:
            await query.edit_message_text("❌ Scheda non trovata.")
            return

    txt_bytes = workout.content_text.encode("utf-8")
    date_str = workout.created_at.strftime("%Y%m%d")
    title_slug = workout.title.replace(" ", "_")
    filename = f"WOD_{title_slug}_{date_str}.txt"

    assert query.message is not None
    msg: Message = query.message  # type: ignore[assignment]
    await msg.reply_document(
        document=io.BytesIO(txt_bytes),
        filename=filename,
        caption=f"📄 {workout.title}",
    )


def build_history_handler() -> CommandHandler[ContextTypes.DEFAULT_TYPE, None]:
    """Build the /history command handler."""
    return CommandHandler(["history", "mie_schede"], history_command)


def build_view_callback_handler() -> (
    CallbackQueryHandler[ContextTypes.DEFAULT_TYPE, None]
):
    """Build the callback handler for viewing a workout."""
    return CallbackQueryHandler(view_workout_callback, pattern=r"^view:")


def build_download_pdf_handler() -> (
    CallbackQueryHandler[ContextTypes.DEFAULT_TYPE, None]
):
    """Build the callback handler for .pdf download."""
    return CallbackQueryHandler(download_pdf_callback, pattern=r"^dl_pdf:")


def build_download_txt_handler() -> (
    CallbackQueryHandler[ContextTypes.DEFAULT_TYPE, None]
):
    """Build the callback handler for .txt download."""
    return CallbackQueryHandler(download_txt_callback, pattern=r"^dl_txt:")
