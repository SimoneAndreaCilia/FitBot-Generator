"""Live workout session handler — guides the user through their workout."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from wod.bot.keyboards import (
    end_workout_keyboard,
    live_set_keyboard,
    select_day_keyboard,
)
from wod.core.types import EffortType
from wod.db.models import WorkoutExercise
from wod.db.repositories import (
    complete_workout_session,
    create_workout_session,
    get_or_create_user,
    get_session_logs,
    get_workout_by_id,
    log_set,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)

# Conversation states
SELECT_DAY, WAIT_SET_INPUT = range(2)


async def start_live_workout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Entry point: User clicked 'Inizia Allenamento'."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None

    workout_id = int(query.data.split(":")[1])
    assert context.user_data is not None
    context.user_data["live_workout_id"] = workout_id

    async with get_session_factory()() as session:
        workout = await get_workout_by_id(session, workout_id)

    if not workout or not workout.exercises:
        await query.edit_message_text("⚠️ Impossibile caricare la scheda.")
        return ConversationHandler.END

    # Check if workout has multiple days
    days = []
    for ex in workout.exercises:
        if ex.day_label and ex.day_label not in days:
            days.append(ex.day_label)

    if len(days) > 1:
        await query.edit_message_text(
            "📅 Quale giorno della scheda vuoi allenare oggi?",
            reply_markup=select_day_keyboard(days),
        )
        return SELECT_DAY

    # If only 1 day or no day labels, start immediately
    day_label = days[0] if days else None
    return await _start_session_for_day(update, context, workout, day_label)


async def select_day_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle day selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert context.user_data is not None

    data = query.data.split(":")[1]
    if data == "cancel":
        await query.edit_message_text("❌ Allenamento annullato.")
        return ConversationHandler.END

    workout_id = context.user_data["live_workout_id"]
    async with get_session_factory()() as session:
        workout = await get_workout_by_id(session, workout_id)

    if not workout:
        await query.edit_message_text("⚠️ Errore nel caricamento della scheda.")
        return ConversationHandler.END

    return await _start_session_for_day(update, context, workout, data)


async def _start_session_for_day(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    workout: Any,
    day_label: Optional[str],
) -> int:
    """Initialize state and create DB session."""
    assert update.effective_user is not None
    assert context.user_data is not None

    # Filter exercises for the selected day
    exercises = [
        ex
        for ex in workout.exercises
        if not day_label or ex.day_label == day_label
    ]
    if not exercises:
        msg = "⚠️ Nessun esercizio trovato per questo giorno."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            assert update.message is not None
            await update.message.reply_text(msg)
        return ConversationHandler.END

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        ws = await create_workout_session(session, user.id, workout.id)
        await session.commit()

    context.user_data["live_session_id"] = ws.id
    context.user_data["live_exercises"] = exercises
    context.user_data["live_ex_index"] = 0
    context.user_data["live_set_number"] = 1

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"🚀 *Allenamento Iniziato!*\nScheda: {workout.title}"
            + (f"\nGiorno: {day_label}" if day_label else ""),
            parse_mode="Markdown",
        )

    return await _ask_current_set(update, context)


async def _ask_current_set(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Prompt the user for the current set's data."""
    assert context.user_data is not None
    exercises: list[WorkoutExercise] = context.user_data["live_exercises"]
    ex_index: int = context.user_data["live_ex_index"]
    set_num: int = context.user_data["live_set_number"]

    # Check if workout is finished
    if ex_index >= len(exercises):
        return await _finish_workout(update, context)

    ex = exercises[ex_index]
    assert ex.exercise is not None

    msg = ""
    if set_num > 1 or ex_index > 0:
        msg += "⏳ *Recupero consigliato:* 3 minuti (se hai raggiunto il cedimento)\n\n"

    msg += f"🏋️ *{ex.exercise.name}*\n"
    if ex.notes:
        msg += f"📝 Note: {ex.notes}\n"
    msg += f"📊 Serie *{set_num}* di {ex.sets}  |  🎯 Target: *{ex.reps}*\n\n"
    msg += "Inserisci i dati della serie appena conclusa:\n"
    msg += "Formato: `kg rip` (es: `60 10`)\n"
    msg += "Se a corpo libero inserisci `0 rip` (es: `0 15`)."

    # Send a new message so the user's input flows naturally
    chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id # type: ignore
    await context.bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode="Markdown",
        reply_markup=live_set_keyboard(),
    )
    return WAIT_SET_INPUT


async def handle_set_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process user input for kg and reps."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    text = update.message.text.strip().lower()
    parts = text.split()
    
    if len(parts) != 2:
        await update.message.reply_text(
            "⚠️ Formato non valido. Usa il formato `kg rip` (es: `60 10`).",
            parse_mode="Markdown",
        )
        return WAIT_SET_INPUT

    try:
        weight = float(parts[0].replace(",", "."))
        reps = int(parts[1])
    except ValueError:
        await update.message.reply_text(
            "⚠️ Valori non validi. Assicurati di inserire numeri (es: `60.5 10`).",
            parse_mode="Markdown",
        )
        return WAIT_SET_INPUT

    # Save to DB
    session_id = context.user_data["live_session_id"]
    exercises: list[WorkoutExercise] = context.user_data["live_exercises"]
    ex_index: int = context.user_data["live_ex_index"]
    set_num: int = context.user_data["live_set_number"]
    ex = exercises[ex_index]

    async with get_session_factory()() as db_session:
        await log_set(
            db_session,
            session_id=session_id,
            workout_exercise_id=ex.id,
            set_number=set_num,
            weight_kg=weight,
            reps_done=reps,
            skipped=False,
        )
        await db_session.commit()

    return await _advance_state_and_rest(update, context)


async def handle_live_set_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Process inline button actions (Skip or Abort)."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert context.user_data is not None

    action = query.data.split(":")[1]

    if action == "abort":
        session_id = context.user_data["live_session_id"]
        async with get_session_factory()() as db_session:
            await complete_workout_session(db_session, session_id, status="abandoned")
            await db_session.commit()
            
        await query.edit_message_text("❌ Allenamento interrotto e salvato parzialmente.")
        context.user_data.pop("live_session_id", None)
        return ConversationHandler.END

    if action == "skip":
        # Save skipped set
        session_id = context.user_data["live_session_id"]
        exercises: list[WorkoutExercise] = context.user_data["live_exercises"]
        ex_index: int = context.user_data["live_ex_index"]
        set_num: int = context.user_data["live_set_number"]
        ex = exercises[ex_index]

        async with get_session_factory()() as db_session:
            await log_set(
                db_session,
                session_id=session_id,
                workout_exercise_id=ex.id,
                set_number=set_num,
                weight_kg=0,
                reps_done=0,
                skipped=True,
            )
            await db_session.commit()

        # Remove the keyboard from the previous prompt
        await query.edit_message_reply_markup(reply_markup=None)
        
        # Advance state
        _advance_indexes(context)
        return await _ask_current_set(update, context)

    return WAIT_SET_INPUT


def _advance_indexes(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Advance the counters to the next set or exercise."""
    assert context.user_data is not None
    exercises: list[WorkoutExercise] = context.user_data["live_exercises"]
    ex_index: int = context.user_data["live_ex_index"]
    set_num: int = context.user_data["live_set_number"]
    
    if ex_index >= len(exercises):
        return

    ex = exercises[ex_index]
    if set_num < ex.sets:
        context.user_data["live_set_number"] += 1
    else:
        context.user_data["live_ex_index"] += 1
        context.user_data["live_set_number"] = 1


async def _advance_state_and_rest(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Advance state and trigger rest timer if not finished."""
    assert context.user_data is not None
    exercises: list[WorkoutExercise] = context.user_data["live_exercises"]
    ex_index: int = context.user_data["live_ex_index"]
    
    current_ex = exercises[ex_index]
    assert current_ex.exercise is not None

    _advance_indexes(context)
    new_ex_index: int = context.user_data["live_ex_index"]

    if new_ex_index >= len(exercises):
        # Workout finished
        return await _finish_workout(update, context)

    return await _ask_current_set(update, context)


async def _finish_workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the workout, save status, and show summary."""
    assert context.user_data is not None
    session_id = context.user_data["live_session_id"]
    workout_id = context.user_data["live_workout_id"]

    async with get_session_factory()() as db_session:
        ws = await complete_workout_session(db_session, session_id, status="completed")
        assert ws is not None
        logs = await get_session_logs(db_session, session_id)
        
        # Calculate duration
        duration = ws.completed_at - ws.started_at if ws.completed_at else None
        duration_str = ""
        if duration:
            mins = int(duration.total_seconds() // 60)
            duration_str = f"⏱️ *Durata:* {mins} min"

        # Build summary text
        total_sets = len(logs)
        skipped_sets = sum(1 for log in logs if log.skipped)
        completed_sets = total_sets - skipped_sets

        summary = (
            f"🎉 *Allenamento Completato!*\n"
            f"Bravissimo! Hai portato a termine la tua sessione.\n\n"
            f"{duration_str}\n"
            f"📊 *Totale:* {total_sets} serie | {completed_sets} completate | {skipped_sets} saltate\n\n"
            f"*Dettaglio:* \n"
        )

        current_ex_id = -1
        for log in logs:
            if log.workout_exercise_id != current_ex_id:
                summary += f"\n🏋️ *{log.workout_exercise.exercise.name}*\n"
                current_ex_id = log.workout_exercise_id

            if log.skipped:
                summary += f"  Serie {log.set_number}: ⏭️ Saltata\n"
            else:
                weight_str = f"{log.weight_kg:g}" if log.weight_kg is not None else "0"
                summary += f"  Serie {log.set_number}: {weight_str}kg × {log.reps_done}\n"

    # Send final summary
    chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id # type: ignore
    await context.bot.send_message(
        chat_id=chat_id,
        text=summary,
        parse_mode="Markdown",
        reply_markup=end_workout_keyboard(session_id),
    )

    # Clean up
    context.user_data.pop("live_session_id", None)
    context.user_data.pop("live_exercises", None)
    
    return ConversationHandler.END


async def cancel_live_workout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle /cancel during a live workout."""
    assert update.message is not None
    
    assert context.user_data is not None
    session_id = context.user_data.get("live_session_id")
    if session_id:
        async with get_session_factory()() as db_session:
            await complete_workout_session(db_session, session_id, status="abandoned")
            await db_session.commit()

    await update.message.reply_text("❌ Allenamento interrotto.")
    return ConversationHandler.END


def build_live_workout_handler() -> ConversationHandler[ContextTypes.DEFAULT_TYPE]:
    """Build the ConversationHandler for the live workout session."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_live_workout, pattern=r"^startw:"),
        ],
        states={
            SELECT_DAY: [
                CallbackQueryHandler(select_day_callback, pattern=r"^selday:"),
            ],
            WAIT_SET_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_input),
                CallbackQueryHandler(handle_live_set_action, pattern=r"^liveset:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_live_workout)],
        per_message=False,
    )
