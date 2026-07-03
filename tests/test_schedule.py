"""Tests for active-hours scheduling helpers."""

from datetime import datetime

import pytest

from motion_detector.config.defaults import create_default_config
from motion_detector.utils.schedule import is_active_now, parse_hhmm, within_window


def test_parse_hhmm_valid():
    assert parse_hhmm("00:00") == 0
    assert parse_hhmm("06:30") == 390
    assert parse_hhmm("23:59") == 1439


@pytest.mark.parametrize("bad", ["24:00", "12:60", "abc", "1230", "", "12"])
def test_parse_hhmm_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        parse_hhmm(bad)


def test_within_daytime_window():
    # 09:00-17:00
    assert within_window(parse_hhmm("12:00"), "09:00", "17:00") is True
    assert within_window(parse_hhmm("08:59"), "09:00", "17:00") is False
    assert within_window(parse_hhmm("17:00"), "09:00", "17:00") is False  # end exclusive


def test_within_wraparound_window():
    # 22:00-06:00 (overnight)
    assert within_window(parse_hhmm("23:30"), "22:00", "06:00") is True
    assert within_window(parse_hhmm("02:00"), "22:00", "06:00") is True
    assert within_window(parse_hhmm("12:00"), "22:00", "06:00") is False


def test_equal_bounds_is_always_active():
    assert within_window(parse_hhmm("12:00"), "08:00", "08:00") is True


def test_is_active_now_disabled_is_always_active():
    config = create_default_config()["system"]
    config.active_hours_enabled = False
    assert is_active_now(config, now=datetime(2026, 1, 1, 3, 0)) is True


def test_is_active_now_respects_window():
    config = create_default_config()["system"]
    config.active_hours_enabled = True
    config.active_start = "22:00"
    config.active_end = "06:00"
    assert is_active_now(config, now=datetime(2026, 1, 1, 23, 0)) is True
    assert is_active_now(config, now=datetime(2026, 1, 1, 12, 0)) is False
