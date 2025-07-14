"""
Motion Detector Package
Core components for motion detection system.
"""

from .core.detector import MotionDetector
from .core.camera import CameraManager
from .core.processor import ImageProcessor
from .utils.logger import setup_logger
from .config.settings import Settings

__all__ = [
    'MotionDetector',
    'CameraManager', 
    'ImageProcessor',
    'setup_logger',
    'Settings'
] 