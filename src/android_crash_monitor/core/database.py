"""SQLite crash database for persistent crash history."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from platformdirs import user_data_dir


DB_DIR = Path(user_data_dir("acm", ensure_exists=True))
DB_PATH = DB_DIR / "crashes.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS crashes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    app_name TEXT,
    description TEXT,
    severity INTEGER DEFAULT 0,
    crash_type TEXT,
    device_serial TEXT,
    raw_data TEXT
);
CREATE INDEX IF NOT EXISTS idx_crashes_timestamp ON crashes(timestamp);
CREATE INDEX IF NOT EXISTS idx_crashes_app ON crashes(app_name);
CREATE INDEX IF NOT EXISTS idx_crashes_severity ON crashes(severity);
"""


class CrashDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def save_crash(self, crash: Dict[str, Any]) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO crashes (timestamp, app_name, description, severity,
                   crash_type, device_serial, raw_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    crash.get("timestamp", datetime.now().isoformat()),
                    crash.get("app_name"),
                    crash.get("description"),
                    crash.get("severity", 0),
                    crash.get("crash_type"),
                    crash.get("device_serial"),
                    json.dumps(crash),
                ),
            )
            return cur.lastrowid

    def query_crashes(
        self,
        app: Optional[str] = None,
        severity: Optional[int] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        conditions = []
        params: List[Any] = []

        if app:
            conditions.append("app_name LIKE ?")
            params.append(f"%{app}%")
        if severity is not None:
            conditions.append("severity >= ?")
            params.append(severity)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM crashes {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM crashes").fetchone()[0]
            by_app = conn.execute(
                "SELECT app_name, COUNT(*) as cnt FROM crashes "
                "GROUP BY app_name ORDER BY cnt DESC LIMIT 5"
            ).fetchall()
            by_severity = conn.execute(
                "SELECT severity, COUNT(*) as cnt FROM crashes "
                "GROUP BY severity ORDER BY severity DESC"
            ).fetchall()
            recent_24h = conn.execute(
                "SELECT COUNT(*) FROM crashes WHERE timestamp >= ?",
                ((datetime.now() - timedelta(hours=24)).isoformat(),),
            ).fetchone()[0]

        return {
            "total": total,
            "last_24h": recent_24h,
            "top_apps": [(row["app_name"], row["cnt"]) for row in by_app],
            "by_severity": [(row["severity"], row["cnt"]) for row in by_severity],
        }

    def prune(self, older_than_days: int = 30) -> int:
        cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM crashes WHERE timestamp < ?", (cutoff,))
            return cur.rowcount
