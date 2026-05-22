"""Tests for the inline keyboard builders."""

from __future__ import annotations

from telegram import InlineKeyboardMarkup

from wod.bot.keyboards import (
    equipment_keyboard,
    experience_keyboard,
    frequency_keyboard,
    history_keyboard,
    split_keyboard,
    workout_actions_keyboard,
)


class TestExperienceKeyboard:
    def test_returns_markup(self) -> None:
        kb = experience_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_three_options(self) -> None:
        kb = experience_keyboard()
        assert len(kb.inline_keyboard) == 3

    def test_callback_data_prefixed(self) -> None:
        kb = experience_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.callback_data.startswith("exp:")


class TestFrequencyKeyboard:
    def test_has_six_options(self) -> None:
        kb = frequency_keyboard()
        assert len(kb.inline_keyboard) == 6

    def test_callback_data_prefixed(self) -> None:
        kb = frequency_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.callback_data.startswith("freq:")


class TestSplitKeyboard:
    def test_has_three_options(self) -> None:
        kb = split_keyboard()
        assert len(kb.inline_keyboard) == 3

    def test_callback_data_prefixed(self) -> None:
        kb = split_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.callback_data.startswith("split:")


class TestEquipmentKeyboard:
    def test_shows_all_items_plus_confirm(self) -> None:
        items = [(1, "barbell"), (2, "dumbbell")]
        kb = equipment_keyboard(items, set())
        # 2 items + 1 select all + 1 confirm button
        assert len(kb.inline_keyboard) == 4

    def test_selected_items_show_checkmark(self) -> None:
        items = [(1, "barbell"), (2, "dumbbell")]
        kb = equipment_keyboard(items, {1})
        first_btn_text = kb.inline_keyboard[0][0].text
        assert "✅" in first_btn_text

    def test_unselected_items_show_empty(self) -> None:
        items = [(1, "barbell"), (2, "dumbbell")]
        kb = equipment_keyboard(items, {1})
        second_btn_text = kb.inline_keyboard[1][0].text
        assert "⬜" in second_btn_text

    def test_confirm_button_callback(self) -> None:
        items = [(1, "barbell")]
        kb = equipment_keyboard(items, set())
        confirm_btn = kb.inline_keyboard[-1][0]
        assert confirm_btn.callback_data == "equip:done"

    def test_empty_equipment_list(self) -> None:
        kb = equipment_keyboard([], set())
        # Select all + confirm button
        assert len(kb.inline_keyboard) == 2


class TestWorkoutActionsKeyboard:
    def test_favorite_button_add(self) -> None:
        kb = workout_actions_keyboard(1, is_favorite=False)
        fav_btn = kb.inline_keyboard[0][0]
        assert "preferiti" in fav_btn.text.lower()
        assert fav_btn.callback_data == "fav:1"

    def test_favorite_button_remove(self) -> None:
        kb = workout_actions_keyboard(1, is_favorite=True)
        fav_btn = kb.inline_keyboard[0][0]
        assert "rimuovi" in fav_btn.text.lower()

    def test_download_buttons(self) -> None:
        kb = workout_actions_keyboard(42, is_favorite=False)
        download_row = kb.inline_keyboard[1]
        assert len(download_row) == 1
        assert download_row[0].callback_data == "dl_pdf:42"


class TestHistoryKeyboard:
    def test_one_item(self) -> None:
        workouts = [(1, "Upper Body", "15/06/2025", False)]
        kb = history_keyboard(workouts)
        assert len(kb.inline_keyboard) == 1
        assert kb.inline_keyboard[0][0].callback_data == "view:1"

    def test_favorite_star(self) -> None:
        workouts = [(1, "Upper Body", "15/06/2025", True)]
        kb = history_keyboard(workouts)
        assert "⭐" in kb.inline_keyboard[0][0].text

    def test_no_star_for_non_fav(self) -> None:
        workouts = [(1, "Upper Body", "15/06/2025", False)]
        kb = history_keyboard(workouts)
        assert "⭐" not in kb.inline_keyboard[0][0].text

    def test_long_label_truncated(self) -> None:
        long_title = "A" * 100
        workouts = [(1, long_title, "15/06/2025", False)]
        kb = history_keyboard(workouts)
        label = kb.inline_keyboard[0][0].text
        assert len(label) <= 64

    def test_empty_list(self) -> None:
        kb = history_keyboard([])
        assert len(kb.inline_keyboard) == 0
