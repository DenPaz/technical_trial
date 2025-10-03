import logging
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl

from src.config.settings import settings
from src.scraper.schemas import Candidate

logger = logging.getLogger(__name__)


class ScoredCandidateResult(BaseModel):
    tweet_url: HttpUrl = Field(
        ...,
        description="The URL of the tweet being scored.",
    )
    score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance score from 0.0 (irrelevant) to 1.0 (highly relevant).",
    )
    reason: str = Field(
        ...,
        description="Brief explanation for the assigned score.",
    )


class TextFilterResults(BaseModel):
    results: List[ScoredCandidateResult]


async def filter_candidates_by_text(
    candidates: List[Candidate],
    description: str,
    score_threshold: float = 0.5,
) -> List[Candidate]:
    if not candidates:
        return []
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        api_key=settings.GOOGLE_API_KEY,
    )
    structured_llm = llm.with_structured_output(TextFilterResults)
    candidate_texts = [{"url": str(c.tweet_url), "text": c.text} for c in candidates]
    prompt = f"""
    You are an intelligent filter for social media content.
    A user is looking for a video described as: "{description}"

    I have found the following tweets. Your task is to evaluate how relevant the TEXT of each tweet is to the user's description. A high score means the text suggests the video is a great match.

    Evaluate each of the following candidates:
    {candidate_texts}

    Provide a relevance score from 0.0 to 1.0 for each tweet. A score of 1.0 means the text is a perfect match for the description. A score of 0.0 means it's completely irrelevant. Also provide a brief reason for your score.
    """

    logger.info(f"Sending {len(candidates)} candidates to LLM for text analysis...")

    try:
        response = await structured_llm.ainvoke(prompt)
        score_map = {str(res.tweet_url): res.score for res in response.results}
        filtered_candidates = []
        for candidate in candidates:
            score = score_map.get(str(candidate.tweet_url), 0.0)
            if score >= score_threshold:
                filtered_candidates.append(candidate)
                logger.info(
                    f"KEEPING candidate {candidate.tweet_url} (score: {score:.2f})"
                )
            else:
                logger.info(
                    f"DROPPING candidate {candidate.tweet_url} (score: {score:.2f})"
                )

        logger.info(
            f"Text filter narrowed down from {len(candidates)} to {len(filtered_candidates)} candidates."
        )
        return filtered_candidates
    except Exception as e:
        logger.error(f"An error occurred during LLM text filtering: {e}", exc_info=True)
        return candidates
