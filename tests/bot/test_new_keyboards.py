"""Tests for the new inline keyboard builders."""

from __future__ import annotations

from wod.bot.keyboards import (
    crea_scheda_choice_keyboard,
    end_workout_keyboard,
    expanded_menu_keyboard,
    live_set_keyboard,
    main_menu_keyboard,
    rest_timer_keyboard,
    select_day_keyboard,
    wod_day_navigation_keyboard,
)


class TestMainMenuKeyboard:
    def test_has_buttons(self) -> None:
        kb = main_menu_keyboard()
        assert len(kb.keyboard) > 0


class TestExpandedMenuKeyboard:
    def test_has_buttons(self) -> None:
        kb = expanded_menu_keyboard()
        assert len(kb.keyboard) > 0


class TestCreaSchedaChoiceKeyboard:
    def test_has_buttons(self) -> None:
        kb = crea_scheda_choice_keyboard()
        assert len(kb.inline_keyboard) > 0


class TestWodDayNavigationKeyboard:
    def test_has_nav_buttons(self) -> None:
        kb = wod_day_navigation_keyboard(1, 3, 100)
        assert len(kb.inline_keyboard) > 0


class TestLiveWorkoutSessionKeyboard:
    def test_has_buttons(self) -> None:
        kb = live_set_keyboard()
        assert len(kb.inline_keyboard) > 0

    def test_select_day(self) -> None:
        kb = select_day_keyboard(["Day 1", "Day 2"])
        assert len(kb.inline_keyboard) > 0

    def test_rest_timer(self) -> None:
        kb = rest_timer_keyboard()
        assert len(kb.inline_keyboard) > 0

    def test_end_workout(self) -> None:
        kb = end_workout_keyboard(1)
        assert len(kb.inline_keyboard) > 0
