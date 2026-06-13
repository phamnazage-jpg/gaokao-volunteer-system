"""SQLite schema for T6.5 案例管理。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('success', 'typical', 'warning')),
    summary TEXT,
    content TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending'
        CHECK(review_status IN ('pending', 'approved', 'rejected')),
    review_note TEXT,
    reviewer TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_cases_category ON cases(category);
CREATE INDEX IF NOT EXISTS idx_cases_review_status ON cases(review_status);
CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at DESC);
"""


def apply_schema(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    if db_path.parent and not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    except Exception:
        conn.close()
        raise
    return conn
