"""Tests for configuration validation helpers."""

from motion_detector.config.settings import Settings
from motion_detector.utils.validators import validate_config


def make_settings(tmp_path):
    return Settings(str(tmp_path / "missing.json"))


def test_validate_config_accepts_defaults(tmp_path):
    ok, errors = validate_config(make_settings(tmp_path))
    assert ok is True
    assert errors == []


def test_validate_config_flags_even_blur_kernel(tmp_path):
    settings = make_settings(tmp_path)
    settings.detection.blur_kernel_size = 20  # must be odd
    ok, errors = validate_config(settings)
    assert ok is False
    assert any("Blur kernel" in e for e in errors)


def test_validate_config_flags_negative_framerate(tmp_path):
    settings = make_settings(tmp_path)
    settings.camera.framerate = -1
    ok, errors = validate_config(settings)
    assert ok is False
    assert any("framerate" in e for e in errors)


def test_validate_config_flags_bad_photo_quality(tmp_path):
    settings = make_settings(tmp_path)
    settings.storage.photo_quality = 0
    ok, errors = validate_config(settings)
    assert ok is False
    assert any("Photo quality" in e for e in errors)
