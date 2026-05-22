"""WOD command handler — generate the Workout of the Day.

Orchestrates the core logic:
1. Load user profile + equipment from DB
2. Filter exercises by user equipment
3. Generate the day's split
4. Calculate intensity (sets × reps)
5. Format, display, and persist the workout
"""

from __future__ import annotations

import datetime
import json
import logging
import random

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from wod.bot.formatters import (
    FormattedExercise,
    FormattedWorkout,
    workout_to_text,
)
from wod.bot.keyboards import workout_actions_keyboard
from wod.core.engine import (
    filter_exercises_by_equipment,
    filter_exercises_by_muscle_groups,
)
from wod.core.intensity import calculate_intensity
from wod.core.split_generator import TrainingDay, generate_weekly_split
from wod.core.types import ExperienceLevel, SplitType
from wod.db.models import Exercise
from wod.db.repositories import (
    get_all_exercises,
    get_or_create_user,
    save_workout,
)
from wod.db.session import get_session_factory

logger = logging.getLogger(__name__)

# Max exercises per muscle group in a single session
MAX_EXERCISES_PER_GROUP = 2


async def wod_command(  # pylint: disable=too-many-locals
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /wod — generate today's workout."""
    assert update.effective_user is not None
    assert update.message is not None

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)

        # Validate profile completeness
        if (
            not user.experience_level
            or not user.training_frequency
            or not user.preferred_split
        ):
            await update.message.reply_text(
                "⚠️ Il tuo profilo non è completo.\n"
                "Usa /start per configurare livello, frequenza e split."
            )
            return

        # Load exercises and user equipment
        all_exercises = list(await get_all_exercises(session))
        user_equipment = list(user.equipment)

        if not user_equipment:
            await update.message.reply_text(
                "⚠️ Non hai selezionato nessuna attrezzatura.\n"
                "Usa /start per configurare la tua Home Gym."
            )
            return

        # 1. Filter exercises by user's available equipment
        available_exercises = filter_exercises_by_equipment(
            all_exercises, user_equipment
        )

        if not available_exercises:
            await update.message.reply_text(
                "😔 Non ho trovato esercizi compatibili con la tua attrezzatura.\n"
                "Prova ad aggiungere più attrezzatura con /start."
            )
            return

        # 2. Generate weekly split
        weekly_plan = generate_weekly_split(
            user.preferred_split, user.training_frequency
        )

        prescribed = []
        global_order = 1
        
        for training_day in weekly_plan:
            # 3. Filter exercises by today's muscle groups
            day_exercises = filter_exercises_by_muscle_groups(
                available_exercises, training_day.muscle_groups
            )

            # 4. Select and prescribe exercises
            selected = _select_exercises(day_exercises, training_day)
            day_prescribed = _prescribe_exercises(
                selected, 
                user.experience_level, 
                day_label=training_day.label, 
                start_order=global_order
            )
            prescribed.extend(day_prescribed)
            global_order += len(day_prescribed)

        if not prescribed:
            await update.message.reply_text(
                "😔 Non ho trovato esercizi sufficienti per i tuoi gruppi muscolari.\n"
                "Prova a rivedere la tua attrezzatura con /start."
            )
            return

        # 5. Format
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        workout_title = f"Scheda Settimanale — {user.preferred_split.value.title().replace('_', ' ')}"
        formatted = FormattedWorkout(
            title=workout_title,
            date=now,
            exercises=prescribed,
        )
        text = workout_to_text(formatted)

        # 6. Persist
        content_json = json.dumps(
            {
                "title": workout_title,
                "exercises": [
                    {
                        "name": ex.name,
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "notes": ex.notes,
                        "day_label": ex.day_label,
                    }
                    for ex in prescribed
                ],
            },
            ensure_ascii=False,
        )

        # Build exercise_entries for DB
        exercise_entries = []
        exercise_name_to_id = {ex.name: ex.id for ex in all_exercises}
        for ex in prescribed:
            exercise_entries.append(
                {
                    "exercise_id": exercise_name_to_id.get(ex.name),
                    "sets": ex.sets,
                    "reps": ex.reps,
                    "order_index": ex.order,
                    "notes": ex.notes,
                    "day_label": ex.day_label,
                }
            )

        workout = await save_workout(
            session,
            user=user,
            title=workout_title,
            content_json=content_json,
            content_text=text,
            exercise_entries=exercise_entries,
        )
        await session.commit()

        # 7. Send to user
        await update.message.reply_text(
            f"```\n{text}\n```",
            parse_mode="Markdown",
            reply_markup=workout_actions_keyboard(workout.id, is_favorite=False),
        )


def _select_exercises(
    exercises: list[Exercise],
    training_day: TrainingDay,
) -> list[Exercise]:
    """Select a balanced subset of exercises for the training day.

    Picks exactly 1 weight=1 and 1 weight=2 exercise per muscle group.
    """
    selected: list[Exercise] = []

    for group in training_day.muscle_groups:
        group_exercises = [ex for ex in exercises if ex.muscle_group == group]

        weight_1 = [ex for ex in group_exercises if getattr(ex, "weight", 1) == 1]
        weight_2 = [ex for ex in group_exercises if getattr(ex, "weight", 1) == 2]

        if weight_1:
            selected.append(random.choice(weight_1))
        if weight_2:
            selected.append(random.choice(weight_2))

    return selected


def _prescribe_exercises(
    exercises: list[Exercise],
    experience: ExperienceLevel,
    day_label: str,
    start_order: int = 1,
) -> list[FormattedExercise]:
    """Apply intensity prescriptions to the selected exercises."""
    result: list[FormattedExercise] = []
    for i, ex in enumerate(exercises, start=start_order):
        prescription = calculate_intensity(experience, ex.effort_type)
        result.append(
            FormattedExercise(
                order=i,
                name=ex.name,
                sets=prescription.sets,
                reps=prescription.reps,
                day_label=day_label,
            )
        )
    return result


def build_wod_handler() -> CommandHandler[ContextTypes.DEFAULT_TYPE, None]:
    """Build the /wod command handler."""
    return CommandHandler("wod", wod_command)
