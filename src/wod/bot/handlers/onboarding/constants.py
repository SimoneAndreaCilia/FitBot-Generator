"""Constants for the onboarding conversation."""

from wod.core.types import BodyType

# Conversation states
(
    NAME,
    HEIGHT,
    WEIGHT,
    BODY_TYPE,
    BMI_DISPLAY,
    EXPERIENCE,
    FREQUENCY,
    SPLIT,
    EQUIPMENT,
) = range(9)

# Body type display labels
BODY_TYPE_LABELS = {
    BodyType.ECTOMORPH: "Ectomorfo",
    BodyType.MESOMORPH: "Mesomorfo",
    BodyType.ENDOMORPH: "Endomorfo",
}
