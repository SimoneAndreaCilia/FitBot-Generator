"""Workout formatters — render a workout to text and PDF.

This package re-exports all public symbols so that existing imports
like ``from wod.bot.formatters import FormattedWorkout`` keep working.
"""

from wod.bot.formatters.dataclasses import (
    FormattedExercise,
    FormattedWorkout,
    SessionLogRow,
    SessionSummary,
    UserProfile,
)
from wod.bot.formatters.pdf_session import session_summary_to_pdf
from wod.bot.formatters.pdf_workout import workout_to_pdf
from wod.bot.formatters.text import workout_to_text

__all__ = [
    "FormattedExercise",
    "FormattedWorkout",
    "SessionLogRow",
    "SessionSummary",
    "UserProfile",
    "session_summary_to_pdf",
    "workout_to_pdf",
    "workout_to_text",
]
