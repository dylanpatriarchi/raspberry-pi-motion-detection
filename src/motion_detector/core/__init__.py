"""
Core Motion Detection Components
Main classes for motion detection functionality.
"""

from .detector import MotionDetector
from .camera import CameraManager
from .processor import ImageProcessor

__all__ = ['MotionDetector', 'CameraManager', 'ImageProcessor'] 