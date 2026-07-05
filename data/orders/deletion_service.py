from __future__ import annotations

import json
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


# 状态 → 触发保留期门禁的子集。
# pending 视为未付款,可由后台直接清理(避免未支付订单卡在 retention 周期里);
# paid/serving/delivered/completed/refunded 才进入"服务完成后 180 天"口径。
# 实际抛 BusinessError 的 gate 在 admin/routes/orders.py 路由层 (避免 data.orders 反向依赖 admin)。
RETENTION_GUARDED_STATUSES = frozenset({
    "paid",
    "serving",
    "delivered",
    "completed",
    "refunded",
})
DEFAULT_RETENTION_DAYS = 180

_DEFAULT_TRUSTED_PORTAL_UPLOAD_ROOT = Path("data/portal_uploads").resolve()
_DEFAULT_TRUSTED_ARTIFACT_ROOTS = (
    (Path("data/portal_uploads").resolve().parent / "order_artifacts").resolve(),
    Path("data/examples").resolve(),
    Path("data/share/reports").resolve(),
)


def _is_within_roots(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(root == path or root in path.parents for root in roots)


@dataclass
class DeletionResult:
    order_id: str
    action: str
    files_deleted: int = 0


class OrderDeletionService:
    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        portal_upload_root: Path = _DEFAULT_TRUSTED_PORTAL_UPLOAD_ROOT,
        artifact_roots: tuple[Path, ...] = _DEFAULT_TRUSTED_ARTIFACT_ROOTS,
    ) -> None:
        self._conn = conn
        self._portal_upload_root = portal_upload_root.resolve()
        self._artifact_roots = tuple(root.resolve() for root in artifact_roots)
        self._conn.executescript(AUDIT_SCHEMA_SQL)
        self._conn.commit()

    @classmethod
    def for_db(
        cls,
        db_path: str | Path,
        *,
        portal_upload_root: Path = _DEFAULT_TRUSTED_PORTAL_UPLOAD_ROOT,
        artifact_roots: tuple[Path, ...] = _DEFAULT_TRUSTED_ARTIFACT_ROOTS,
    ) -> "OrderDeletionService":
        conn = apply_schema(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return cls(
            conn,
            portal_upload_root=portal_upload_root,
            artifact_roots=artifact_roots,
        )

    def close(self) -> None:
        self._conn.close()

    def delete_order(self, order_id: str, *, actor: str, reason: str) -> DeletionResult:
        with OrdersDAO(self._conn) as dao:
            try:
                order = dao.get(order_id)
            except OrderNotFound:
                raise
            intake_payload = self._get_intake_payload(order_id)
            files_deleted = self._delete_order_files(
                order_id,
                intake_payload=intake_payload,
                artifact_paths=(order.audit_report, order.pdf_path),
            )
            deleted = dao.delete(
                order_id,
                actor=actor,
                reason=reason,
                files_deleted=files_deleted,
            )
            if not deleted:
                raise OrderNotFound(f"订单不存在: {order_id}")
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
            intake_payload = self._get_intake_payload(order_id)
            files_deleted = self._delete_order_files(
                order_id,
                intake_payload=intake_payload,
                artifact_paths=(),
            )
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
            if self._table_exists("order_intakes"):
                self._conn.execute(
                    "UPDATE order_intakes SET payload_json='{}', updated_at=?, status='submitted' WHERE order_id=?",
                    (now, order_id),
                )
            if self._table_exists("payments"):
                self._conn.execute(
                    "UPDATE payments SET callback_payload=NULL, checkout_token=NULL WHERE order_id=?",
                    (order_id,),
                )
            if self._table_exists("delivery_notifications"):
                self._conn.execute(
                    "UPDATE delivery_notifications SET payload_json='{}' WHERE order_id=?",
                    (order_id,),
                )
            self._insert_audit(
                order_id=order_id,
                action="anonymize",
                actor=actor,
                reason=reason,
                files_deleted=files_deleted,
            )
            self._conn.commit()
            return DeletionResult(
                order_id=order_id,
                action="anonymized",
                files_deleted=files_deleted,
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

    def _get_intake_payload(self, order_id: str) -> dict[str, object]:
        if not self._table_exists("order_intakes"):
            return {}
        row = self._conn.execute(
            "SELECT payload_json FROM order_intakes WHERE order_id=?",
            (order_id,),
        ).fetchone()
        if row is None:
            return {}
        raw = row[0] or "{}"
        try:
            parsed = json.loads(str(raw))
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _delete_order_files(
        self,
        order_id: str,
        *,
        intake_payload: dict[str, object],
        artifact_paths: tuple[str | None, ...],
    ) -> int:
        deleted = self._delete_artifacts(*artifact_paths)
        deleted += self._delete_portal_attachments(order_id, intake_payload)
        return deleted

    def _delete_portal_attachments(
        self, order_id: str, intake_payload: dict[str, object]
    ) -> int:
        attachments = intake_payload.get("attachments")
        if not isinstance(attachments, list):
            return 0
        deleted = 0
        parent_dirs: set[Path] = set()
        for item in attachments:
            if not isinstance(item, dict):
                continue
            raw_path = item.get("storage_path")
            if not raw_path:
                continue
            path = Path(str(raw_path)).expanduser().resolve()
            if not _is_within_roots(path, (self._portal_upload_root,)):
                continue
            if path.is_file():
                path.unlink()
                deleted += 1
            parent_dirs.add(path.parent)
        order_dir = self._portal_upload_root / order_id
        if order_dir.exists() and order_dir.is_dir() and not any(order_dir.iterdir()):
            order_dir.rmdir()
        return deleted

    def _table_exists(self, table_name: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table_name,),
        ).fetchone()
        return row is not None

    def _delete_artifacts(self, *paths: str | None) -> int:
        deleted = 0
        for raw_path in paths:
            if not raw_path:
                continue
            path = Path(raw_path).expanduser().resolve()
            if not _is_within_roots(path, self._artifact_roots):
                continue
            if path.is_file():
                path.unlink()
                deleted += 1
        return deleted
