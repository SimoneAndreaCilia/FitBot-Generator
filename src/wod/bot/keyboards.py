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

from wod.bot.locales import get_text

# ---------------------------------------------------------------------------
# Reply keyboards (persistent buttons below the message bar)
# ---------------------------------------------------------------------------


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Build the compact 3-button main menu (always visible)."""
    buttons = [
        [
            KeyboardButton(get_text(lang, "btn_new_workout")),
            KeyboardButton(get_text(lang, "btn_other")),
            KeyboardButton(get_text(lang, "btn_profile")),
        ],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def expanded_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Build the expanded 5-button menu shown after pressing 'Altro'."""
    buttons = [
        [
            KeyboardButton(get_text(lang, "btn_new_workout")),
            KeyboardButton(get_text(lang, "btn_history")),
            KeyboardButton(get_text(lang, "btn_favorites")),
        ],
        [
            KeyboardButton(get_text(lang, "btn_profile")),
            KeyboardButton(get_text(lang, "btn_wod")),
            KeyboardButton(get_text(lang, "btn_language")),
        ],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


# ---------------------------------------------------------------------------
# "Creati una scheda" choice keyboard
# ---------------------------------------------------------------------------


def crea_scheda_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard to choose between existing profile or new onboarding."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_use_existing"), callback_data="crea:existing"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_create_new"), callback_data="crea:new"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# WOD day navigation keyboard
# ---------------------------------------------------------------------------


def wod_day_navigation_keyboard(
    lang: str, day_index: int, total_days: int, workout_id: int
) -> InlineKeyboardMarkup:
    """Build navigation buttons for browsing workout days."""
    buttons = []
    nav_row = []

    if day_index > 0:
        nav_row.append(
            InlineKeyboardButton(
                get_text(lang, "btn_back"), callback_data=f"wodday:{day_index - 1}"
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            get_text(lang, "btn_day_nav", current=day_index + 1, total=total_days),
            callback_data="wodday:noop",
        )
    )

    if day_index < total_days - 1:
        nav_row.append(
            InlineKeyboardButton(
                get_text(lang, "btn_forward"), callback_data=f"wodday:{day_index + 1}"
            )
        )

    buttons.append(
        [
            InlineKeyboardButton(
                get_text(lang, "btn_start_workout"),
                callback_data=f"startw:{workout_id}:{day_index}",
            )
        ]
    )

    if len(nav_row) > 1:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Onboarding keyboards
# ---------------------------------------------------------------------------


def experience_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard for selecting experience level."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_exp_beginner"), callback_data="exp:beginner"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_exp_intermediate"), callback_data="exp:intermediate"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_exp_advanced"), callback_data="exp:advanced"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def frequency_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard for selecting training frequency (days per week)."""
    buttons = []
    for i in range(1, 7):
        buttons.append(
            [
                InlineKeyboardButton(
                    get_text(lang, "btn_freq_days", days=i),
                    callback_data=f"freq:{i}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons)


def split_keyboard(lang: str, frequency: int | None = None) -> InlineKeyboardMarkup:
    """Build a keyboard for selecting the training split."""
    all_splits = [
        (get_text(lang, "btn_split_full"), "split:full_body", 1),
        (get_text(lang, "btn_split_upper"), "split:upper_lower", 2),
        (get_text(lang, "btn_split_ppl"), "split:push_pull_legs", 3),
    ]
    buttons = [
        [InlineKeyboardButton(label, callback_data=cb)]
        for label, cb, min_days in all_splits
        if frequency is None or frequency >= min_days
    ]
    return InlineKeyboardMarkup(buttons)


def equipment_keyboard(
    lang: str,
    equipment_list: list[tuple[int, str]],
    selected_ids: set[int],
) -> InlineKeyboardMarkup:
    """Build a toggleable keyboard for equipment selection."""
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
                    get_text(lang, "btn_equip_deselect"),
                    callback_data="equip:none",
                )
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    get_text(lang, "btn_equip_select"),
                    callback_data="equip:all",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                get_text(lang, "btn_equip_done"),
                callback_data="equip:done",
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def body_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard for selecting body type (somatotype)."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_body_ecto"), callback_data="body:ectomorph"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_body_meso"), callback_data="body:mesomorph"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_body_endo"), callback_data="body:endomorph"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def bmi_continue_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard with a 'Continue' button after BMI display."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_bmi_continue"), callback_data="bmi:continue"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def profile_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard with the 'Edit profile' button."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_profile"), callback_data="edit_profile"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def edit_field_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard for selecting which profile field to edit."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_name"), callback_data="editf:name"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_height"), callback_data="editf:height"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_weight"), callback_data="editf:weight"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_body"), callback_data="editf:body_type"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_exp"), callback_data="editf:experience"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_freq"), callback_data="editf:frequency"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_split"), callback_data="editf:split"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_edit_equip"), callback_data="editf:equipment"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_cancel"), callback_data="editf:cancel"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def regenerate_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard to offer workout regeneration."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_regen_yes"), callback_data="regen:yes"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_regen_no"), callback_data="regen:no"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Workout keyboards
# ---------------------------------------------------------------------------


def workout_actions_keyboard(
    lang: str,
    workout_id: int,
    is_favorite: bool,
) -> InlineKeyboardMarkup:
    """Actions available for a generated workout."""
    fav_text = (
        get_text(lang, "btn_remove_fav")
        if is_favorite
        else get_text(lang, "btn_add_fav")
    )
    buttons = [
        [InlineKeyboardButton(fav_text, callback_data=f"fav:{workout_id}")],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_dl_pdf"),
                callback_data=f"dl_pdf:{workout_id}",
            ),
            InlineKeyboardButton(
                get_text(lang, "btn_dl_txt"),
                callback_data=f"dl_txt:{workout_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def history_keyboard(
    lang: str,  # pylint: disable=unused-argument
    workouts: list[tuple[int, str, str, bool]],
) -> InlineKeyboardMarkup:
    """Build a keyboard for workout history."""
    buttons = []
    for wid, title, date_str, is_fav in workouts:
        star = "⭐" if is_fav else ""
        label = f"{star} {date_str} — {title}"
        if len(label) > 64:
            label = label[:61] + "..."
        buttons.append([InlineKeyboardButton(label, callback_data=f"view:{wid}")])
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Live workout session keyboards
# ---------------------------------------------------------------------------


def select_day_keyboard(lang: str, days: list[str]) -> InlineKeyboardMarkup:
    """Keyboard to select which day to train."""
    buttons = []
    for day in days:
        buttons.append(
            [
                InlineKeyboardButton(
                    get_text(lang, "btn_sel_day", day=day),
                    callback_data=f"selday:{day}",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                get_text(lang, "btn_cancel"), callback_data="selday:cancel"
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def live_set_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard shown during a live set to allow skipping or aborting."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_skip_set"), callback_data="liveset:skip"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(lang, "btn_abort_workout"), callback_data="liveset:abort"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def rest_timer_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard shown during rest timer."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_skip_rest"), callback_data="liverest:skip"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def end_workout_keyboard(lang: str, session_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown when a workout is completed."""
    buttons = [
        [
            InlineKeyboardButton(
                get_text(lang, "btn_dl_summary"), callback_data=f"dl_sum:{session_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)
