"""Generated workout, workout exercise, and favorite workout ORM models."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wod.db.models.base import Base

if TYPE_CHECKING:
    from wod.db.models.exercise import Exercise
    from wod.db.models.session import WorkoutSession
    from wod.db.models.user import User


class GeneratedWorkout(Base):
    """A workout card generated for a user."""

    __tablename__ = "generated_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Human-readable workout title (e.g. 'Upper Body — Day 1')",
    )
    content_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full workout data serialized as JSON",
    )
    content_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Plain-text version for quick display / .txt export",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workouts",
    )
    exercises: Mapped[List["WorkoutExercise"]] = relationship(
        "WorkoutExercise",
        back_populates="workout",
        lazy="selectin",
        order_by="WorkoutExercise.order_index",
        cascade="all, delete-orphan",
    )
    favorite: Mapped[Optional["FavoriteWorkout"]] = relationship(
        "FavoriteWorkout",
        back_populates="workout",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sessions: Mapped[List["WorkoutSession"]] = relationship(
        "WorkoutSession",
        back_populates="workout",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<GeneratedWorkout(id={self.id}, user_id={self.user_id}, "
            f"title={self.title!r})>"
        )


class WorkoutExercise(Base):
    """A single exercise entry within a generated workout."""

    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("generated_workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to catalogue; SET NULL if exercise is deleted",
    )
    day_label: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Label of the training day this exercise belongs to",
    )
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[str] = mapped_column(String(16), nullable=False)
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position of this exercise in the workout sequence",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="Optional coaching cue or tempo annotation",
    )

    # Relationships
    workout: Mapped["GeneratedWorkout"] = relationship(
        "GeneratedWorkout",
        back_populates="exercises",
    )
    exercise: Mapped[Optional["Exercise"]] = relationship(
        "Exercise",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkoutExercise(workout_id={self.workout_id}, "
            f"exercise_id={self.exercise_id}, "
            f"{self.sets}x{self.reps})>"
        )


class FavoriteWorkout(Base):
    """A user's bookmarked workout — prevents accidental loss."""

    __tablename__ = "favorite_workouts"
    __table_args__ = (
        UniqueConstraint("user_id", "workout_id", name="uq_user_workout_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("generated_workouts.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="favorites",
    )
    workout: Mapped["GeneratedWorkout"] = relationship(
        "GeneratedWorkout",
        back_populates="favorite",
    )

    def __repr__(self) -> str:
        return (
            f"<FavoriteWorkout(user_id={self.user_id}, "
            f"workout_id={self.workout_id})>"
        )
