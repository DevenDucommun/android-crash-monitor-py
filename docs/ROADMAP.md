# Roadmap

Versioning follows [SemVer](https://semver.org/). Current release: **v2.1.0**.

---

## v2.2.0 — Data Persistence & Diagnostics

*Focus: local crash history, setup UX, and operational polish.*

| Feature | Description |
|---------|-------------|
| **SQLite crash database** | Persist all detected crashes to `~/.local/share/acm/crashes.db`. Query history, filter by app/severity/date, support retention policies. |
| **`acm doctor`** | Diagnose environment: ADB reachable, USB debugging on, device authorized, Python version, permissions. Actionable fix suggestions for each check. |
| **Config file** | `~/.config/acm/config.toml` for thresholds, device aliases, notification targets, and retention settings. |

---

## v2.3.0 — Notifications & Integrations

*Focus: alerting pipelines and external system connectivity.*

| Feature | Description |
|---------|-------------|
| **Webhook notifications** | Fire HTTP POST to Slack, Discord, or generic endpoints on critical/high-severity patterns. Configurable via `config.toml`. |
| **`acm replay`** | Replay a saved crash session from the SQLite DB or a JSON export. Enables demos and regression testing without a device. |

---

## v2.4.0 — API & Extensibility

*Focus: programmatic access and community contributions.*

| Feature | Description |
|---------|-------------|
| **`acm serve`** | REST API + WebSocket feed exposing crash data, live events, and analytics. Useful for dashboards or CI integration. |
| **Plugin system** | Load custom pattern detectors from `~/.config/acm/plugins/`. Python entry-point interface with schema validation. |

---

## v3.0.0 — Platform

*Focus: multi-device fleet management and containerized deployment.*

| Feature | Description |
|---------|-------------|
| **Docker Compose environment** | Mock ADB + simulated crash stream for contributors. One-command local dev setup. |
| **Fleet dashboard** | Web UI for monitoring multiple devices simultaneously. Built on `acm serve`. |
| **CI/CD integration** | GitHub Action / CLI mode that fails a build if crash count exceeds threshold during instrumented test runs. |

---

## Principles

- Each minor version is independently shippable and useful
- Features build on each other (SQLite enables replay; serve enables dashboard)
- No breaking CLI changes until v3.0
- macOS `.dmg` updated with each minor release
