"""Tests for crash exporters, crash-file loading and `acm logs --export`."""

import csv
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from android_crash_monitor.core.monitor import (
    CrashEvent,
    CrashType,
    LogEntry,
    LogLevel,
    MonitoringStats,
)
from android_crash_monitor.exporters import (
    ExportData,
    ExportError,
    MultiFormatExporter,
    get_available_formats,
    get_exporter,
)
from android_crash_monitor.exporters.base import (
    find_crash_files,
    load_crashes_from_files,
    load_session_stats,
)

pytestmark = pytest.mark.unit


def make_log(message: str = "FATAL EXCEPTION: main") -> LogEntry:
    return LogEntry(
        timestamp="11-02 10:00:00.000",
        level=LogLevel.ERROR,
        tag="AndroidRuntime",
        pid=1234,
        tid=1234,
        message=message,
        device_serial="emulator-5554",
        raw_line=f"11-02 10:00:00.000 1234 1234 E AndroidRuntime: {message}",
    )


def make_crash(title: str = "NullPointerException in MainActivity", **overrides) -> CrashEvent:
    fields = dict(
        timestamp="11-02 10:00:00.000",
        crash_type=CrashType.CRASH,
        app_package="com.example.app",
        app_name="Example",
        severity=8,
        title=title,
        description="java.lang.NullPointerException: Attempt to invoke virtual method",
        stack_trace=["at com.example.app.MainActivity.onCreate(MainActivity.java:42)"],
        related_logs=[make_log()],
        device_serial="emulator-5554",
        device_model="Pixel 8",
        session_id="session_1",
        detection_patterns=["FATAL EXCEPTION"],
        first_seen="11-02 10:00:00.000",
    )
    fields.update(overrides)
    return CrashEvent(**fields)


def make_stats() -> MonitoringStats:
    return MonitoringStats(
        session_id="session_1",
        start_time="2026-11-02T10:00:00",
        end_time="2026-11-02T10:05:00",
        uptime_seconds=300.0,
        devices_monitored=["emulator-5554"],
        reconnection_count=0,
        total_logs_processed=1000,
        logs_per_second=3.3,
        total_crashes=2,
        crashes_by_type={"crash": 1, "anr": 1},
        crashes_by_app={"com.example.app": 2},
        memory_usage_mb=42.0,
        cpu_usage_percent=1.5,
    )


@pytest.fixture
def export_data() -> ExportData:
    data = ExportData()
    data.add_crashes([
        make_crash(),
        make_crash("ANR in Example", crash_type=CrashType.ANR, severity=6, related_logs=[]),
    ])
    data.set_stats(make_stats())
    data.add_logs([make_log(), make_log("second line")])
    data.add_metadata("source", "tests")
    return data


# --- every registered format -------------------------------------------------

@pytest.mark.parametrize("fmt", get_available_formats())
def test_every_format_exports_a_non_empty_file(fmt, export_data, tmp_path):
    exporter = get_exporter(fmt)
    out = tmp_path / exporter.generate_filename("report")

    exporter.export(export_data, out)

    assert out.is_file()
    assert out.stat().st_size > 0
    assert out.suffix == f".{exporter.file_extension}"


@pytest.mark.parametrize("fmt", [f for f in get_available_formats() if f != "logs-csv"])
def test_every_format_handles_empty_data(fmt, tmp_path):
    out = tmp_path / f"empty.{fmt}"
    get_exporter(fmt).export(ExportData(), out)
    assert out.is_file()


def test_logs_csv_refuses_empty_logs(tmp_path):
    with pytest.raises(ExportError, match="No log entries"):
        get_exporter("logs-csv").export(ExportData(), tmp_path / "logs.csv")


def test_get_exporter_is_case_insensitive():
    assert get_exporter("JSON").format_name == get_exporter("json").format_name


def test_get_exporter_rejects_unknown_format():
    with pytest.raises(ExportError, match="Unsupported export format"):
        get_exporter("pdf")


def test_export_to_directory_path_fails(export_data, tmp_path):
    with pytest.raises(ExportError, match="directory"):
        get_exporter("json").export(export_data, tmp_path)


def test_export_creates_missing_parent_directories(export_data, tmp_path):
    out = tmp_path / "nested" / "dir" / "report.json"
    get_exporter("json").export(export_data, out)
    assert out.is_file()


# --- format content ------------------------------------------------------------

def test_json_contains_crashes_stats_and_metadata(export_data, tmp_path):
    out = tmp_path / "report.json"
    get_exporter("json").export(export_data, out)
    doc = json.loads(out.read_text())

    assert len(doc["crashes"]) == 2
    assert doc["crashes"][0]["crash_type"] == "crash"
    assert doc["crashes"][1]["crash_type"] == "anr"
    assert doc["statistics"]["total_crashes"] == 2
    assert doc["metadata"]["crash_count"] == 2
    assert doc["metadata"]["source"] == "tests"
    assert "logs" not in doc


def test_detailed_json_includes_raw_logs(export_data, tmp_path):
    out = tmp_path / "report.json"
    get_exporter("detailed-json").export(export_data, out)
    doc = json.loads(out.read_text())

    assert [log["message"] for log in doc["logs"]] == ["FATAL EXCEPTION: main", "second line"]


def test_compact_json_is_single_line(export_data, tmp_path):
    out = tmp_path / "report.json"
    get_exporter("compact-json").export(export_data, out)
    assert len(out.read_text().strip().splitlines()) == 1


def test_csv_has_header_and_one_row_per_crash(export_data, tmp_path):
    out = tmp_path / "report.csv"
    get_exporter("csv").export(export_data, out)
    rows = list(csv.reader(out.open(newline="", encoding="utf-8")))

    assert rows[0][:4] == ["Timestamp", "Crash Type", "Severity", "Title"]
    assert len(rows) == 3
    assert rows[1][3] == "NullPointerException in MainActivity"


def test_csv_quotes_commas_and_newlines(tmp_path):
    data = ExportData()
    data.add_crash(make_crash('Crash, with "quotes"', description="line one\nline two"))
    out = tmp_path / "report.csv"
    get_exporter("csv").export(data, out)
    rows = list(csv.reader(out.open(newline="", encoding="utf-8")))

    assert len(rows) == 2
    assert rows[1][3] == 'Crash, with "quotes"'


def test_logs_csv_exports_log_entries(export_data, tmp_path):
    out = tmp_path / "logs.csv"
    get_exporter("logs-csv").export(export_data, out)
    rows = list(csv.reader(out.open(newline="", encoding="utf-8")))

    assert len(rows) == 3
    assert any("second line" in cell for cell in rows[2])


def test_html_escapes_crash_text(tmp_path):
    data = ExportData()
    data.add_crash(make_crash(
        "<script>alert(1)</script>",
        description='<img src=x onerror="alert(1)">',
        stack_trace=["at <evil>"],
    ))
    out = tmp_path / "report.html"
    get_exporter("html").export(data, out)
    page = out.read_text(encoding="utf-8")

    assert "<script>alert(1)</script>" not in page
    assert "<img src=x" not in page
    assert "&lt;script&gt;" in page


@pytest.mark.parametrize("fmt", ["txt", "md"])
def test_text_formats_mention_each_crash(fmt, export_data, tmp_path):
    out = tmp_path / f"report.{fmt}"
    get_exporter(fmt).export(export_data, out)
    text = out.read_text(encoding="utf-8")

    assert "NullPointerException in MainActivity" in text
    assert "ANR in Example" in text


def test_multi_format_exporter_writes_each_format(export_data, tmp_path):
    multi = MultiFormatExporter()
    for fmt in ("json", "csv", "html"):
        multi.add_format(fmt, get_exporter(fmt))

    results = multi.export_all(export_data, tmp_path, base_name="bundle")

    assert set(results) == {"json", "csv", "html"}
    assert all(path.is_file() for path in results.values())


# --- loading saved crash files -----------------------------------------------

def test_crash_event_round_trips_through_dict():
    crash = make_crash()
    assert CrashEvent.from_dict(crash.to_dict()) == crash


def test_crash_event_from_partial_or_unknown_dict():
    crash = CrashEvent.from_dict({"title": "old file", "crash_type": "something_new"})

    assert crash.title == "old file"
    assert crash.crash_type is CrashType.UNKNOWN
    assert crash.related_logs == []
    assert crash.stack_trace == []


def test_load_crashes_from_files_returns_crash_events(tmp_path):
    for i, crash in enumerate([make_crash(), make_crash("second")]):
        (tmp_path / f"crash_{i}.json").write_text(json.dumps(crash.to_dict()))

    crashes = load_crashes_from_files(sorted(find_crash_files(tmp_path)))

    assert [c.title for c in crashes] == ["NullPointerException in MainActivity", "second"]
    assert all(isinstance(c, CrashEvent) for c in crashes)


def test_load_crashes_from_corrupt_file_raises_export_error(tmp_path):
    bad = tmp_path / "crash_bad.json"
    bad.write_text("{not json")
    with pytest.raises(ExportError, match="crash_bad.json"):
        load_crashes_from_files([bad])


def test_find_crash_files_on_missing_directory(tmp_path):
    assert find_crash_files(tmp_path / "missing") == []


def test_load_session_stats_round_trip(tmp_path):
    from dataclasses import asdict

    stats_file = tmp_path / "stats.json"
    stats_file.write_text(json.dumps(asdict(make_stats())))

    assert load_session_stats(stats_file) == make_stats()
    assert load_session_stats(tmp_path / "missing.json") is None


# --- end to end: acm logs --export -------------------------------------------

@pytest.fixture
def acm_home(tmp_path, monkeypatch):
    """Isolated HOME holding two saved crash files where `acm monitor` writes them."""
    home = tmp_path / "home"
    logs_dir = home / "android_logs"
    logs_dir.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    for i, crash in enumerate([make_crash(), make_crash("ANR in Example", crash_type=CrashType.ANR)]):
        (logs_dir / f"crash_{i}.json").write_text(json.dumps(crash.to_dict(), default=str))
    return home


@pytest.mark.parametrize("fmt", ["json", "csv", "html", "txt", "md", "compact-json", "detailed-json", "excel-csv"])
def test_acm_logs_export_from_saved_crash_files(fmt, acm_home, tmp_path):
    # Saved crash files load as dicts; json/html/text exporters used to crash on them.
    from android_crash_monitor.cli import cli

    out = tmp_path / f"export.{fmt}"
    result = CliRunner().invoke(cli, ["logs", "--export", fmt, "-o", str(out)])

    assert result.exit_code == 0, result.output
    assert result.exception is None, result.exception
    assert out.is_file() and out.stat().st_size > 0
    assert "Export completed" in result.output
    if fmt in ("json", "detailed-json"):
        assert len(json.loads(out.read_text())["crashes"]) == 2
