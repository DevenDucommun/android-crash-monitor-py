# Roadmap

Versioning follows [SemVer](https://semver.org/). Latest release: **v2.2.0** (tagged 2026-06-08).
`main` is ahead of v2.2.0 with the fixes listed under [Unreleased](#unreleased-on-main).

Status words used below:
- **Shipped** — on `main` and covered by tests.
- **Partial** — code exists but is not connected end to end.
- **Planned** — intended next; not started.
- **Proposed** — idea only; needs a decision before it is planned.

---

## Unreleased on `main`

Merged 2026-11-02, not yet in a tagged release:

| PR | Change |
|----|--------|
| #10 | Python 3.10 minimum; CI tests 3.10, 3.12, 3.13, 3.14 on Linux and macOS |
| #11 | Year-less logcat timestamps parse correctly (leap day, New Year, Python 3.15 change); analysis tests can now fail; Dependabot enabled |
| #12 | GitHub Actions bumped to v7 |
| #13 | mypy clean and enforced in CI; fixed crashes in cascade detection, `Config.save()` / `copy_profile()`, and the system-info summary; removed the unused setup wizard |
| #14 | `acm logs --export` works for all 8 formats (6 crashed before); exporter and `doctor` tests; `acm doctor` exits 1 on failure |

Test coverage: 37% → 52%.

---

## Next: execution plan

Work in this order. Each step is one PR unless noted.

### 1. Finish v2.2.0 wiring → release v2.2.1

v2.2.0 advertised a crash database and a config file. Both are **Partial**:

| Gap | Today | Done when |
|-----|-------|-----------|
| **Crash database is never written** | `acm history` reads `crashes.db`, but `acm monitor` only writes `crash_*.json` files, so history is always empty. | `acm monitor` saves every crash to the database as well as to JSON; `acm history` lists them; a test runs a simulated monitor session and reads it back through `acm history`. |
| **`config.toml` is never read** | `core/user_config.py` parses `severity_threshold`, `retention_days`, `notification_enabled`, `webhook_url` and `device_aliases`, but nothing loads it. | Monitor applies `severity_threshold`, prunes the database by `retention_days`, and shows `device_aliases`; tests cover each setting. |
| **`doctor` suggests a command that doesn't exist** | The config-file hint says `acm config init`. | Either add `acm config init` (writes the default `config.toml`) or change the hint; test covers it. |

**Decision needed first:** there are two config systems. JSON profiles live in the `android-crash-monitor` config dir (`ConfigManager`); `config.toml` lives in the `acm` dir. Pick one of:
- (a) Keep both: profiles for monitoring settings, `config.toml` for user preferences (smallest change).
- (b) Merge into `config.toml` and migrate profiles (cleaner, larger).

Then tag **v2.2.1** (release needs owner approval).

### 2. Release dry run in CI

The DMG build (`release.yml`) only runs when a tag is pushed, so packaging breaks are found at release time.

- Add a job that runs PyInstaller + `dmgbuild` on macOS without publishing, triggered on PRs that touch `build_app.spec`, `dmg_settings.py`, `pyproject.toml` or the release workflow, plus manual dispatch.
- Done when: the job is green on a PR and fails if the spec is broken.
- Can be done in parallel with step 1.

### 3. v2.3.0 — `acm replay` (Planned)

Replay a saved crash session without a device, from JSON crash files or the database.

- `acm replay <dir|--session ID> [--speed N]` feeds saved crashes through the same analysis and alerting path as live monitoring.
- Gives the test suite realistic end-to-end input and makes demos possible without hardware.
- Depends on step 1 (database).
- Done when: a recorded session replays through analysis with the same pattern results as the live run; covered by tests.

### 4. v2.3.0 — Webhook notifications (Planned)

POST critical/high-severity crashes and patterns to Slack, Discord or a generic URL.

- Uses `notification_enabled` and `webhook_url` from `config.toml` (depends on step 1).
- Rate-limited, with a timeout and retry, and never blocks monitoring.
- Testable with `acm replay` and a local HTTP server; no device needed.
- Done when: replaying a session with a critical crash sends one correctly formatted POST per alert to a test server.

Then tag **v2.3.0**.

### 5. Enhanced crash detector (needs a device)

`core/monitor.py` and `core/enhanced_detector.py` import each other, so `ENHANCED_DETECTION_AVAILABLE` is always `False` and `acm monitor` always uses the standard detector.

- Break the import cycle (move shared types out of `monitor.py` or import lazily).
- Turning it on enables a detector path that has never run against real logcat output, so it must be validated on a physical device before merging.
- Schedule when a device is available; `acm replay` (step 3) can cover most of it beforehand.

---

## Later

### v2.4.0 — API & Extensibility (Proposed)

| Feature | Description |
|---------|-------------|
| **`acm serve`** | REST API + WebSocket feed exposing crash data, live events and analytics, for dashboards or CI. |
| **Plugin system** | Load custom pattern detectors from the config dir via a Python entry-point interface with schema validation. |

### v3.0.0 — Platform (Proposed)

| Feature | Description |
|---------|-------------|
| **Docker Compose environment** | Mock ADB + simulated crash stream for contributors; one-command local setup. Builds on `acm replay`. |
| **Fleet dashboard** | Web UI for monitoring several devices at once, built on `acm serve`. |
| **CI/CD integration** | GitHub Action / CLI mode that fails a build when crash count exceeds a threshold during instrumented tests. |

### Ongoing quality

- Coverage is lowest in `gui.py` (0%), `cli.py`, `core/monitor.py` and `setup/setup.py` (under 30%). Raise it alongside each feature rather than as a separate project.
- ~2,800 flake8 style warnings remain (unused imports, whitespace). Clean up in one formatting-only PR when nothing else is in flight.

---

## Principles

- Each minor version is independently shippable and useful.
- Finish and connect a feature before advertising it.
- Features build on each other: database → replay → webhooks testing; `serve` → dashboard.
- No breaking CLI changes until v3.0.
- macOS `.dmg` updated with each minor release.
