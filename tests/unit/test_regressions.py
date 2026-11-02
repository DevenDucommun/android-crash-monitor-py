"""Regression tests for runtime bugs surfaced by mypy."""

import json

import pytest

from android_crash_monitor.analysis.enhanced_pattern_detector import (
    EnhancedPattern,
    PatternSeverity,
    PatternType,
    StatisticalPatternDetector,
)
from android_crash_monitor.core.config import Config, ConfigManager, MonitoringConfig
from android_crash_monitor.core.system import SystemDetector

pytestmark = pytest.mark.unit


def _pattern(pattern_id: str, severity: PatternSeverity) -> EnhancedPattern:
    crashes = [{"timestamp": "2026-11-02 10:00:05"}, {"timestamp": "2026-11-02 10:01:05"}]
    return EnhancedPattern(
        pattern_id=pattern_id,
        pattern_type=PatternType.SIMPLE,
        name=pattern_id,
        description=pattern_id,
        frequency=len(crashes),
        confidence_score=0.8,
        correlation_strength=0.5,
        temporal_clustering_score=0.5,
        severity=severity,
        affected_crashes=crashes,
    )


def test_cascade_detection_with_overlapping_patterns_does_not_crash():
    # max() on two PatternSeverity members raised TypeError (Enum is not orderable).
    detector = StatisticalPatternDetector()
    low = _pattern("db_errors", PatternSeverity.LOW)
    high = _pattern("anr", PatternSeverity.HIGH)

    cascades = detector._detect_cascade_patterns([low, high], low.affected_crashes)

    assert cascades
    assert cascades[0].severity == PatternSeverity.HIGH


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "android_crash_monitor.core.config.user_config_dir", lambda *a, **k: str(tmp_path / "cfg")
    )
    monkeypatch.setattr(
        "android_crash_monitor.core.config.user_data_dir", lambda *a, **k: str(tmp_path / "data")
    )
    return tmp_path


def test_config_save_writes_profile(config_home):
    # A second save_profile definition with swapped arguments shadowed this one,
    # so Config.save() raised TypeError.
    target = config_home / "work.json"
    Config(profile_name="work").save(target)

    assert json.loads(target.read_text())["profile_name"] == "work"


def test_copy_profile(config_home):
    manager = ConfigManager()
    Config(profile_name="source").save(manager.get_config_dir() / "source.json")

    manager.copy_profile("source", "copy")

    assert (manager.get_config_dir() / "copy.json").exists()


def test_save_monitoring_profile(config_home):
    manager = ConfigManager()
    manager.save_monitoring_profile("setup", MonitoringConfig())

    assert (manager.get_config_dir() / "setup.json").exists()


def test_system_info_dict_uses_real_fields():
    # Referenced SystemInfo.os_name / .architecture / .has_download_tools, which do not exist.
    info = SystemDetector().get_system_info_dict()

    assert info["os_name"]
    assert info["architecture"]
    assert isinstance(info["has_download_tools"], bool)
