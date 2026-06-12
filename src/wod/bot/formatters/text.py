"""Plain-text workout rendering."""

from __future__ import annotations

from wod.bot.formatters.dataclasses import FormattedWorkout
from wod.bot.locales import get_text


def workout_to_text(lang: str, workout: FormattedWorkout) -> str:
    """Render a workout as a plain-text string.

    Example output::

        ══════════════════════════════
          Upper Body — Day 1
          📅 2025-06-15 14:30
        ══════════════════════════════

        #  Esercizio               Serie × Reps   Note
        ── ─────────────────────── ────────────── ─────
        1  Barbell Bench Press       4 × 10
        2  Dumbbell Row              4 × 10       Slow
        3  Bicep Curl                3 × 12
        ══════════════════════════════
    """
    sep = "═" * 34
    date_str = workout.date.strftime("%Y-%m-%d %H:%M")

    lines = [
        sep,
        f"  {workout.title}",
        f"  📅 {date_str}",
        sep,
        "",
        (
            f"{'#':<3} {get_text(lang, 'txt_col_ex'):<25} "
            f"{get_text(lang, 'txt_col_set_reps'):<15} "
            f"{get_text(lang, 'txt_col_int'):<20} {get_text(lang, 'txt_col_notes')}"
        ),
        f"{'──':<3} {'─' * 25:<25} {'─' * 14:<15} {'─' * 19:<20} {'─' * 5}",
    ]

    current_day = None
    for ex in workout.exercises:
        if ex.day_label and ex.day_label != current_day:
            lines.append(f"\n--- {ex.day_label} ---")
            current_day = ex.day_label
        note = ex.notes or ""
        lines.append(
            f"{ex.order:<3} {ex.name:<25} {ex.sets:>3} × {ex.reps:<10} "
            f"{ex.intensity:<20} {note}"
        )

    lines.append(sep)
    return "\n".join(lines)
