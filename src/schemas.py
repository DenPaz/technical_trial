from datetime import datetime

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from pydantic import field_validator


class Candidate(BaseModel):
    """
    Represents a single tweet that has been identified by the scraper as a
    potential match. This is the initial, unprocessed data object that enters
    the pipeline.
    """

    tweet_url: HttpUrl = Field(
        ...,
        description="The URL of the tweet.",
    )
    video_urls: list[HttpUrl] = Field(
        default_factory=list,
        description="A list of all video stream URLs found in the tweet.",
    )
    best_video_url: HttpUrl | None = Field(
        default=None,
        description="The URL of the highest quality video stream, if available.",
    )
    text: str = Field(
        ...,
        description="The full text content of the tweet.",
    )
    author: str = Field(
        ...,
        description="The screen name of the tweet's author.",
    )
    created_at: datetime = Field(
        ...,
        description="The date and time when the tweet was created.",
    )

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, value: str) -> datetime:
        """
        Parses the created_at string from Twitter into a datetime object.
        """
        if isinstance(value, datetime):
            return value
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")


class ClipFindings(BaseModel):
    """
    Represents a single continuous clip identified by the vision analyzer
    within a candidate video. A single video can yield multiple findings.
    """

    start_time_s: float = Field(
        ...,
        ge=0,
        description="The start time of the clip in seconds.",
    )
    end_time_s: float = Field(
        ...,
        ge=0,
        description="The end time of the clip in seconds.",
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description=(
            "The AI's confidence that this clip matches the description (0.0 to 1.0)."
        ),
    )
    reason: str = Field(
        ...,
        description="A brief justification for the confidence score.",
    )


class VisionResult(BaseModel):
    """
    Contains all the findings (clips) from a single video analysis. This is the
    structured output from the vision analyzer node.
    """

    tweet_url: HttpUrl
    best_video_url: HttpUrl
    findings: list[ClipFindings] = Field(
        default_factory=list,
        description="A list of all relevant clips found within the video.",
    )


class FinalAlternate(BaseModel):
    """
    A simplified schema for alternate clip suggestions in the final output.
    """

    start_time_s: float
    end_time_s: float
    confidence: float


class FinalTrace(BaseModel):
    """
    Contains metadata about the pipeline's execution for a single run,
    providing traceability and insight into the filtering process.
    """

    candidates_considered: int = 0
    filtered_by_text: int = 0
    vision_calls: int = 0
    final_choice_rank: int = 0


class FinalResult(BaseModel):
    """
    The final, comprehensive output object of the entire pipeline, formatted
    as specified in the technical trial requirements.
    """

    tweet_url: HttpUrl
    video_url: HttpUrl
    start_time_s: float
    end_time_s: float
    confidence: float
    reason: str
    alternates: list[FinalAlternate] = Field(default_factory=list)
    trace: FinalTrace = Field(default_factory=FinalTrace)


__all__ = [
    "Candidate",
    "ClipFindings",
    "FinalAlternate",
    "FinalResult",
    "FinalTrace",
    "VisionResult",
]
