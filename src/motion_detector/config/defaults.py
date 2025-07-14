"""
Default Configuration
Default settings for the motion detection system.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class CameraConfig:
    """Camera configuration settings."""
    resolution: Tuple[int, int] = (640, 480)
    framerate: int = 30
    warmup_time: float = 2.0
    device_index: int = 0


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


DEFAULT_CONFIG = {
    'camera': CameraConfig(),
    'detection': DetectionConfig(),
    'storage': StorageConfig(),
    'display': DisplayConfig(),
    'logging': LoggingConfig(),
    'system': SystemConfig()
} 