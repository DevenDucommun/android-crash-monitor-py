"""Tests for logcat timestamp parsing and year inference."""

import warnings
from datetime import datetime

import pytest

from android_crash_monitor.utils.time_utils import parse_android_timestamp

pytestmark = pytest.mark.unit


def test_full_year_formats():
    assert parse_android_timestamp("2024-10-24 04:15:36.123") == datetime(
        2024, 10, 24, 4, 15, 36, 123000
    )
    assert parse_android_timestamp("2024-10-24 04:15:36") == datetime(2024, 10, 24, 4, 15, 36)


def test_yearless_uses_reference_year():
    now = datetime(2026, 11, 2, 12, 0)
    assert parse_android_timestamp("10-06 22:36:33.972", now=now) == datetime(
        2026, 10, 6, 22, 36, 33, 972000
    )
    assert parse_android_timestamp("11-02 11:59:59", now=now) == datetime(2026, 11, 2, 11, 59, 59)


def test_december_logs_read_in_january_roll_back_a_year():
    now = datetime(2027, 1, 1, 0, 5)
    assert parse_android_timestamp("12-31 23:59:59.000", now=now) == datetime(
        2026, 12, 31, 23, 59, 59
    )


def test_small_device_clock_skew_stays_in_current_year():
    # Device clock 40 minutes ahead of the host, across New Year.
    assert parse_android_timestamp(
        "01-01 00:30:00", now=datetime(2026, 12, 31, 23, 50)
    ) == datetime(2027, 1, 1, 0, 30)
    # Same calendar day, slightly ahead.
    assert parse_android_timestamp("12-31 23:30:00", now=datetime(2026, 12, 31, 23, 0)) == datetime(
        2026, 12, 31, 23, 30
    )


def test_january_log_read_in_late_december_is_this_year():
    assert parse_android_timestamp("01-15 09:00:00", now=datetime(2026, 12, 20)) == datetime(
        2026, 1, 15, 9, 0
    )


def test_leap_day_parses_in_leap_year():
    assert parse_android_timestamp("02-29 13:45:01.123", now=datetime(2028, 3, 1)) == datetime(
        2028, 2, 29, 13, 45, 1, 123000
    )


def test_leap_day_after_year_rollover():
    # Read on Jan 1 2029: Feb 29 can only be from 2028.
    assert parse_android_timestamp("02-29 13:45:01", now=datetime(2029, 1, 1)) == datetime(
        2028, 2, 29, 13, 45, 1
    )


def test_no_strptime_deprecation_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        parse_android_timestamp("02-29 13:45:01.123", now=datetime(2028, 3, 1))
        parse_android_timestamp("10-06 22:36:33", now=datetime(2026, 11, 2))


@pytest.mark.parametrize("bad", ["", "   ", "not a timestamp", "13-45 99:99:99", "02-30 10:00:00"])
def test_invalid_input_returns_none(bad):
    assert parse_android_timestamp(bad, now=datetime(2026, 11, 2)) is None


def test_whitespace_is_stripped():
    assert parse_android_timestamp("  2024-10-24 04:15:36  ") == datetime(2024, 10, 24, 4, 15, 36)
