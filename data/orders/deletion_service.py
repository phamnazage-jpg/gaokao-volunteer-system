from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from data.orders.dao import OrderNotFound, OrdersDAO
from data.orders.models import utc_now_iso
from data.orders.schema import apply_schema


AUDIT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS order_deletion_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('delete','anonymize')),
    actor TEXT,
    reason TEXT,
    files_deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_deletion_audits_order_id ON order_deletion_audits(order_id);
"""


@dataclass
class DeletionResult:
    order_id: str
    action: str
    files_deleted: int = 0


class OrderDeletionService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(AUDIT_SCHEMA_SQL)
        self._conn.commit()

    @classmethod
    def for_db(cls, db_path: str | Path) -> "OrderDeletionService":
        conn = apply_schema(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return cls(conn)

    def close(self) -> None:
        self._conn.close()

    def delete_order(self, order_id: str, *, actor: str, reason: str) -> DeletionResult:
        with OrdersDAO(self._conn) as dao:
            try:
                order = dao.get(order_id)
            except OrderNotFound:
                raise
            files_deleted = self._delete_artifacts(order.audit_report, order.pdf_path)
            deleted = dao.delete(order_id)
            if not deleted:
                raise OrderNotFound(f"订单不存在: {order_id}")
            self._insert_audit(
                order_id=order_id,
                action="delete",
                actor=actor,
                reason=reason,
                files_deleted=files_deleted,
            )
            self._conn.commit()
            return DeletionResult(
                order_id=order_id, action="deleted", files_deleted=files_deleted
            )

    def anonymize_order(
        self, order_id: str, *, actor: str, reason: str
    ) -> DeletionResult:
        with OrdersDAO(self._conn) as dao:
            try:
                dao.get(order_id)
            except OrderNotFound:
                raise
            now = utc_now_iso()
            self._conn.execute(
                """
                UPDATE orders
                SET customer_name=?,
                    customer_phone_enc=NULL,
                    customer_phone_hash=NULL,
                    customer_wechat=NULL,
                    customer_email=NULL,
                    candidate_name=?,
                    candidate_id_card_enc=NULL,
                    candidate_interests=NULL,
                    candidate_strong_subjects=NULL,
                    candidate_weak_subjects=NULL,
                    candidate_family=NULL,
                    notes=?,
                    status_updated_at=?
                WHERE id=?
                """,
                (
                    "已匿名化",
                    "匿名考生",
                    f"[ANONYMIZED] {reason}",
                    now,
                    order_id,
                ),
            )
            if self._table_exists("payments"):
                self._conn.execute(
                    "UPDATE payments SET checkout_token=NULL, callback_payload=NULL WHERE order_id=?",
                    (order_id,),
                )
            if self._table_exists("order_intakes"):
                self._conn.execute(
                    "UPDATE order_intakes SET payload_json='{}', updated_at=? WHERE order_id=?",
                    (now, order_id),
                )
            self._insert_audit(
                order_id=order_id,
                action="anonymize",
                actor=actor,
                reason=reason,
                files_deleted=0,
            )
            self._conn.commit()
            return DeletionResult(
                order_id=order_id, action="anonymized", files_deleted=0
            )

    def audit_count(self, order_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM order_deletion_audits WHERE order_id=?",
            (order_id,),
        ).fetchone()
        return int(row[0] if row is not None else 0)

    def _insert_audit(
        self,
        *,
        order_id: str,
        action: str,
        actor: str,
        reason: str,
        files_deleted: int,
    ) -> None:
        self._conn.execute(
            "INSERT INTO order_deletion_audits(order_id, action, actor, reason, files_deleted, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, action, actor, reason, files_deleted, utc_now_iso()),
        )

    def _table_exists(self, table_name: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table_name,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _delete_artifacts(*paths: str | None) -> int:
        deleted = 0
        for raw_path in paths:
            if not raw_path:
                continue
            path = Path(raw_path)
            if path.is_file():
                path.unlink()
                deleted += 1
        return deleted
