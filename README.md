# Raspberry Pi Motion Detection System
## First Edition

A professional-grade motion detection system for Raspberry Pi using OpenCV and advanced computer vision techniques. This system monitors scenes in real-time and automatically captures photos when significant motion is detected.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/opencv-4.8+-green.svg)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Raspberry Pi](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)

## 🚀 Features

- **Real-time Motion Detection**: Advanced computer vision algorithms using OpenCV
- **Professional Architecture**: Modular design with separation of concerns
- **Configurable Settings**: Comprehensive JSON-based configuration system
- **Performance Monitoring**: Built-in FPS tracking and system diagnostics
- **Automatic Photo Capture**: Timestamp-based photo saving with configurable delays
- **Error Recovery**: Robust camera error handling and automatic recovery
- **Raspberry Pi Optimized**: Automatic performance optimizations for ARM processors
- **Logging System**: Professional logging with rotation and performance metrics
- **Storage Management**: Automatic cleanup and disk space monitoring
- **Preview Window**: Optional real-time preview with motion overlay
- **System Service**: Systemd integration for automatic startup
- **Docker Support**: Containerized deployment option

## 📋 Requirements

### Hardware
- Raspberry Pi 3B+ or newer (Pi 4 recommended)
- Pi Camera Module or USB webcam
- MicroSD card (16GB+ recommended)
- Adequate power supply (3A+ for Pi 4)

### Software
- Raspberry Pi OS (Bullseye or newer)
- Python 3.7+
- OpenCV 4.8+
- 512MB+ available RAM
- 1GB+ free disk space

## 🛠️ Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/dylanpatriarchi/raspberry-pi-motion-detection.git
cd raspberry-pi-motion-detection

# Install dependencies
make install

# Run system diagnostics
make diagnostics

# Start the system
make run
```

### Detailed Installation

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libatlas-base-dev libhdf5-dev
sudo apt install -y libharfbuzz0b libwebp6 libxcb1
```

#### 2. Enable Camera (for Pi Camera Module)

```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
```

#### 3. Project Setup

```bash
# Clone and enter project directory
git clone https://github.com/your-username/raspberry-pi-motion-detection.git
cd raspberry-pi-motion-detection

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install for Raspberry Pi
make install-pi

# Or install for development
make install-dev
```

#### 4. Configuration

```bash
# Create default configuration
make create-config

# Edit configuration (optional)
nano config/settings.json
```

## ⚙️ Configuration

The system uses a comprehensive JSON configuration system. Key settings include:

### Camera Settings
```json
{
  "camera": {
    "resolution": [640, 480],
    "framerate": 30,
    "warmup_time": 2.0,
    "device_index": 0
  }
}
```

### Motion Detection
```json
{
  "detection": {
    "motion_threshold": 1000,
    "min_area": 500,
    "blur_kernel_size": 21,
    "delta_threshold": 25
  }
}
```

### Storage Settings
```json
{
  "storage": {
    "output_directory": "data/captured_images",
    "photo_delay": 5.0,
    "photo_format": "jpg",
    "photo_quality": 95,
    "max_photos": 1000
  }
}
```

For complete configuration options, see the generated `config/settings.json` file.

## 🎯 Usage

### Basic Usage

```bash
# Start with default settings
python3 main.py

# Use custom configuration
python3 main.py --config custom.json

# Enable debug mode
python3 main.py --debug

# Headless mode (no preview)
python3 main.py --no-preview

# Run system diagnostics
python3 main.py --diagnostics
```

### Using Make Commands

```bash
# Install and run
make install
make run

# Development workflow
make install-dev
make lint
make test
make run-debug

# System management
make diagnostics
make backup-data
make clean
```

### Interactive Controls

When preview window is enabled:
- **q**: Quit application
- **r**: Reset background frame
- **s**: Save manual photo

## 📊 System Monitoring

### Performance Metrics
- Real-time FPS monitoring
- Processing time tracking
- Memory usage monitoring
- Motion detection statistics

### System Diagnostics
```bash
make diagnostics
```

This will check:
- OpenCV installation
- Camera accessibility
- System resources
- Disk space
- Performance capabilities

## 🔧 Advanced Features

### Automatic Startup

Install as system service:
```bash
make install-service
sudo systemctl start motion-detector
sudo systemctl status motion-detector
```

### Docker Deployment

```bash
# Build and run with Docker
make docker

# Or manually
docker build -t motion-detector .
docker run -it --device=/dev/video0 -v $(pwd)/data:/app/data motion-detector
```

### Performance Profiling

```bash
# Run performance benchmark
make benchmark

# Generate performance profile
make profile
```

## 📁 Project Structure

```
raspberry-pi-motion-detection/
├── src/motion_detector/           # Main source code
│   ├── core/                      # Core components
│   │   ├── detector.py           # Main detector class
│   │   ├── camera.py             # Camera management
│   │   └── processor.py          # Image processing
│   ├── config/                    # Configuration management
│   │   ├── settings.py           # Settings class
│   │   └── defaults.py           # Default values
│   └── utils/                     # Utility functions
│       ├── logger.py             # Logging system
│       ├── file_manager.py       # File operations
│       └── validators.py         # System validation
├── tests/                         # Unit tests
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── data/                          # Data storage
│   └── captured_images/          # Motion photos
├── logs/                          # Log files
├── config/                        # Configuration files
├── main.py                        # Main entry point
├── requirements.txt               # Dependencies
├── setup.py                       # Package setup
└── Makefile                       # Build automation
```

## 🐛 Troubleshooting

### Common Issues

#### Camera Not Detected
```bash
# Check camera status
vcgencmd get_camera
# Should return: supported=1 detected=1

# Test camera access
make check-system
```

#### Performance Issues
```bash
# Check system resources
make diagnostics

# For Raspberry Pi Zero/1, use lower settings:
# - Resolution: 320x240
# - Framerate: 10-15
# - Disable preview
```

#### Storage Issues
```bash
# Check disk space
df -h

# Clean old files
make clean
```

#### OpenCV Issues
```bash
# Reinstall OpenCV
pip3 uninstall opencv-python
pip3 install opencv-python>=4.8.0
```

### Debug Mode

Enable detailed logging:
```bash
python3 main.py --debug
```

### Log Analysis

Logs are stored in `logs/motion_detection.log` with automatic rotation.

## 🔐 Security Considerations

- Run with minimal privileges
- Secure file permissions on captured images
- Consider network security for remote access
- Regular security updates

## 🚀 Performance Optimization

### Raspberry Pi Optimization

The system automatically detects ARM processors and applies optimizations:
- Reduced resolution and framerate
- Optimized processing parameters
- Memory usage optimization
- Disabled preview for headless operation

### Manual Optimization

```json
{
  "camera": {
    "resolution": [320, 240],
    "framerate": 15
  },
  "detection": {
    "blur_kernel_size": 15,
    "dilate_iterations": 1
  },
  "display": {
    "show_preview": false
  }
}
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
python3 -m pytest tests/ --cov=src/motion_detector

# Run specific test
python3 -m pytest tests/test_detector.py -v
```

## 📚 API Documentation

Generate API documentation:
```bash
make docs
```

Documentation will be available in `docs/html/`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

```bash
# Development setup
make setup-dev
source venv/bin/activate
make install-dev

# Before committing
make lint
make test
make format
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenCV community for computer vision libraries
- Raspberry Pi Foundation for the hardware platform
- Contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/raspberry-pi-motion-detection/issues)
- **Documentation**: [Wiki](https://github.com/your-username/raspberry-pi-motion-detection/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/raspberry-pi-motion-detection/discussions)

## 🔄 Changelog

### Version 1.0.0
- Initial professional release
- Modular architecture implementation
- Comprehensive configuration system
- Performance monitoring and diagnostics
- Docker support
- Systemd service integration
- Automatic Raspberry Pi optimizations

---

**Note**: This system is designed for educational and personal use. For commercial security applications, consider professional-grade solutions with additional features like encryption, authentication, and compliance certifications. 