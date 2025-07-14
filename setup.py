#!/usr/bin/env python3
"""
Setup script for Raspberry Pi Motion Detection System
Professional motion detection system for Raspberry Pi using OpenCV.
"""

from setuptools import setup, find_packages
import os
import sys

# Read version from __init__.py
version = {}
with open(os.path.join("src", "__init__.py")) as f:
    exec(f.read(), version)

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Platform-specific requirements
platform_requirements = []
if sys.platform.startswith("linux"):
    # Additional Linux-specific packages
    platform_requirements.extend([
        "RPi.GPIO; platform_machine=='armv7l'",  # Raspberry Pi GPIO
    ])

setup(
    name="raspberry-pi-motion-detection",
    version=version.get("__version__", "1.0.0"),
    author=version.get("__author__", "Motion Detection Team"),
    author_email=version.get("__email__", "contact@motiondetection.com"),
    description=version.get("__description__", "Professional motion detection system for Raspberry Pi"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/raspberry-pi-motion-detection",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/raspberry-pi-motion-detection/issues",
        "Documentation": "https://github.com/your-username/raspberry-pi-motion-detection/wiki",
        "Source Code": "https://github.com/your-username/raspberry-pi-motion-detection",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
        "Topic :: Multimedia :: Video :: Capture",
    ],
    python_requires=">=3.7",
    install_requires=requirements + platform_requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "raspberry-pi": [
            "picamera2>=0.3.12",
            "RPi.GPIO>=0.7.1",
        ],
        "enhanced": [
            "pillow>=9.0.0",
            "scikit-image>=0.19.0",
            "matplotlib>=3.5.0",
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "picamera2>=0.3.12",
            "RPi.GPIO>=0.7.1",
            "pillow>=9.0.0",
            "scikit-image>=0.19.0",
            "matplotlib>=3.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "motion-detector=motion_detector.cli:main",
            "motion-detector-config=motion_detector.config_tool:main",
            "motion-detector-test=motion_detector.system_test:main",
        ],
    },
    include_package_data=True,
    package_data={
        "motion_detector": [
            "config/*.json",
            "docs/*.md",
        ],
    },
    zip_safe=False,
    keywords=[
        "raspberry-pi",
        "motion-detection",
        "opencv",
        "computer-vision",
        "surveillance",
        "security",
        "camera",
        "image-processing",
    ],
) 