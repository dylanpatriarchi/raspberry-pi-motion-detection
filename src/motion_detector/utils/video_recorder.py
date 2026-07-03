"""
Video Clip Recorder

Records a short video clip when motion is detected. Recording runs on a
background thread so the detection loop is never blocked, and only one
clip is recorded at a time. Frames are pulled from a caller-supplied
source callable, which keeps the recorder decoupled from the camera.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Tuple

import cv2
import numpy as np

FrameSource = Callable[[], Optional[np.ndarray]]


class VideoRecorder:
    """Write fixed-duration clips via ``cv2.VideoWriter``."""

    def __init__(
        self,
        output_directory: str,
        fps: int = 10,
        video_format: str = "avi",
        logger: Optional[logging.Logger] = None,
    ):
        self.output_directory = Path(output_directory)
        self.fps = max(1, int(fps))
        self.video_format = video_format
        self.logger = logger or logging.getLogger(__name__)

        self.output_directory.mkdir(parents=True, exist_ok=True)

        self._recording = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_recording(self) -> bool:
        return self._recording.is_set()

    def _fourcc(self) -> int:
        if self.video_format == "mp4":
            return cv2.VideoWriter_fourcc(*"mp4v")
        # MJPG in an AVI container is broadly supported, including on headless
        # OpenCV builds without ffmpeg.
        return cv2.VideoWriter_fourcc(*"MJPG")

    def record(
        self, frame_source: FrameSource, duration: float, filename: str
    ) -> Tuple[Optional[str], int]:
        """Record synchronously for ``duration`` seconds.

        Args:
            frame_source: Callable returning the next BGR frame (or None).
            duration: Clip length in seconds.
            filename: Output filename (created inside the output directory).

        Returns:
            (filepath, frame_count); filepath is None if nothing was written.
        """
        filepath = self.output_directory / filename
        interval = 1.0 / self.fps
        end_time = time.time() + max(0.0, duration)

        writer = None
        frames_written = 0
        self._recording.set()
        try:
            while time.time() < end_time:
                frame = frame_source()
                if frame is None:
                    time.sleep(interval)
                    continue

                if writer is None:
                    height, width = frame.shape[:2]
                    writer = cv2.VideoWriter(
                        str(filepath), self._fourcc(), self.fps, (width, height)
                    )
                    if not writer.isOpened():
                        self.logger.error(f"Could not open video writer for {filepath}")
                        return None, 0

                writer.write(frame)
                frames_written += 1
                time.sleep(interval)
        except Exception as exc:
            self.logger.error(f"Video recording failed: {exc}")
        finally:
            if writer is not None:
                writer.release()
            self._recording.clear()

        if frames_written == 0:
            self.logger.warning("Video recording produced no frames")
            return None, 0

        self.logger.info(f"Recorded clip {filepath} ({frames_written} frames)")
        return str(filepath), frames_written

    def start_async(self, frame_source: FrameSource, duration: float, filename: str) -> bool:
        """Record in the background. Returns False if already recording."""
        if self.is_recording:
            self.logger.debug("Recording already in progress; skipping new clip")
            return False

        self._thread = threading.Thread(
            target=self.record,
            args=(frame_source, duration, filename),
            daemon=True,
        )
        self._thread.start()
        return True

    def wait(self, timeout: Optional[float] = None) -> None:
        """Block until the current recording thread finishes (mainly for tests)."""
        if self._thread is not None:
            self._thread.join(timeout)
