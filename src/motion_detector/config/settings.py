"""
Settings Management
Professional configuration management with validation and file I/O.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .defaults import DEFAULT_CONFIG, CameraConfig, DetectionConfig, StorageConfig, DisplayConfig, LoggingConfig, SystemConfig


class Settings:
    """
    Professional settings management class with validation and persistence.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or "config/settings.json"
        self.logger = logging.getLogger(__name__)
        
        # Load default configuration
        self.camera = DEFAULT_CONFIG['camera']
        self.detection = DEFAULT_CONFIG['detection']
        self.storage = DEFAULT_CONFIG['storage']
        self.display = DEFAULT_CONFIG['display']
        self.logging = DEFAULT_CONFIG['logging']
        self.system = DEFAULT_CONFIG['system']
        
        # Load user configuration if exists
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            self.logger.info(f"Config file {self.config_file} not found, using defaults")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configurations with loaded data
            self._update_from_dict(config_data)
            self.logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            self.logger.info("Using default configuration")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config_data = self._to_dict()
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving config file: {e}")
    
    def _update_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        if 'camera' in config_data:
            self._update_dataclass(self.camera, config_data['camera'])
        
        if 'detection' in config_data:
            self._update_dataclass(self.detection, config_data['detection'])
        
        if 'storage' in config_data:
            self._update_dataclass(self.storage, config_data['storage'])
        
        if 'display' in config_data:
            self._update_dataclass(self.display, config_data['display'])
        
        if 'logging' in config_data:
            self._update_dataclass(self.logging, config_data['logging'])
        
        if 'system' in config_data:
            self._update_dataclass(self.system, config_data['system'])
    
    def _update_dataclass(self, dataclass_instance: Any, data: Dict[str, Any]) -> None:
        """Update dataclass instance with dictionary data."""
        for key, value in data.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'camera': self._dataclass_to_dict(self.camera),
            'detection': self._dataclass_to_dict(self.detection),
            'storage': self._dataclass_to_dict(self.storage),
            'display': self._dataclass_to_dict(self.display),
            'logging': self._dataclass_to_dict(self.logging),
            'system': self._dataclass_to_dict(self.system)
        }
    
    def _dataclass_to_dict(self, dataclass_instance: Any) -> Dict[str, Any]:
        """Convert dataclass instance to dictionary."""
        return {
            field: getattr(dataclass_instance, field)
            for field in dataclass_instance.__dataclass_fields__
        }
    
    def validate(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Validate camera settings
            if self.camera.resolution[0] <= 0 or self.camera.resolution[1] <= 0:
                raise ValueError("Camera resolution must be positive")
            
            if self.camera.framerate <= 0:
                raise ValueError("Camera framerate must be positive")
            
            # Validate detection settings
            if self.detection.motion_threshold <= 0:
                raise ValueError("Motion threshold must be positive")
            
            if self.detection.min_area <= 0:
                raise ValueError("Minimum area must be positive")
            
            # Validate storage settings
            if self.storage.photo_delay < 0:
                raise ValueError("Photo delay cannot be negative")
            
            if self.storage.photo_quality < 1 or self.storage.photo_quality > 100:
                raise ValueError("Photo quality must be between 1 and 100")
            
            # Validate logging settings
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.logging.level not in valid_log_levels:
                raise ValueError(f"Log level must be one of {valid_log_levels}")
            
            self.logger.info("Configuration validation successful")
            return True
            
        except ValueError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.camera = DEFAULT_CONFIG['camera']
        self.detection = DEFAULT_CONFIG['detection']
        self.storage = DEFAULT_CONFIG['storage']
        self.display = DEFAULT_CONFIG['display']
        self.logging = DEFAULT_CONFIG['logging']
        self.system = DEFAULT_CONFIG['system']
        
        self.logger.info("Configuration reset to defaults")
    
    def get_summary(self) -> str:
        """Get a summary of current configuration."""
        return f"""
Motion Detection Configuration Summary:
=====================================
Camera: {self.camera.resolution} @ {self.camera.framerate}fps
Detection: Threshold={self.detection.motion_threshold}, Min Area={self.detection.min_area}
Storage: {self.storage.output_directory}, Delay={self.storage.photo_delay}s
Display: Preview={self.display.show_preview}, Contours={self.display.draw_contours}
Logging: Level={self.logging.level}, File={self.logging.log_to_file}
System: Debug={self.system.debug_mode}, Performance={self.system.performance_monitoring}
""" 