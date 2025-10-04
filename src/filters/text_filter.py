import json
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl

from src.config.settings import settings
from src.prompts.utils import load_prompt
from src.schemas import Candidate

logger = logging.getLogger(__name__)


class _ScoredCandidateResult(BaseModel):
    """
    Internal schema for parsing LLM output.
    """

    tweet_url: HttpUrl
    score: float = Field(ge=0, le=1)
    reason: str


class _TextFilterResults(BaseModel):
    """
    Root schema for the structured output from the LLM.
    """

    results: list[_ScoredCandidateResult]


async def filter_candidates_by_text(
    candidates: list[Candidate],
    description: str,
    score_threshold: float = 0.5,
) -> list[Candidate]:
    """
    Filters a list of candidates based on the relevance of their text content.

    This function uses an LLM to score each candidate's tweet text against the
    user's description, keeping only those that meet a minimum score threshold.

    Args:
        candidates: The list of raw Candidate objects from the scraper.
        description: The user's original search description.
        score_threshold: The minimum score (0.0 to 1.0) to keep a candidate.

    Returns:
        A filtered list of candidates that are deemed textually relevant.
    """
    if not candidates:
        return []

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key.get_secret_value(),
        temperature=0.0,
    )
    structured_llm = llm.with_structured_output(_TextFilterResults)

    prompt_template = load_prompt("text_filter_prompt.txt")
    if not prompt_template:
        logger.error("Could not load text filter prompt template.")
        return candidates

    candidate_texts_for_prompt = [
        {"url": str(c.tweet_url), "text": c.text} for c in candidates
    ]
    candidate_texts_json = json.dumps(candidate_texts_for_prompt, indent=2)

    prompt = prompt_template.format(
        description=description,
        candidate_texts=candidate_texts_json,
    )

    logger.info("Sending %d candidates to LLM for text analysis...", len(candidates))
    try:
        response = await structured_llm.ainvoke(prompt)
        score_map = {str(r.tweet_url): r.score for r in response.results}

        filtered_candidates = []
        for candidate in candidates:
            score = score_map.get(str(candidate.tweet_url), 0.0)
            if score >= score_threshold:
                filtered_candidates.append(candidate)
                logger.info(
                    "KEEPING candidate %s (score=%.2f)",
                    candidate.tweet_url,
                    score,
                )
            else:
                logger.info(
                    "DROPPING candidate %s (score=%.2f)",
                    candidate.tweet_url,
                    score,
                )
        logger.info(
            "Text filtering reduced candidates from %d to %d",
            len(candidates),
            len(filtered_candidates),
        )
    except Exception:
        logger.exception("An error occurred during LLM text filtering.")
        return candidates
    else:
        return filtered_candidates
