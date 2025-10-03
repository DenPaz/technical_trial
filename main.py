import argparse
import asyncio
import logging

from src.config.loggin import setup_logging
from src.filters.text_filter import filter_candidates_by_text
from src.scraper.service import scrape_candidates
from src.vision.analyzer import analyze_video_for_clip

setup_logging()
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="AI-powered Twitter clip scraper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--description",
        type=str,
        required=True,
        help="Description of the media to search for.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Target duration of the final clip in seconds.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=10,
        help="Maximum number of candidate tweets to scrape.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="results.json",
        help="Output file for the results.",
    )
    return parser.parse_args()


async def main() -> None:
    """The main asynchronous entry point of the application."""
    args = parse_arguments()
    logger.info(f"Starting job with parameters: {args}")

    try:
        # Step 1: Scrape initial candidates
        scraped_candidates = await scrape_candidates(
            args.description,
            args.max_candidates,
        )
        logger.info(f"Scraper returned {len(scraped_candidates)} candidates.")

        # Step 2: Filter candidates based on text relevance
        filtered_candidates = await filter_candidates_by_text(
            scraped_candidates,
            args.description,
        )
        if not filtered_candidates:
            logger.warning("No candidates remained after text filtering. Exiting.")
            return

        # Step 3: Analyze video for the remaining candidates concurrently
        logger.info(
            f"Starting vision analysis for {len(filtered_candidates)} candidates..."
        )
        vision_tasks = [
            analyze_video_for_clip(c, args.description, args.duration)
            for c in filtered_candidates
        ]
        vision_results = await asyncio.gather(*vision_tasks)

        # Filter out any None results from failed analyses
        successful_results = [res for res in vision_results if res and res.findings]

        if not successful_results:
            logger.warning("Vision analysis did not find any matching clips. Exiting.")
            return

        # TODO: Implement Step 4 - Select the best clip from successful_results

        logger.info(
            f"Vision analysis complete. Found {len(successful_results)} videos with potential clips."
        )
        for result in successful_results:
            for finding in result.findings:
                logger.info(
                    f"  - Found clip in {result.tweet_url} "
                    f"from {finding.start_time_s:.1f}s to {finding.end_time_s:.1f}s "
                    f"(Confidence: {finding.confidence:.2f})"
                )

    except Exception as e:
        logger.error(f"An error occurred in the main pipeline: {e}", exc_info=True)
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
