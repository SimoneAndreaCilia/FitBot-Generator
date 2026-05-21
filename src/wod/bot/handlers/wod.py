"""WOD command handler — generate the Workout of the Day.

Orchestrates the core logic:
1. Load user profile + equipment from DB
2. Filter exercises by user equipment
3. Generate the day's split
4. Calculate intensity (sets × reps)
5. Format, display, and persist the workout
"""

from __future__ import annotations

import json
import logging
import random
import datetime

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


async def wod_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

        # 2. Generate today's training day from the weekly split
        training_day = _pick_today_training_day(
            user.preferred_split, user.training_frequency
        )

        # 3. Filter exercises by today's muscle groups
        day_exercises = filter_exercises_by_muscle_groups(
            available_exercises, training_day.muscle_groups
        )

        if not day_exercises:
            await update.message.reply_text(
                "😔 Non ho trovato esercizi per i gruppi muscolari di oggi.\n"
                "Prova a rivedere la tua attrezzatura con /start."
            )
            return

        # 4. Select and prescribe exercises
        selected = _select_exercises(day_exercises, training_day)
        prescribed = _prescribe_exercises(selected, user.experience_level)

        # 5. Format
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        formatted = FormattedWorkout(
            title=training_day.label,
            date=now,
            exercises=prescribed,
        )
        text = workout_to_text(formatted)

        # 6. Persist
        content_json = json.dumps(
            {
                "title": training_day.label,
                "day_number": training_day.day_number,
                "exercises": [
                    {
                        "name": ex.name,
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "notes": ex.notes,
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
                }
            )

        workout = await save_workout(
            session,
            user=user,
            title=training_day.label,
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


def _pick_today_training_day(split_type: SplitType, frequency: int) -> TrainingDay:
    """Pick today's training day based on the day of the week.

    Cycles through the weekly plan using the current ISO weekday
    modulo the training frequency.
    """
    weekly_plan = generate_weekly_split(split_type, frequency)
    today_index = (datetime.date.today().isoweekday() - 1) % len(weekly_plan)
    return weekly_plan[today_index]


def _select_exercises(
    exercises: list[Exercise],
    training_day: TrainingDay,
) -> list[Exercise]:
    """Select a balanced subset of exercises for the training day.

    Picks up to ``MAX_EXERCISES_PER_GROUP`` exercises per muscle group,
    preferring compound movements first.
    """
    selected: list[Exercise] = []

    for group in training_day.muscle_groups:
        group_exercises = [ex for ex in exercises if ex.muscle_group == group]

        # Compounds first, then isolations
        compounds = [ex for ex in group_exercises if ex.effort_type.value == "compound"]
        isolations = [
            ex for ex in group_exercises if ex.effort_type.value == "isolation"
        ]

        random.shuffle(compounds)
        random.shuffle(isolations)

        picks = (compounds + isolations)[:MAX_EXERCISES_PER_GROUP]
        selected.extend(picks)

    return selected


def _prescribe_exercises(
    exercises: list[Exercise],
    experience: ExperienceLevel,
) -> list[FormattedExercise]:
    """Apply intensity prescriptions to the selected exercises."""
    result: list[FormattedExercise] = []
    for i, ex in enumerate(exercises, start=1):
        prescription = calculate_intensity(experience, ex.effort_type)
        result.append(
            FormattedExercise(
                order=i,
                name=ex.name,
                sets=prescription.sets,
                reps=prescription.reps,
            )
        )
    return result


def build_wod_handler() -> CommandHandler[ContextTypes.DEFAULT_TYPE, None]:
    """Build the /wod command handler."""
    return CommandHandler("wod", wod_command)
