"""Constants for the profile editing conversation."""

from wod.core.types import BodyType, ExperienceLevel, SplitType

# ---------------------------------------------------------------------------
# Edit conversation states
# ---------------------------------------------------------------------------

(
    CHOOSE_FIELD,
    EDIT_NAME,
    EDIT_HEIGHT,
    EDIT_WEIGHT,
    EDIT_BODY_TYPE,
    EDIT_EXPERIENCE,
    EDIT_FREQUENCY,
    EDIT_SPLIT,
    EDIT_EQUIPMENT,
    REGEN_CONFIRM,
) = range(10)

# Body type display labels
BODY_TYPE_LABELS = {
    BodyType.ECTOMORPH: "Ectomorfo",
    BodyType.MESOMORPH: "Mesomorfo",
    BodyType.ENDOMORPH: "Endomorfo",
}

# Experience level display labels
EXPERIENCE_LABELS = {
    ExperienceLevel.BEGINNER: "Principiante",
    ExperienceLevel.INTERMEDIATE: "Intermedio",
    ExperienceLevel.ADVANCED: "Avanzato",
}

# Split type display labels
SPLIT_LABELS = {
    SplitType.FULL_BODY: "Full Body",
    SplitType.UPPER_LOWER: "Upper/Lower",
    SplitType.PUSH_PULL_LEGS: "Push/Pull/Legs",
}
