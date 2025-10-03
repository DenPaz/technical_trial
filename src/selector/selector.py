import logging
from typing import List

from src.scraper.schemas import FinalAlternate
from src.scraper.schemas import FinalResult
from src.scraper.schemas import FinalTrace
from src.scraper.schemas import VisionResult

logger = logging.getLogger(__name__)


def select_best_clip(
    vision_results: List[VisionResult], trace_info: dict
) -> FinalResult | None:
    """
    Selects the best clip from a list of vision analysis results.

    Args:
        vision_results: A list of successful results from the vision analyzer.
        trace_info: A dictionary containing trace data for the pipeline run.

    Returns:
        A formatted FinalResult object for the best clip, or None if no clips were found.
    """
    if not vision_results:
        return None

    all_findings = []
    for result in vision_results:
        for finding in result.findings:
            # Add the parent video info to each finding for later use
            all_findings.append(
                {
                    "tweet_url": result.tweet_url,
                    "video_url": result.best_video_url,
                    "clip": finding,
                }
            )

    if not all_findings:
        logger.warning("No clips were found in any of the analyzed videos.")
        return None

    # Rank all found clips by confidence score, descending
    all_findings.sort(key=lambda x: x["clip"].confidence, reverse=True)

    best_finding = all_findings[0]
    alternates = all_findings[1:3]  # Get up to two alternates

    # Create the final trace object
    final_trace = FinalTrace(
        candidates_considered=trace_info.get("scraped_count", 0),
        filtered_by_text=trace_info.get("text_filtered_count", 0),
        vision_calls=trace_info.get("vision_analysis_count", 0),
        final_choice_rank=1,
    )

    # Format the final result object
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
        f"Selected best clip from {best_finding['tweet_url']} with confidence {best_finding['clip'].confidence:.2f}"
    )
    return final_result
