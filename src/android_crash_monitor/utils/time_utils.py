#!/usr/bin/env python3
"""
Time Utilities

Centralized timestamp parsing and manipulation for Android crash monitoring.
"""

from datetime import datetime
from typing import Optional


def parse_android_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse Android logcat timestamp with robust format handling.
    
    Handles multiple timestamp formats commonly found in Android logs:
    - With year: YYYY-MM-DD HH:MM:SS.fff
    - Without year: MM-DD HH:MM:SS.fff (assumes current year)
    - Without microseconds: MM-DD HH:MM:SS
    
    Args:
        timestamp_str: Timestamp string from Android logcat
        
    Returns:
        Parsed datetime object, or None if parsing fails
        
    Examples:
        >>> parse_android_timestamp("2024-10-24 04:15:36.123")
        datetime(2024, 10, 24, 4, 15, 36, 123000)
        
        >>> parse_android_timestamp("10-24 04:15:36.123")  # Assumes current year
        datetime(2024, 10, 24, 4, 15, 36, 123000)
    """
    if not timestamp_str:
        return None
    
    # Try different timestamp formats (prefer formats with year)
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',  # With year and microseconds
        '%Y-%m-%d %H:%M:%S',      # With year, no microseconds
        '%m-%d %H:%M:%S.%f',      # Without year, with microseconds
        '%m-%d %H:%M:%S'          # Without year, no microseconds
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(timestamp_str.strip(), fmt)
            # For formats without year, assume current year
            if '%Y' not in fmt:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    
    # If all formats fail, return None
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
