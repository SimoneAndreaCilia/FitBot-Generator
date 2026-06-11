"""Live workout session ORM models."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wod.db.models.base import Base

if TYPE_CHECKING:
    from wod.db.models.user import User
    from wod.db.models.workout import GeneratedWorkout, WorkoutExercise


class WorkoutSession(Base):
    """A live workout session — tracks when a user performs a workout."""

    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("generated_workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="in_progress",
        nullable=False,
        comment="'in_progress', 'completed', or 'abandoned'",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    workout: Mapped["GeneratedWorkout"] = relationship(
        "GeneratedWorkout", back_populates="sessions"
    )
    logs: Mapped[List["SetLog"]] = relationship(
        "SetLog",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SetLog.logged_at",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkoutSession(id={self.id}, user_id={self.user_id}, "
            f"status={self.status!r})>"
        )


class SetLog(Base):
    """A single set performed by the user during a workout session."""

    __tablename__ = "set_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    set_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="1-indexed set number",
    )
    weight_kg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    reps_done: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    skipped: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    logged_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )

    # Relationships
    session: Mapped["WorkoutSession"] = relationship(
        "WorkoutSession", back_populates="logs"
    )
    workout_exercise: Mapped["WorkoutExercise"] = relationship("WorkoutExercise")

    def __repr__(self) -> str:
        return (
            f"<SetLog(session_id={self.session_id}, set={self.set_number}, "
            f"skipped={self.skipped})>"
        )
