import pytest

from src.graph import GraphState
from src.graph import decide_after_filter
from src.graph import decide_after_vision
from src.schemas import Candidate
from src.schemas import VisionResult

pytestmark = pytest.mark.asyncio


async def test_decide_after_filter():
    """
    Tests the conditional edge that runs after the text filtering node.
    """
    state_with_candidates = GraphState(
        description="",
        duration_seconds=0,
        max_candidates=0,
        candidates=[],
        filtered_candidates=[
            Candidate(
                tweet_url="https://x.com/user/status/1",
                text="test",
                author="test",
                created_at="Sun Oct 05 12:00:00 +0000 2025",
            ),
        ],
        vision_results=[],
        final_result=None,
        trace_info={},
    )
    decision = await decide_after_filter(state_with_candidates)
    assert decision == "continue"

    state_without_candidates = GraphState(
        description="",
        duration_seconds=0,
        max_candidates=0,
        candidates=[],
        filtered_candidates=[],
        vision_results=[],
        final_result=None,
        trace_info={},
    )
    decision = await decide_after_filter(state_without_candidates)
    assert decision == "end"


async def test_decide_after_vision():
    """
    Tests the conditional edge that runs after the vision analysis node.
    """
    state_with_results = GraphState(
        description="",
        duration_seconds=0,
        max_candidates=0,
        candidates=[],
        filtered_candidates=[],
        vision_results=[
            VisionResult(
                tweet_url="https://x.com/user/status/1",
                best_video_url="https://video.x.com/1.mp4",
                findings=[],
            ),
        ],
        final_result=None,
        trace_info={},
    )
    decision = await decide_after_vision(state_with_results)
    assert decision == "continue"

    state_without_results = GraphState(
        description="",
        duration_seconds=0,
        max_candidates=0,
        candidates=[],
        filtered_candidates=[],
        vision_results=[],
        final_result=None,
        trace_info={},
    )
    decision = await decide_after_vision(state_without_results)
    assert decision == "end"
