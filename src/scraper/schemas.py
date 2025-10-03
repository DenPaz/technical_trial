from datetime import datetime
from typing import List

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from pydantic import field_validator


class Candidate(BaseModel):
    """
    A single tweet/video candidate discovered by the scraper.
    """

    tweet_url: HttpUrl
    video_urls: List[HttpUrl] = Field(default_factory=list)
    text: str
    author: str
    created_at: datetime
    like_count: int
    retweet_count: int

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, value):
        """
        Custom validator to parse Twitter's specific datetime format.
        """
        if isinstance(value, str):
            return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
        return value


class ScoredCandidate(BaseModel):
    """
    A candidate with an attached text relevance score.
    """

    candidate: Candidate
    text_score: float = Field(..., ge=0, le=1)


class ClipFinding(BaseModel):
    """
    A single suggested clip segment from a video that matches the description.
    """

    start_time_s: float = Field(..., ge=0)
    end_time_s: float = Field(..., gt=0)
    confidence: float = Field(..., ge=0, le=1)
    reason: str


class VisionResult(BaseModel):
    """
    Model for the structured output returned by vision analysis.
    """

    tweet_url: HttpUrl
    best_video_url: HttpUrl
    findings: List[ClipFinding] = Field(default_factory=list)


class FinalAlternate(BaseModel):
    """
    An alternate clip suggestion for the final JSON output.
    """

    start_time_s: float
    end_time_s: float
    confidence: float


class FinalTrace(BaseModel):
    """
    Trace section to measure pipeline behavior.
    """

    candidates_considered: int = 0
    filtered_by_text: int = 0
    vision_calls: int = 0
    final_choice_rank: int = 0


class FinalResult(BaseModel):
    """
    Final output shape for the clip suggestion.
    """

    tweet_url: HttpUrl
    video_url: HttpUrl
    start_time_s: float
    end_time_s: float
    confidence: float
    reason: str
    alternates: List[FinalAlternate] = Field(default_factory=list)
    trace: FinalTrace = Field(default_factory=FinalTrace)


__all__ = [
    "Candidate",
    "ScoredCandidate",
    "ClipFinding",
    "VisionResult",
    "FinalAlternate",
    "FinalTrace",
    "FinalResult",
]
