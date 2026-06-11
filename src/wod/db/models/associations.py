"""Many-to-many association tables."""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from wod.db.models.base import Base


class ExerciseEquipment(Base):
    """Many-to-many: which equipment an exercise requires."""

    __tablename__ = "exercise_equipment"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserEquipment(Base):
    """Many-to-many: which equipment a user owns."""

    __tablename__ = "user_equipment"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        primary_key=True,
    )
