"""Data classes used across workout formatters."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FormattedExercise:  # pylint: disable=too-many-instance-attributes
    """Data needed to render a single exercise line."""

    order: int
    name: str
    sets: int
    reps: str
    intensity: str = ""
    notes: Optional[str] = None
    day_label: Optional[str] = None
    actual_data: list[str] = field(default_factory=list)


@dataclass
class UserProfile:  # pylint: disable=too-many-instance-attributes
    """User profile data for rendering in PDF header."""

    name: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_type: Optional[str] = None
    experience_level: Optional[str] = None
    training_frequency: Optional[int] = None
    preferred_split: Optional[str] = None
    equipment: list[str] = field(default_factory=list)


@dataclass
class SessionLogRow:  # pylint: disable=too-many-instance-attributes
    """Data needed to render a single performed set in the summary PDF."""

    order: int
    exercise_name: str
    set_number: int
    kg: str
    reps: str
    rest: str
    intensity: str
    skipped: bool


@dataclass
class SessionSummary:
    """Data needed to render a complete session summary PDF."""

    title: str
    date: datetime.datetime
    rows: list[SessionLogRow]
    user_profile: Optional[UserProfile] = None


@dataclass
class FormattedWorkout:
    """Data needed to render a complete workout card."""

    title: str
    date: datetime.datetime
    exercises: list[FormattedExercise]
    user_profile: Optional[UserProfile] = None
