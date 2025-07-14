"""
Professional Logging Utility
Advanced logging setup with rotation, formatting, and performance monitoring.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    log_format: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup professional logger with file rotation and formatting.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        log_format: Custom log format (optional)
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class PerformanceLogger:
    """
    Performance monitoring logger for tracking system metrics.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize performance logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
        self.metrics = {}
    
    def log_fps(self, fps: float) -> None:
        """Log frames per second."""
        self.metrics['fps'] = fps
        self.logger.debug(f"FPS: {fps:.2f}")
    
    def log_processing_time(self, operation: str, time_ms: float) -> None:
        """Log processing time for an operation."""
        self.metrics[f'{operation}_time'] = time_ms
        self.logger.debug(f"{operation} processing time: {time_ms:.2f}ms")
    
    def log_memory_usage(self, memory_mb: float) -> None:
        """Log memory usage."""
        self.metrics['memory_mb'] = memory_mb
        self.logger.debug(f"Memory usage: {memory_mb:.2f}MB")
    
    def log_detection_stats(self, contours_found: int, motion_detected: bool) -> None:
        """Log detection statistics."""
        self.metrics['contours_found'] = contours_found
        self.metrics['motion_detected'] = motion_detected
        self.logger.debug(f"Detection stats - Contours: {contours_found}, Motion: {motion_detected}")
    
    def get_metrics_summary(self) -> dict:
        """Get current metrics summary."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


class MotionDetectionLogger:
    """
    Specialized logger for motion detection events.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize motion detection logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
        self.detection_count = 0
        self.photo_count = 0
    
    def log_motion_detected(self, area: float, contours: int) -> None:
        """Log motion detection event."""
        self.detection_count += 1
        self.logger.info(f"Motion detected #{self.detection_count} - Area: {area:.0f}, Contours: {contours}")
    
    def log_photo_saved(self, filepath: str, file_size: int) -> None:
        """Log photo saved event."""
        self.photo_count += 1
        size_kb = file_size / 1024
        self.logger.info(f"Photo saved #{self.photo_count}: {filepath} ({size_kb:.1f}KB)")
    
    def log_camera_event(self, event: str, details: str = "") -> None:
        """Log camera-related events."""
        self.logger.info(f"Camera event: {event} {details}".strip())
    
    def log_system_event(self, event: str, details: str = "") -> None:
        """Log system events."""
        self.logger.info(f"System event: {event} {details}".strip())
    
    def get_statistics(self) -> dict:
        """Get detection statistics."""
        return {
            'total_detections': self.detection_count,
            'total_photos': self.photo_count
        } 