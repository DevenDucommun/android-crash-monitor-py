# Android Crash Monitor

[![CI](https://github.com/DevenDucommun/android-crash-monitor-py/actions/workflows/ci.yml/badge.svg)](https://github.com/DevenDucommun/android-crash-monitor-py/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A cross-platform Android crash monitoring tool with real-time log analysis, intelligent pattern detection, and automated reporting. Supports both a CLI for developers and a GUI for non-technical users.

**Tech Stack:** Python + Click CLI + Rich TUI | Tkinter GUI | ADB | PyInstaller + dmgbuild (macOS .dmg distribution)

## Features

- **Real-time log streaming** — monitors logcat, kernel, and crash streams simultaneously
- **Crash pattern detection** — identifies ANRs, native crashes, Java exceptions, and cascade failures
- **Root cause analysis** — correlates events across log streams to find the trigger
- **Predictive analytics** — detects patterns that precede crashes (memory pressure, thermal throttling)
- **SQLite crash database** — persistent history with query, filtering, and retention policies
- **Environment diagnostics** — `acm doctor` checks ADB, devices, permissions with fix suggestions
- **TOML configuration** — `~/.config/acm/config.toml` for thresholds, device aliases, notifications
- **Multi-device support** — monitors multiple connected Android devices concurrently
- **Export** — JSON, CSV, HTML reports with severity classification
- **macOS GUI** — drag-and-drop `.dmg` installer for non-technical users
- **Cross-platform CLI** — works on macOS, Linux, and Windows via ADB

## Installation

### macOS (GUI)

Download the `.dmg` from the [Releases](../../releases) page, drag to Applications, and launch.

### CLI (all platforms)

```bash
pip install -e .
acm start
```

### From source

```bash
git clone https://github.com/DevenDucommun/android-crash-monitor-py.git
cd android-crash-monitor-py
pip install -e ".[dev]"
acm --help
```

## Usage

### Quick start

```bash
# Interactive setup — detects ADB, devices, and configures monitoring
acm setup

# Start monitoring (streams crashes in real-time)
acm start

# Analyze recent crashes
acm analyze

# Monitor with verbose output
acm start -vvv
```

### CLI commands

| Command | Description |
|---------|-------------|
| `acm start` | One-command setup and monitoring |
| `acm doctor` | Diagnose environment (ADB, devices, permissions) |
| `acm history` | Query crash history from local SQLite database |
| `acm analyze` | Analyze collected crash data for patterns |
| `acm monitor` | Start monitoring (post-setup) |
| `acm logs --export json` | Export crash data to JSON/CSV/HTML |
| `acm setup` | Interactive first-run configuration |

### GUI

```bash
python launch-gui.py
```

The GUI provides real-time device status indicators, one-click monitoring, and plain-English error explanations.

## Architecture

```
src/android_crash_monitor/
├── cli.py               # Click CLI entrypoint
├── gui.py               # Tkinter GUI application
├── core/
│   ├── adb.py           # ADB connection management
│   ├── monitor.py       # Log stream orchestration
│   ├── database.py      # SQLite crash persistence
│   ├── doctor.py        # Environment diagnostics
│   ├── user_config.py   # TOML configuration
│   ├── config.py        # Internal monitoring config
│   └── enhanced_*.py    # Advanced detection engines
├── analysis/
│   ├── crash_analyzer.py        # Crash classification
│   ├── pattern_detector.py      # Pattern matching engine
│   ├── predictive_analytics.py  # Pre-crash signal detection
│   ├── root_cause_analyzer.py   # Cross-stream correlation
│   └── report_generator.py      # Multi-format export
├── setup/               # Interactive setup wizard
├── exporters/           # JSON, CSV, HTML, text exporters
├── ui/                  # Rich console UI components
└── utils/               # Logging, time, crash utilities
```

## Building the macOS Installer

```bash
pip install -e ".[build]"
./build_macos_installer.sh
```

This produces:
- `dist/Android Crash Monitor.app` — standalone macOS application
- `AndroidCrashMonitor-2.2.0.dmg` — distributable disk image installer

The build uses PyInstaller to bundle Python + dependencies into a self-contained `.app`, then dmgbuild to create a drag-to-install `.dmg` with Applications shortcut.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Requirements

- Python 3.9+
- ADB (Android Debug Bridge) installed and in PATH
- Android device with USB debugging enabled

## License

MIT — see [LICENSE](LICENSE).
