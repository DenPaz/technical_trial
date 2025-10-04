import logging

from src.schemas import FinalAlternate
from src.schemas import FinalResult
from src.schemas import FinalTrace
from src.schemas import VisionResult

logger = logging.getLogger(__name__)


def select_best_clip(
    vision_results: list[VisionResult],
    trace_info: dict,
) -> FinalResult | None:
    """
    Selects the best clip from a list of vision analysis results.

    This function aggregates all clips findings from all analysed videos,
    ranks them by confidence score, and then constructs the final output
    object with the best clip, up to two alternates, and trace information.

    Args:
        vision_results: A list of successful results from the vision analyzer.
        trace_info: A dictionary containing trace data for the pipeline run.

    Returns:
        A formatted FinalResult object for the best clip, or None if no clips
        were found across all videos.
    """
    if not vision_results:
        return None

    all_findings = []
    for result in vision_results:
        all_findings.extend(
            {
                "tweet_url": result.tweet_url,
                "video_url": result.best_video_url,
                "clip": finding,
            }
            for finding in result.findings
        )
    if not all_findings:
        return None

    all_findings.sort(key=lambda x: x["clip"].confidence, reverse=True)

    best_finding = all_findings[0]
    alternates = all_findings[1:3]

    final_trace = FinalTrace(
        candidates_considered=trace_info.get("scraped_count", 0),
        filtered_by_text=trace_info.get("text_filtered_count", 0),
        vision_calls=trace_info.get("vision_analysis_count", 0),
        final_choice_rank=1,
    )

    final_result = FinalResult(
        tweet_url=best_finding["tweet_url"],
        video_url=best_finding["video_url"],
        start_time_s=best_finding["clip"].start_time_s,
        end_time_s=best_finding["clip"].end_time_s,
        confidence=best_finding["clip"].confidence,
        reason=best_finding["clip"].reason,
        alternates=[
            FinalAlternate(
                start_time_s=alt["clip"].start_time_s,
                end_time_s=alt["clip"].end_time_s,
                confidence=alt["clip"].confidence,
            )
            for alt in alternates
        ],
        trace=final_trace,
    )

    logger.info(
        "Selected best clip from %s with confidence %.2f",
        best_finding["tweet_url"],
        best_finding["clip"].confidence,
    )
    return final_result
