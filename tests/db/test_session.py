"""Tests for the database session module."""

from __future__ import annotations

import os
from unittest.mock import patch

from wod.db.session import get_engine, get_session_factory, reset_engine


class TestSessionFactory:
    """Tests for the lazy session/engine initialization."""

    def setup_method(self) -> None:
        """Reset globals before each test."""
        reset_engine()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_engine()

    def test_get_engine_with_explicit_url(self) -> None:
        engine = get_engine("sqlite+aiosqlite:///:memory:")
        assert engine is not None
        assert "memory" in str(engine.url)

    def test_get_engine_returns_same_instance(self) -> None:
        e1 = get_engine("sqlite+aiosqlite:///:memory:")
        e2 = get_engine("sqlite+aiosqlite:///:memory:")
        assert e1 is e2

    def test_get_session_factory_returns_callable(self) -> None:
        factory = get_session_factory("sqlite+aiosqlite:///:memory:")
        assert callable(factory)

    def test_get_session_factory_returns_same_instance(self) -> None:
        f1 = get_session_factory("sqlite+aiosqlite:///:memory:")
        f2 = get_session_factory("sqlite+aiosqlite:///:memory:")
        assert f1 is f2

    def test_reset_clears_engine(self) -> None:
        e1 = get_engine("sqlite+aiosqlite:///:memory:")
        reset_engine()
        e2 = get_engine("sqlite+aiosqlite:///:memory:")
        assert e1 is not e2

    def test_get_engine_from_settings(self) -> None:
        """When no URL is provided, engine should use settings."""
        env = {
            "TELEGRAM_BOT_TOKEN": "tok",
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        }
        with patch.dict(os.environ, env, clear=True):
            engine = get_engine()
            assert engine is not None
