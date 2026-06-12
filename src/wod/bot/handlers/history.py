"""History handler — /history command and workout viewing.

Shows the user's last N generated workouts with inline buttons
to view details, download as .txt or .pdf, and toggle favorites.
"""

from __future__ import annotations

import io
import logging
from typing import cast

from sqlalchemy import select
from telegram import Message, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from wod.bot.formatters import (
    FormattedExercise,
    FormattedWorkout,
    SessionLogRow,
    SessionSummary,
    UserProfile,
    session_summary_to_pdf,
    workout_to_pdf,
)
from wod.bot.keyboards import history_keyboard, workout_actions_keyboard
from wod.bot.locales import get_text
from wod.bot.utils import send_workout_text
from wod.config import get_settings
from wod.core.intensity import calculate_intensity
from wod.core.types import EffortType
from wod.db.models import WorkoutSession
from wod.db.repositories import (
    get_or_create_user,
    get_session_logs,
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
        lang = user.language or "it"

    if not workouts:
        await update.message.reply_text(get_text(lang, "hist_empty"))
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
        get_text(lang, "hist_title"),
        parse_mode="Markdown",
        reply_markup=history_keyboard(lang, workout_tuples),
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
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        lang = user.language or "it"
        workout = await get_workout_by_id(session, workout_id)
        if workout is None:
            await query.edit_message_text(get_text(lang, "hist_not_found"))
            return

        favorites = await get_user_favorites(session, user.id)
        is_fav = any(f.workout_id == workout_id for f in favorites)

    await send_workout_text(
        update,
        workout.content_text,
        reply_markup=workout_actions_keyboard(lang, workout_id, is_fav),
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
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        lang = user.language or "it"
        workout = await get_workout_by_id(session, workout_id)
        if workout is None:
            await query.edit_message_text(get_text(lang, "hist_not_found"))
            return

        # Load user profile with equipment for the PDF
        user_with_eq = await get_user_with_equipment(
            session, telegram_id=query.from_user.id
        )

        user_profile = None
        if user_with_eq is not None:
            user_profile = UserProfile(
                name=user_with_eq.name,
                height_cm=user_with_eq.height_cm,
                weight_kg=user_with_eq.weight_kg,
                body_type=(
                    user_with_eq.body_type.value if user_with_eq.body_type else None
                ),
                experience_level=(
                    user_with_eq.experience_level.value
                    if user_with_eq.experience_level
                    else None
                ),
                training_frequency=user_with_eq.training_frequency,
                preferred_split=(
                    user_with_eq.preferred_split.value
                    if user_with_eq.preferred_split
                    else None
                ),
                equipment=[eq.name for eq in user_with_eq.equipment],
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
                    actual_data=[],
                )
                for we in workout.exercises
            ],
            user_profile=user_profile,
        )

        pdf_bytes = workout_to_pdf(lang, formatted)
        date_str = workout.created_at.strftime("%Y%m%d")

    title_slug = workout.title.replace(" ", "_")
    filename = f"WOD_{title_slug}_{date_str}.pdf"

    assert query.message is not None
    msg: Message = cast(Message, query.message)
    await msg.reply_document(
        document=io.BytesIO(pdf_bytes),
        filename=filename,
        caption=f"📕 {workout.title}",
    )


async def download_summary_callback(  # pylint: disable=too-many-statements
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle dl_sum:<session_id> — send session summary as .pdf file."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None

    session_id = int(query.data.split(":")[1])

    async with get_session_factory()() as db_session:
        user = await get_or_create_user(db_session, telegram_id=query.from_user.id)
        lang = user.language or "it"

        # Get the session
        stmt = select(WorkoutSession).where(WorkoutSession.id == session_id)
        result = await db_session.execute(stmt)
        ws = result.scalar_one_or_none()

        if not ws:
            await query.edit_message_text(get_text(lang, "hist_session_not_found"))
            return

        workout = await get_workout_by_id(db_session, ws.workout_id)
        if not workout:
            await query.edit_message_text(get_text(lang, "hist_not_found"))
            return

        user_with_eq = await get_user_with_equipment(
            db_session, telegram_id=query.from_user.id
        )

        user_profile = None
        if user_with_eq is not None:
            user_profile = UserProfile(
                name=user_with_eq.name,
                height_cm=user_with_eq.height_cm,
                weight_kg=user_with_eq.weight_kg,
                body_type=(
                    user_with_eq.body_type.value if user_with_eq.body_type else None
                ),
                experience_level=(
                    user_with_eq.experience_level.value
                    if user_with_eq.experience_level
                    else None
                ),
                training_frequency=user_with_eq.training_frequency,
                preferred_split=(
                    user_with_eq.preferred_split.value
                    if user_with_eq.preferred_split
                    else None
                ),
                equipment=[eq.name for eq in user_with_eq.equipment],
            )

        logs = await get_session_logs(db_session, ws.id)
        session_rows = []

        ex_by_id = {we.id: we for we in workout.exercises}

        for log in logs:
            we = ex_by_id.get(log.workout_exercise_id)
            if not we:
                continue

            exercise_name = (
                we.exercise.name if we.exercise else f"Esercizio #{we.order_index + 1}"
            )

            intensity = "-"
            rest = "-"
            if we.exercise and user_with_eq and user_with_eq.experience_level:
                try:
                    prescription = calculate_intensity(
                        user_with_eq.experience_level, we.exercise.effort_type
                    )
                    intensity = prescription.intensity
                    rest = (
                        "120s"
                        if we.exercise.effort_type == EffortType.COMPOUND
                        else "60s"
                    )
                except KeyError:
                    pass

            weight_str = f"{log.weight_kg:g}" if log.weight_kg is not None else "0"

            session_rows.append(
                SessionLogRow(
                    order=we.order_index + 1,
                    exercise_name=exercise_name,
                    set_number=log.set_number,
                    kg=weight_str,
                    reps=str(log.reps_done) if log.reps_done is not None else "0",
                    rest=rest,
                    intensity=intensity,
                    skipped=log.skipped,
                )
            )

        summary = SessionSummary(
            title=workout.title,
            date=ws.completed_at or ws.started_at or workout.created_at,
            rows=session_rows,
            user_profile=user_profile,
        )
        pdf_bytes = session_summary_to_pdf(lang, summary)
        date_str = summary.date.strftime("%Y%m%d")

    title_slug = workout.title.replace(" ", "_")
    filename = f"WOD_{title_slug}_{date_str}_Riepilogo.pdf"

    assert query.message is not None
    msg: Message = cast(Message, query.message)
    await msg.reply_document(
        document=io.BytesIO(pdf_bytes),
        filename=filename,
        caption=f"📕 Riepilogo: {workout.title}",
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
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        lang = user.language or "it"
        workout = await get_workout_by_id(session, workout_id)
        if workout is None:
            await query.edit_message_text(get_text(lang, "hist_not_found"))
            return

    txt_bytes = workout.content_text.encode("utf-8")
    date_str = workout.created_at.strftime("%Y%m%d")
    title_slug = workout.title.replace(" ", "_")
    filename = f"WOD_{title_slug}_{date_str}.txt"

    assert query.message is not None
    msg: Message = cast(Message, query.message)
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
    """Build the callback handler for .txt downloads."""
    return CallbackQueryHandler(download_txt_callback, pattern=r"^dl_txt:\d+$")


def build_download_summary_handler() -> (
    CallbackQueryHandler[ContextTypes.DEFAULT_TYPE, None]
):
    """Build the callback handler for session summary downloads."""
    return CallbackQueryHandler(download_summary_callback, pattern=r"^dl_sum:\d+$")
