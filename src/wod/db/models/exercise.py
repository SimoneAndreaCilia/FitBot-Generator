"""Exercise ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wod.core.types import EffortType, MuscleGroup
from wod.db.models.base import Base

if TYPE_CHECKING:
    from wod.db.models.equipment import Equipment


class Exercise(Base):
    """An exercise in the catalogue."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )
    muscle_group: Mapped[MuscleGroup] = mapped_column(
        Enum(MuscleGroup, name="muscle_group_enum"),
        nullable=False,
        index=True,
    )
    effort_type: Mapped[EffortType] = mapped_column(
        Enum(EffortType, name="effort_type_enum"),
        nullable=False,
    )
    weight: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
        comment="1 for primary/compound, 2 for secondary/isolation",
    )
    tier: Mapped[str] = mapped_column(
        String(1),
        default="C",
        server_default="C",
        nullable=False,
        comment="Exercise tier: A, B, or C",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    equipment: Mapped[List["Equipment"]] = relationship(
        "Equipment",
        secondary="exercise_equipment",
        back_populates="exercises",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Exercise(id={self.id}, name={self.name!r}, "
            f"group={self.muscle_group.value})>"
        )
