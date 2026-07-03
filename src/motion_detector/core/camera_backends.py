"""
Camera Capture Backends

Abstracts the low-level frame source so the rest of the system is agnostic
to how frames are produced. Two backends are provided:

* ``OpenCVBackend`` - ``cv2.VideoCapture`` over V4L2/USB webcams. Works on any
  platform and is the right choice for USB cameras.
* ``PiCamera2Backend`` - the modern ``picamera2`` stack, required for the
  Raspberry Pi Camera Module on recent Raspberry Pi OS releases where
  ``cv2.VideoCapture`` no longer sees the CSI camera.

``create_backend`` selects one from configuration, defaulting to ``auto``
(use picamera2 when the library is importable, otherwise OpenCV).
"""

import importlib.util
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import cv2
import numpy as np


def picamera2_available() -> bool:
    """Return True if the picamera2 library can be imported."""
    return importlib.util.find_spec("picamera2") is not None


class CaptureBackend(ABC):
    """Minimal interface every capture backend must implement."""

    name = "base"

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def open(self) -> None:
        """Open the device. Raise RuntimeError if it cannot be opened."""

    @abstractmethod
    def is_opened(self) -> bool:
        """Return True while the device is open and usable."""

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Return (success, frame) with the frame in BGR order."""

    @abstractmethod
    def describe(self) -> dict:
        """Return {'resolution': (w, h), 'fps': float, 'backend': str}."""

    @abstractmethod
    def release(self) -> None:
        """Release the device and any associated resources."""


class OpenCVBackend(CaptureBackend):
    """Capture backend backed by ``cv2.VideoCapture`` (V4L2 / USB)."""

    name = "opencv"

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._capture: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        capture = cv2.VideoCapture(self.config.device_index)
        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"Cannot open camera device {self.config.device_index}")

        self._capture = capture
        self._configure()

    def _configure(self) -> None:
        capture = self._capture
        if capture is None:
            return
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
        capture.set(cv2.CAP_PROP_FPS, self.config.framerate)
        # Keep only the freshest frame to minimize latency.
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))

    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._capture is None:
            return False, None
        return self._capture.read()

    def describe(self) -> dict:
        if self._capture is None:
            return {"resolution": tuple(self.config.resolution), "fps": 0.0, "backend": self.name}
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self._capture.get(cv2.CAP_PROP_FPS))
        driver = (
            self._capture.getBackendName()
            if hasattr(self._capture, "getBackendName")
            else self.name
        )
        return {"resolution": (width, height), "fps": fps, "backend": driver}

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None


class PiCamera2Backend(CaptureBackend):
    """Capture backend for the Raspberry Pi Camera Module via picamera2."""

    name = "picamera2"

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._camera = None
        self._started = False

    def open(self) -> None:
        try:
            from picamera2 import Picamera2  # noqa: WPS433 (lazy, optional dependency)
        except ImportError as exc:  # pragma: no cover - depends on hardware libs
            raise RuntimeError(
                "picamera2 backend requested but the 'picamera2' package is not "
                "installed. Install it with: pip install '.[raspberry-pi]'"
            ) from exc

        camera = Picamera2()
        video_config = camera.create_video_configuration(
            main={"size": tuple(self.config.resolution), "format": "RGB888"},
        )
        camera.configure(video_config)
        try:
            camera.set_controls({"FrameRate": float(self.config.framerate)})
        except Exception:  # pragma: no cover - control support varies by sensor
            self.logger.debug("Sensor did not accept FrameRate control; using default")
        camera.start()

        self._camera = camera
        self._started = True

    def is_opened(self) -> bool:
        return self._started and self._camera is not None

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._camera is None:
            return False, None
        try:
            # picamera2 returns an RGB array; the rest of the pipeline expects BGR.
            frame_rgb = self._camera.capture_array()
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            return True, frame_bgr
        except Exception as exc:  # pragma: no cover - hardware failure path
            self.logger.debug(f"picamera2 capture failed: {exc}")
            return False, None

    def describe(self) -> dict:
        return {
            "resolution": tuple(self.config.resolution),
            "fps": float(self.config.framerate),
            "backend": self.name,
        }

    def release(self) -> None:
        if self._camera is not None:
            try:  # pragma: no cover - hardware teardown
                self._camera.stop()
                self._camera.close()
            except Exception as exc:  # pragma: no cover
                self.logger.debug(f"picamera2 release failed: {exc}")
            finally:
                self._camera = None
                self._started = False


def create_backend(config, logger: Optional[logging.Logger] = None) -> CaptureBackend:
    """Instantiate the capture backend selected by ``config.backend``.

    Args:
        config: Camera configuration object (may expose a ``backend`` attribute).
        logger: Optional logger passed to the backend.

    Returns:
        CaptureBackend: An unopened backend instance.
    """
    logger = logger or logging.getLogger(__name__)
    requested = getattr(config, "backend", "auto")

    if requested == "opencv":
        return OpenCVBackend(config, logger)
    if requested == "picamera2":
        return PiCamera2Backend(config, logger)

    # auto: prefer picamera2 when its library is present (i.e. on a configured
    # Raspberry Pi), otherwise fall back to OpenCV.
    if picamera2_available():
        logger.info("Auto-selected picamera2 backend")
        return PiCamera2Backend(config, logger)
    logger.info("Auto-selected OpenCV backend")
    return OpenCVBackend(config, logger)
