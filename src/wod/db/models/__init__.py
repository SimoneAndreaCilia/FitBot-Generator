"""SQLAlchemy ORM models for the WOD application.

This package defines the complete data model:

* **User** — Telegram user profile with training preferences.
* **Equipment** — Available gym equipment items.
* **Exercise** — Catalogue of exercises with muscle-group and effort-type metadata.
* **GeneratedWorkout** — A saved workout card tied to a user.
* **WorkoutExercise** — Individual exercise entry within a generated workout.
* **FavoriteWorkout** — User-bookmarked workouts.
* **WorkoutSession** — Live workout session tracking.
* **SetLog** — Individual set performed during a session.

Association tables handle the many-to-many relationships between
exercises ↔ equipment and users ↔ equipment.
"""

from wod.db.models.associations import ExerciseEquipment, UserEquipment
from wod.db.models.base import Base
from wod.db.models.equipment import Equipment
from wod.db.models.exercise import Exercise
from wod.db.models.session import SetLog, WorkoutSession
from wod.db.models.user import User
from wod.db.models.workout import FavoriteWorkout, GeneratedWorkout, WorkoutExercise

__all__ = [
    "Base",
    "Equipment",
    "Exercise",
    "ExerciseEquipment",
    "FavoriteWorkout",
    "GeneratedWorkout",
    "SetLog",
    "User",
    "UserEquipment",
    "WorkoutExercise",
    "WorkoutSession",
]
