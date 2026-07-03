#!/usr/bin/env python3
"""
Main Entry Point for Raspberry Pi Motion Detection System

Thin wrapper that runs the package CLI from a source checkout. The same
entry point is installed as the ``motion-detector`` console script (see
setup.py) once the package is installed.
"""

import os
import sys

# Make the src/ layout importable when running directly from a checkout.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from motion_detector.cli import main

if __name__ == "__main__":
    main()
