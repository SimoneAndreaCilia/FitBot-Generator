"""Common PDF helpers — palette, label map, and profile section builder."""

from __future__ import annotations

from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from wod.bot.formatters.dataclasses import UserProfile
from wod.bot.locales import get_text

# ---------------------------------------------------------------------------
# Colour palette (reused across PDF elements)
# ---------------------------------------------------------------------------
DARK_NAVY = colors.HexColor("#16213e")
ACCENT_BLUE = colors.HexColor("#0f3460")
LIGHT_BG = colors.HexColor("#f8f9fa")
ALT_ROW = colors.HexColor("#eef1f6")
BORDER = colors.HexColor("#c8cdd3")
TEXT_DARK = colors.HexColor("#1a1a2e")
TEXT_MUTED = colors.HexColor("#555555")
SESSION_BG = colors.HexColor("#e8ecf1")

BASE_TABLE_STYLE: list[tuple[Any, ...]] = [
    # Header row
    ("BACKGROUND", (0, 0), (-1, 0), DARK_NAVY),
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
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_ROW]),
    # Grid & alignment
    ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]


def human_label(lang: str, value: Optional[str]) -> str:
    """Translate an enum value to its localized human-readable label."""
    if value is None:
        return "—"

    # Try to find a specific translation, fallback to formatting the value
    translated = get_text(lang, f"lbl_{value}")
    if translated == f"lbl_{value}":
        return value.replace("_", " ").title()
    return translated


def build_profile_section(
    lang: str,
    profile: UserProfile,
    styles: Any,
) -> list[Any]:
    """Build PDF elements for the user profile info box."""
    elements: list[Any] = []

    section_title = ParagraphStyle(
        "ProfileTitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=DARK_NAVY,
        spaceAfter=8,
        spaceBefore=0,
    )
    elements.append(Paragraph(get_text(lang, "pdf_prof_title"), section_title))

    # Build profile data as a 2-column key/value table
    info_rows: list[list[str]] = []
    if profile.name:
        info_rows.append([get_text(lang, "pdf_prof_name"), profile.name])
    if profile.height_cm is not None:
        info_rows.append(
            [get_text(lang, "pdf_prof_height"), f"{profile.height_cm:.0f} cm"]
        )
    if profile.weight_kg is not None:
        info_rows.append(
            [get_text(lang, "pdf_prof_weight"), f"{profile.weight_kg:.1f} kg"]
        )
    if profile.body_type:
        info_rows.append(
            [get_text(lang, "pdf_prof_body"), human_label(lang, profile.body_type)]
        )
    if profile.experience_level:
        info_rows.append(
            [
                get_text(lang, "pdf_prof_level"),
                human_label(lang, profile.experience_level),
            ]
        )
    if profile.training_frequency is not None:
        info_rows.append(
            [
                get_text(lang, "pdf_prof_freq"),
                get_text(lang, "pdf_prof_freq_val", freq=profile.training_frequency),
            ]
        )
    if profile.preferred_split:
        info_rows.append(
            [
                get_text(lang, "pdf_prof_split"),
                human_label(lang, profile.preferred_split),
            ]
        )
    if profile.equipment:
        info_rows.append(
            [get_text(lang, "pdf_prof_equip"), ", ".join(profile.equipment)]
        )

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
                ("TEXTCOLOR", (0, 0), (0, -1), ACCENT_BLUE),
                ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, BORDER),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 16))
    return elements
