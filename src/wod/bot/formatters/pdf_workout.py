"""PDF rendering for workout cards."""

from __future__ import annotations

import io
from collections import OrderedDict
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from wod.bot.formatters.dataclasses import FormattedExercise, FormattedWorkout
from wod.bot.formatters.pdf_common import (
    BASE_TABLE_STYLE,
    BORDER,
    DARK_NAVY,
    TEXT_DARK,
    TEXT_MUTED,
    build_profile_section,
)


def _group_exercises_by_day(
    exercises: list[FormattedExercise],
) -> OrderedDict[str, list[FormattedExercise]]:
    """Group exercises by their day_label, preserving insertion order.

    Exercises without a ``day_label`` are grouped under a single key.
    """
    groups: OrderedDict[str, list[FormattedExercise]] = OrderedDict()
    for ex in exercises:
        key = ex.day_label or "__single__"
        groups.setdefault(key, []).append(ex)
    return groups


def _build_session_table(
    session_label: Optional[str],
    exercises: list[FormattedExercise],
    styles: Any,
) -> list[Any]:
    """Build PDF elements for one training session (heading + table)."""
    elements: list[Any] = []
    page_width = A4[0] - 4 * cm

    # Session heading (skip if there is only one unnamed session)
    if session_label is not None:
        heading_style = ParagraphStyle(
            f"Session_{session_label}",
            parent=styles["Heading3"],
            fontSize=12,
            textColor=DARK_NAVY,
            spaceBefore=14,
            spaceAfter=6,
        )
        elements.append(Paragraph(f"🏋️ {session_label}", heading_style))

    # Table header + data rows
    header = ["#", "Esercizio", "Serie", "Reps", "Intensità", "Note"]
    table_data: list[list[str]] = [header]
    note_style = ParagraphStyle(
        "NoteStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=TEXT_DARK,
    )

    for ex in exercises:
        notes_text = ex.notes or ""
        if ex.actual_data:
            if notes_text:
                notes_text += "<br/><br/>"
            notes_text += "<b>Dati reali:</b><br/>" + "<br/>".join(ex.actual_data)

        notes_element = Paragraph(notes_text, note_style) if notes_text else ""

        table_data.append(
            [
                str(ex.order),
                ex.name,
                str(ex.sets),
                ex.reps,
                ex.intensity or "",
                notes_element,
            ]
        )

    col_widths = [
        1.0 * cm,  # #
        5.5 * cm,  # Esercizio
        1.5 * cm,  # Serie
        1.8 * cm,  # Reps
        3.0 * cm,  # Intensità
        page_width - 12.8 * cm,  # Note (remaining)
    ]

    table = Table(table_data, colWidths=col_widths)
    style_commands: list[tuple[Any, ...]] = [
        *BASE_TABLE_STYLE,
        ("ALIGN", (0, 0), (0, -1), "CENTER"),  # #
        ("ALIGN", (2, 0), (4, -1), "CENTER"),  # Serie, Reps, Intensità
    ]

    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    elements.append(Spacer(1, 10))
    return elements


def workout_to_pdf(workout: FormattedWorkout) -> bytes:
    """Render a workout as a PDF document and return the bytes.

    The PDF includes:
    * Workout title and date header
    * User profile summary (if provided)
    * One table per training session / day, clearly separated
    * Footer note
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "WorkoutTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=4,
        textColor=TEXT_DARK,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "WorkoutDate",
        parent=styles["Normal"],
        fontSize=11,
        textColor=TEXT_MUTED,
        spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=1,  # center
    )

    elements: list[Any] = []

    # ── Title & date ────────────────────────────────────────────
    elements.append(Paragraph(workout.title, title_style))
    date_str = workout.date.strftime("%d/%m/%Y — %H:%M")
    elements.append(Paragraph(f"📅  {date_str}", subtitle_style))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=BORDER,
            spaceBefore=4,
            spaceAfter=12,
        )
    )

    # ── User profile ────────────────────────────────────────────
    if workout.user_profile is not None:
        elements.extend(build_profile_section(workout.user_profile, styles))

    # ── Exercise tables (one per session/day) ───────────────────
    grouped = _group_exercises_by_day(workout.exercises)

    if len(grouped) == 1 and "__single__" in grouped:
        # No day labels → single table without session heading
        elements.extend(_build_session_table(None, grouped["__single__"], styles))
    else:
        for day_label, day_exercises in grouped.items():
            elements.extend(_build_session_table(day_label, day_exercises, styles))

    # ── Footer ──────────────────────────────────────────────────
    elements.append(Spacer(1, 20))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#dddddd"),
            spaceBefore=0,
            spaceAfter=6,
        )
    )
    elements.append(
        Paragraph(
            "Generato con WOD Bot — Il tuo personal trainer digitale 💪",
            footer_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
