"""Unit tests for UserConfig."""

import pytest
from pathlib import Path

from android_crash_monitor.core.user_config import UserConfig, DEFAULT_TOML


@pytest.fixture
def config(tmp_path):
    return UserConfig(config_path=tmp_path / "config.toml")


class TestUserConfig:
    def test_defaults_when_no_file(self, config):
        assert config.severity_threshold == 5
        assert config.retention_days == 30
        assert config.notification_enabled is False
        assert config.webhook_url == ""
        assert config.device_aliases == {}

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "config.toml"
        cfg = UserConfig(config_path=path)
        cfg.set("severity_threshold", 8)
        cfg.set("webhook_url", "https://hooks.slack.com/test")
        cfg.save()

        cfg2 = UserConfig(config_path=path)
        assert cfg2.severity_threshold == 8
        assert cfg2.webhook_url == "https://hooks.slack.com/test"

    def test_init_default_creates_file(self, tmp_path):
        path = tmp_path / "config.toml"
        cfg = UserConfig(config_path=path)
        cfg.init_default()
        assert path.exists()
        content = path.read_text()
        assert "severity_threshold" in content

    def test_parse_toml_with_devices(self, tmp_path):
        path = tmp_path / "config.toml"
        path.write_text('''
[general]
severity_threshold = 7
retention_days = 14

[notifications]
enabled = true
webhook_url = "https://discord.com/webhook"

[devices]
"ABC123" = "Pixel 6"
"DEF456" = "Galaxy S23"
''')
        cfg = UserConfig(config_path=path)
        assert cfg.severity_threshold == 7
        assert cfg.retention_days == 14
        assert cfg.notification_enabled is True
        assert cfg.device_aliases.get("ABC123") == "Pixel 6"
