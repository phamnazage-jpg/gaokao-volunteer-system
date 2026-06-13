"""Webhook 审计日志 (T8.1)

记录每一次 Webhook 接收的处理决策:

- decision: 'accepted' | 'rejected' | 'parse_error' | 'duplicate'
- reject_reason: 拒绝原因（短字符串，便于排查）
- raw_body_hash: SHA-256(body)，不存原始 body 避免敏感信息二次落地
- order_id: 映射到的内部订单号（若已有）
- remote_addr: 来源 IP（用于限流/取证）

表结构与设计文档 CHANNEL_INTEGRATION.md §4.3 一致。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .signature import sha256_hex

# 审计表 DDL（与 channel_sync/webhook_server 共用）
WEBHOOK_AUDIT_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS webhook_audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at     TEXT NOT NULL,
    channel         TEXT NOT NULL,
    event_id        TEXT,
    decision        TEXT NOT NULL,
    reject_reason   TEXT,
    order_id        TEXT,
    raw_body_hash   TEXT,
    remote_addr     TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhook_audit_event
    ON webhook_audit(channel, event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_audit_decision
    ON webhook_audit(channel, decision, received_at);
"""

VALID_DECISIONS: frozenset[str] = frozenset(
    {"accepted", "rejected", "parse_error", "duplicate"}
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class WebhookAuditEntry:
    """单条审计记录的入参结构。"""

    channel: str
    decision: str
    event_id: Optional[str] = None
    reject_reason: Optional[str] = None
    order_id: Optional[str] = None
    raw_body: Optional[bytes] = None
    remote_addr: Optional[str] = None
    received_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.decision not in VALID_DECISIONS:
            raise ValueError(
                f"非法 decision: {self.decision!r}; 允许: {sorted(VALID_DECISIONS)}"
            )
        if not self.received_at:
            self.received_at = utc_now_iso()


def apply_audit_schema(conn: sqlite3.Connection) -> None:
    """幂等地把 webhook_audit 表与索引装上。"""
    conn.executescript(WEBHOOK_AUDIT_SCHEMA)
    conn.commit()


def record(
    conn: sqlite3.Connection,
    entry: WebhookAuditEntry,
) -> int:
    """写入一条审计记录，返回 rowid。"""
    raw_hash = sha256_hex(entry.raw_body) if entry.raw_body else None
    cur = conn.execute(
        """
        INSERT INTO webhook_audit(
            received_at, channel, event_id, decision,
            reject_reason, order_id, raw_body_hash, remote_addr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.received_at,
            entry.channel,
            entry.event_id,
            entry.decision,
            entry.reject_reason,
            entry.order_id,
            raw_hash,
            entry.remote_addr,
        ),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def count_by_event(conn: sqlite3.Connection, channel: str, event_id: str) -> int:
    """统计 (channel, event_id) 在审计表里的出现次数。"""
    row = conn.execute(
        "SELECT COUNT(*) FROM webhook_audit "
        "WHERE channel=? AND event_id=? AND decision='accepted'",
        (channel, event_id),
    ).fetchone()
    return int(row[0]) if row else 0


def list_recent(
    conn: sqlite3.Connection,
    *,
    channel: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """列出最近审计记录，按 id 倒序。"""
    where: list[str] = []
    args: list = []
    if channel:
        where.append("channel=?")
        args.append(channel)
    if decision:
        where.append("decision=?")
        args.append(decision)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    args.append(int(limit))
    cur = conn.execute(
        f"SELECT id, received_at, channel, event_id, decision, "
        f"reject_reason, order_id, raw_body_hash, remote_addr "
        f"FROM webhook_audit {where_sql} "
        f"ORDER BY id DESC LIMIT ?",
        args,
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def open_audit_db(db_path: str | Path) -> sqlite3.Connection:
    """打开（或创建）含 webhook_audit 表的数据库连接。

    订单表如果存在就一起连进来（同一 SQLite 文件）；如果不存在则只装审计表。
    """
    db_path = Path(db_path)
    if db_path.parent and not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        apply_audit_schema(conn)
    except Exception:
        conn.close()
        raise
    return conn
