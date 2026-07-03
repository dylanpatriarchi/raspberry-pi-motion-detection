"""
Active-Hours Scheduling

Pure helpers deciding whether the detector should act at a given time.
Kept free of any camera/OpenCV dependency so they are trivial to unit
test. Time windows are expressed as "HH:MM" strings and support
wrap-around across midnight (e.g. 22:00-06:00).
"""

from datetime import datetime
from typing import Optional


def parse_hhmm(value: str) -> int:
    """Parse an "HH:MM" string into minutes since midnight.

    Raises:
        ValueError: if the string is not a valid 24-hour time.
    """
    try:
        hours_str, minutes_str = value.split(":")
        hours, minutes = int(hours_str), int(minutes_str)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time '{value}', expected HH:MM")

    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"Time '{value}' out of range")
    return hours * 60 + minutes


def within_window(now_minutes: int, start: str, end: str) -> bool:
    """Return True if ``now_minutes`` falls inside the [start, end) window.

    A window where start == end is treated as always active (24h). Windows
    where start > end wrap across midnight.
    """
    start_minutes = parse_hhmm(start)
    end_minutes = parse_hhmm(end)

    if start_minutes == end_minutes:
        return True
    if start_minutes < end_minutes:
        return start_minutes <= now_minutes < end_minutes
    # Wrap-around window, e.g. 22:00 -> 06:00.
    return now_minutes >= start_minutes or now_minutes < end_minutes


def is_active_now(config, now: Optional[datetime] = None) -> bool:
    """Return True if the current time is within the configured active hours.

    When ``active_hours_enabled`` is false, the system is always active.
    """
    if not getattr(config, "active_hours_enabled", False):
        return True

    now = now or datetime.now()
    now_minutes = now.hour * 60 + now.minute
    return within_window(now_minutes, config.active_start, config.active_end)
