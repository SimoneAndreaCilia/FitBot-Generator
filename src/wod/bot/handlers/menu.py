"""Menu handler — intercepts ReplyKeyboard button presses.

Provides handlers for the persistent menu buttons shown below the
message bar. Each button press is a regular text message matching
the button label.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from telegram import Message, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from wod.bot.keyboards import (
    BTN_ALTRO,
    BTN_CREA_SCHEDA,
    BTN_PREFERITI,
    BTN_PROFILO,
    BTN_STORICO,
    BTN_WOD,
    crea_scheda_choice_keyboard,
    expanded_menu_keyboard,
    frequency_keyboard,
    split_keyboard,
    wod_day_navigation_keyboard,
)
from wod.core.types import SplitType
from wod.db.repositories import (
    get_or_create_user,
    get_user_with_equipment,
    get_user_workouts,
    update_user_profile,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# "🏋️ Creati una scheda" button
# ---------------------------------------------------------------------------


async def handle_crea_scheda(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle the 'Creati una scheda' button press.

    If the user has a complete profile, offer to use it or create a new one.
    If no profile exists, guide them directly to onboarding.
    """
    assert update.effective_user is not None
    assert update.message is not None

    async with get_session_factory()() as session:
        user = await get_user_with_equipment(session, update.effective_user.id)

    has_complete_profile = (
        user is not None
        and user.experience_level is not None
        and user.training_frequency is not None
        and user.preferred_split is not None
        and len(user.equipment) > 0
    )

    if has_complete_profile:
        await update.message.reply_text(
            "📋 Hai già un profilo configurato!\n\n"
            "Vuoi usare il profilo esistente per generare una nuova scheda, "
            "oppure crearne uno da zero?",
            reply_markup=crea_scheda_choice_keyboard(),
        )
    else:
        # No complete profile — send them to create a new one via callback
        await update.message.reply_text(
            "🏋️ Non hai ancora un profilo completo.\nCreiamone uno insieme!",
            reply_markup=crea_scheda_choice_keyboard(),
        )


# Conversation states for "crea scheda con profilo esistente"
(
    CREA_FREQ,
    CREA_SPLIT,
) = range(2)


async def handle_crea_scheda_existing(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle 'crea:existing' callback — ask frequency before generating."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    await query.edit_message_text(
        "📅 Quanti giorni a settimana vuoi allenarti?",
        reply_markup=frequency_keyboard(),
    )
    return CREA_FREQ


async def _crea_freq_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle frequency selection during existing-profile workout creation."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert context.user_data is not None

    freq = int(query.data.split(":")[1])
    context.user_data["crea_frequency"] = freq

    await query.edit_message_text(
        f"✅ Frequenza: *{freq} giorni/settimana*\n\n"
        "Scegli il tipo di split settimanale:",
        parse_mode="Markdown",
        reply_markup=split_keyboard(frequency=freq),
    )
    return CREA_SPLIT


async def _crea_split_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle split selection, update profile, then generate workout."""
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert query.from_user is not None
    assert context.user_data is not None

    split_str = query.data.split(":")[1]
    split_type = SplitType(split_str)
    freq = context.user_data.get("crea_frequency", 3)

    # Persist the new frequency + split to the user's profile
    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(
            session, user, training_frequency=freq, preferred_split=split_type
        )
        await session.commit()

    await query.edit_message_text("⏳ Generazione della scheda in corso...")

    # Delegate to wod_command
    from wod.bot.handlers.wod import (  # pylint: disable=import-outside-toplevel
        wod_command,
    )

    assert query.message is not None
    if isinstance(query.message, Message):
        fake_update = Update(
            update_id=update.update_id,
            message=query.message,
        )
        # pylint: disable=protected-access
        fake_update._effective_user = query.from_user  # noqa: SLF001
        # pylint: enable=protected-access
        await wod_command(fake_update, context)

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# "Altro" button
# ---------------------------------------------------------------------------


async def handle_altro(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Altro' button — expand the menu."""
    assert update.message is not None

    await update.message.reply_text(
        "📋 *Menu completo:*",
        parse_mode="Markdown",
        reply_markup=expanded_menu_keyboard(),
    )


# ---------------------------------------------------------------------------
# "👤 Profilo" button
# ---------------------------------------------------------------------------


async def handle_profilo(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Profilo' button — delegate to profile display logic."""
    # Import here to avoid circular imports
    from wod.bot.handlers.profile import (  # pylint: disable=import-outside-toplevel
        profile_command,
    )

    await profile_command(update, _context)


# ---------------------------------------------------------------------------
# "📜 Storico" button
# ---------------------------------------------------------------------------


async def handle_storico(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Storico' button — delegate to history display logic."""
    from wod.bot.handlers.history import (  # pylint: disable=import-outside-toplevel
        history_command,
    )

    await history_command(update, _context)


# ---------------------------------------------------------------------------
# "⭐ Preferiti" button
# ---------------------------------------------------------------------------


async def handle_preferiti(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Preferiti' button — delegate to favorites display logic."""
    from wod.bot.handlers.favorites import (  # pylint: disable=import-outside-toplevel
        favorites_command,
    )

    await favorites_command(update, _context)


# ---------------------------------------------------------------------------
# "🔥 WOD del giorno" button + navigation
# ---------------------------------------------------------------------------


def _parse_workout_days(content_json: str) -> list[dict[str, Any]]:
    """Parse a workout's JSON content into per-day exercise lists.

    Returns a list of dicts: [{"label": "Day 1 — Upper", "exercises": [...]}, ...]
    """
    data = json.loads(content_json)
    exercises = data.get("exercises", [])

    # Group exercises by day_label
    days: dict[str, list[dict[str, Any]]] = {}
    day_order: list[str] = []

    for ex in exercises:
        label = ex.get("day_label", "Giorno 1")
        if label not in days:
            days[label] = []
            day_order.append(label)
        days[label].append(ex)

    return [{"label": label, "exercises": days[label]} for label in day_order]


def _format_day_text(day: dict[str, Any], day_index: int, total_days: int) -> str:
    """Format a single training day for display."""
    lines = [
        f"🔥 *WOD del giorno — {day['label']}*",
        f"📅 Giorno {day_index + 1} di {total_days}\n",
    ]

    for i, ex in enumerate(day["exercises"], start=1):
        name = ex.get("name", "Esercizio")
        sets = ex.get("sets", "?")
        reps = ex.get("reps", "?")
        notes = ex.get("notes", "")
        line = f"*{i}.* {name} — {sets}×{reps}"
        if notes:
            line += f"  _{notes}_"
        lines.append(line)

    return "\n".join(lines)


async def handle_wod_giorno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'WOD del giorno' button — show the first training day."""
    assert update.effective_user is not None
    assert update.message is not None
    assert context.user_data is not None

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        workouts = await get_user_workouts(session, user.id, limit=1)

    if not workouts:
        await update.message.reply_text(
            "⚠️ Non hai ancora generato nessuna scheda.\n"
            "Usa 🏋️ *Creati una scheda* per crearne una!",
            parse_mode="Markdown",
        )
        return

    workout = workouts[0]
    days = _parse_workout_days(workout.content_json)

    if not days:
        await update.message.reply_text(
            "⚠️ La scheda non contiene giornate di allenamento."
        )
        return

    # Store workout data in user_data for navigation
    context.user_data["wod_days"] = days
    context.user_data["wod_current_day"] = 0
    context.user_data["wod_workout_id"] = workout.id

    text = _format_day_text(days[0], 0, len(days))
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=wod_day_navigation_keyboard(0, len(days), workout.id),
    )


async def handle_wod_navigation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle wodday:<index> callbacks — navigate between training days.

    Deletes the previous message and sends a new one with the requested day.
    """
    query = update.callback_query
    assert query is not None
    await query.answer()
    assert query.data is not None
    assert context.user_data is not None

    data = query.data.split(":")[1]

    if data == "noop":
        return

    day_index = int(data)
    days = context.user_data.get("wod_days", [])

    if not days or day_index < 0 or day_index >= len(days):
        await query.answer("⚠️ Giornata non disponibile.", show_alert=True)
        return

    context.user_data["wod_current_day"] = day_index

    text = _format_day_text(days[day_index], day_index, len(days))

    workout_id = context.user_data.get("wod_workout_id")
    assert isinstance(workout_id, int)
    # Edit the existing message (replaces content in-place, keeping it clean)
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=wod_day_navigation_keyboard(day_index, len(days), workout_id),
    )


# ---------------------------------------------------------------------------
# Handler builders
# ---------------------------------------------------------------------------


def build_menu_handlers() -> list[MessageHandler]:
    """Build all MessageHandler instances for menu button presses.

    These should be registered AFTER ConversationHandlers so they don't
    interfere with active conversations.
    """
    return [
        MessageHandler(
            filters.TEXT & filters.Regex(f"^{re.escape(BTN_CREA_SCHEDA)}$"),
            handle_crea_scheda,
        ),
        MessageHandler(
            filters.TEXT & filters.Regex(f"^{re.escape(BTN_ALTRO)}$"),
            handle_altro,
        ),
        MessageHandler(
            filters.TEXT & filters.Regex(f"^{re.escape(BTN_PROFILO)}$"),
            handle_profilo,
        ),
        MessageHandler(
            filters.TEXT & filters.Regex(f"^{re.escape(BTN_STORICO)}$"),
            handle_storico,
        ),
        MessageHandler(
            filters.TEXT & filters.Regex(f"^{re.escape(BTN_PREFERITI)}$"),
            handle_preferiti,
        ),
        MessageHandler(
            filters.TEXT & filters.Regex(f"^{re.escape(BTN_WOD)}$"),
            handle_wod_giorno,
        ),
    ]


def build_crea_scheda_existing_handler() -> (
    ConversationHandler[ContextTypes.DEFAULT_TYPE]
):
    """Build the ConversationHandler for 'use existing profile' choice.

    Flow: choose frequency → choose split (filtered) → generate.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                handle_crea_scheda_existing, pattern=r"^crea:existing$"
            ),
        ],
        states={
            CREA_FREQ: [
                CallbackQueryHandler(_crea_freq_callback, pattern=r"^freq:"),
            ],
            CREA_SPLIT: [
                CallbackQueryHandler(_crea_split_callback, pattern=r"^split:"),
            ],
        },
        fallbacks=[],
        per_message=False,
    )


def build_wod_navigation_handler() -> CallbackQueryHandler:
    """Build the callback handler for WOD day navigation."""
    return CallbackQueryHandler(handle_wod_navigation, pattern=r"^wodday:")
