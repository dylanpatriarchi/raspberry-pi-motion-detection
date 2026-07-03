#!/usr/bin/env python3
"""
Setup script for Raspberry Pi Motion Detection System
Professional motion detection system for Raspberry Pi using OpenCV.
"""

from setuptools import setup, find_packages
import os
import re
import sys


def read_metadata():
    """Parse dunder metadata from the package __init__ without importing it.

    Importing the package would pull in cv2/numpy, which are not available at
    build time, so the values are read with a simple regex instead.
    """
    init_path = os.path.join("src", "motion_detector", "__init__.py")
    with open(init_path, "r", encoding="utf-8") as fh:
        contents = fh.read()

    def find(name, default):
        match = re.search(rf'^{name}\s*=\s*["\']([^"\']*)["\']', contents, re.MULTILINE)
        return match.group(1) if match else default

    return {
        "__version__": find("__version__", "1.0.0"),
        "__author__": find("__author__", "Dylan Patriarchi"),
        "__email__": find("__email__", "dylanpatri04@gmail.com"),
        "__description__": find(
            "__description__", "Professional motion detection system for Raspberry Pi"
        ),
    }


version = read_metadata()

# Read long description from README
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = read_metadata()["__description__"]

# Core runtime dependencies. Kept in sync with requirements.txt, which is
# shipped in the sdist (see MANIFEST.in); fall back to this list if the file
# is unavailable at build time.
_CORE_REQUIREMENTS = [
    "opencv-python>=4.8.0,<5.0.0",
    "numpy>=1.24.0,<2.0.0",
    "psutil>=5.9.0,<6.0.0",
]
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = list(_CORE_REQUIREMENTS)

# Platform-specific requirements
platform_requirements = []
if sys.platform.startswith("linux"):
    # Additional Linux-specific packages
    platform_requirements.extend(
        [
            "RPi.GPIO; platform_machine=='armv7l'",  # Raspberry Pi GPIO
        ]
    )

setup(
    name="raspberry-pi-motion-detection",
    version=version.get("__version__", "1.0.0"),
    author=version.get("__author__", "Dylan Patriarchi"),
    author_email=version.get("__email__", "dylanpatri04@gmail.com"),
    description=version.get(
        "__description__", "Professional motion detection system for Raspberry Pi"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dylanpatriarchi/raspberry-pi-motion-detection",
    project_urls={
        "Bug Tracker": "https://github.com/dylanpatriarchi/raspberry-pi-motion-detection/issues",
        "Documentation": "https://github.com/dylanpatriarchi/raspberry-pi-motion-detection/wiki",
        "Source Code": "https://github.com/dylanpatriarchi/raspberry-pi-motion-detection",
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
            "pdoc3>=0.10.0",
            "pre-commit>=3.0.0",
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
            "pdoc3>=0.10.0",
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
