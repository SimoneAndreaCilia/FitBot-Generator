"""Seed the database with exercises and equipment from JSON data."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wod.db.models import Base, Equipment, Exercise
from wod.db.session import get_engine, get_session_factory


SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed_exercises.json"


async def seed_database() -> None:
    """Load seed data into the database, skipping duplicates."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with open(SEED_FILE, encoding="utf-8") as f:
        data = json.load(f)

    async with get_session_factory()() as session:
        # Seed equipment
        eq_map: dict[str, Equipment] = {}
        for eq_name in data["equipment"]:
            eq = await _get_or_create_equipment(session, eq_name)
            eq_map[eq_name] = eq

        # Seed exercises
        for ex_data in data["exercises"]:
            await _get_or_create_exercise(session, ex_data, eq_map)

        await session.commit()

    print(
        f"[OK] Seeded {len(data['equipment'])} equipment items "
        f"and {len(data['exercises'])} exercises."
    )


async def _get_or_create_equipment(
    session: AsyncSession, name: str
) -> Equipment:
    """Fetch or create an equipment entry."""
    stmt = select(Equipment).where(Equipment.name == name)
    result = await session.execute(stmt)
    eq = result.scalar_one_or_none()
    if eq is None:
        eq = Equipment(name=name)
        session.add(eq)
        await session.flush()
    return eq


async def _get_or_create_exercise(
    session: AsyncSession,
    ex_data: dict,
    eq_map: dict[str, Equipment],
) -> Exercise:
    """Fetch or create an exercise entry with its equipment links."""
    stmt = select(Exercise).where(Exercise.name == ex_data["name"])
    result = await session.execute(stmt)
    ex = result.scalar_one_or_none()
    if ex is None:
        ex = Exercise(
            name=ex_data["name"],
            muscle_group=ex_data["muscle_group"],
            effort_type=ex_data["effort_type"],
            weight=ex_data.get("weight", 1),
            tier=ex_data.get("tier", "C"),
            description=ex_data.get("description", ""),
            equipment=[eq_map[eq_name] for eq_name in ex_data.get("equipment", [])],
        )
        session.add(ex)
        await session.flush()
    return ex


if __name__ == "__main__":
    asyncio.run(seed_database())