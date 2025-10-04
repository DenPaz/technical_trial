# ruff: noqa: PLR2004
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.vision.analyzer import _extract_frames


@pytest.fixture
def dummy_video_file():
    """
    Creates a dummy 10-second video file for testing purposes.
    """
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        video_path = Path(tmp.name)

    width, height = 100, 100
    fps = 30
    duration_seconds = 10
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for _ in range(fps * duration_seconds):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        out.write(frame)

    out.release()

    yield video_path

    video_path.unlink()


def test_extract_frames(dummy_video_file):
    """
    Tests that the frame extraction logic correctly calculates the number of frames
    to extract based on the specified interval.
    """
    frames = _extract_frames(dummy_video_file, interval_seconds=2)
    assert len(frames) == 5

    frames = _extract_frames(dummy_video_file, interval_seconds=3)
    assert len(frames) == 4

    frames = _extract_frames(dummy_video_file, interval_seconds=1)
    assert len(frames) == 10
