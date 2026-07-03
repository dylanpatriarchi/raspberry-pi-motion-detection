"""
Motion Detector Package
Core components for motion detection system.
"""

__version__ = "1.0.0"
__author__ = "Dylan Patriarchi"
__email__ = "dylanpatri04@gmail.com"
__description__ = "Professional motion detection system for Raspberry Pi"

from .core.detector import MotionDetector
from .core.camera import CameraManager
from .core.processor import ImageProcessor
from .utils.logger import setup_logger
from .config.settings import Settings

__all__ = ["MotionDetector", "CameraManager", "ImageProcessor", "setup_logger", "Settings"]
