"""Tests for the workout formatters (text and PDF output)."""

from __future__ import annotations

import datetime

from wod.bot.formatters import (
    FormattedExercise,
    FormattedWorkout,
    SessionLogRow,
    SessionSummary,
    UserProfile,
    session_summary_to_pdf,
    workout_to_pdf,
    workout_to_text,
)


def _make_workout() -> FormattedWorkout:
    """Create a sample workout for testing."""
    return FormattedWorkout(
        title="Upper Body — Day 1",
        date=datetime.datetime(2025, 6, 15, 14, 30, tzinfo=datetime.timezone.utc),
        exercises=[
            FormattedExercise(order=1, name="Bench Press", sets=4, reps="10"),
            FormattedExercise(
                order=2, name="Dumbbell Row", sets=4, reps="10", notes="Slow"
            ),
            FormattedExercise(order=3, name="Bicep Curl", sets=3, reps="12"),
        ],
    )


class TestWorkoutToText:
    """Tests for plain-text rendering."""

    def test_contains_title(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert "Upper Body — Day 1" in text

    def test_contains_date(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert "2025-06-15" in text

    def test_contains_exercises(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert "Bench Press" in text
        assert "Dumbbell Row" in text
        assert "Bicep Curl" in text

    def test_contains_sets_reps(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert "4" in text
        assert "10" in text
        assert "3" in text
        assert "12" in text

    def test_contains_notes(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert "Slow" in text

    def test_output_is_string(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert isinstance(text, str)

    def test_separator_lines(self) -> None:
        text = workout_to_text("it", _make_workout())
        assert "═" in text

    def test_empty_exercises(self) -> None:
        workout = FormattedWorkout(
            title="Empty",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            exercises=[],
        )
        text = workout_to_text("it", workout)
        assert "Empty" in text


class TestWorkoutToPdf:
    """Tests for PDF rendering."""

    def test_returns_bytes(self) -> None:
        pdf = workout_to_pdf("it", _make_workout())
        assert isinstance(pdf, bytes)

    def test_pdf_starts_with_header(self) -> None:
        pdf = workout_to_pdf("it", _make_workout())
        assert pdf[:5] == b"%PDF-"

    def test_workout_to_pdf_multiple_days(self) -> None:
        workout = _make_workout()

        workout.exercises.append(
            FormattedExercise(
                order=2,
                name="Squat",
                sets=3,
                reps="10",
                day_label="Day 2",
            )
        )
        pdf = workout_to_pdf("it", workout)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_pdf_not_empty(self) -> None:
        pdf = workout_to_pdf("it", _make_workout())
        assert len(pdf) > 100

    def test_empty_exercises_pdf(self) -> None:
        workout = FormattedWorkout(
            title="Empty",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            exercises=[],
        )
        pdf = workout_to_pdf("it", workout)
        assert pdf[:5] == b"%PDF-"

    def test_with_user_profile(self) -> None:
        workout = _make_workout()
        workout.user_profile = UserProfile(
            name="John",
            height_cm=180,
            weight_kg=80,
            body_type="Ectomorph",
            equipment=["Dumbbell"],
        )
        pdf = workout_to_pdf("it", workout)
        assert b"%PDF-" in pdf

    def test_with_actual_data(self) -> None:
        workout = _make_workout()
        workout.exercises[0].actual_data = ["Set 1: 100kg x 10"]
        workout.exercises[1].notes = "Some notes"
        workout.exercises[1].actual_data = ["Set 1: 50kg x 10"]
        pdf = workout_to_pdf("it", workout)
        assert b"%PDF-" in pdf


class TestSessionSummaryToPdf:
    def test_returns_bytes(self) -> None:
        summary = SessionSummary(
            title="My Workout",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            user_profile=UserProfile(name="Alice"),
            rows=[
                SessionLogRow(
                    order=1,
                    exercise_name="Squat",
                    set_number=1,
                    kg="60.5",
                    reps="10",
                    rest="90s",
                    intensity="8 RPE",
                    skipped=False,
                ),
                SessionLogRow(
                    order=2,
                    exercise_name="Bench Press",
                    set_number=2,
                    kg="0",
                    reps="0",
                    rest="90s",
                    intensity="",
                    skipped=True,
                ),
            ],
        )
        pdf = session_summary_to_pdf("it", summary)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_empty_rows(self) -> None:
        summary = SessionSummary(
            title="Empty Workout",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            rows=[],
        )
        pdf = session_summary_to_pdf("it", summary)
        assert pdf[:5] == b"%PDF-"
