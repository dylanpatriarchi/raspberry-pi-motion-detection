"""Tests for the ImageProcessor motion-detection pipeline."""

import numpy as np
import pytest

from motion_detector.config.defaults import create_default_config
from motion_detector.core.processor import ImageProcessor


@pytest.fixture
def processor():
    return ImageProcessor(create_default_config()["detection"])


def _background(width=320, height=240):
    return np.full((height, width, 3), 20, dtype=np.uint8)


def _frame_with_motion(width=320, height=240):
    frame = _background(width, height)
    # A large bright block, comfortably above min_area / motion_threshold.
    frame[60:180, 80:220] = 255
    return frame


def test_preprocess_returns_single_channel(processor):
    gray = processor.preprocess_frame(_background())
    assert gray.ndim == 2


def test_first_detect_initializes_background(processor):
    detected, contours, _ = processor.detect_motion(_background())
    assert detected is False
    assert contours == []
    assert processor.background_initialized is True


def test_static_scene_reports_no_motion(processor):
    bg = _background()
    processor.initialize_background(bg)
    detected, contours, _ = processor.detect_motion(bg)
    assert detected is False
    assert contours == []


def test_large_change_triggers_motion(processor):
    processor.initialize_background(_background())
    detected, contours, _ = processor.detect_motion(_frame_with_motion())
    assert detected is True
    assert len(contours) >= 1


def test_small_change_below_min_area_is_ignored(processor):
    processor.initialize_background(_background())
    frame = _background()
    frame[10:14, 10:14] = 255  # ~16 px, well under min_area (500)
    detected, contours, _ = processor.detect_motion(frame)
    assert detected is False
    assert contours == []


def test_statistics_track_frames_and_events(processor):
    processor.initialize_background(_background())
    processor.detect_motion(_background())
    processor.detect_motion(_frame_with_motion())

    stats = processor.get_processing_statistics()
    assert stats["frames_processed"] == 2
    assert stats["motion_detected_count"] == 1

    processor.reset_statistics()
    assert processor.get_processing_statistics()["frames_processed"] == 0


def test_update_background_moves_toward_new_frame(processor):
    processor.initialize_background(_background())
    before = processor.background_frame.mean()
    for _ in range(20):
        processor.update_background(np.full((240, 320, 3), 200, dtype=np.uint8))
    assert processor.background_frame.mean() > before


def test_optimize_for_raspberry_pi_reduces_cost(processor):
    processor.config.blur_kernel_size = 21
    processor.config.dilate_iterations = 2
    processor.optimize_for_raspberry_pi()
    assert processor.config.blur_kernel_size <= 15
    assert processor.config.dilate_iterations == 1


def _subtractor_processor(algorithm):
    config = create_default_config()["detection"]
    config.algorithm = algorithm
    return ImageProcessor(config)


@pytest.mark.parametrize("algorithm", ["mog2", "knn"])
def test_subtractor_detects_motion(algorithm):
    processor = _subtractor_processor(algorithm)
    assert processor._bg_subtractor is not None

    # Let the subtractor learn the static background for several frames.
    for _ in range(15):
        processor.detect_motion(_background())

    detected, contours, _ = processor.detect_motion(_frame_with_motion())
    assert detected is True
    assert len(contours) >= 1


@pytest.mark.parametrize("algorithm", ["mog2", "knn"])
def test_subtractor_ignores_update_background(algorithm):
    processor = _subtractor_processor(algorithm)
    # update_background must be a no-op in subtractor mode (no crash, no state).
    processor.update_background(_background())
    assert processor.background_initialized is False


def test_frame_diff_has_no_subtractor(processor):
    assert processor._bg_subtractor is None


def test_no_regions_means_full_frame(processor):
    assert processor._get_roi_mask((240, 320)) is None


def test_roi_covering_motion_still_detects(processor):
    # Region covers the moving block (x 80-220, y 60-180).
    processor.config.regions = [[70, 50, 170, 150]]
    processor.initialize_background(_background())
    detected, contours, _ = processor.detect_motion(_frame_with_motion())
    assert detected is True
    assert len(contours) >= 1


def test_roi_excluding_motion_suppresses_detection(processor):
    # Region in a corner far from the moving block.
    processor.config.regions = [[0, 0, 40, 40]]
    processor.initialize_background(_background())
    detected, contours, _ = processor.detect_motion(_frame_with_motion())
    assert detected is False
    assert contours == []


def test_roi_mask_is_clipped_and_cached(processor):
    processor.config.regions = [[300, 220, 999, 999]]  # extends past bounds
    mask = processor._get_roi_mask((240, 320))
    assert mask.shape == (240, 320)
    assert mask[230, 310] == 255  # inside the clipped region
    # Second call returns the cached instance.
    assert processor._get_roi_mask((240, 320)) is mask


def test_draw_contours_and_overlay_preserve_shape(processor):
    processor.initialize_background(_background())
    frame = _frame_with_motion()
    _, contours, _ = processor.detect_motion(frame)
    assert processor.draw_contours(frame, contours).shape == frame.shape
    assert processor.add_overlay_info(frame, True, 24.0).shape == frame.shape
