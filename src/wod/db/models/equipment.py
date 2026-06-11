"""Equipment ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wod.db.models.base import Base

if TYPE_CHECKING:
    from wod.db.models.exercise import Exercise
    from wod.db.models.user import User


class Equipment(Base):
    """A piece of gym equipment (e.g. barbell, bench, pull-up bar)."""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    # Relationships
    exercises: Mapped[List["Exercise"]] = relationship(
        "Exercise",
        secondary="exercise_equipment",
        back_populates="equipment",
        lazy="selectin",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_equipment",
        back_populates="equipment",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Equipment(id={self.id}, name={self.name!r})>"
