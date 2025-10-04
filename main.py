import argparse
import asyncio
import logging
from pathlib import Path

from src.config.logging import setup_logging
from src.graph import GraphState
from src.graph import app

setup_logging()
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for the application.
    """
    parser = argparse.ArgumentParser(
        description="AI-powered Twitter video clip finder.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--description",
        type=str,
        required=True,
        help="Description of the video content to search for.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Target duration of the video clip in seconds.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=10,
        help="Maximum number of candidate tweets to initially scrape.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results.json"),
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


async def main() -> None:
    """
    The main asynchronous function that orchestrates the application.
    """
    args = parse_args()
    logger.info("Starting application with arguments: %s", args)

    initial_state = GraphState(
        description=args.description,
        duration_seconds=args.duration,
        max_candidates=args.max_candidates,
        trace_info={},
        candidates=[],
        filtered_candidates=[],
        vision_results=[],
        final_result=None,
    )

    try:
        final_state = await app.ainvoke(initial_state)

        final_result = final_state.get("final_result")
        if final_result:
            output_path = args.out
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(final_result.model_dump_json(indent=2))
            logger.info("✅ Success! Results written to %s", output_path)
        else:
            logger.warning("Pipeline finished but no suitable video clip was found.")
    except Exception:
        logger.exception("An error occurred in the graph pipeline")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception:
        logger.exception("An unhandled error occurred.")
