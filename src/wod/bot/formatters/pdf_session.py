"""PDF rendering for session summaries."""

from __future__ import annotations

import io
from typing import Any

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

from wod.bot.formatters.dataclasses import SessionLogRow, SessionSummary
from wod.bot.formatters.pdf_common import (
    BASE_TABLE_STYLE,
    BORDER,
    DARK_NAVY,
    TEXT_MUTED,
    build_profile_section,
)
from wod.bot.locales import get_text


def _build_session_log_table(
    lang: str,
    rows: list[SessionLogRow],
    _styles: Any,
) -> list[Any]:
    """Build PDF elements for a performed session log table."""
    elements: list[Any] = []
    page_width = A4[0] - 4 * cm

    header = [
        get_text(lang, "pdf_sess_col_ex"),
        get_text(lang, "pdf_sess_col_set"),
        get_text(lang, "pdf_sess_col_kg"),
        get_text(lang, "pdf_sess_col_reps"),
        get_text(lang, "pdf_sess_col_rest"),
        get_text(lang, "pdf_sess_col_int"),
    ]
    table_data: list[list[str]] = [header]

    for row in rows:
        if row.skipped:
            table_data.append(
                [
                    row.exercise_name,
                    str(row.set_number),
                    "-",
                    get_text(lang, "pdf_sess_skipped"),
                    "-",
                    "-",
                ]
            )
        else:
            table_data.append(
                [
                    row.exercise_name,
                    str(row.set_number),
                    row.kg,
                    row.reps,
                    row.rest,
                    row.intensity,
                ]
            )

    col_widths = [
        6.0 * cm,  # Esercizio
        1.5 * cm,  # Serie
        1.5 * cm,  # Kg
        2.5 * cm,  # Ripetizioni
        2.5 * cm,  # Recupero
        page_width - 14.0 * cm,  # Intensità
    ]

    table = Table(table_data, colWidths=col_widths)
    style_commands: list[tuple[Any, ...]] = [
        *BASE_TABLE_STYLE,
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),  # Center align data cols
    ]

    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    elements.append(Spacer(1, 10))
    return elements


def session_summary_to_pdf(lang: str, summary: SessionSummary) -> bytes:
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
        textColor=DARK_NAVY,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "WorkoutSubtitle",
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

    # Title & date
    elements.append(Paragraph(summary.title, title_style))
    date_str = summary.date.strftime("%d/%m/%Y — %H:%M")
    elements.append(
        Paragraph(get_text(lang, "pdf_sess_title", date=date_str), subtitle_style)
    )
    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=BORDER,
            spaceBefore=4,
            spaceAfter=12,
        )
    )

    # User profile
    if summary.user_profile is not None:
        elements.extend(build_profile_section(lang, summary.user_profile, styles))

    # The log table
    if summary.rows:
        elements.extend(_build_session_log_table(lang, summary.rows, styles))
    else:
        elements.append(Paragraph(get_text(lang, "pdf_sess_empty"), subtitle_style))

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
            get_text(lang, "pdf_footer"),
            footer_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
