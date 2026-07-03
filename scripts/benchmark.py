#!/usr/bin/env python3
"""
Motion Detection Pipeline Benchmark

Measures the throughput of the image-processing pipeline on synthetic
frames, so it runs anywhere without a camera. Reports achievable FPS and
per-stage timing at several resolutions, and the effect of the Raspberry
Pi optimizations.

Usage:
    python3 scripts/benchmark.py                 # default 300 iterations
    python3 scripts/benchmark.py --iterations 500
    python3 scripts/benchmark.py --resolutions 320x240 640x480
"""

import argparse
import logging
import os
import sys
import time
from typing import List, Tuple

import numpy as np

# Make the src/ layout importable when run from a checkout.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from motion_detector.config.defaults import create_default_config  # noqa: E402
from motion_detector.core.processor import ImageProcessor  # noqa: E402

DEFAULT_RESOLUTIONS = [(320, 240), (640, 480), (1280, 720)]
WARMUP_ITERATIONS = 20


def _silent_logger() -> logging.Logger:
    """A logger that swallows the processor's debug output during timing."""
    logger = logging.getLogger("benchmark")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.CRITICAL)
    return logger


def _make_frames(width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    """Build a static background frame and a frame containing motion."""
    rng = np.random.default_rng(1234)
    background = rng.integers(0, 60, size=(height, width, 3), dtype=np.uint8)

    moving = background.copy()
    # A bright rectangle roughly a fifth of the frame simulates an intruder.
    y0, y1 = height // 3, (height // 3) + height // 5
    x0, x1 = width // 3, (width // 3) + width // 5
    moving[y0:y1, x0:x1] = 255
    return background, moving


def _time_calls(fn, iterations: int) -> float:
    """Return the mean wall-clock time per call in milliseconds."""
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    return (elapsed / iterations) * 1000.0


def benchmark_resolution(width: int, height: int, iterations: int, optimize_pi: bool) -> dict:
    """Benchmark the pipeline at a single resolution."""
    config = create_default_config()["detection"]
    processor = ImageProcessor(config, _silent_logger())
    if optimize_pi:
        processor.optimize_for_raspberry_pi()

    background, moving = _make_frames(width, height)

    # Prime the background model and warm caches.
    processor.initialize_background(background)
    for _ in range(WARMUP_ITERATIONS):
        processor.detect_motion(moving)

    preprocess_ms = _time_calls(lambda: processor.preprocess_frame(moving), iterations)

    def full_cycle():
        processor.detect_motion(moving)
        processor.update_background(moving)

    cycle_ms = _time_calls(full_cycle, iterations)
    fps = 1000.0 / cycle_ms if cycle_ms > 0 else float("inf")

    return {
        "resolution": f"{width}x{height}",
        "preprocess_ms": preprocess_ms,
        "cycle_ms": cycle_ms,
        "fps": fps,
    }


def parse_resolutions(values: List[str]) -> List[Tuple[int, int]]:
    resolutions = []
    for value in values:
        try:
            w, h = value.lower().split("x")
            resolutions.append((int(w), int(h)))
        except ValueError:
            raise SystemExit(f"Invalid resolution '{value}', expected WIDTHxHEIGHT")
    return resolutions


def print_table(title: str, rows: List[dict]) -> None:
    print(f"\n{title}")
    print("-" * 58)
    print(f"{'Resolution':>12} | {'Preprocess':>11} | {'Cycle':>9} | {'FPS':>7}")
    print("-" * 58)
    for row in rows:
        print(
            f"{row['resolution']:>12} | "
            f"{row['preprocess_ms']:>8.2f} ms | "
            f"{row['cycle_ms']:>6.2f} ms | "
            f"{row['fps']:>7.1f}"
        )
    print("-" * 58)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the motion detection pipeline")
    parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        default=300,
        help="Timed iterations per resolution (default: 300)",
    )
    parser.add_argument(
        "--resolutions",
        "-r",
        nargs="+",
        metavar="WxH",
        help="Resolutions to test, e.g. 320x240 640x480 (default: 320x240 640x480 1280x720)",
    )
    args = parser.parse_args()

    resolutions = parse_resolutions(args.resolutions) if args.resolutions else DEFAULT_RESOLUTIONS

    print("⚡ Motion Detection Pipeline Benchmark")
    print(f"   Iterations per resolution: {args.iterations}")

    baseline = [
        benchmark_resolution(w, h, args.iterations, optimize_pi=False) for w, h in resolutions
    ]
    optimized = [
        benchmark_resolution(w, h, args.iterations, optimize_pi=True) for w, h in resolutions
    ]

    print_table("Baseline configuration", baseline)
    print_table("Raspberry Pi optimized", optimized)

    print("\nNote: timings are CPU-bound and exclude camera capture latency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
