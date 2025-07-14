"""
Main Motion Detector
Professional motion detection system orchestrating all components.
"""

import signal
import sys
import time
import platform
import cv2
from typing import Optional
import logging

from .camera import CameraManager
from .processor import ImageProcessor
from ..config.settings import Settings
from ..utils.logger import setup_logger, MotionDetectionLogger
from ..utils.file_manager import FileManager
from ..utils.validators import validate_config, run_system_diagnostics


class MotionDetector:
    """
    Main motion detection system coordinating all components.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize motion detection system.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        # Load configuration
        self.settings = Settings(config_file)
        
        # Setup logging
        self.logger = setup_logger(
            name="MotionDetector",
            log_file=self.settings.logging.log_file if self.settings.logging.log_to_file else None,
            level=self.settings.logging.level,
            log_format=self.settings.logging.log_format,
            max_file_size=self.settings.logging.max_file_size,
            backup_count=self.settings.logging.backup_count
        )
        
        # Initialize specialized loggers
        self.motion_logger = MotionDetectionLogger(self.logger)
        
        # Initialize components
        self.camera_manager: Optional[CameraManager] = None
        self.image_processor: Optional[ImageProcessor] = None
        self.file_manager: Optional[FileManager] = None
        
        # System state
        self.is_running = False
        self.is_initialized = False
        self.last_photo_time = 0
        
        # Performance monitoring
        self.start_time = time.time()
        self.frame_count = 0
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        self.logger.info("MotionDetector initialized")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self.motion_logger.log_system_event("System initialization started")
            
            # Validate configuration
            if not self.settings.validate():
                self.logger.error("Configuration validation failed")
                return False
            
            # Run system diagnostics
            if self.settings.system.debug_mode:
                diagnostics = run_system_diagnostics(self.logger)
                if not diagnostics.get('system_ready', False):
                    self.logger.warning("System diagnostics indicate potential issues")
            
            # Apply Raspberry Pi optimizations if detected
            if platform.machine().startswith('arm'):
                self.logger.info("ARM processor detected, applying Raspberry Pi optimizations")
                self._apply_raspberry_pi_optimizations()
            
            # Initialize file manager
            self.file_manager = FileManager(
                self.settings.storage.output_directory,
                self.logger
            )
            
            # Initialize image processor
            self.image_processor = ImageProcessor(
                self.settings.detection,
                self.logger
            )
            
            # Apply processor optimizations if needed
            if platform.machine().startswith('arm'):
                self.image_processor.optimize_for_raspberry_pi()
            
            # Initialize camera manager
            self.camera_manager = CameraManager(
                self.settings.camera,
                self.logger
            )
            
            if not self.camera_manager.initialize():
                self.logger.error("Camera initialization failed")
                return False
            
            # Validate storage space
            if not self.file_manager.validate_storage_space():
                self.logger.warning("Low storage space detected")
            
            self.is_initialized = True
            self.motion_logger.log_system_event("System initialization completed")
            
            # Log configuration summary
            self.logger.info(self.settings.get_summary())
            
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    def _apply_raspberry_pi_optimizations(self) -> None:
        """Apply Raspberry Pi specific optimizations."""
        # Reduce camera resolution for better performance
        if self.settings.camera.resolution[0] > 640:
            self.settings.camera.resolution = (640, 480)
            self.logger.info("Reduced camera resolution for Raspberry Pi")
        
        # Reduce framerate for stability
        if self.settings.camera.framerate > 15:
            self.settings.camera.framerate = 15
            self.logger.info("Reduced framerate for Raspberry Pi")
        
        # Disable preview by default on headless systems
        if not self.settings.display.show_preview:
            self.settings.display.show_preview = False
    
    def start(self) -> None:
        """Start the motion detection system."""
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize motion detection system")
        
        if self.is_running:
            self.logger.warning("Motion detection system already running")
            return
        
        try:
            self.motion_logger.log_system_event("Motion detection started")
            self.is_running = True
            self.start_time = time.time()
            
            # Start camera streaming for better performance
            if self.camera_manager:
                self.camera_manager.start_streaming()
            
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Error in motion detection system: {e}")
            self.stop()
            raise
    
    def _main_loop(self) -> None:
        """Main detection loop."""
        self.logger.info("Motion detection system active - Press Ctrl+C to stop")
        
        try:
            while self.is_running:
                # Get frame from camera
                frame = self.camera_manager.get_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                self.frame_count += 1
                
                # Process frame for motion detection
                motion_detected, contours, diff_image = self.image_processor.detect_motion(frame)
                
                # Handle motion detection
                if motion_detected:
                    self._handle_motion_detected(frame, contours)
                
                # Update background
                self.image_processor.update_background(frame)
                
                # Display preview if enabled
                if self.settings.display.show_preview:
                    self._display_preview(frame, contours, motion_detected)
                
                # Cleanup old files periodically
                if self.settings.storage.cleanup_enabled and self.frame_count % 1000 == 0:
                    self.file_manager.cleanup_old_files(
                        self.settings.storage.max_photos,
                        max_age_days=30
                    )
                
                # Performance monitoring
                if self.settings.system.performance_monitoring and self.frame_count % 100 == 0:
                    self._log_performance_stats()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.stop()
    
    def _handle_motion_detected(self, frame, contours) -> None:
        """Handle motion detection event."""
        current_time = time.time()
        
        # Check if enough time has passed since last photo
        if current_time - self.last_photo_time < self.settings.storage.photo_delay:
            return
        
        try:
            # Calculate total motion area
            total_area = sum(cv2.contourArea(contour) for contour in contours)
            
            # Log motion detection
            self.motion_logger.log_motion_detected(total_area, len(contours))
            
            # Save photo
            filename = self.file_manager.generate_filename("motion", self.settings.storage.photo_format)
            filepath, file_size = self.file_manager.save_image(frame, filename)
            
            # Log photo saved
            self.motion_logger.log_photo_saved(filepath, file_size)
            
            # Update last photo time
            self.last_photo_time = current_time
            
        except Exception as e:
            self.logger.error(f"Error handling motion detection: {e}")
    
    def _display_preview(self, frame, contours, motion_detected) -> None:
        """Display preview window with motion detection overlay."""
        try:
            import cv2
            
            display_frame = frame.copy()
            
            # Draw contours if enabled
            if self.settings.display.draw_contours:
                display_frame = self.image_processor.draw_contours(display_frame, contours)
            
            # Add overlay information
            if self.settings.display.show_fps:
                fps = self.camera_manager.performance_logger.metrics.get('fps', 0)
                display_frame = self.image_processor.add_overlay_info(display_frame, motion_detected, fps)
            
            # Scale preview if needed
            if self.settings.display.preview_scale != 1.0:
                height, width = display_frame.shape[:2]
                new_width = int(width * self.settings.display.preview_scale)
                new_height = int(height * self.settings.display.preview_scale)
                display_frame = cv2.resize(display_frame, (new_width, new_height))
            
            # Show preview
            cv2.imshow(self.settings.display.preview_window_name, display_frame)
            
            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.logger.info("Quit key pressed")
                self.stop()
            elif key == ord('r'):
                self.logger.info("Reset background")
                self.image_processor.background_initialized = False
            elif key == ord('s'):
                self.logger.info("Manual photo capture")
                self._handle_motion_detected(frame, contours)
            
        except Exception as e:
            self.logger.error(f"Error displaying preview: {e}")
    
    def _log_performance_stats(self) -> None:
        """Log performance statistics."""
        try:
            uptime = time.time() - self.start_time
            fps = self.frame_count / uptime if uptime > 0 else 0
            
            # Get component statistics
            camera_info = self.camera_manager.get_camera_info()
            processing_stats = self.image_processor.get_processing_statistics()
            file_stats = self.file_manager.get_file_statistics()
            
            self.logger.info(f"Performance Stats - Uptime: {uptime:.1f}s, FPS: {fps:.1f}, "
                           f"Frames: {self.frame_count}, Motion Events: {processing_stats.get('motion_detected_count', 0)}")
            
        except Exception as e:
            self.logger.error(f"Error logging performance stats: {e}")
    
    def stop(self) -> None:
        """Stop the motion detection system."""
        if not self.is_running:
            return
        
        self.motion_logger.log_system_event("Motion detection stopping")
        self.is_running = False
        
        try:
            # Stop camera streaming
            if self.camera_manager:
                self.camera_manager.stop_streaming()
            
            # Close preview window
            if self.settings.display.show_preview:
                import cv2
                cv2.destroyAllWindows()
            
            # Log final statistics
            self._log_final_statistics()
            
            self.motion_logger.log_system_event("Motion detection stopped")
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
    
    def _log_final_statistics(self) -> None:
        """Log final system statistics."""
        try:
            uptime = time.time() - self.start_time
            
            # Get final statistics from all components
            camera_stats = self.camera_manager.get_camera_info() if self.camera_manager else {}
            processing_stats = self.image_processor.get_processing_statistics() if self.image_processor else {}
            file_stats = self.file_manager.get_file_statistics() if self.file_manager else {}
            motion_stats = self.motion_logger.get_statistics()
            
            self.logger.info("=== FINAL STATISTICS ===")
            self.logger.info(f"Total uptime: {uptime:.1f} seconds")
            self.logger.info(f"Total frames processed: {self.frame_count}")
            self.logger.info(f"Average FPS: {self.frame_count / uptime:.1f}")
            self.logger.info(f"Motion detection events: {motion_stats.get('total_detections', 0)}")
            self.logger.info(f"Photos captured: {motion_stats.get('total_photos', 0)}")
            self.logger.info(f"Total files stored: {file_stats.get('total_files', 0)}")
            self.logger.info(f"Storage used: {file_stats.get('total_size_mb', 0):.1f} MB")
            
        except Exception as e:
            self.logger.error(f"Error logging final statistics: {e}")
    
    def cleanup(self) -> None:
        """Clean up all system resources."""
        try:
            self.logger.info("Cleaning up system resources...")
            
            # Cleanup components
            if self.camera_manager:
                self.camera_manager.cleanup()
            
            if self.image_processor:
                self.image_processor.cleanup()
            
            # Close OpenCV windows
            import cv2
            cv2.destroyAllWindows()
            
            self.logger.info("System cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_system_status(self) -> dict:
        """
        Get current system status.
        
        Returns:
            dict: System status information
        """
        return {
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'uptime': time.time() - self.start_time if self.is_running else 0,
            'frame_count': self.frame_count,
            'camera_info': self.camera_manager.get_camera_info() if self.camera_manager else {},
            'processing_stats': self.image_processor.get_processing_statistics() if self.image_processor else {},
            'file_stats': self.file_manager.get_file_statistics() if self.file_manager else {},
            'motion_stats': self.motion_logger.get_statistics()
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 