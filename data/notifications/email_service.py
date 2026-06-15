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
    status TEXT NOT NULL DEFAULT 'ready',
    attempt_count INTEGER NOT NULL DEFAULT 1,
    last_attempt_at TEXT,
    failure_reason TEXT,
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
    status: str
    attempt_count: int
    last_attempt_at: str | None
    failure_reason: str | None
    created_at: str


class DeliveryNotificationService:
    def __init__(
        self, conn: sqlite3.Connection, *, owns_connection: bool = True
    ) -> None:
        self._conn = conn
        self._owns_connection = owns_connection

    @classmethod
    def for_db(cls, db_path: str | Path) -> "DeliveryNotificationService":
        conn = apply_schema(db_path)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        cls._ensure_columns(conn)
        conn.commit()
        return cls(conn)

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "DeliveryNotificationService":
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        cls._ensure_columns(conn)
        return cls(conn, owns_connection=False)

    @staticmethod
    def _ensure_columns(conn: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(delivery_notifications)"
            ).fetchall()
        }
        if "status" not in columns:
            conn.execute(
                "ALTER TABLE delivery_notifications ADD COLUMN status TEXT NOT NULL DEFAULT 'ready'"
            )
        if "attempt_count" not in columns:
            conn.execute(
                "ALTER TABLE delivery_notifications ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 1"
            )
        if "last_attempt_at" not in columns:
            conn.execute(
                "ALTER TABLE delivery_notifications ADD COLUMN last_attempt_at TEXT"
            )
        if "failure_reason" not in columns:
            conn.execute(
                "ALTER TABLE delivery_notifications ADD COLUMN failure_reason TEXT"
            )

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()

    def notify_report_ready(
        self, order_id: str, payload_json: str, channel: str = "station"
    ) -> None:
        self.notify_event(
            order_id,
            event_type="report_ready",
            channel=channel,
            payload_json=payload_json,
        )

    def notify_event(
        self,
        order_id: str,
        *,
        event_type: str,
        channel: str,
        payload_json: str,
    ) -> None:
        try:
            self._conn.execute(
                "INSERT INTO delivery_notifications(order_id, event_type, channel, payload_json, status, attempt_count, last_attempt_at, failure_reason, created_at) VALUES (?, ?, ?, ?, 'ready', 1, ?, NULL, ?)",
                (
                    order_id,
                    event_type,
                    channel,
                    payload_json,
                    utc_now_iso(),
                    utc_now_iso(),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            self._conn.rollback()

    def mark_sent(
        self,
        order_id: str,
        event_type: str = "report_ready",
        *,
        payload_json: str | None = None,
        sent_at: str | None = None,
    ) -> None:
        if sent_at is None:
            sent_at = utc_now_iso()
        if payload_json is None:
            self._conn.execute(
                "UPDATE delivery_notifications SET status='sent', last_attempt_at=?, failure_reason=NULL WHERE order_id=? AND event_type=?",
                (sent_at, order_id, event_type),
            )
        else:
            self._conn.execute(
                "UPDATE delivery_notifications SET status='sent', payload_json=?, last_attempt_at=?, failure_reason=NULL WHERE order_id=? AND event_type=?",
                (payload_json, sent_at, order_id, event_type),
            )
        self._conn.commit()

    def mark_failed(
        self,
        order_id: str,
        failure_reason: str,
        *,
        event_type: str = "report_ready",
    ) -> None:
        self._conn.execute(
            "UPDATE delivery_notifications SET status='failed', attempt_count=attempt_count+1, last_attempt_at=?, failure_reason=? WHERE order_id=? AND event_type=?",
            (utc_now_iso(), failure_reason, order_id, event_type),
        )
        self._conn.commit()

    def list_events(
        self,
        order_id: str,
        *,
        status: str | None = None,
        channel: str | None = None,
    ) -> list[DeliveryNotificationEvent]:
        sql = "SELECT order_id, event_type, channel, payload_json, status, attempt_count, last_attempt_at, failure_reason, created_at FROM delivery_notifications WHERE order_id=?"
        params: list[object] = [order_id]
        if status is not None:
            sql += " AND status=?"
            params.append(status)
        if channel is not None:
            sql += " AND channel=?"
            params.append(channel)
        sql += " ORDER BY id ASC"
        rows = self._conn.execute(sql, tuple(params)).fetchall()
        return [DeliveryNotificationEvent(**dict(row)) for row in rows]

    def list_pending_events(
        self,
        *,
        channel: str | None = None,
        statuses: tuple[str, ...] = ("ready",),
        limit: int = 100,
    ) -> list[DeliveryNotificationEvent]:
        placeholders = ",".join("?" for _ in statuses)
        sql = (
            "SELECT order_id, event_type, channel, payload_json, status, attempt_count, last_attempt_at, failure_reason, created_at FROM delivery_notifications WHERE status IN ("
            + placeholders
            + ")"
        )
        params: list[object] = list(statuses)
        if channel is not None:
            sql += " AND channel=?"
            params.append(channel)
        sql += " ORDER BY id ASC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, tuple(params)).fetchall()
        return [DeliveryNotificationEvent(**dict(row)) for row in rows]
