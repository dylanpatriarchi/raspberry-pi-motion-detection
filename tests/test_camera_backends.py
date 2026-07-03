"""Tests for camera backend selection and behavior."""

import pytest

from motion_detector.config.defaults import create_default_config
from motion_detector.core import camera_backends
from motion_detector.core.camera_backends import (
    CaptureBackend,
    OpenCVBackend,
    PiCamera2Backend,
    create_backend,
    picamera2_available,
)


@pytest.fixture
def camera_config():
    return create_default_config()["camera"]


def test_picamera2_available_returns_bool():
    assert isinstance(picamera2_available(), bool)


def test_capture_backend_is_abstract(camera_config):
    with pytest.raises(TypeError):
        CaptureBackend(camera_config)


def test_explicit_opencv_selection(camera_config):
    camera_config.backend = "opencv"
    assert isinstance(create_backend(camera_config), OpenCVBackend)


def test_explicit_picamera2_selection(camera_config):
    camera_config.backend = "picamera2"
    assert isinstance(create_backend(camera_config), PiCamera2Backend)


def test_auto_falls_back_to_opencv_without_picamera2(camera_config, monkeypatch):
    camera_config.backend = "auto"
    monkeypatch.setattr(camera_backends, "picamera2_available", lambda: False)
    assert isinstance(create_backend(camera_config), OpenCVBackend)


def test_auto_prefers_picamera2_when_available(camera_config, monkeypatch):
    camera_config.backend = "auto"
    monkeypatch.setattr(camera_backends, "picamera2_available", lambda: True)
    assert isinstance(create_backend(camera_config), PiCamera2Backend)


def test_opencv_describe_without_open_uses_config(camera_config):
    backend = OpenCVBackend(camera_config)
    info = backend.describe()
    assert info["resolution"] == tuple(camera_config.resolution)
    assert info["backend"] == "opencv"
    assert backend.is_opened() is False


def test_picamera2_open_raises_helpful_error_when_missing(camera_config):
    # picamera2 is not installed in the test environment, so open() should
    # raise a RuntimeError explaining how to install it.
    backend = PiCamera2Backend(camera_config)
    with pytest.raises(RuntimeError, match="picamera2"):
        backend.open()
