import asyncio
import base64
import logging
import tempfile
from pathlib import Path

import cv2
import yt_dlp
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic import Field

from src.config.settings import settings
from src.prompts.utils import load_prompt
from src.schemas import Candidate
from src.schemas import ClipFindings
from src.schemas import VisionResult

logger = logging.getLogger(__name__)


class _VisionAnalysisResponse(BaseModel):
    """
    Internal schema for parsing the structured output from the Gemini model.
    """

    findings: list[ClipFindings] = Field(
        default_factory=list,
        description="A list of all relevant clips found within the video.",
    )


def _download_video(url: str, output_dir: Path) -> Path | None:
    """
    Downloads a video from a Twitter URL using yt-dlp.

    This is a private helper function for the vision module.

    Args:
        url: The URL of the tweet containing the video.
        output_dir: The temporary directory to save the downloaded file.

    Returns:
        The path to the downloaded video file, or None on failure.
    """
    try:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "merge_output_format": "mp4",
            "overwrites": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                logger.error("yt-dlp could not extract info from %s", url)
                return None

            filename = ydl.prepare_filename(info)
            if not filename or not Path(filename).exists():
                logger.error("yt-dlp failed to download file for %s", url)
                return None

            logger.info("Successfully downloaded video to %s", filename)
            return Path(filename)
    except Exception:
        logger.exception("yt-dlp downloader failed for %s", url)
        return None


def _extract_frames(video_path: Path, interval_seconds: int = 2) -> list[bytes]:
    """
    Extracts frames from a video file at a specified interval.

    This is a private helper function for the vision module.

    Args:
        video_path: The path to the video file.
        interval_seconds: The interval in seconds at which to extract frames.

    Returns:
        A list of frames, where each frame is a byte string (JPEG format).
    """
    frames: list[bytes] = []
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("Could not open video file: %s", video_path)
        return frames

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = int(fps * interval_seconds)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            success, buffer = cv2.imencode(".jpg", frame)
            if success:
                frames.append(buffer.tobytes())
        frame_count += 1
    cap.release()

    logger.info("Extracted %d frames from %s", len(frames), video_path.name)
    return frames


async def analyze_video_for_clip(
    candidate: Candidate,
    description: str,
    duration_seconds: int,
) -> VisionResult | None:
    """
    Analyzes a single video to find clips that match a description.

    This function downloads the video, extracts frames, and uses the Gemini
    vision model to identify relevant segments.

    Args:
        candidate: The Candidate object containing video URLs and metadata.
        description: The user's original search description.
        duration_seconds: The target duration for the video clip.

    Returns:
        A VisionResult object containing any found clips, or None if an
        error occurrs or no clips are found.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = await asyncio.to_thread(
            _download_video,
            url=str(candidate.tweet_url),
            output_dir=Path(tmpdir),
        )
        if not video_path:
            return None

        frames = _extract_frames(video_path, interval_seconds=2)
        if not frames:
            logger.warning("No frames extracted from video: %s", video_path)
            return None

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key.get_secret_value(),
        temperature=0.1,
    )
    structured_llm = llm.with_structured_output(_VisionAnalysisResponse)

    prompt_template = load_prompt("vision_analyzer_prompt.txt")
    if not prompt_template:
        logger.error("Could not load vision analysis prompt. Aborting analysis.")
        return None

    prompt_text = prompt_template.format(
        description=description,
        duration_seconds=duration_seconds,
    )

    base64_frames = [base64.b64encode(f).decode("utf-8") for f in frames]
    prompt_messages = [
        (
            "human",
            [
                {"type": "text", "text": prompt_text},
                *(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_frame}"},
                    }
                    for b64_frame in base64_frames
                ),
            ],
        ),
    ]

    logger.info(
        "Sending %d frames from %s to Gemini Vision...",
        len(frames),
        candidate.tweet_url,
    )

    try:
        response = await structured_llm.ainvoke(prompt_messages)
        if not response.findings:
            logger.warning(
                "No relevant clips found in video: %s",
                candidate.tweet_url,
            )
            return None
    except Exception:
        logger.exception("Vision analysis failed for %s", candidate.tweet_url)
        return None
    else:
        return VisionResult(
            tweet_url=candidate.tweet_url,
            best_video_url=candidate.best_video_url,
            findings=response.findings,
        )
