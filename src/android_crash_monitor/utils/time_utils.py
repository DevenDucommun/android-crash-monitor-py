#!/usr/bin/env python3
"""
Time Utilities

Centralized timestamp parsing and manipulation for Android crash monitoring.
"""

from datetime import datetime, timedelta
from typing import Optional


_YEAR_FORMATS = ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S')
_YEARLESS_FORMATS = ('%m-%d %H:%M:%S.%f', '%m-%d %H:%M:%S')

# Tolerance for device clocks running slightly ahead of the host before a
# year-less timestamp is treated as belonging to the previous year.
_FUTURE_TOLERANCE = timedelta(days=1)


def parse_android_timestamp(timestamp_str: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse Android logcat timestamp with robust format handling.

    Handles multiple timestamp formats commonly found in Android logs:
    - With year: YYYY-MM-DD HH:MM:SS[.fff]
    - Without year (default ``adb logcat`` output): MM-DD HH:MM:SS[.fff]

    Year-less timestamps get the most recent year that does not place them in
    the future, so December entries read in January resolve to the previous
    year. The year is supplied *before* parsing, which keeps leap-day entries
    (``02-29``) parseable and avoids strptime's ambiguous default year
    (deprecated in Python 3.13, changing in 3.15).

    Args:
        timestamp_str: Timestamp string from Android logcat
        now: Reference time for year inference (defaults to ``datetime.now()``)

    Returns:
        Parsed datetime object, or None if parsing fails

    Examples:
        >>> parse_android_timestamp("2024-10-24 04:15:36.123")
        datetime.datetime(2024, 10, 24, 4, 15, 36, 123000)

        >>> parse_android_timestamp("12-31 23:59:59.000", now=datetime(2025, 1, 1))
        datetime.datetime(2024, 12, 31, 23, 59, 59)
    """
    if not timestamp_str:
        return None
    text = timestamp_str.strip()

    for fmt in _YEAR_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    reference = now or datetime.now()
    for fmt in _YEARLESS_FORMATS:
        # Newest candidate first: next year covers a device clock that is
        # slightly ahead across New Year; previous year covers December logs
        # read in January.
        for year in (reference.year + 1, reference.year, reference.year - 1):
            try:
                parsed = datetime.strptime(f"{year}-{text}", f"%Y-{fmt}")
            except ValueError:
                continue
            if parsed <= reference + _FUTURE_TOLERANCE:
                return parsed

    return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "2h 30m" or "45s"
        
    Examples:
        >>> format_duration(7200)
        '2h 0m'
        
        >>> format_duration(45)
        '45s'
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"


def get_time_difference_seconds(time1: datetime, time2: datetime) -> float:
    """
    Get time difference between two datetime objects in seconds.
    
    Args:
        time1: First datetime
        time2: Second datetime
        
    Returns:
        Absolute difference in seconds
    """
    return abs((time1 - time2).total_seconds())


def is_within_time_window(timestamp: datetime, window_minutes: int) -> bool:
    """
    Check if timestamp is within specified time window from now.
    
    Args:
        timestamp: Timestamp to check
        window_minutes: Time window in minutes
        
    Returns:
        True if timestamp is within the window
    """
    now = datetime.now()
    diff_minutes = abs((now - timestamp).total_seconds() / 60)
    return diff_minutes <= window_minutes
