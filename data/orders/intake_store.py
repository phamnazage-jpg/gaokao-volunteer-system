from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from data.orders.models import utc_now_iso
from data.orders.schema import apply_schema


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS order_intakes (
    order_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('draft','submitted')),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    submitted_at TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
"""


@dataclass
class IntakeRecord:
    order_id: str
    status: str
    payload: dict[str, Any]
    created_at: str
    updated_at: str
    submitted_at: Optional[str] = None


class IntakeStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @classmethod
    def for_db(cls, db_path: str | Path) -> "IntakeStore":
        conn = apply_schema(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        return cls(conn)

    def close(self) -> None:
        self._conn.close()

    def get(self, order_id: str) -> Optional[IntakeRecord]:
        row = self._conn.execute(
            "SELECT order_id, status, payload_json, created_at, updated_at, submitted_at FROM order_intakes WHERE order_id=?",
            (order_id,),
        ).fetchone()
        if row is None:
            return None
        return IntakeRecord(
            order_id=row["order_id"],
            status=row["status"],
            payload=json.loads(row["payload_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            submitted_at=row["submitted_at"],
        )

    def save(
        self, *, order_id: str, payload: dict[str, Any], submit: bool
    ) -> IntakeRecord:
        now = utc_now_iso()
        status = "submitted" if submit else "draft"
        current = self.get(order_id)
        if current is None:
            self._conn.execute(
                "INSERT INTO order_intakes(order_id, status, payload_json, created_at, updated_at, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    order_id,
                    status,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                    now,
                    now if submit else None,
                ),
            )
        else:
            self._conn.execute(
                "UPDATE order_intakes SET status=?, payload_json=?, updated_at=?, submitted_at=? WHERE order_id=?",
                (
                    status,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                    now if submit else current.submitted_at,
                    order_id,
                ),
            )
        self._conn.commit()
        record = self.get(order_id)
        assert record is not None
        return record
