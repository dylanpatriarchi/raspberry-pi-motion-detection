"""Tests for configuration defaults and Settings management."""

import json

from motion_detector.config.defaults import create_default_config
from motion_detector.config.settings import Settings


def test_create_default_config_returns_fresh_instances():
    """Each call must return independent objects, not shared globals."""
    first = create_default_config()
    second = create_default_config()

    assert first["camera"] is not second["camera"]

    first["camera"].framerate = 999
    assert second["camera"].framerate == 30


def test_settings_instances_are_isolated(tmp_path):
    """Mutating one Settings instance must not affect another."""
    s1 = Settings(str(tmp_path / "missing.json"))
    s2 = Settings(str(tmp_path / "missing.json"))

    s1.camera.framerate = 5
    assert s2.camera.framerate == 30


def test_reset_to_defaults_restores_values(tmp_path):
    settings = Settings(str(tmp_path / "missing.json"))
    settings.camera.framerate = 7
    settings.detection.min_area = 1

    settings.reset_to_defaults()

    assert settings.camera.framerate == 30
    assert settings.detection.min_area == 500


def test_load_config_normalizes_resolution_to_tuple(tmp_path):
    config_file = tmp_path / "settings.json"
    config_file.write_text(json.dumps({"camera": {"resolution": [1280, 720]}}))

    settings = Settings(str(config_file))

    assert settings.camera.resolution == (1280, 720)
    assert isinstance(settings.camera.resolution, tuple)


def test_load_config_does_not_mutate_module_defaults(tmp_path):
    """Loading a file must never leak into a fresh default config."""
    config_file = tmp_path / "settings.json"
    config_file.write_text(json.dumps({"camera": {"framerate": 1}}))

    Settings(str(config_file))

    assert create_default_config()["camera"].framerate == 30


def test_validate_accepts_defaults(tmp_path):
    assert Settings(str(tmp_path / "missing.json")).validate() is True


def test_validate_rejects_bad_photo_quality(tmp_path):
    settings = Settings(str(tmp_path / "missing.json"))
    settings.storage.photo_quality = 500
    assert settings.validate() is False


def test_save_and_reload_roundtrip(tmp_path):
    config_file = tmp_path / "settings.json"
    settings = Settings(str(config_file))
    settings.camera.framerate = 12
    settings.save_config()

    reloaded = Settings(str(config_file))
    assert reloaded.camera.framerate == 12
