"""Workout formatters — render a workout to text and PDF."""

from __future__ import annotations

import datetime
import io
from collections import OrderedDict
from dataclasses import dataclass, field
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


@dataclass
class FormattedExercise:
    """Data needed to render a single exercise line."""

    order: int
    name: str
    sets: int
    reps: str
    intensity: str = ""
    notes: Optional[str] = None
    day_label: Optional[str] = None
    actual_data: list[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """User profile data for rendering in PDF header."""

    name: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_type: Optional[str] = None
    experience_level: Optional[str] = None
    training_frequency: Optional[int] = None
    preferred_split: Optional[str] = None
    equipment: list[str] = field(default_factory=list)


@dataclass
class SessionLogRow:
    """Data needed to render a single performed set in the summary PDF."""

    order: int
    exercise_name: str
    set_number: int
    kg: str
    reps: str
    rest: str
    intensity: str
    skipped: bool


@dataclass
class SessionSummary:
    """Data needed to render a complete session summary PDF."""

    title: str
    date: datetime.datetime
    rows: list[SessionLogRow]
    user_profile: Optional[UserProfile] = None


@dataclass
class FormattedWorkout:
    """Data needed to render a complete workout card."""

    title: str
    date: datetime.datetime
    exercises: list[FormattedExercise]
    user_profile: Optional[UserProfile] = None


# ---------------------------------------------------------------------------
# Colour palette (reused across PDF elements)
# ---------------------------------------------------------------------------
_DARK_NAVY = colors.HexColor("#16213e")
_ACCENT_BLUE = colors.HexColor("#0f3460")
_LIGHT_BG = colors.HexColor("#f8f9fa")
_ALT_ROW = colors.HexColor("#eef1f6")
_BORDER = colors.HexColor("#c8cdd3")
_TEXT_DARK = colors.HexColor("#1a1a2e")
_TEXT_MUTED = colors.HexColor("#555555")
_SESSION_BG = colors.HexColor("#e8ecf1")


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
        f"{'#':<3} {'Esercizio':<25} {'Serie × Reps':<15} {'Intensità':<20} {'Note'}",
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


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

_LABEL_MAP: dict[str, str] = {
    "beginner": "Principiante",
    "intermediate": "Intermedio",
    "advanced": "Avanzato",
    "ectomorph": "Ectomorfo",
    "mesomorph": "Mesomorfo",
    "endomorph": "Endomorfo",
    "full_body": "Full Body",
    "upper_lower": "Upper / Lower",
    "push_pull_legs": "Push / Pull / Legs",
}


def _human_label(value: Optional[str]) -> str:
    """Translate an enum value to its Italian human-readable label."""
    if value is None:
        return "—"
    return _LABEL_MAP.get(value, value.replace("_", " ").title())


def _build_profile_section(
    profile: UserProfile,
    styles: Any,
) -> list[Any]:
    """Build PDF elements for the user profile info box."""
    elements: list[Any] = []

    section_title = ParagraphStyle(
        "ProfileTitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=_DARK_NAVY,
        spaceAfter=8,
        spaceBefore=0,
    )
    elements.append(Paragraph("👤 Profilo Atleta", section_title))

    # Build profile data as a 2-column key/value table
    info_rows: list[list[str]] = []
    if profile.name:
        info_rows.append(["Nome", profile.name])
    if profile.height_cm is not None:
        info_rows.append(["Altezza", f"{profile.height_cm:.0f} cm"])
    if profile.weight_kg is not None:
        info_rows.append(["Peso", f"{profile.weight_kg:.1f} kg"])
    if profile.body_type:
        info_rows.append(["Somatotipo", _human_label(profile.body_type)])
    if profile.experience_level:
        info_rows.append(["Livello", _human_label(profile.experience_level)])
    if profile.training_frequency is not None:
        info_rows.append(
            ["Frequenza", f"{profile.training_frequency}x / settimana"]
        )
    if profile.preferred_split:
        info_rows.append(["Split", _human_label(profile.preferred_split)])
    if profile.equipment:
        info_rows.append(["Attrezzatura", ", ".join(profile.equipment)])

    if not info_rows:
        return elements

    # Render as a clean 2-column table
    page_width = A4[0] - 4 * cm  # account for margins
    table = Table(
        info_rows,
        colWidths=[4 * cm, page_width - 4 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), _ACCENT_BLUE),
                ("TEXTCOLOR", (1, 0), (1, -1), _TEXT_DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, _BORDER),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 16))
    return elements


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
            textColor=_DARK_NAVY,
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
        textColor=_TEXT_DARK,
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
        1.0 * cm,   # #
        5.5 * cm,   # Esercizio
        1.5 * cm,   # Serie
        1.8 * cm,   # Reps
        3.0 * cm,   # Intensità
        page_width - 12.8 * cm,  # Note (remaining)
    ]

    table = Table(table_data, colWidths=col_widths)
    style_commands: list[tuple[Any, ...]] = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), _DARK_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Alternating row colours
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
        # Grid & alignment
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),   # #
        ("ALIGN", (2, 0), (4, -1), "CENTER"),    # Serie, Reps, Intensità
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    elements.append(Spacer(1, 10))
    return elements


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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
        textColor=_TEXT_DARK,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "WorkoutDate",
        parent=styles["Normal"],
        fontSize=11,
        textColor=_TEXT_MUTED,
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
            color=_BORDER,
            spaceBefore=4,
            spaceAfter=12,
        )
    )

    # ── User profile ────────────────────────────────────────────
    if workout.user_profile is not None:
        elements.extend(_build_profile_section(workout.user_profile, styles))

    # ── Exercise tables (one per session/day) ───────────────────
    grouped = _group_exercises_by_day(workout.exercises)

    if len(grouped) == 1 and "__single__" in grouped:
        # No day labels → single table without session heading
        elements.extend(
            _build_session_table(None, grouped["__single__"], styles)
        )
    else:
        for day_label, day_exercises in grouped.items():
            elements.extend(
                _build_session_table(day_label, day_exercises, styles)
            )

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


def _build_session_log_table(
    rows: list[SessionLogRow],
    styles: Any,
) -> list[Any]:
    """Build PDF elements for a performed session log table."""
    elements: list[Any] = []
    page_width = A4[0] - 4 * cm

    header = ["Esercizio", "Serie", "Kg", "Ripetizioni", "Recupero", "Intensità (CT)"]
    table_data: list[list[str]] = [header]

    for row in rows:
        if row.skipped:
            table_data.append([
                row.exercise_name,
                str(row.set_number),
                "-",
                "Saltata",
                "-",
                "-",
            ])
        else:
            table_data.append([
                row.exercise_name,
                str(row.set_number),
                row.kg,
                row.reps,
                row.rest,
                row.intensity,
            ])

    col_widths = [
        6.0 * cm,   # Esercizio
        1.5 * cm,   # Serie
        1.5 * cm,   # Kg
        2.5 * cm,   # Ripetizioni
        2.5 * cm,   # Recupero
        page_width - 14.0 * cm,  # Intensità
    ]

    table = Table(table_data, colWidths=col_widths)
    style_commands: list[tuple[Any, ...]] = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), _DARK_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Alternating row colours
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
        # Grid & alignment
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),  # Center align data cols
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    elements.append(Spacer(1, 10))
    return elements


def session_summary_to_pdf(summary: SessionSummary) -> bytes:
    """Generate a PDF document from a SessionSummary.

    Args:
        summary: The structured data representing a completed workout session.

    Returns:
        The generated PDF as a byte string.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "WorkoutTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=_DARK_NAVY,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "WorkoutSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=_TEXT_MUTED,
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

    # Title & date
    elements.append(Paragraph(summary.title, title_style))
    date_str = summary.date.strftime("%d/%m/%Y — %H:%M")
    elements.append(Paragraph(f"📅 Riepilogo Sessione — {date_str}", subtitle_style))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=_BORDER,
            spaceBefore=4,
            spaceAfter=12,
        )
    )

    # User profile
    if summary.user_profile is not None:
        elements.extend(_build_profile_section(summary.user_profile, styles))

    # The log table
    if summary.rows:
        elements.extend(_build_session_log_table(summary.rows, styles))
    else:
        elements.append(Paragraph("Nessun dato registrato per questa sessione.", subtitle_style))

    # Footer
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
