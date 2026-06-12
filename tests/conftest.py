"""Shared pytest fixtures for the WOD test suite."""

# pylint: disable=redefined-outer-name

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from wod.core.types import EffortType, ExperienceLevel, MuscleGroup, SplitType
from wod.db.models import Base, Equipment, Exercise, User


@pytest.fixture()
async def async_engine() -> Any:
    """Create a disposable in-memory SQLite engine for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Enable foreign-key enforcement for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(  # type: ignore[no-untyped-def]
        dbapi_connection,
        _connection_record,
    ):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(async_engine: Any) -> Any:
    """Yield an async session bound to the in-memory database."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture()
def sample_equipment() -> list[Equipment]:
    """Return a set of common equipment objects (not yet persisted)."""
    return [
        Equipment(name="barbell"),
        Equipment(name="dumbbell"),
        Equipment(name="pull_up_bar"),
        Equipment(name="bench"),
        Equipment(name="kettlebell"),
        Equipment(name="bodyweight"),
    ]


@pytest.fixture()
def sample_exercises(sample_equipment: list[Equipment]) -> list[Exercise]:
    """Return sample exercises linked to equipment (not yet persisted)."""
    barbell, dumbbell, pull_up_bar, bench, _kb, bodyweight = sample_equipment
    return [
        Exercise(
            name="Barbell Bench Press",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
            description="Flat barbell bench press",
            equipment=[barbell, bench],
        ),
        Exercise(
            name="Dumbbell Row",
            muscle_group=MuscleGroup.BACK,
            effort_type=EffortType.COMPOUND,
            description="Single-arm dumbbell row",
            equipment=[dumbbell, bench],
        ),
        Exercise(
            name="Pull-Up",
            muscle_group=MuscleGroup.BACK,
            effort_type=EffortType.COMPOUND,
            description="Bodyweight pull-up",
            equipment=[pull_up_bar],
        ),
        Exercise(
            name="Push-Up",
            muscle_group=MuscleGroup.CHEST,
            effort_type=EffortType.COMPOUND,
            description="Bodyweight push-up",
            equipment=[bodyweight],
        ),
        Exercise(
            name="Bodyweight Squat",
            muscle_group=MuscleGroup.QUADS,
            effort_type=EffortType.COMPOUND,
            description="Air squat",
            equipment=[bodyweight],
        ),
        Exercise(
            name="Overhead Press",
            muscle_group=MuscleGroup.SHOULDERS,
            effort_type=EffortType.COMPOUND,
            description="Standing barbell overhead press",
            equipment=[barbell],
        ),
        Exercise(
            name="Bicep Curl",
            muscle_group=MuscleGroup.BICEPS,
            effort_type=EffortType.ISOLATION,
            description="Standing dumbbell bicep curl",
            equipment=[dumbbell],
        ),
        Exercise(
            name="Plank",
            muscle_group=MuscleGroup.CORE,
            effort_type=EffortType.ISOLATION,
            description="Front plank hold",
            equipment=[bodyweight],
        ),
    ]


@pytest.fixture()
def sample_user() -> User:
    """Return a sample user (not yet persisted)."""
    return User(
        telegram_id=123456789,
        username="test_user",
        experience_level=ExperienceLevel.INTERMEDIATE,
        training_frequency=4,
        preferred_split=SplitType.UPPER_LOWER,
    )
