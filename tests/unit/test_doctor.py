"""Tests for `acm doctor` environment checks."""

import subprocess
from types import SimpleNamespace

import pytest

from android_crash_monitor.core import doctor
from android_crash_monitor.core.doctor import Status

pytestmark = pytest.mark.unit


@pytest.fixture
def no_adb(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)


@pytest.fixture
def fake_adb(monkeypatch):
    """Pretend adb is installed; tests set `outputs[subcommand]` to a result or exception."""
    outputs = {}
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/adb" if name == "adb" else None)

    def run(cmd, **kwargs):
        result = outputs[cmd[1]]
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(doctor.subprocess, "run", run)
    return outputs


def completed(stdout="", returncode=0):
    return SimpleNamespace(stdout=stdout, returncode=returncode)


def test_python_check_passes_on_supported_interpreter():
    assert doctor._check_python().status is Status.PASS


def test_python_check_fails_below_310(monkeypatch):
    # Needs both tuple comparison and .major/.minor/.micro, like sys.version_info.
    version = type("V", (tuple,), {"major": 3, "minor": 9, "micro": 18})((3, 9, 18))
    monkeypatch.setattr(doctor.sys, "version_info", version)
    check = doctor._check_python()
    assert check.status is Status.FAIL
    assert "3.10+" in check.message


def test_adb_missing(no_adb):
    assert doctor._check_adb_installed().status is Status.FAIL
    assert doctor._check_adb_server().status is Status.WARN
    assert doctor._check_device().status is Status.WARN


def test_adb_installed_and_server_ok(fake_adb):
    fake_adb["version"] = completed("Android Debug Bridge version 1.0.41\nVersion 35.0.2\n")

    assert doctor._check_adb_installed().status is Status.PASS
    server = doctor._check_adb_server()
    assert server.status is Status.PASS
    assert server.message == "Android Debug Bridge version 1.0.41"


@pytest.mark.parametrize("result", [completed(returncode=1), subprocess.TimeoutExpired("adb", 5)])
def test_adb_server_not_responding(fake_adb, result):
    fake_adb["version"] = result
    check = doctor._check_adb_server()
    assert check.status is Status.FAIL
    assert check.fix == "Run: adb start-server"


@pytest.mark.parametrize(
    "stdout, status, message",
    [
        ("List of devices attached\nemulator-5554\tdevice\n\n", Status.PASS, "1 device(s) ready"),
        ("List of devices attached\nA\tdevice\nB\tdevice\n", Status.PASS, "2 device(s) ready"),
        ("List of devices attached\nR58M\tunauthorized\n", Status.WARN, "device found but unauthorized"),
        ("List of devices attached\n\n", Status.FAIL, "no devices found"),
        ("List of devices attached\nR58M\toffline\n", Status.FAIL, "no devices found"),
    ],
)
def test_device_check_parses_adb_devices(fake_adb, stdout, status, message):
    fake_adb["devices"] = completed(stdout)
    check = doctor._check_device()
    assert (check.status, check.message) == (status, message)


def test_device_check_timeout(fake_adb):
    fake_adb["devices"] = subprocess.TimeoutExpired("adb", 5)
    assert doctor._check_device().status is Status.FAIL


def test_data_dir_writable(monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "user_data_dir", lambda app: str(tmp_path / "data"))
    check = doctor._check_data_dir()
    assert check.status is Status.PASS
    assert not (tmp_path / "data" / ".write_test").exists()


def test_data_dir_not_writable(monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    monkeypatch.setattr(doctor, "user_data_dir", lambda app: str(blocker / "data"))
    assert doctor._check_data_dir().status is Status.FAIL


def test_config_present_and_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "user_config_dir", lambda app: str(tmp_path))
    assert doctor._check_config().status is Status.WARN

    (tmp_path / "config.toml").write_text("")
    assert doctor._check_config().status is Status.PASS


def test_run_checks_returns_all_checks(no_adb, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "user_data_dir", lambda app: str(tmp_path / "data"))
    monkeypatch.setattr(doctor, "user_config_dir", lambda app: str(tmp_path / "cfg"))

    names = [check.name for check in doctor.run_checks()]

    assert names == [
        "Python version", "ADB installed", "ADB server",
        "Device connected", "Data directory", "Config file",
    ]


def _invoke_doctor(monkeypatch, tmp_path):
    from click.testing import CliRunner

    from android_crash_monitor import cli as cli_module

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(doctor, "user_data_dir", lambda app: str(tmp_path / "data"))
    monkeypatch.setattr(doctor, "user_config_dir", lambda app: str(tmp_path / "cfg"))
    return CliRunner().invoke(cli_module.cli, ["doctor"])


def test_acm_doctor_exits_1_when_a_check_fails(no_adb, monkeypatch, tmp_path):
    result = _invoke_doctor(monkeypatch, tmp_path)

    assert result.exit_code == 1, result.output
    assert "issue(s) need attention" in result.output


def test_acm_doctor_exits_0_when_only_warnings(fake_adb, monkeypatch, tmp_path):
    # Config file missing is a WARN, everything else passes.
    fake_adb["version"] = completed("Android Debug Bridge version 1.0.41\n")
    fake_adb["devices"] = completed("List of devices attached\nemulator-5554\tdevice\n")

    result = _invoke_doctor(monkeypatch, tmp_path)

    assert result.exit_code == 0, result.output
    assert "All checks passed" in result.output
