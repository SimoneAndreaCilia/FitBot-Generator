"""Workout formatters — render a workout to text and PDF."""

from __future__ import annotations

import io
import datetime
from dataclasses import dataclass
from typing import Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


@dataclass
class FormattedExercise:
    """Data needed to render a single exercise line."""

    order: int
    name: str
    sets: int
    reps: int
    notes: Optional[str] = None


@dataclass
class FormattedWorkout:
    """Data needed to render a complete workout card."""

    title: str
    date: datetime.datetime
    exercises: list[FormattedExercise]


def workout_to_text(workout: FormattedWorkout) -> str:
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
        f"{'#':<3} {'Esercizio':<25} {'Serie × Reps':<15} {'Note'}",
        f"{'──':<3} {'─' * 25:<25} {'─' * 14:<15} {'─' * 5}",
    ]

    for ex in workout.exercises:
        note = ex.notes or ""
        lines.append(
            f"{ex.order:<3} {ex.name:<25} {ex.sets:>3} × {ex.reps:<10} {note}"
        )

    lines.append(sep)
    return "\n".join(lines)


def workout_to_pdf(workout: FormattedWorkout) -> bytes:
    """Render a workout as a PDF document and return the bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "WorkoutTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    subtitle_style = ParagraphStyle(
        "WorkoutDate",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20,
    )

    elements: list[Any] = []

    # Title
    elements.append(Paragraph(workout.title, title_style))
    date_str = workout.date.strftime("%d/%m/%Y — %H:%M")
    elements.append(Paragraph(f"📅 {date_str}", subtitle_style))
    elements.append(Spacer(1, 12))

    # Table
    table_data = [["#", "Esercizio", "Serie", "Reps", "Note"]]
    for ex in workout.exercises:
        table_data.append(
            [str(ex.order), ex.name, str(ex.sets), str(ex.reps), ex.notes or ""]
        )

    table = Table(table_data, colWidths=[1.2 * cm, 7 * cm, 2 * cm, 2 * cm, 4 * cm])
    alt_colors = [
        colors.white,
        colors.HexColor("#f0f0f0"),
    ]
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), alt_colors),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (3, -1), "CENTER"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
