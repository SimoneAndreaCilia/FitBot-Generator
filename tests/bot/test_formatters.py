"""Tests for the workout formatters (text and PDF output)."""

from __future__ import annotations

import datetime

from wod.bot.formatters import FormattedExercise, FormattedWorkout, workout_to_pdf, workout_to_text


def _make_workout() -> FormattedWorkout:
    """Create a sample workout for testing."""
    return FormattedWorkout(
        title="Upper Body — Day 1",
        date=datetime.datetime(2025, 6, 15, 14, 30, tzinfo=datetime.timezone.utc),
        exercises=[
            FormattedExercise(order=1, name="Bench Press", sets=4, reps=10),
            FormattedExercise(order=2, name="Dumbbell Row", sets=4, reps=10, notes="Slow"),
            FormattedExercise(order=3, name="Bicep Curl", sets=3, reps=12),
        ],
    )


class TestWorkoutToText:
    """Tests for plain-text rendering."""

    def test_contains_title(self) -> None:
        text = workout_to_text(_make_workout())
        assert "Upper Body — Day 1" in text

    def test_contains_date(self) -> None:
        text = workout_to_text(_make_workout())
        assert "2025-06-15" in text

    def test_contains_exercises(self) -> None:
        text = workout_to_text(_make_workout())
        assert "Bench Press" in text
        assert "Dumbbell Row" in text
        assert "Bicep Curl" in text

    def test_contains_sets_reps(self) -> None:
        text = workout_to_text(_make_workout())
        assert "4" in text
        assert "10" in text
        assert "3" in text
        assert "12" in text

    def test_contains_notes(self) -> None:
        text = workout_to_text(_make_workout())
        assert "Slow" in text

    def test_output_is_string(self) -> None:
        text = workout_to_text(_make_workout())
        assert isinstance(text, str)

    def test_separator_lines(self) -> None:
        text = workout_to_text(_make_workout())
        assert "═" in text

    def test_empty_exercises(self) -> None:
        workout = FormattedWorkout(
            title="Empty",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            exercises=[],
        )
        text = workout_to_text(workout)
        assert "Empty" in text


class TestWorkoutToPdf:
    """Tests for PDF rendering."""

    def test_returns_bytes(self) -> None:
        pdf = workout_to_pdf(_make_workout())
        assert isinstance(pdf, bytes)

    def test_pdf_starts_with_header(self) -> None:
        pdf = workout_to_pdf(_make_workout())
        assert pdf[:5] == b"%PDF-"

    def test_pdf_not_empty(self) -> None:
        pdf = workout_to_pdf(_make_workout())
        assert len(pdf) > 100

    def test_empty_exercises_pdf(self) -> None:
        workout = FormattedWorkout(
            title="Empty",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            exercises=[],
        )
        pdf = workout_to_pdf(workout)
        assert pdf[:5] == b"%PDF-"
