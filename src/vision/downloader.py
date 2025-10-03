# src/vision/downloader.py
import logging
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)


def download_video(url: str, output_dir: Path) -> Path | None:
    """
    Downloads a video from a URL using yt-dlp.

    Args:
        url: The URL of the video's tweet page.
        output_dir: The directory to save the video file in.

    Returns:
        The path to the downloaded video file, or None on failure.
    """
    try:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                logger.error(f"yt-dlp could not extract info from {url}")
                return None

            filename = ydl.prepare_filename(info)
            if not filename or not Path(filename).exists():
                logger.error(f"yt-dlp failed to download file for {url}")
                return None

            logger.info(f"Successfully downloaded video to {filename}")
            return Path(filename)

    except Exception as e:
        logger.error(f"yt-dlp downloader failed for {url}: {e}")
        return None
