"""Tests for the inline keyboard builders."""

from __future__ import annotations

from telegram import InlineKeyboardMarkup

from wod.bot.keyboards import (
    bmi_continue_keyboard,
    body_type_keyboard,
    edit_field_keyboard,
    equipment_keyboard,
    experience_keyboard,
    frequency_keyboard,
    history_keyboard,
    profile_keyboard,
    regenerate_keyboard,
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
                assert isinstance(btn.callback_data, str)
                assert btn.callback_data.startswith("exp:")


class TestFrequencyKeyboard:
    def test_has_six_options(self) -> None:
        kb = frequency_keyboard()
        assert len(kb.inline_keyboard) == 6

    def test_callback_data_prefixed(self) -> None:
        kb = frequency_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert isinstance(btn.callback_data, str)
                assert btn.callback_data.startswith("freq:")


class TestSplitKeyboard:
    def test_has_three_options(self) -> None:
        kb = split_keyboard()
        assert len(kb.inline_keyboard) == 3

    def test_callback_data_prefixed(self) -> None:
        kb = split_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert isinstance(btn.callback_data, str)
                assert btn.callback_data.startswith("split:")

    def test_one_day_only_full_body(self) -> None:
        kb = split_keyboard(frequency=1)
        assert len(kb.inline_keyboard) == 1
        assert kb.inline_keyboard[0][0].callback_data == "split:full_body"

    def test_two_days_full_body_and_upper_lower(self) -> None:
        kb = split_keyboard(frequency=2)
        assert len(kb.inline_keyboard) == 2
        values = {row[0].callback_data for row in kb.inline_keyboard}
        assert values == {"split:full_body", "split:upper_lower"}

    def test_three_plus_days_all_splits(self) -> None:
        for freq in (3, 4, 5, 6):
            kb = split_keyboard(frequency=freq)
            assert len(kb.inline_keyboard) == 3


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

    def test_select_all_button_when_not_all_selected(self) -> None:
        items = [(1, "barbell"), (2, "dumbbell")]
        kb = equipment_keyboard(items, {1})
        # The third button (index 2) is "Seleziona tutti"
        select_all_btn = kb.inline_keyboard[2][0]
        assert "seleziona tutti" in select_all_btn.text.lower()
        assert select_all_btn.callback_data == "equip:all"

    def test_deselect_all_button_when_all_selected(self) -> None:
        items = [(1, "barbell"), (2, "dumbbell")]
        kb = equipment_keyboard(items, {1, 2})
        # The third button (index 2) is "Deseleziona tutti"
        deselect_all_btn = kb.inline_keyboard[2][0]
        assert "deseleziona tutti" in deselect_all_btn.text.lower()
        assert deselect_all_btn.callback_data == "equip:none"


class TestWorkoutActionsKeyboard:
    def test_favorite_button_add(self) -> None:
        kb = workout_actions_keyboard(1, is_favorite=False)
        # Row 0: Favorite
        fav_btn = kb.inline_keyboard[0][0]
        assert "preferiti" in fav_btn.text.lower()
        assert fav_btn.callback_data == "fav:1"

    def test_favorite_button_remove(self) -> None:
        kb = workout_actions_keyboard(1, is_favorite=True)
        fav_btn = kb.inline_keyboard[0][0]
        assert "rimuovi" in fav_btn.text.lower()

    def test_download_buttons(self) -> None:
        kb = workout_actions_keyboard(42, is_favorite=False)
        # Row 1: Downloads
        download_row = kb.inline_keyboard[1]
        assert len(download_row) == 2
        assert download_row[0].callback_data == "dl_pdf:42"
        assert download_row[1].callback_data == "dl_txt:42"


class TestHistoryKeyboard:
    def test_one_item(self) -> None:
        workouts: list[tuple[int, str, str, bool]] = [
            (1, "Upper Body", "15/06/2025", False)
        ]
        kb = history_keyboard(workouts)
        assert len(kb.inline_keyboard) == 1
        assert kb.inline_keyboard[0][0].callback_data == "view:1"

    def test_favorite_star(self) -> None:
        workouts: list[tuple[int, str, str, bool]] = [
            (1, "Upper Body", "15/06/2025", True)
        ]
        kb = history_keyboard(workouts)
        assert "⭐" in kb.inline_keyboard[0][0].text

    def test_no_star_for_non_fav(self) -> None:
        workouts: list[tuple[int, str, str, bool]] = [
            (1, "Upper Body", "15/06/2025", False)
        ]
        kb = history_keyboard(workouts)
        assert "⭐" not in kb.inline_keyboard[0][0].text

    def test_long_label_truncated(self) -> None:
        long_title = "A" * 100
        workouts: list[tuple[int, str, str, bool]] = [
            (1, long_title, "15/06/2025", False)
        ]
        kb = history_keyboard(workouts)
        label = kb.inline_keyboard[0][0].text
        assert len(label) <= 64

    def test_empty_list(self) -> None:
        kb = history_keyboard([])
        assert len(kb.inline_keyboard) == 0


class TestBodyTypeKeyboard:
    def test_returns_markup(self) -> None:
        kb = body_type_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_three_options(self) -> None:
        kb = body_type_keyboard()
        assert len(kb.inline_keyboard) == 3

    def test_callback_data_prefixed(self) -> None:
        kb = body_type_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert isinstance(btn.callback_data, str)
                assert btn.callback_data.startswith("body:")

    def test_callback_values(self) -> None:
        kb = body_type_keyboard()
        values = {row[0].callback_data for row in kb.inline_keyboard}
        assert values == {"body:ectomorph", "body:mesomorph", "body:endomorph"}


class TestBmiContinueKeyboard:
    def test_returns_markup(self) -> None:
        kb = bmi_continue_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_one_button(self) -> None:
        kb = bmi_continue_keyboard()
        assert len(kb.inline_keyboard) == 1

    def test_callback_data(self) -> None:
        kb = bmi_continue_keyboard()
        assert kb.inline_keyboard[0][0].callback_data == "bmi:continue"


class TestProfileKeyboard:
    def test_returns_markup(self) -> None:
        kb = profile_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_edit_button(self) -> None:
        kb = profile_keyboard()
        assert len(kb.inline_keyboard) == 1
        assert kb.inline_keyboard[0][0].callback_data == "edit_profile"


class TestEditFieldKeyboard:
    def test_returns_markup(self) -> None:
        kb = edit_field_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_nine_options(self) -> None:
        """8 editable fields + 1 cancel button."""
        kb = edit_field_keyboard()
        assert len(kb.inline_keyboard) == 9

    def test_callback_data_prefixed(self) -> None:
        kb = edit_field_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert isinstance(btn.callback_data, str)
                assert btn.callback_data.startswith("editf:")

    def test_cancel_button_present(self) -> None:
        kb = edit_field_keyboard()
        last_btn = kb.inline_keyboard[-1][0]
        assert last_btn.callback_data == "editf:cancel"


class TestRegenerateKeyboard:
    def test_returns_markup(self) -> None:
        kb = regenerate_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_two_options(self) -> None:
        kb = regenerate_keyboard()
        assert len(kb.inline_keyboard) == 2

    def test_callback_values(self) -> None:
        kb = regenerate_keyboard()
        values = {row[0].callback_data for row in kb.inline_keyboard}
        assert values == {"regen:yes", "regen:no"}
