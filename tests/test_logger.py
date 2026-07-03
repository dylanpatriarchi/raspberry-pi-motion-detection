"""Tests for logging helper classes."""

import logging

from motion_detector.utils.logger import (
    MotionDetectionLogger,
    PerformanceLogger,
    setup_logger,
)


def test_setup_logger_replaces_handlers():
    first = setup_logger("dup-test", level="INFO")
    count = len(first.handlers)
    second = setup_logger("dup-test", level="INFO")
    # Handlers are cleared on each setup, so the count must not grow.
    assert len(second.handlers) == count


def test_motion_logger_counts_events():
    logger = MotionDetectionLogger(logging.getLogger("motion-test"))
    logger.log_motion_detected(1200.0, 3)
    logger.log_motion_detected(800.0, 1)
    logger.log_photo_saved("/tmp/x.jpg", 2048)

    stats = logger.get_statistics()
    assert stats["total_detections"] == 2
    assert stats["total_photos"] == 1


def test_performance_logger_tracks_and_resets_metrics():
    perf = PerformanceLogger(logging.getLogger("perf-test"))
    perf.log_fps(24.0)
    perf.log_processing_time("detect", 12.5)

    assert perf.get_metrics_summary()["fps"] == 24.0
    perf.reset_metrics()
    assert perf.get_metrics_summary() == {}
