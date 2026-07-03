"""Tests for the FileManager utility."""

import cv2
import numpy as np
import pytest

from motion_detector.utils.file_manager import FileManager


@pytest.fixture
def manager(tmp_path):
    return FileManager(str(tmp_path / "images"))


@pytest.fixture
def sample_image():
    return (np.random.rand(120, 160, 3) * 255).astype("uint8")


def test_generate_filename_format(manager):
    name = manager.generate_filename("motion", "jpg")
    assert name.startswith("motion_")
    assert name.endswith(".jpg")


def test_build_encode_params_jpeg(manager):
    params = manager._build_encode_params(".jpg", 80)
    assert params == [cv2.IMWRITE_JPEG_QUALITY, 80]


def test_build_encode_params_png_maps_compression(manager):
    # High quality -> low PNG compression.
    assert manager._build_encode_params(".png", 100) == [cv2.IMWRITE_PNG_COMPRESSION, 0]
    assert manager._build_encode_params(".png", 10)[1] > 0


def test_build_encode_params_clamps_out_of_range(manager):
    assert manager._build_encode_params(".jpg", 500) == [cv2.IMWRITE_JPEG_QUALITY, 100]
    assert manager._build_encode_params(".jpg", -5) == [cv2.IMWRITE_JPEG_QUALITY, 1]


def test_build_encode_params_none_returns_empty(manager):
    assert manager._build_encode_params(".jpg", None) == []


def test_save_image_quality_affects_size(manager, sample_image):
    _, high = manager.save_image(sample_image, "high.jpg", quality=95)
    _, low = manager.save_image(sample_image, "low.jpg", quality=10)
    assert high > low


def test_save_image_returns_existing_path(manager, sample_image):
    path, size = manager.save_image(sample_image, "shot.jpg", quality=90)
    assert path.endswith("shot.jpg")
    assert size > 0


def test_cleanup_old_files_respects_max_count(manager, sample_image):
    for i in range(5):
        manager.save_image(sample_image, f"img_{i}.jpg", quality=90)

    deleted = manager.cleanup_old_files(max_files=2, max_age_days=365)
    assert deleted == 3

    stats = manager.get_file_statistics()
    assert stats["total_files"] == 2
