"""Inline keyboard builders for the Telegram Bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
