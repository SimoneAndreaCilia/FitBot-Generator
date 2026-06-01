"""Tests for config module."""

# pylint: disable=duplicate-code

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from wod.config import Settings


class TestSettings:
    """Tests for the Settings configuration class."""

    def test_requires_telegram_token(self) -> None:
        """Settings should fail without TELEGRAM_BOT_TOKEN."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                Settings(_env_file=None)

    def test_loads_from_env(self) -> None:
        """Settings should load TELEGRAM_BOT_TOKEN from env vars."""
        env = {"TELEGRAM_BOT_TOKEN": "test-token-123"}
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.telegram_bot_token == "test-token-123"

    def test_default_database_url(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "tok"}
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert "sqlite" in s.database_url

    def test_custom_database_url(self) -> None:
        env = {
            "TELEGRAM_BOT_TOKEN": "tok",
            "DATABASE_URL": "postgresql+asyncpg://localhost/wod",
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.database_url == "postgresql+asyncpg://localhost/wod"

    def test_default_training_frequency(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "tok"}
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.default_training_frequency == 3

    def test_default_max_history(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "tok"}
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.max_history_items == 10
