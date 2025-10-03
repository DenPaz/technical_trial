from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Project base directory
BASE_DIR = Path(__file__).parent.parent.parent


class AppSettings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    TWITTER_USERNAME: str = Field(
        ...,
        description="Twitter/X username for login.",
    )
    TWITTER_PASSWORD: str = Field(
        ...,
        description="Twitter/X password for login.",
    )
    TWITTER_EMAIL: str | None = Field(
        None,
        description="Twitter/X email (sometimes required for login).",
    )
    GOOGLE_API_KEY: str = Field(
        ...,
        description="API key for Google Gemini.",
    )
    GEMINI_MODEL: str = Field(
        "gemini-2.5-flash",
        description="Google Gemini model to use for analysis.",
    )
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = AppSettings()
