"""Keyboard builders for the Telegram Bot.

Includes both InlineKeyboardMarkup (buttons attached to messages) and
ReplyKeyboardMarkup (persistent buttons below the message bar).
"""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ---------------------------------------------------------------------------
# Menu button text constants (used for matching in handlers)
# ---------------------------------------------------------------------------

BTN_CREA_SCHEDA = "🏋️Nuova scheda"
BTN_ALTRO = "Altro"
BTN_PROFILO = "👤 Profilo"
BTN_STORICO = "📜 Storico"
BTN_PREFERITI = "⭐ Preferiti"
BTN_WOD = "🔥 WOD del giorno"


# ---------------------------------------------------------------------------
# Reply keyboards (persistent buttons below the message bar)
# ---------------------------------------------------------------------------


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the compact 3-button main menu (always visible)."""
    buttons = [
        [
            KeyboardButton(BTN_CREA_SCHEDA),
            KeyboardButton(BTN_ALTRO),
            KeyboardButton(BTN_PROFILO),
        ],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def expanded_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the expanded 5-button menu shown after pressing 'Altro'."""
    buttons = [
        [
            KeyboardButton(BTN_CREA_SCHEDA),
            KeyboardButton(BTN_STORICO),
            KeyboardButton(BTN_PREFERITI),
        ],
        [
            KeyboardButton(BTN_PROFILO),
            KeyboardButton(BTN_WOD),
        ],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


# ---------------------------------------------------------------------------
# "Creati una scheda" choice keyboard
# ---------------------------------------------------------------------------


def crea_scheda_choice_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard to choose between existing profile or new onboarding."""
    buttons = [
        [
            InlineKeyboardButton(
                "📋 Usa profilo esistente", callback_data="crea:existing"
            )
        ],
        [InlineKeyboardButton("🆕 Crea nuovo profilo", callback_data="crea:new")],
    ]
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# WOD day navigation keyboard
# ---------------------------------------------------------------------------


def wod_day_navigation_keyboard(
    day_index: int, total_days: int
) -> InlineKeyboardMarkup:
    """Build navigation buttons for browsing workout days.

    Args:
        day_index: Current day index (0-based).
        total_days: Total number of training days.
    """
    buttons = []
    nav_row = []

    if day_index > 0:
        nav_row.append(
            InlineKeyboardButton("◀️ Indietro", callback_data=f"wodday:{day_index - 1}")
        )

    nav_row.append(
        InlineKeyboardButton(
            f"📅 {day_index + 1}/{total_days}", callback_data="wodday:noop"
        )
    )

    if day_index < total_days - 1:
        nav_row.append(
            InlineKeyboardButton("Avanti ▶️", callback_data=f"wodday:{day_index + 1}")
        )

    buttons.append(nav_row)
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Onboarding keyboards
# ---------------------------------------------------------------------------


def experience_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for selecting experience level."""
    buttons = [
        [InlineKeyboardButton("🟢 Principiante", callback_data="exp:beginner")],
        [InlineKeyboardButton("🟡 Intermedio", callback_data="exp:intermediate")],
        [InlineKeyboardButton("🔴 Avanzato", callback_data="exp:advanced")],
    ]
    return InlineKeyboardMarkup(buttons)


def frequency_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for selecting training frequency (days per week)."""
    buttons = []
    for i in range(1, 7):
        emoji = "📅"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{emoji} {i} giorni/settimana",
                    callback_data=f"freq:{i}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons)


def split_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for selecting the training split."""
    buttons = [
        [InlineKeyboardButton("💪 Full Body", callback_data="split:full_body")],
        [InlineKeyboardButton("⬆️⬇️ Upper/Lower", callback_data="split:upper_lower")],
        [
            InlineKeyboardButton(
                "🔄 Push/Pull/Legs", callback_data="split:push_pull_legs"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def equipment_keyboard(
    equipment_list: list[tuple[int, str]],
    selected_ids: set[int],
) -> InlineKeyboardMarkup:
    """Build a toggleable keyboard for equipment selection.

    Args:
        equipment_list: List of (id, name) tuples for all equipment.
        selected_ids: IDs already selected by the user.
    """
    emoji_map = {
        "barbell": "🏋️",
        "dumbbell": "🦾",
        "kettlebell": "💣",
        "pull_up_bar": "🪜",
        "bench": "🛋️",
        "resistance_band": "〰️",
        "bodyweight": "🤸",
    }

    buttons = []
    for eq_id, eq_name in equipment_list:
        check = "✅" if eq_id in selected_ids else "⬜"
        emoji = emoji_map.get(eq_name, "🔧")
        display_name = eq_name.replace("_", " ").title()
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{check} {emoji} {display_name}",
                    callback_data=f"equip:{eq_id}",
                )
            ]
        )
    all_selected = len(equipment_list) > 0 and all(
        eq_id in selected_ids for eq_id, _ in equipment_list
    )
    if all_selected:
        buttons.append(
            [
                InlineKeyboardButton(
                    "❌ Deseleziona tutti",
                    callback_data="equip:none",
                )
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    "☑️ Seleziona tutti",
                    callback_data="equip:all",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                "✅ Conferma selezione",
                callback_data="equip:done",
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def body_type_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for selecting body type (somatotype)."""
    buttons = [
        [InlineKeyboardButton("🦴 Ectomorfo", callback_data="body:ectomorph")],
        [InlineKeyboardButton("💪 Mesomorfo", callback_data="body:mesomorph")],
        [InlineKeyboardButton("🐻 Endomorfo", callback_data="body:endomorph")],
    ]
    return InlineKeyboardMarkup(buttons)


def bmi_continue_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard with a 'Continue' button after BMI display."""
    buttons = [
        [InlineKeyboardButton("Avanti ➡️", callback_data="bmi:continue")],
    ]
    return InlineKeyboardMarkup(buttons)


def profile_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard with the 'Edit profile' button."""
    buttons = [
        [InlineKeyboardButton("✏️ Modifica profilo", callback_data="edit_profile")],
    ]
    return InlineKeyboardMarkup(buttons)


def edit_field_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for selecting which profile field to edit."""
    buttons = [
        [InlineKeyboardButton("📛 Nome", callback_data="editf:name")],
        [InlineKeyboardButton("📏 Altezza", callback_data="editf:height")],
        [InlineKeyboardButton("⚖️ Peso", callback_data="editf:weight")],
        [InlineKeyboardButton("🦴 Corporatura", callback_data="editf:body_type")],
        [InlineKeyboardButton("📊 Livello", callback_data="editf:experience")],
        [InlineKeyboardButton("📅 Frequenza", callback_data="editf:frequency")],
        [InlineKeyboardButton("🔀 Split", callback_data="editf:split")],
        [InlineKeyboardButton("🔧 Attrezzatura", callback_data="editf:equipment")],
        [InlineKeyboardButton("❌ Annulla", callback_data="editf:cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def regenerate_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard to offer workout regeneration."""
    buttons = [
        [InlineKeyboardButton("🔄 Rigenera scheda", callback_data="regen:yes")],
        [InlineKeyboardButton("❌ No, grazie", callback_data="regen:no")],
    ]
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Workout keyboards
# ---------------------------------------------------------------------------


def workout_actions_keyboard(
    workout_id: int,
    is_favorite: bool,
) -> InlineKeyboardMarkup:
    """Actions available for a generated workout."""
    fav_text = "💔 Rimuovi dai preferiti" if is_favorite else "⭐ Aggiungi ai preferiti"
    buttons = [
        [InlineKeyboardButton(fav_text, callback_data=f"fav:{workout_id}")],
        [
            InlineKeyboardButton(
                "📕 Scarica .pdf",
                callback_data=f"dl_pdf:{workout_id}",
            ),
            InlineKeyboardButton(
                "📄 Scarica .txt",
                callback_data=f"dl_txt:{workout_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def history_keyboard(
    workouts: list[tuple[int, str, str, bool]],
) -> InlineKeyboardMarkup:
    """Build a keyboard for workout history.

    Args:
        workouts: List of (id, title, date_str, is_favorite) tuples.
    """
    buttons = []
    for wid, title, date_str, is_fav in workouts:
        star = "⭐" if is_fav else ""
        label = f"{star} {date_str} — {title}"
        # Truncate label to 64 chars (Telegram limit)
        if len(label) > 64:
            label = label[:61] + "..."
        buttons.append([InlineKeyboardButton(label, callback_data=f"view:{wid}")])
    return InlineKeyboardMarkup(buttons)
