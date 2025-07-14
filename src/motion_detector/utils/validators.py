"""
Validation Utilities
Professional validation functions for configuration and system checks.
"""

import cv2
import os
import platform
import psutil
from typing import List, Tuple, Optional
import logging


def validate_config(config) -> Tuple[bool, List[str]]:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration object to validate
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, error_messages)
    """
    errors = []
    
    # Validate camera configuration
    if config.camera.resolution[0] <= 0 or config.camera.resolution[1] <= 0:
        errors.append("Camera resolution must be positive integers")
    
    if config.camera.framerate <= 0:
        errors.append("Camera framerate must be positive")
    
    if config.camera.warmup_time < 0:
        errors.append("Camera warmup time cannot be negative")
    
    # Validate detection configuration
    if config.detection.motion_threshold <= 0:
        errors.append("Motion threshold must be positive")
    
    if config.detection.min_area <= 0:
        errors.append("Minimum area must be positive")
    
    if config.detection.blur_kernel_size <= 0 or config.detection.blur_kernel_size % 2 == 0:
        errors.append("Blur kernel size must be positive and odd")
    
    if config.detection.threshold_value < 0 or config.detection.threshold_value > 255:
        errors.append("Threshold value must be between 0 and 255")
    
    # Validate storage configuration
    if config.storage.photo_delay < 0:
        errors.append("Photo delay cannot be negative")
    
    if config.storage.photo_quality < 1 or config.storage.photo_quality > 100:
        errors.append("Photo quality must be between 1 and 100")
    
    if config.storage.max_photos <= 0:
        errors.append("Maximum photos must be positive")
    
    # Validate logging configuration
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.logging.level not in valid_log_levels:
        errors.append(f"Log level must be one of {valid_log_levels}")
    
    return len(errors) == 0, errors


def validate_system_requirements() -> Tuple[bool, List[str]]:
    """
    Validate system requirements for motion detection.
    
    Returns:
        Tuple[bool, List[str]]: (requirements_met, warning_messages)
    """
    warnings = []
    
    # Check OpenCV installation
    try:
        cv2_version = cv2.__version__
        if cv2_version < "4.0.0":
            warnings.append(f"OpenCV version {cv2_version} is outdated, recommend 4.0+")
    except ImportError:
        warnings.append("OpenCV not installed or not accessible")
    
    # Check available memory
    memory = psutil.virtual_memory()
    if memory.available < 512 * 1024 * 1024:  # 512MB
        warnings.append(f"Low available memory: {memory.available / (1024**2):.0f}MB")
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
    
    # Check disk space
    disk_usage = psutil.disk_usage('/')
    free_gb = disk_usage.free / (1024**3)
    if free_gb < 1:
        warnings.append(f"Low disk space: {free_gb:.1f}GB available")
    
    # Platform-specific checks
    if platform.system() == "Linux":
        # Check for Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo:
                    warnings.append("Running on Raspberry Pi - consider performance optimizations")
        except:
            pass
    
    return len(warnings) == 0, warnings


def validate_camera_access(device_index: int = 0) -> Tuple[bool, str]:
    """
    Validate camera access and capabilities.
    
    Args:
        device_index: Camera device index
    
    Returns:
        Tuple[bool, str]: (camera_accessible, message)
    """
    try:
        camera = cv2.VideoCapture(device_index)
        
        if not camera.isOpened():
            return False, f"Camera device {device_index} not accessible"
        
        # Test frame capture
        ret, frame = camera.read()
        if not ret or frame is None:
            camera.release()
            return False, f"Camera device {device_index} cannot capture frames"
        
        # Get camera properties
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = camera.get(cv2.CAP_PROP_FPS)
        
        camera.release()
        
        message = f"Camera accessible - Resolution: {width}x{height}, FPS: {fps:.1f}"
        return True, message
        
    except Exception as e:
        return False, f"Camera validation failed: {str(e)}"


def validate_directory_permissions(directory: str) -> Tuple[bool, str]:
    """
    Validate directory permissions for read/write operations.
    
    Args:
        directory: Directory path to validate
    
    Returns:
        Tuple[bool, str]: (permissions_ok, message)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Test write permission
        test_file = os.path.join(directory, '.permission_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True, f"Directory {directory} is writable"
        except PermissionError:
            return False, f"No write permission for directory {directory}"
        
    except Exception as e:
        return False, f"Directory validation failed: {str(e)}"


def validate_network_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> Tuple[bool, str]:
    """
    Validate network connectivity (useful for remote monitoring features).
    
    Args:
        host: Host to test connectivity
        port: Port to test
        timeout: Timeout in seconds
    
    Returns:
        Tuple[bool, str]: (connected, message)
    """
    import socket
    
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True, "Network connectivity available"
    except socket.error:
        return False, "No network connectivity"


def validate_performance_requirements(resolution: Tuple[int, int], framerate: int) -> Tuple[bool, List[str]]:
    """
    Validate if system can handle specified performance requirements.
    
    Args:
        resolution: Target resolution (width, height)
        framerate: Target framerate
    
    Returns:
        Tuple[bool, List[str]]: (requirements_met, recommendations)
    """
    recommendations = []
    
    # Calculate approximate processing load
    pixels_per_second = resolution[0] * resolution[1] * framerate
    
    # Get system specs
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Performance recommendations
    if pixels_per_second > 30_000_000:  # 30M pixels/second
        recommendations.append("High processing load - consider reducing resolution or framerate")
    
    if cpu_count < 4 and framerate > 15:
        recommendations.append("Low CPU count - consider reducing framerate for better performance")
    
    if memory_gb < 1 and resolution[0] * resolution[1] > 640 * 480:
        recommendations.append("Low memory - consider reducing resolution")
    
    # Platform-specific recommendations
    if platform.machine().startswith('arm'):  # Likely Raspberry Pi
        if resolution[0] * resolution[1] > 640 * 480:
            recommendations.append("ARM processor detected - consider lower resolution for better performance")
        if framerate > 15:
            recommendations.append("ARM processor detected - consider lower framerate")
    
    return len(recommendations) == 0, recommendations


def run_system_diagnostics(logger: Optional[logging.Logger] = None) -> dict:
    """
    Run comprehensive system diagnostics.
    
    Args:
        logger: Logger instance for output
    
    Returns:
        dict: Diagnostic results
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    results = {
        'system_info': {
            'platform': platform.system(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3)
        },
        'opencv_available': False,
        'camera_accessible': False,
        'disk_space_ok': False,
        'memory_ok': False,
        'performance_ok': False
    }
    
    # Test OpenCV
    try:
        import cv2
        results['opencv_available'] = True
        results['opencv_version'] = cv2.__version__
        logger.info(f"OpenCV {cv2.__version__} available")
    except ImportError:
        logger.error("OpenCV not available")
    
    # Test camera
    camera_ok, camera_msg = validate_camera_access()
    results['camera_accessible'] = camera_ok
    results['camera_message'] = camera_msg
    logger.info(camera_msg)
    
    # Test disk space
    disk_usage = psutil.disk_usage('/')
    free_gb = disk_usage.free / (1024**3)
    results['disk_space_ok'] = free_gb > 1
    results['disk_free_gb'] = free_gb
    logger.info(f"Disk space: {free_gb:.1f}GB available")
    
    # Test memory
    memory = psutil.virtual_memory()
    available_mb = memory.available / (1024**2)
    results['memory_ok'] = available_mb > 512
    results['memory_available_mb'] = available_mb
    logger.info(f"Memory: {available_mb:.0f}MB available")
    
    # Overall system health
    results['system_ready'] = all([
        results['opencv_available'],
        results['camera_accessible'],
        results['disk_space_ok'],
        results['memory_ok']
    ])
    
    return results 