from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from data.orders.models import utc_now_iso
from data.orders.schema import apply_schema


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS delivery_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    channel TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(order_id, event_type),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
"""


@dataclass
class DeliveryNotificationEvent:
    order_id: str
    event_type: str
    channel: str
    payload_json: str
    created_at: str


class DeliveryNotificationService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @classmethod
    def for_db(cls, db_path: str | Path) -> "DeliveryNotificationService":
        conn = apply_schema(db_path)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        return cls(conn)

    def close(self) -> None:
        self._conn.close()

    def notify_report_ready(
        self, order_id: str, payload_json: str, channel: str = "station"
    ) -> None:
        try:
            self._conn.execute(
                "INSERT INTO delivery_notifications(order_id, event_type, channel, payload_json, created_at) VALUES (?, 'report_ready', ?, ?, ?)",
                (order_id, channel, payload_json, utc_now_iso()),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            self._conn.rollback()

    def list_events(self, order_id: str) -> list[DeliveryNotificationEvent]:
        rows = self._conn.execute(
            "SELECT order_id, event_type, channel, payload_json, created_at FROM delivery_notifications WHERE order_id=? ORDER BY id ASC",
            (order_id,),
        ).fetchall()
        return [DeliveryNotificationEvent(**dict(row)) for row in rows]
