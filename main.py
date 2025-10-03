import argparse
import asyncio
import logging
from pathlib import Path

from src.config.logging import setup_logging
from src.config.settings import BASE_DIR
from src.graph import app

setup_logging()
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-powered Twitter video clip scraper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--description",
        type=str,
        required=True,
        help="Description of the media content to search for.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Target duration of the video clips in seconds.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=10,
        help="Maximum number of candidate tweets to scrape.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=BASE_DIR / "results.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


async def main() -> None:
    """The main async entry point of the application."""
    args = parse_args()
    logger.info(f"Starting application with arguments: {args}")

    # Define the initial state to pass to the graph
    initial_state = {
        "description": args.description,
        "duration_seconds": args.duration,
        "max_candidates": args.max_candidates,
        "trace_info": {},  # Initialize an empty dictionary for tracing
    }

    try:
        # Asynchronously invoke the LangGraph app with the initial state
        final_state = await app.ainvoke(initial_state)
        final_result = final_state.get("final_result")

        # Write the final result to the output file
        if final_result:
            output_path = args.out
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(final_result.model_dump_json(indent=2))
            logger.info(f"✅ Success! Results written to {output_path}")
        else:
            logger.warning(
                "The pipeline finished, but could not determine a final best clip."
            )

    except Exception as e:
        logger.error(f"An error occurred in the graph pipeline: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
