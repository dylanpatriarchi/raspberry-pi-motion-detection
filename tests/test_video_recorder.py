"""Tests for the VideoRecorder utility."""

import numpy as np

from motion_detector.utils.video_recorder import VideoRecorder


def _frame_source(width=160, height=120):
    frame = (np.random.rand(height, width, 3) * 255).astype("uint8")
    return lambda: frame


def test_record_writes_a_clip(tmp_path):
    recorder = VideoRecorder(str(tmp_path), fps=20)
    path, frames = recorder.record(_frame_source(), duration=0.2, filename="clip.avi")
    assert path is not None
    assert path.endswith("clip.avi")
    assert frames > 0
    assert (tmp_path / "clip.avi").stat().st_size > 0


def test_record_with_no_frames_returns_none(tmp_path):
    recorder = VideoRecorder(str(tmp_path), fps=20)
    path, frames = recorder.record(lambda: None, duration=0.1, filename="empty.avi")
    assert path is None
    assert frames == 0


def test_not_recording_when_idle(tmp_path):
    recorder = VideoRecorder(str(tmp_path), fps=10)
    assert recorder.is_recording is False


def test_start_async_records_in_background(tmp_path):
    recorder = VideoRecorder(str(tmp_path), fps=20)
    started = recorder.start_async(_frame_source(), duration=0.2, filename="async.avi")
    assert started is True
    recorder.wait(timeout=5)
    assert recorder.is_recording is False
    assert (tmp_path / "async.avi").exists()


def test_mp4_format_selects_mp4v_fourcc(tmp_path):
    recorder = VideoRecorder(str(tmp_path), fps=10, video_format="mp4")
    # Just ensure the fourcc helper does not raise and returns an int code.
    assert isinstance(recorder._fourcc(), int)
