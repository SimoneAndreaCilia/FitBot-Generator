"""SQLAlchemy ORM models for the WOD application.

This module defines the complete data model:

* **User** — Telegram user profile with training preferences.
* **Equipment** — Available gym equipment items.
* **Exercise** — Catalogue of exercises with muscle-group and effort-type metadata.
* **GeneratedWorkout** — A saved workout card tied to a user.
* **WorkoutExercise** — Individual exercise entry within a generated workout.
* **FavoriteWorkout** — User-bookmarked workouts.

Association tables handle the many-to-many relationships between
exercises ↔ equipment and users ↔ equipment.
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from wod.core.types import BodyType, EffortType, ExperienceLevel, MuscleGroup, SplitType

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Association tables (many-to-many)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Generated workouts
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Live Workout Sessions
# ---------------------------------------------------------------------------


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
