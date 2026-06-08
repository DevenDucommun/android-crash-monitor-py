"""Unit tests for CrashDatabase."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from android_crash_monitor.core.database import CrashDatabase


@pytest.fixture
def db(tmp_path):
    return CrashDatabase(db_path=tmp_path / "test.db")


class TestCrashDatabase:
    def test_save_and_query(self, db):
        crash = {
            "timestamp": "2024-01-15T10:30:00",
            "app_name": "TestApp",
            "description": "OutOfMemoryError",
            "severity": 8,
            "crash_type": "runtime_error",
            "device_serial": "ABC123",
        }
        row_id = db.save_crash(crash)
        assert row_id == 1

        results = db.query_crashes()
        assert len(results) == 1
        assert results[0]["app_name"] == "TestApp"
        assert results[0]["severity"] == 8

    def test_query_filter_by_app(self, db):
        db.save_crash({"app_name": "AppA", "timestamp": "2024-01-15T10:00:00"})
        db.save_crash({"app_name": "AppB", "timestamp": "2024-01-15T11:00:00"})

        results = db.query_crashes(app="AppA")
        assert len(results) == 1
        assert results[0]["app_name"] == "AppA"

    def test_query_filter_by_severity(self, db):
        db.save_crash({"severity": 3, "timestamp": "2024-01-15T10:00:00"})
        db.save_crash({"severity": 8, "timestamp": "2024-01-15T11:00:00"})

        results = db.query_crashes(severity=5)
        assert len(results) == 1
        assert results[0]["severity"] == 8

    def test_query_filter_by_since(self, db):
        old = (datetime.now() - timedelta(days=5)).isoformat()
        new = datetime.now().isoformat()

        db.save_crash({"timestamp": old, "app_name": "Old"})
        db.save_crash({"timestamp": new, "app_name": "New"})

        since = (datetime.now() - timedelta(days=1)).isoformat()
        results = db.query_crashes(since=since)
        assert len(results) == 1
        assert results[0]["app_name"] == "New"

    def test_query_limit(self, db):
        for i in range(10):
            db.save_crash({"timestamp": f"2024-01-15T{i:02d}:00:00", "app_name": f"App{i}"})

        results = db.query_crashes(limit=3)
        assert len(results) == 3

    def test_get_stats(self, db):
        for i in range(5):
            db.save_crash({
                "timestamp": datetime.now().isoformat(),
                "app_name": "FrequentApp",
                "severity": 7,
            })
        db.save_crash({
            "timestamp": datetime.now().isoformat(),
            "app_name": "RareApp",
            "severity": 3,
        })

        stats = db.get_stats()
        assert stats["total"] == 6
        assert stats["last_24h"] == 6
        assert stats["top_apps"][0] == ("FrequentApp", 5)

    def test_prune(self, db):
        old = (datetime.now() - timedelta(days=60)).isoformat()
        new = datetime.now().isoformat()

        db.save_crash({"timestamp": old, "app_name": "Old"})
        db.save_crash({"timestamp": new, "app_name": "New"})

        pruned = db.prune(older_than_days=30)
        assert pruned == 1

        results = db.query_crashes()
        assert len(results) == 1
        assert results[0]["app_name"] == "New"

    def test_raw_data_stored(self, db):
        crash = {"timestamp": "2024-01-15T10:00:00", "app_name": "App", "extra_field": "preserved"}
        db.save_crash(crash)

        results = db.query_crashes()
        import json
        raw = json.loads(results[0]["raw_data"])
        assert raw["extra_field"] == "preserved"
