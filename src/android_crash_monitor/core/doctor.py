"""Environment diagnostics for Android Crash Monitor."""

import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

from platformdirs import user_config_dir, user_data_dir


class Status(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class Check:
    name: str
    status: Status
    message: str
    fix: str = ""


def run_checks() -> List[Check]:
    checks = [
        _check_python(),
        _check_adb_installed(),
        _check_adb_server(),
        _check_device(),
        _check_data_dir(),
        _check_config(),
    ]
    return checks


def _check_python() -> Check:
    v = sys.version_info
    if v >= (3, 9):
        return Check("Python version", Status.PASS, f"{v.major}.{v.minor}.{v.micro}")
    return Check(
        "Python version",
        Status.FAIL,
        f"{v.major}.{v.minor} (need 3.9+)",
        fix="Install Python 3.9+ from python.org or your package manager",
    )


def _check_adb_installed() -> Check:
    path = shutil.which("adb")
    if path:
        return Check("ADB installed", Status.PASS, path)
    return Check(
        "ADB installed",
        Status.FAIL,
        "adb not found in PATH",
        fix="Install Android SDK Platform-Tools: https://developer.android.com/tools/releases/platform-tools",
    )


def _check_adb_server() -> Check:
    if not shutil.which("adb"):
        return Check("ADB server", Status.WARN, "skipped (adb not installed)")
    try:
        result = subprocess.run(
            ["adb", "version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            return Check("ADB server", Status.PASS, version)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return Check(
        "ADB server",
        Status.FAIL,
        "adb server not responding",
        fix="Run: adb start-server",
    )


def _check_device() -> Check:
    if not shutil.which("adb"):
        return Check("Device connected", Status.WARN, "skipped (adb not installed)")
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=5
        )
        lines = [l for l in result.stdout.strip().split("\n")[1:] if l.strip()]
        devices = [l for l in lines if "device" in l and "unauthorized" not in l]
        unauthorized = [l for l in lines if "unauthorized" in l]

        if devices:
            return Check("Device connected", Status.PASS, f"{len(devices)} device(s) ready")
        if unauthorized:
            return Check(
                "Device connected",
                Status.WARN,
                "device found but unauthorized",
                fix="Accept the USB debugging prompt on your device",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return Check(
        "Device connected",
        Status.FAIL,
        "no devices found",
        fix="Connect a device via USB with USB debugging enabled",
    )


def _check_data_dir() -> Check:
    data_dir = Path(user_data_dir("acm"))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        test_file = data_dir / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        return Check("Data directory", Status.PASS, str(data_dir))
    except OSError:
        return Check(
            "Data directory",
            Status.FAIL,
            f"cannot write to {data_dir}",
            fix=f"Fix permissions: chmod 755 {data_dir}",
        )


def _check_config() -> Check:
    config_dir = Path(user_config_dir("acm"))
    config_file = config_dir / "config.toml"
    if config_file.exists():
        return Check("Config file", Status.PASS, str(config_file))
    return Check(
        "Config file",
        Status.WARN,
        "not found (using defaults)",
        fix=f"Create {config_file} or run: acm config init",
    )
