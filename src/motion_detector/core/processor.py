"""
Image Processing
Professional image processing for motion detection with optimized algorithms.
"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Optional
import logging

from ..utils.logger import PerformanceLogger


class ImageProcessor:
    """
    Professional image processing for motion detection.
    """
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        """
        Initialize image processor.
        
        Args:
            config: Detection configuration object
            logger: Logger instance (optional)
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.performance_logger = PerformanceLogger(self.logger)
        
        # Background subtraction
        self.background_frame: Optional[np.ndarray] = None
        self.background_initialized = False
        
        # Processing statistics
        self.processing_stats = {
            'frames_processed': 0,
            'motion_detected_count': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for motion detection.
        
        Args:
            frame: Input frame
            
        Returns:
            np.ndarray: Preprocessed frame
        """
        start_time = time.time()
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(
                gray, 
                (self.config.blur_kernel_size, self.config.blur_kernel_size), 
                0
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.performance_logger.log_processing_time("preprocess", processing_time)
            
            return blurred
            
        except Exception as e:
            self.logger.error(f"Preprocessing failed: {e}")
            return frame
    
    def initialize_background(self, frame: np.ndarray) -> None:
        """
        Initialize background frame for motion detection.
        
        Args:
            frame: Initial frame to use as background
        """
        try:
            self.background_frame = self.preprocess_frame(frame)
            self.background_initialized = True
            self.logger.info("Background frame initialized")
            
        except Exception as e:
            self.logger.error(f"Background initialization failed: {e}")
    
    def update_background(self, frame: np.ndarray, learning_rate: float = 0.05) -> None:
        """
        Update background frame using running average.
        
        Args:
            frame: Current frame
            learning_rate: Learning rate for background update
        """
        if not self.background_initialized:
            self.initialize_background(frame)
            return
        
        try:
            processed_frame = self.preprocess_frame(frame)
            
            # Update background using weighted average
            self.background_frame = cv2.addWeighted(
                self.background_frame, 
                1 - learning_rate,
                processed_frame, 
                learning_rate, 
                0
            )
            
        except Exception as e:
            self.logger.error(f"Background update failed: {e}")
    
    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, List[np.ndarray], np.ndarray]:
        """
        Detect motion in frame compared to background.
        
        Args:
            frame: Current frame
            
        Returns:
            Tuple[bool, List[np.ndarray], np.ndarray]: (motion_detected, contours, diff_image)
        """
        start_time = time.time()
        
        try:
            # Preprocess current frame
            processed_frame = self.preprocess_frame(frame)
            
            # Initialize background if needed
            if not self.background_initialized:
                self.initialize_background(frame)
                return False, [], processed_frame
            
            # Calculate frame difference
            frame_delta = cv2.absdiff(self.background_frame, processed_frame)
            
            # Apply threshold to get binary image
            thresh = cv2.threshold(
                frame_delta, 
                self.config.delta_threshold, 
                255, 
                cv2.THRESH_BINARY
            )[1]
            
            # Morphological operations to clean up the image
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Dilate to fill holes in contours
            dilated = cv2.dilate(thresh, None, iterations=self.config.dilate_iterations)
            
            # Find contours
            contours, _ = cv2.findContours(
                dilated, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Filter contours by area
            significant_contours = []
            total_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.config.min_area:
                    significant_contours.append(contour)
                    total_area += area
            
            # Determine if motion detected
            motion_detected = total_area > self.config.motion_threshold
            
            # Update statistics
            self.processing_stats['frames_processed'] += 1
            if motion_detected:
                self.processing_stats['motion_detected_count'] += 1
            
            processing_time = (time.time() - start_time) * 1000
            self.processing_stats['total_processing_time'] += processing_time
            self.processing_stats['average_processing_time'] = (
                self.processing_stats['total_processing_time'] / 
                self.processing_stats['frames_processed']
            )
            
            self.performance_logger.log_processing_time("motion_detection", processing_time)
            self.performance_logger.log_detection_stats(len(significant_contours), motion_detected)
            
            if motion_detected:
                self.logger.debug(f"Motion detected - Total area: {total_area:.0f}, Contours: {len(significant_contours)}")
            
            return motion_detected, significant_contours, dilated
            
        except Exception as e:
            self.logger.error(f"Motion detection failed: {e}")
            return False, [], np.zeros_like(frame[:,:,0])
    
    def draw_contours(self, frame: np.ndarray, contours: List[np.ndarray]) -> np.ndarray:
        """
        Draw contours on frame for visualization.
        
        Args:
            frame: Original frame
            contours: List of contours to draw
            
        Returns:
            np.ndarray: Frame with contours drawn
        """
        try:
            frame_copy = frame.copy()
            
            for contour in contours:
                # Draw bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Draw contour area
                area = cv2.contourArea(contour)
                cv2.putText(
                    frame_copy, 
                    f"Area: {int(area)}", 
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 255, 0), 
                    1
                )
                
                # Draw contour outline
                cv2.drawContours(frame_copy, [contour], -1, (0, 0, 255), 2)
            
            return frame_copy
            
        except Exception as e:
            self.logger.error(f"Drawing contours failed: {e}")
            return frame
    
    def add_overlay_info(self, frame: np.ndarray, motion_detected: bool, fps: float = 0.0) -> np.ndarray:
        """
        Add overlay information to frame.
        
        Args:
            frame: Input frame
            motion_detected: Whether motion was detected
            fps: Current FPS
            
        Returns:
            np.ndarray: Frame with overlay information
        """
        try:
            frame_copy = frame.copy()
            
            # Status text
            status_text = "MOTION DETECTED!" if motion_detected else "Monitoring..."
            status_color = (0, 0, 255) if motion_detected else (0, 255, 0)
            
            cv2.putText(
                frame_copy, 
                status_text, 
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                status_color, 
                2
            )
            
            # FPS counter
            if fps > 0:
                cv2.putText(
                    frame_copy, 
                    f"FPS: {fps:.1f}", 
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 255, 255), 
                    1
                )
            
            # Processing statistics
            stats_text = f"Frames: {self.processing_stats['frames_processed']}"
            cv2.putText(
                frame_copy, 
                stats_text, 
                (10, frame.shape[0] - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (255, 255, 255), 
                1
            )
            
            motion_text = f"Motion Events: {self.processing_stats['motion_detected_count']}"
            cv2.putText(
                frame_copy, 
                motion_text, 
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (255, 255, 255), 
                1
            )
            
            return frame_copy
            
        except Exception as e:
            self.logger.error(f"Adding overlay info failed: {e}")
            return frame
    
    def get_processing_statistics(self) -> dict:
        """
        Get processing statistics.
        
        Returns:
            dict: Processing statistics
        """
        return self.processing_stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            'frames_processed': 0,
            'motion_detected_count': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
        self.performance_logger.reset_metrics()
    
    def optimize_for_raspberry_pi(self) -> None:
        """Apply Raspberry Pi specific optimizations."""
        # Reduce blur kernel size for better performance
        if self.config.blur_kernel_size > 15:
            self.config.blur_kernel_size = 15
            self.logger.info("Reduced blur kernel size for Raspberry Pi optimization")
        
        # Reduce dilate iterations
        if self.config.dilate_iterations > 1:
            self.config.dilate_iterations = 1
            self.logger.info("Reduced dilate iterations for Raspberry Pi optimization")
    
    def cleanup(self) -> None:
        """Clean up processor resources."""
        self.background_frame = None
        self.background_initialized = False
        self.reset_statistics()
        self.logger.info("Image processor cleanup completed") 