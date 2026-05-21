"""SQLAlchemy async engine and session factory.

Uses lazy initialization so that importing this module does **not**
require environment variables to be set (important for testing and
static analysis).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_ENGINE: Optional[AsyncEngine] = None
_SESSION_FACTORY: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine(database_url: Optional[str] = None) -> AsyncEngine:
    """Return the global async engine, creating it on first call.

    Args:
        database_url: Override the URL from settings (useful in tests).
    """
    global _ENGINE  # noqa: PLW0603  # pylint: disable=global-statement
    if _ENGINE is None:
        if database_url is None:
            # pylint: disable=import-outside-toplevel
            from wod.config import get_settings

            database_url = get_settings().database_url
        _ENGINE = create_async_engine(database_url, echo=False, future=True)
    return _ENGINE


def get_session_factory(
    database_url: Optional[str] = None,
) -> async_sessionmaker[AsyncSession]:
    """Return the global session factory, creating it on first call."""
    global _SESSION_FACTORY  # noqa: PLW0603  # pylint: disable=global-statement
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = async_sessionmaker(
            get_engine(database_url),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _SESSION_FACTORY


async def get_session() -> AsyncSession:
    """Yield an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        return session


def reset_engine() -> None:
    """Reset the engine and session factory (for testing)."""
    # pylint: disable=global-statement
    global _ENGINE, _SESSION_FACTORY
    _ENGINE = None
    _SESSION_FACTORY = None