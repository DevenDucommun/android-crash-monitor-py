#!/usr/bin/env python3
"""
Crash Processing Utilities

Common functions for processing crash data across analyzers.
"""

from typing import Dict, List, Optional


def extract_crash_text(crash: Dict) -> str:
    """
    Extract searchable text from crash data.
    
    Combines various text fields from crash data into a single searchable string.
    
    Args:
        crash: Crash data dictionary
        
    Returns:
        Combined text from all relevant fields
    """
    text_parts = [
        crash.get('title', ''),
        crash.get('description', ''),
        crash.get('app_name', ''),
        crash.get('package_name', ''),
        crash.get('stack_trace', ''),
        crash.get('exception_type', ''),
        ' '.join([log.get('message', '') for log in crash.get('related_logs', [])])
    ]
    return ' '.join(text_parts).lower()


def get_crash_severity(crash: Dict) -> str:
    """
    Determine crash severity from crash data.
    
    Args:
        crash: Crash data dictionary
        
    Returns:
        Severity level: 'critical', 'high', 'medium', or 'low'
    """
    # Check for explicit severity
    if 'severity' in crash:
        return crash['severity'].lower()
    
    # Infer from exception type
    exception_type = crash.get('exception_type', '').lower()
    critical_exceptions = ['outofmemoryerror', 'stackoverflowerror', 'virtualmachineerror']
    high_exceptions = ['nullpointerexception', 'illegalstateexception', 'securityexception']
    
    if any(exc in exception_type for exc in critical_exceptions):
        return 'critical'
    elif any(exc in exception_type for exc in high_exceptions):
        return 'high'
    elif 'error' in exception_type:
        return 'medium'
    else:
        return 'low'


def normalize_package_name(package: str) -> str:
    """
    Normalize package name for comparison.
    
    Args:
        package: Package name string
        
    Returns:
        Normalized package name
    """
    if not package:
        return ''
    return package.strip().lower()


def is_system_crash(crash: Dict) -> bool:
    """
    Check if crash is from a system component.
    
    Args:
        crash: Crash data dictionary
        
    Returns:
        True if crash is from system component
    """
    package = crash.get('package_name', '').lower()
    system_packages = ['android', 'com.android', 'system', 'framework']
    return any(pkg in package for pkg in system_packages)


def group_crashes_by_exception(crashes: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group crashes by exception type.
    
    Args:
        crashes: List of crash dictionaries
        
    Returns:
        Dictionary mapping exception types to lists of crashes
    """
    grouped = {}
    for crash in crashes:
        exc_type = crash.get('exception_type', 'Unknown')
        if exc_type not in grouped:
            grouped[exc_type] = []
        grouped[exc_type].append(crash)
    return grouped


def group_crashes_by_package(crashes: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group crashes by package name.
    
    Args:
        crashes: List of crash dictionaries
        
    Returns:
        Dictionary mapping package names to lists of crashes
    """
    grouped = {}
    for crash in crashes:
        package = crash.get('package_name', 'Unknown')
        if package not in grouped:
            grouped[package] = []
        grouped[package].append(crash)
    return grouped


def calculate_crash_frequency(crashes: List[Dict], time_window_minutes: int = 60) -> float:
    """
    Calculate crash frequency (crashes per hour).
    
    Args:
        crashes: List of crash dictionaries with timestamps
        time_window_minutes: Time window to consider
        
    Returns:
        Crashes per hour rate
    """
    if not crashes or time_window_minutes <= 0:
        return 0.0
    
    # Convert to crashes per hour
    crashes_per_minute = len(crashes) / time_window_minutes
    return crashes_per_minute * 60


def find_common_stack_frames(crashes: List[Dict], min_occurrences: int = 2) -> List[str]:
    """
    Find stack frames that appear in multiple crashes.
    
    Args:
        crashes: List of crash dictionaries
        min_occurrences: Minimum number of occurrences to be considered common
        
    Returns:
        List of common stack frames
    """
    from collections import Counter
    
    all_frames = []
    for crash in crashes:
        stack_trace = crash.get('stack_trace', '')
        # Simple split by lines - could be more sophisticated
        frames = [line.strip() for line in stack_trace.split('\n') if line.strip()]
        all_frames.extend(frames)
    
    frame_counts = Counter(all_frames)
    return [frame for frame, count in frame_counts.items() if count >= min_occurrences]


def get_crash_summary(crash: Dict) -> str:
    """
    Generate a one-line summary of a crash.
    
    Args:
        crash: Crash data dictionary
        
    Returns:
        Summary string
    """
    exception = crash.get('exception_type', 'Unknown')
    package = crash.get('package_name', 'Unknown')
    timestamp = crash.get('timestamp', 'Unknown time')
    
    return f"{exception} in {package} at {timestamp}"
