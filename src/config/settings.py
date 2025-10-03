from functools import lru_cache
from pathlib import Path

from pydantic import EmailStr
from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class AppSettings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    twitter_username: str = Field(..., env="TWITTER_USERNAME")
    twitter_email: EmailStr = Field(..., env="TWITTER_EMAIL")
    twitter_password: SecretStr = Field(..., env="TWITTER_PASSWORD")
    gemini_api_key: SecretStr = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.5-flash", env="GEMINI_MODEL")
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Get cached application settings.
    """
    return AppSettings()


settings = get_settings()
