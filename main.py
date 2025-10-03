import argparse
import asyncio
import logging

from src.config import setup_logging
from src.filters.text_filter import filter_candidates_by_text
from src.scraper.service import scrape_candidates

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
    """
    The main asynchronous entry point of the application.
    """
    args = parse_arguments()
    logger.info(f"Starting job with parameters: {args}")
    try:
        scraped_candidates = await scrape_candidates(
            args.description,
            args.max_candidates,
        )
        filtered_candidates = await filter_candidates_by_text(
            scraped_candidates,
            args.description,
            score_threshold=0.5,
        )
        logger.info(f"Pipeline finished. Final candidates: {len(filtered_candidates)}")
        for c in filtered_candidates:
            logger.info(
                "Final Candidate: %s | author=%s | video=%s",
                c.tweet_url,
                c.author,
                c.best_video_url,
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
