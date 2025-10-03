import json
import logging
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl

from src.config.settings import settings
from src.prompts.utils import load_prompt
from src.scraper.schemas import Candidate

logger = logging.getLogger(__name__)


class ScoredCandidateResult(BaseModel):
    tweet_url: HttpUrl
    score: float = Field(ge=0, le=1)
    reason: str


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
        model=settings.gemini_model,
        api_key=settings.gemini_api_key.get_secret_value(),
        temperature=0.0,
    )
    structured_llm = llm.with_structured_output(TextFilterResults)
    prompt_template = load_prompt("text_filter_prompt.txt")
    if not prompt_template:
        logger.error("Could not load text filter prompt template.")
        return candidates
    candidate_texts = [{"url": str(c.tweet_url), "text": c.text} for c in candidates]
    candidate_texts_json = json.dumps(candidate_texts, indent=2)
    prompt = prompt_template.format(
        description=description,
        candidate_texts=candidate_texts_json,
    )
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
