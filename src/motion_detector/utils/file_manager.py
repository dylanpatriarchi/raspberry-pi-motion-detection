"""
File Management Utility
Professional file operations for motion detection system.
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from datetime import datetime, timedelta


class FileManager:
    """
    Professional file management for motion detection system.
    """
    
    def __init__(self, base_directory: str, logger: Optional[logging.Logger] = None):
        """
        Initialize file manager.
        
        Args:
            base_directory: Base directory for file operations
            logger: Logger instance (optional)
        """
        self.base_directory = Path(base_directory)
        self.logger = logger or logging.getLogger(__name__)
        
        # Ensure base directory exists
        self.ensure_directory_exists(self.base_directory)
    
    def ensure_directory_exists(self, directory: Path) -> None:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            directory: Directory path to check/create
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory ensured: {directory}")
        except Exception as e:
            self.logger.error(f"Failed to create directory {directory}: {e}")
            raise
    
    def generate_filename(self, prefix: str = "motion", extension: str = "jpg") -> str:
        """
        Generate unique filename with timestamp.
        
        Args:
            prefix: Filename prefix
            extension: File extension (without dot)
        
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        return f"{prefix}_{timestamp}.{extension}"
    
    def save_image(self, image_data, filename: Optional[str] = None) -> Tuple[str, int]:
        """
        Save image data to file.
        
        Args:
            image_data: Image data to save
            filename: Optional filename (generated if not provided)
        
        Returns:
            Tuple[str, int]: (filepath, file_size)
        """
        if filename is None:
            filename = self.generate_filename()
        
        filepath = self.base_directory / filename
        
        try:
            # Save image (assuming OpenCV format)
            import cv2
            success = cv2.imwrite(str(filepath), image_data)
            
            if not success:
                raise RuntimeError("Failed to save image")
            
            file_size = filepath.stat().st_size
            self.logger.debug(f"Image saved: {filepath} ({file_size} bytes)")
            
            return str(filepath), file_size
            
        except Exception as e:
            self.logger.error(f"Failed to save image {filepath}: {e}")
            raise
    
    def cleanup_old_files(self, max_files: int = 1000, max_age_days: int = 30) -> int:
        """
        Clean up old files based on count and age.
        
        Args:
            max_files: Maximum number of files to keep
            max_age_days: Maximum age in days
        
        Returns:
            int: Number of files deleted
        """
        try:
            files = list(self.base_directory.glob("*.jpg"))
            files.extend(self.base_directory.glob("*.png"))
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            deleted_count = 0
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            # Delete files beyond max_files limit
            for file in files[max_files:]:
                try:
                    file.unlink()
                    deleted_count += 1
                    self.logger.debug(f"Deleted old file (count limit): {file}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete file {file}: {e}")
            
            # Delete files older than max_age_days
            for file in files[:max_files]:
                if file.stat().st_mtime < cutoff_time:
                    try:
                        file.unlink()
                        deleted_count += 1
                        self.logger.debug(f"Deleted old file (age limit): {file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete file {file}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleanup completed: {deleted_count} files deleted")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0
    
    def get_file_statistics(self) -> dict:
        """
        Get statistics about files in the directory.
        
        Returns:
            dict: File statistics
        """
        try:
            files = list(self.base_directory.glob("*"))
            image_files = [f for f in files if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            
            if not image_files:
                return {
                    'total_files': 0,
                    'total_size_mb': 0,
                    'oldest_file': None,
                    'newest_file': None
                }
            
            total_size = sum(f.stat().st_size for f in image_files)
            oldest_file = min(image_files, key=lambda x: x.stat().st_mtime)
            newest_file = max(image_files, key=lambda x: x.stat().st_mtime)
            
            return {
                'total_files': len(image_files),
                'total_size_mb': total_size / (1024 * 1024),
                'oldest_file': {
                    'name': oldest_file.name,
                    'date': datetime.fromtimestamp(oldest_file.stat().st_mtime).isoformat()
                },
                'newest_file': {
                    'name': newest_file.name,
                    'date': datetime.fromtimestamp(newest_file.stat().st_mtime).isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file statistics: {e}")
            return {}
    
    def create_backup(self, backup_directory: str) -> bool:
        """
        Create backup of all files.
        
        Args:
            backup_directory: Directory to store backup
        
        Returns:
            bool: True if backup successful
        """
        try:
            backup_path = Path(backup_directory)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = backup_path / f"backup_{timestamp}"
            backup_subdir.mkdir(exist_ok=True)
            
            # Copy all files
            files_copied = 0
            for file in self.base_directory.glob("*"):
                if file.is_file():
                    shutil.copy2(file, backup_subdir)
                    files_copied += 1
            
            self.logger.info(f"Backup created: {backup_subdir} ({files_copied} files)")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def get_disk_usage(self) -> dict:
        """
        Get disk usage information.
        
        Returns:
            dict: Disk usage statistics
        """
        try:
            usage = shutil.disk_usage(self.base_directory)
            return {
                'total_gb': usage.total / (1024**3),
                'used_gb': usage.used / (1024**3),
                'free_gb': usage.free / (1024**3),
                'usage_percent': (usage.used / usage.total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {e}")
            return {}
    
    def validate_storage_space(self, required_mb: float = 100) -> bool:
        """
        Validate available storage space.
        
        Args:
            required_mb: Required space in MB
        
        Returns:
            bool: True if sufficient space available
        """
        try:
            usage = shutil.disk_usage(self.base_directory)
            available_mb = usage.free / (1024**2)
            
            if available_mb < required_mb:
                self.logger.warning(f"Low disk space: {available_mb:.1f}MB available, {required_mb}MB required")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate storage space: {e}")
            return False 