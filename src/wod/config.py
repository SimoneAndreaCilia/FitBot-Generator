"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings.

    Values are loaded from environment variables or a `.env` file located
    at the project root. The ``TELEGRAM_BOT_TOKEN`` variable is the only
    **required** setting — all others have sensible defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = Field(
        ...,
        description="Bot token obtained from @BotFather",
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///wod.db",
        description="Async SQLAlchemy database URL",
    )

    # App behaviour
    default_training_frequency: int = Field(
        default=3,
        ge=1,
        le=7,
        description="Default training days per week for new users",
    )
    max_history_items: int = Field(
        default=10,
        ge=1,
        description="Maximum number of workouts shown in /history",
    )


def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()  # type: ignore[call-arg]
