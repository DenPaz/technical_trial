from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl


class Candidate(BaseModel):
    """
    A single tweet/video candidate discovered by the scraper.
    """

    tweet_url: HttpUrl
    canonical_url: Optional[HttpUrl] = None
    video_page_url: Optional[HttpUrl] = None
    best_video_url: Optional[HttpUrl] = None
    video_urls: List[HttpUrl] = Field(default_factory=list)
    text: str
    author: str
    created_at: str
    like_count: int
    retweet_count: int


class ScoredCandidate(BaseModel):
    """
    A candidate with an attached text relevance score.
    """

    candidate: Candidate
    text_score: float


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
    model_name: Optional[str] = None
    raw_notes: Optional[str] = None


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

    candidates_considered: int
    filtered_by_text: int
    vision_calls: int
    final_choice_rank: int


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
    trace: FinalTrace


__all__ = [
    "Candidate",
    "ScoredCandidate",
    "ClipFinding",
    "VisionResult",
    "FinalAlternate",
    "FinalTrace",
    "FinalResult",
]
