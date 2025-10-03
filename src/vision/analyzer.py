import asyncio
import base64
import logging
import tempfile
from pathlib import Path
from typing import List
from typing import Optional

import cv2
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic import Field

from src.config.settings import settings
from src.scraper.schemas import Candidate
from src.scraper.schemas import ClipFinding
from src.scraper.schemas import VisionResult
from src.vision.downloader import download_video

logger = logging.getLogger(__name__)


class VisionAnalysisResponse(BaseModel):
    findings: List[ClipFinding] = Field(default_factory=list)


def _extract_frames(video_path: Path, interval_seconds: int = 2) -> List[bytes]:
    # This function is correct and remains unchanged
    frames = []
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Could not open video file: {video_path}")
        return frames
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps == 0:
        fps = 30
    frame_interval = int(fps * interval_seconds)
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            success, buffer = cv2.imencode(".jpg", frame)
            if success:
                frames.append(buffer.tobytes())
        frame_count += 1
    cap.release()
    logger.info(f"Extracted {len(frames)} frames from {video_path.name}")
    return frames


async def analyze_video_for_clip(
    candidate: Candidate, description: str, duration_seconds: int
) -> Optional[VisionResult]:
    """Analyzes a single video to find a clip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        video_path = await asyncio.to_thread(
            download_video, url=str(candidate.tweet_url), output_dir=tmp_path
        )
        if not video_path:
            return None

        frames = _extract_frames(video_path, interval_seconds=2)
        if not frames:
            return None

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini.vision_model,
        api_key=settings.gemini.api_key,
    )
    structured_llm = llm.with_structured_output(VisionAnalysisResponse)

    # --- FIX: Properly encode image bytes as Base64 strings ---
    base64_frames = [base64.b64encode(frame).decode("utf-8") for frame in frames]

    prompt_messages = [
        ("system", "You are an expert video analyst..."),  # Shortened
        (
            "human",
            [
                {
                    "type": "text",
                    "text": f"Analyze these frames for a clip about '{description}' lasting {duration_seconds}s...",
                },
                # Pass the correctly encoded strings to the prompt
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
        f"Sending {len(frames)} frames from {candidate.tweet_url} to Gemini Vision..."
    )
    try:
        response = await structured_llm.ainvoke(prompt_messages)
        if not response.findings:
            logger.warning(f"No relevant clips found in video {candidate.tweet_url}")
            return None

        return VisionResult(
            tweet_url=candidate.tweet_url,
            best_video_url=candidate.best_video_url,
            findings=response.findings,
        )
    except Exception as e:
        logger.error(
            f"Vision analysis failed for {candidate.tweet_url}: {e}", exc_info=True
        )
        return None
