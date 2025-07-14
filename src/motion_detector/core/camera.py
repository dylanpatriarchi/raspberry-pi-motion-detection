"""
Camera Management
Professional camera handling with error recovery and performance monitoring.
"""

import cv2
import time
import threading
from typing import Optional, Tuple, Any
import logging
import numpy as np

from ..utils.logger import PerformanceLogger, MotionDetectionLogger


class CameraManager:
    """
    Professional camera management with error recovery and performance monitoring.
    """
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        """
        Initialize camera manager.
        
        Args:
            config: Camera configuration object
            logger: Logger instance (optional)
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.performance_logger = PerformanceLogger(self.logger)
        self.motion_logger = MotionDetectionLogger(self.logger)
        
        self.camera: Optional[cv2.VideoCapture] = None
        self.is_initialized = False
        self.is_streaming = False
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
        # Threading for frame capture
        self.capture_thread: Optional[threading.Thread] = None
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # Error recovery
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.last_error_time = 0
        self.error_recovery_delay = 5.0  # seconds
    
    def initialize(self) -> bool:
        """
        Initialize camera with configuration settings.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self.motion_logger.log_camera_event("Initializing camera", f"device {self.config.device_index}")
            
            # Create camera object
            self.camera = cv2.VideoCapture(self.config.device_index)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"Cannot open camera device {self.config.device_index}")
            
            # Configure camera properties
            self._configure_camera()
            
            # Warmup period
            if self.config.warmup_time > 0:
                self.logger.info(f"Camera warmup: {self.config.warmup_time}s")
                time.sleep(self.config.warmup_time)
            
            # Test frame capture
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                raise RuntimeError("Cannot capture test frame")
            
            self.is_initialized = True
            self.consecutive_errors = 0
            
            # Log camera info
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.motion_logger.log_camera_event(
                "Camera initialized",
                f"{actual_width}x{actual_height} @ {actual_fps:.1f}fps"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            self.is_initialized = False
            return False
    
    def _configure_camera(self) -> None:
        """Configure camera properties."""
        if not self.camera:
            return
        
        # Set resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
        
        # Set framerate
        self.camera.set(cv2.CAP_PROP_FPS, self.config.framerate)
        
        # Set buffer size to reduce latency
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Additional optimizations
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    def start_streaming(self) -> bool:
        """
        Start threaded frame capture.
        
        Returns:
            bool: True if streaming started successfully
        """
        if not self.is_initialized:
            self.logger.error("Camera not initialized")
            return False
        
        if self.is_streaming:
            self.logger.warning("Camera already streaming")
            return True
        
        try:
            self.stop_event.clear()
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            self.is_streaming = True
            self.motion_logger.log_camera_event("Streaming started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            return False
    
    def stop_streaming(self) -> None:
        """Stop threaded frame capture."""
        if not self.is_streaming:
            return
        
        self.stop_event.set()
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        self.is_streaming = False
        self.motion_logger.log_camera_event("Streaming stopped")
    
    def _capture_loop(self) -> None:
        """Main capture loop running in separate thread."""
        while not self.stop_event.is_set():
            try:
                if not self.camera or not self.camera.isOpened():
                    self._handle_camera_error("Camera not available in capture loop")
                    continue
                
                start_time = time.time()
                ret, frame = self.camera.read()
                capture_time = (time.time() - start_time) * 1000  # ms
                
                if not ret or frame is None:
                    self._handle_camera_error("Failed to capture frame")
                    continue
                
                # Update frame with thread safety
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                
                # Update performance metrics
                self.frame_count += 1
                self.fps_counter += 1
                self.performance_logger.log_processing_time("capture", capture_time)
                
                # Calculate FPS every second
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    fps = self.fps_counter / (current_time - self.last_fps_time)
                    self.performance_logger.log_fps(fps)
                    self.fps_counter = 0
                    self.last_fps_time = current_time
                
                # Reset error counter on successful capture
                self.consecutive_errors = 0
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.001)
                
            except Exception as e:
                self._handle_camera_error(f"Capture loop error: {e}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest captured frame.
        
        Returns:
            Optional[np.ndarray]: Latest frame or None if not available
        """
        if not self.is_streaming:
            # Direct capture if not streaming
            return self._capture_single_frame()
        
        # Return latest frame from streaming
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        
        return None
    
    def _capture_single_frame(self) -> Optional[np.ndarray]:
        """Capture single frame directly from camera."""
        if not self.camera or not self.camera.isOpened():
            return None
        
        try:
            ret, frame = self.camera.read()
            if ret and frame is not None:
                self.frame_count += 1
                return frame
        except Exception as e:
            self._handle_camera_error(f"Single frame capture error: {e}")
        
        return None
    
    def _handle_camera_error(self, error_message: str) -> None:
        """Handle camera errors with recovery logic."""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        self.logger.warning(f"Camera error ({self.consecutive_errors}/{self.max_consecutive_errors}): {error_message}")
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.logger.error("Maximum consecutive errors reached, attempting recovery")
            self._attempt_recovery()
    
    def _attempt_recovery(self) -> None:
        """Attempt to recover from camera errors."""
        try:
            self.motion_logger.log_camera_event("Attempting recovery")
            
            # Release current camera
            if self.camera:
                self.camera.release()
                time.sleep(1.0)
            
            # Wait before recovery attempt
            time.sleep(self.error_recovery_delay)
            
            # Reinitialize camera
            if self.initialize():
                self.logger.info("Camera recovery successful")
                self.motion_logger.log_camera_event("Recovery successful")
            else:
                self.logger.error("Camera recovery failed")
                self.motion_logger.log_camera_event("Recovery failed")
                
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {e}")
    
    def get_camera_info(self) -> dict:
        """
        Get current camera information.
        
        Returns:
            dict: Camera information and statistics
        """
        if not self.camera:
            return {}
        
        try:
            return {
                'device_index': self.config.device_index,
                'resolution': (
                    int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                ),
                'fps': self.camera.get(cv2.CAP_PROP_FPS),
                'is_initialized': self.is_initialized,
                'is_streaming': self.is_streaming,
                'frame_count': self.frame_count,
                'consecutive_errors': self.consecutive_errors,
                'backend': self.camera.getBackendName() if hasattr(self.camera, 'getBackendName') else 'Unknown'
            }
        except Exception as e:
            self.logger.error(f"Failed to get camera info: {e}")
            return {}
    
    def reset_statistics(self) -> None:
        """Reset performance statistics."""
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.performance_logger.reset_metrics()
    
    def cleanup(self) -> None:
        """Clean up camera resources."""
        try:
            self.motion_logger.log_camera_event("Cleaning up camera resources")
            
            # Stop streaming
            self.stop_streaming()
            
            # Release camera
            if self.camera:
                self.camera.release()
                self.camera = None
            
            # Reset state
            self.is_initialized = False
            self.is_streaming = False
            
            # Clean up OpenCV windows
            cv2.destroyAllWindows()
            
            self.logger.info("Camera cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during camera cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 