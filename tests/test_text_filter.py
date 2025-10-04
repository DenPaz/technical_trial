# ruff: noqa: PLR2004
from unittest.mock import AsyncMock

import pytest
from pydantic import HttpUrl

from src.filters.text_filter import _ScoredCandidateResult
from src.filters.text_filter import _TextFilterResults
from src.filters.text_filter import filter_candidates_by_text
from src.schemas import Candidate

pytestmark = pytest.mark.asyncio


async def test_filter_candidates_by_text(mocker):
    """
    Tests that the text filter correctly keeps candidates above a score
    threshold and drops those below, based on a mocked LLM response.
    """
    candidates = [
        Candidate(
            tweet_url=HttpUrl("https://x.com/user/status/1"),
            text="This is a highly relevant tweet.",
            author="test",
            created_at="Sun Oct 05 12:00:00 +0000 2025",
        ),
        Candidate(
            tweet_url=HttpUrl("https://x.com/user/status/2"),
            text="This is not relevant at all.",
            author="test",
            created_at="Sun Oct 05 12:00:00 +0000 2025",
        ),
        Candidate(
            tweet_url=HttpUrl("https://x.com/user/status/3"),
            text="This one is good enough to pass.",
            author="test",
            created_at="Sun Oct 05 12:00:00 +0000 2025",
        ),
    ]

    mock_llm_response = _TextFilterResults(
        results=[
            _ScoredCandidateResult(
                tweet_url=HttpUrl("https://x.com/user/status/1"),
                score=0.9,
                reason="Direct match.",
            ),
            _ScoredCandidateResult(
                tweet_url=HttpUrl("https://x.com/user/status/2"),
                score=0.1,
                reason="Irrelevant topic.",
            ),
            _ScoredCandidateResult(
                tweet_url=HttpUrl("https://x.com/user/status/3"),
                score=0.6,
                reason="Passable.",
            ),
        ],
    )

    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = mock_llm_response

    mocker.patch(
        "src.filters.text_filter.ChatGoogleGenerativeAI.with_structured_output",
        return_value=mock_structured_llm,
    )

    filtered_candidates = await filter_candidates_by_text(
        candidates=candidates,
        description="test description",
        score_threshold=0.5,
    )

    assert len(filtered_candidates) == 2

    returned_urls = {str(c.tweet_url) for c in filtered_candidates}
    expected_urls = {
        "https://x.com/user/status/1",
        "https://x.com/user/status/3",
    }
    assert returned_urls == expected_urls
