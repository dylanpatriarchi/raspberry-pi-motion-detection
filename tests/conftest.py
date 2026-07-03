"""Shared pytest fixtures and path setup for the test suite."""

import os
import sys

# Make the src/ layout importable without installing the package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))
