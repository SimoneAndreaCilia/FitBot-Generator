"""Tests for the database seeding module."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from wod.db.models import Equipment, Exercise
from wod.db.seeding import auto_seed_if_empty, locate_seed_file, seed_database
from wod.db.session import get_engine, get_session_factory, reset_engine


class TestSeeding:
    """Tests for the database seeding and auto-seeding logic."""

    def setup_method(self) -> None:
        """Reset engine and bind to an in-memory database before each test."""
        reset_engine()
        get_engine("sqlite+aiosqlite:///:memory:")
        get_session_factory("sqlite+aiosqlite:///:memory:")

    def teardown_method(self) -> None:
        """Reset the global database engine after each test."""
        reset_engine()

    def test_locate_seed_file(self) -> None:
        """Verify that the seed JSON file is correctly located on the filesystem."""
        path = locate_seed_file()
        assert path.exists()
        assert path.name == "seed_exercises.json"

    @pytest.mark.asyncio
    async def test_seed_database(self) -> None:
        """Verify that seed_database creates tables and populates data."""
        await seed_database()

        async with get_session_factory()() as session:
            eq_res = await session.execute(select(Equipment))
            eqs = eq_res.scalars().all()
            assert len(eqs) > 0

            ex_res = await session.execute(select(Exercise))
            exs = ex_res.scalars().all()
            assert len(exs) > 0

    @pytest.mark.asyncio
    async def test_auto_seed_if_empty(self) -> None:
        """Verify that auto_seed_if_empty seeds only when the database is empty."""
        # 1. First run: Empty database -> should seed
        await auto_seed_if_empty()

        async with get_session_factory()() as session:
            ex_res = await session.execute(select(Exercise))
            first_count = len(ex_res.scalars().all())
            assert first_count > 0

        # 2. Second run: Already seeded -> should skip
        await auto_seed_if_empty()

        async with get_session_factory()() as session:
            ex_res = await session.execute(select(Exercise))
            second_count = len(ex_res.scalars().all())
            assert second_count == first_count
