# ruff: noqa: PLR2004
from pydantic import HttpUrl

from src.schemas import ClipFindings
from src.schemas import VisionResult
from src.selector.selector import select_best_clip


def test_select_best_clip_from_multiple_results():
    """
    Ensures the function correctly selects the clip with the highest confidence
    and formats the output as expected, including alternates.
    """
    mock_vision_results = [
        VisionResult(
            tweet_url=HttpUrl("https://x.com/user1/status/111"),
            best_video_url=HttpUrl("https://video.x.com/111.mp4"),
            findings=[
                ClipFindings(
                    start_time_s=10.0,
                    end_time_s=25.0,
                    confidence=0.8,
                    reason="This is an okay match.",
                ),
            ],
        ),
        VisionResult(
            tweet_url=HttpUrl("https://x.com/user2/status/222"),
            best_video_url=HttpUrl("https://video.x.com/222.mp4"),
            findings=[
                ClipFindings(
                    start_time_s=50.0,
                    end_time_s=65.0,
                    confidence=0.75,
                    reason="This is a weak alternate match.",
                ),
                ClipFindings(
                    start_time_s=30.5,
                    end_time_s=45.5,
                    confidence=0.95,
                    reason="This is the best match.",
                ),
            ],
        ),
        VisionResult(
            tweet_url=HttpUrl("https://x.com/user3/status/333"),
            best_video_url=HttpUrl("https://video.x.com/333.mp4"),
            findings=[],  # This video had no findings
        ),
    ]
    mock_trace_info = {
        "scraped_count": 20,
        "text_filtered_count": 8,
        "vision_analysis_count": 3,
    }
    final_result = select_best_clip(mock_vision_results, mock_trace_info)

    assert final_result is not None

    assert final_result.confidence == 0.95
    assert final_result.reason == "This is the best match."
    assert str(final_result.tweet_url) == "https://x.com/user2/status/222"

    assert len(final_result.alternates) == 2
    assert final_result.alternates[0].confidence == 0.8
    assert final_result.alternates[1].confidence == 0.75

    assert final_result.trace.candidates_considered == 20
    assert final_result.trace.filtered_by_text == 8
    assert final_result.trace.vision_calls == 3


def test_select_best_clip_returns_none_when_no_findings():
    """
    Ensures the function gracefully returns None when no clips are found
    across all vision results.
    """
    mock_vision_results = [
        VisionResult(
            tweet_url=HttpUrl("https://x.com/user1/status/111"),
            best_video_url=HttpUrl("https://video.x.com/111.mp4"),
            findings=[],
        ),
    ]
    mock_trace_info = {}
    final_result = select_best_clip(mock_vision_results, mock_trace_info)

    assert final_result is None
