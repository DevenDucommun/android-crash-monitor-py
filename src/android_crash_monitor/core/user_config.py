"""User-facing TOML configuration for Android Crash Monitor."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from platformdirs import user_config_dir


CONFIG_DIR = Path(user_config_dir("acm", ensure_exists=True))
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "severity_threshold": 5,
    "retention_days": 30,
    "notification_enabled": False,
    "webhook_url": "",
    "device_aliases": {},
}

DEFAULT_TOML = """\
# Android Crash Monitor Configuration

[general]
# Minimum severity level to record (0-10)
severity_threshold = 5

# Days to retain crash history before pruning
retention_days = 30

[notifications]
# Enable webhook notifications for critical crashes
enabled = false

# Webhook URL (Slack, Discord, or generic HTTP POST)
webhook_url = \"\"

[devices]
# Device aliases: serial = \"friendly name\"
# Example:
# \"1C311FDF6000FS\" = \"Pixel 6\"
"""


class UserConfig:
    def __init__(self, config_path: Optional[Path] = None):
        self.path = config_path or CONFIG_PATH
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        self._data = dict(DEFAULTS)
        if not self.path.exists():
            return
        content = self.path.read_text()
        parsed = _parse_toml(content)
        general = parsed.get("general", {})
        notif = parsed.get("notifications", {})
        devices = parsed.get("devices", {})

        if "severity_threshold" in general:
            self._data["severity_threshold"] = int(general["severity_threshold"])
        if "retention_days" in general:
            self._data["retention_days"] = int(general["retention_days"])
        if "enabled" in notif:
            self._data["notification_enabled"] = notif["enabled"]
        if "webhook_url" in notif:
            self._data["webhook_url"] = notif["webhook_url"]
        if devices:
            self._data["device_aliases"] = devices

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Android Crash Monitor Configuration\n",
            "[general]",
            f"severity_threshold = {self._data['severity_threshold']}",
            f"retention_days = {self._data['retention_days']}",
            "",
            "[notifications]",
            f"enabled = {'true' if self._data['notification_enabled'] else 'false'}",
            f'webhook_url = \"{self._data["webhook_url"]}\"',
            "",
            "[devices]",
        ]
        for serial, name in self._data.get("device_aliases", {}).items():
            lines.append(f'\"{serial}\" = \"{name}\"')
        self.path.write_text("\n".join(lines) + "\n")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def init_default(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(DEFAULT_TOML)

    @property
    def severity_threshold(self) -> int:
        return self._data["severity_threshold"]

    @property
    def retention_days(self) -> int:
        return self._data["retention_days"]

    @property
    def webhook_url(self) -> str:
        return self._data["webhook_url"]

    @property
    def notification_enabled(self) -> bool:
        return self._data["notification_enabled"]

    @property
    def device_aliases(self) -> Dict[str, str]:
        return self._data.get("device_aliases", {})


def _parse_toml(content: str) -> Dict[str, Any]:
    """Parse TOML using stdlib tomllib (3.11+) or minimal fallback."""
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(content)
    return _parse_toml_fallback(content)


def _parse_toml_fallback(content: str) -> Dict[str, Any]:
    """Minimal TOML parser for 3.9/3.10."""
    result: Dict[str, Any] = {}
    current_table = result

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            table_name = line[1:-1].strip()
            result[table_name] = {}
            current_table = result[table_name]
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip().strip('"')
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                current_table[key] = value[1:-1]
            elif value == "true":
                current_table[key] = True
            elif value == "false":
                current_table[key] = False
            elif "." in value:
                try:
                    current_table[key] = float(value)
                except ValueError:
                    current_table[key] = value
            else:
                try:
                    current_table[key] = int(value)
                except ValueError:
                    current_table[key] = value
    return result
