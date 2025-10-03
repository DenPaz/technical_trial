import logging
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


def setup_logging() -> None:
    """
    Configures the logging for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


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
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = AppSettings()


class TweetCandidate(BaseModel):
    """Represents a scrapped tweet that is a candidate for analysis."""

    tweet_id: str
    tweet_url: str
    tweet_text: str
    author_handle: str
    created_at: str
    video_url: Optional[str] = None


class VideoAnalysisResult(BaseModel):
    """Structured output from the Gemini Vision analysis for a single video."""

    tweet_id: str
    is_relevant: bool
    start_time_s: Optional[float] = None
    end_time_s: Optional[float] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None


class FinalResult(BaseModel):
    """The final structured output for the user."""

    tweet_url: str
    video_url: str
    start_time_s: float
    end_time_s: float
    confidence: float
    reason: str
    alternates: List[dict[str, Any]] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
