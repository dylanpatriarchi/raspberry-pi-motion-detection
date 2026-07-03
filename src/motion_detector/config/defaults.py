"""
Default Configuration
Default settings for the motion detection system.
"""

from dataclasses import dataclass
from typing import Tuple

# Capture backends recognized by config validation and backend selection.
VALID_CAMERA_BACKENDS = ("auto", "opencv", "picamera2")


@dataclass
class CameraConfig:
    """Camera configuration settings."""

    resolution: Tuple[int, int] = (640, 480)
    framerate: int = 30
    warmup_time: float = 2.0
    device_index: int = 0
    # Capture backend: "auto" (picamera2 if available, else OpenCV),
    # "opencv" (USB/V4L2), or "picamera2" (Raspberry Pi Camera Module).
    backend: str = "auto"


@dataclass
class DetectionConfig:
    """Motion detection configuration settings."""

    motion_threshold: int = 1000
    min_area: int = 500
    blur_kernel_size: int = 21
    threshold_value: int = 25
    delta_threshold: int = 25
    dilate_iterations: int = 2
    contour_approximation: float = 0.02


@dataclass
class StorageConfig:
    """Photo storage configuration settings."""

    output_directory: str = "data/captured_images"
    photo_delay: float = 5.0
    photo_format: str = "jpg"
    photo_quality: int = 95
    max_photos: int = 1000  # Maximum photos to keep
    cleanup_enabled: bool = True


@dataclass
class DisplayConfig:
    """Display and preview configuration settings."""

    show_preview: bool = True
    preview_window_name: str = "Motion Detection"
    draw_contours: bool = True
    show_fps: bool = True
    preview_scale: float = 1.0


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    log_to_file: bool = True
    log_file: str = "logs/motion_detection.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class SystemConfig:
    """System-wide configuration settings."""

    debug_mode: bool = False
    performance_monitoring: bool = False
    auto_cleanup: bool = True
    graceful_shutdown_timeout: float = 10.0


def create_default_config() -> dict:
    """Build a fresh set of default configuration objects.

    Each call returns brand-new dataclass instances so that mutating one
    ``Settings`` object (e.g. applying Raspberry Pi optimizations or loading a
    config file) never leaks into another instance or into the module-level
    defaults.

    Returns:
        dict: Mapping of section name to a fresh config dataclass instance.
    """
    return {
        "camera": CameraConfig(),
        "detection": DetectionConfig(),
        "storage": StorageConfig(),
        "display": DisplayConfig(),
        "logging": LoggingConfig(),
        "system": SystemConfig(),
    }


# Backwards-compatible module-level defaults. Treat as read-only: use
# create_default_config() whenever a mutable copy is required.
DEFAULT_CONFIG = create_default_config()
