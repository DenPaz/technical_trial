from functools import lru_cache
from pathlib import Path

from pydantic import EmailStr
from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Root directory of the project
BASE_DIR = Path(__file__).resolve().parents[2]


class AppSettings(BaseSettings):
    """
    Application settings loaded from environment variables in the .env file.
    """

    twitter_username: str = Field(...)
    twitter_email: EmailStr = Field(...)
    twitter_password: SecretStr = Field(...)

    gemini_api_key: SecretStr = Field(...)
    gemini_model: str = Field("gemini-2.5-flash")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> AppSettings:
    """
    Returns a cached instance of the application settings.
    """
    return AppSettings()


settings = get_settings()
