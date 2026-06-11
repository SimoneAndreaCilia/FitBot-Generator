"""User ORM model."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.models.base import Base

if TYPE_CHECKING:
    from wod.db.models.equipment import Equipment
    from wod.db.models.session import WorkoutSession
    from wod.db.models.workout import FavoriteWorkout, GeneratedWorkout


class User(Base):
    """A Telegram user with training preferences and owned equipment."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Telegram user ID",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Telegram @username (may be absent)",
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="User's display name",
    )
    height_cm: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Height in centimeters",
    )
    weight_kg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Weight in kilograms",
    )
    body_type: Mapped[Optional[BodyType]] = mapped_column(
        Enum(BodyType, name="body_type_enum"),
        nullable=True,
        comment="ectomorph / mesomorph / endomorph",
    )
    experience_level: Mapped[Optional[ExperienceLevel]] = mapped_column(
        Enum(ExperienceLevel, name="experience_level_enum"),
        nullable=True,
        comment="beginner / intermediate / advanced",
    )
    training_frequency: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Training sessions per week (1-7)",
    )
    preferred_split: Mapped[Optional[SplitType]] = mapped_column(
        Enum(SplitType, name="split_type_enum"),
        nullable=True,
        comment="Preferred weekly split strategy",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    # Relationships
    equipment: Mapped[List["Equipment"]] = relationship(
        "Equipment",
        secondary="user_equipment",
        back_populates="users",
        lazy="selectin",
    )
    workouts: Mapped[List["GeneratedWorkout"]] = relationship(
        "GeneratedWorkout",
        back_populates="user",
        lazy="selectin",
        order_by="GeneratedWorkout.created_at.desc()",
    )
    favorites: Mapped[List["FavoriteWorkout"]] = relationship(
        "FavoriteWorkout",
        back_populates="user",
        lazy="selectin",
    )
    sessions: Mapped[List["WorkoutSession"]] = relationship(
        "WorkoutSession",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"level={self.experience_level})>"
        )
