"""SQLite Schema 模块 (T4.1)

定义 orders 主表与 order_status_history 审计表的 DDL，并提供幂等的
apply_schema() 应用函数。所有表使用 IF NOT EXISTS；启用外键约束。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL: str = """
-- 订单主表
CREATE TABLE IF NOT EXISTS orders (
    -- 主键 / 业务标识
    id                  TEXT PRIMARY KEY,
    source              TEXT NOT NULL,
    external_id         TEXT,
    service_version     TEXT NOT NULL,
    amount_cents        INTEGER NOT NULL CHECK(amount_cents >= 0),
    status              TEXT NOT NULL CHECK(status IN
                            ('pending','paid','serving','delivered','completed','refunded')),
    status_updated_at   TEXT NOT NULL,

    -- 客户信息（加密 + 脱敏）
    customer_name       TEXT,
    customer_phone_enc  TEXT,
    customer_phone_hash TEXT,
    customer_wechat     TEXT,
    customer_email      TEXT,

    -- 考生信息
    candidate_name          TEXT,
    candidate_id_card_enc   TEXT,
    candidate_province      TEXT,
    candidate_score         INTEGER,
    candidate_rank          INTEGER,
    candidate_subjects      TEXT,
    candidate_interests     TEXT,
    candidate_strong_subjects TEXT,
    candidate_weak_subjects TEXT,
    candidate_family        TEXT,

    -- 服务信息
    assigned_consultant TEXT,
    plan_file           TEXT,
    audit_report        TEXT,
    pdf_path            TEXT,

    -- 时间戳（ISO8601 UTC）
    created_at          TEXT NOT NULL,
    paid_at             TEXT,
    started_at          TEXT,
    delivered_at        TEXT,
    completed_at        TEXT,

    -- 元数据
    notes               TEXT,
    tags                TEXT,
    upgrade_from        TEXT,

    FOREIGN KEY (upgrade_from) REFERENCES orders(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status     ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_source     ON orders(source);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_phone_hash ON orders(customer_phone_hash);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_orders_external
    ON orders(source, external_id) WHERE external_id IS NOT NULL;

-- 状态历史（审计）
CREATE TABLE IF NOT EXISTS order_status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    actor       TEXT,
    reason      TEXT,
    changed_at  TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_status_history_order ON order_status_history(order_id);

-- Portal token revoke list（v2 token jti 撤销表）
CREATE TABLE IF NOT EXISTS portal_token_revocations (
    jti         TEXT PRIMARY KEY,
    order_id    TEXT,
    reason      TEXT,
    revoked_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_portal_token_revocations_order
    ON portal_token_revocations(order_id);

-- Schema migration registry (T3-04)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL
);
"""


def apply_schema(db_path: str | Path) -> sqlite3.Connection:
    """应用 schema 到指定 SQLite 文件，返回连接。

    - 启用外键约束 (PRAGMA foreign_keys = ON)
    - 父目录自动创建
    - 幂等：可重复执行
    """
    db_path = Path(db_path)
    if db_path.parent and not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        # T3-04: Run versioned migrations
        current_version = get_schema_version(conn)
        for version, name in _MIGRATIONS:
            if version <= current_version:
                continue
            _apply_migration(conn, version, name)
        conn.commit()
    except Exception:
        conn.close()
        raise
    return conn


_MIGRATIONS: list[tuple[int, str]] = [
    (1, "initial_schema"),
    (2, "add_customer_email"),
    (3, "add_consent_audit_columns"),
    (4, "add_portal_token_revocations"),
]


def _apply_migration(conn: sqlite3.Connection, version: int, name: str) -> None:
    """Apply a single migration and record it in schema_migrations."""
    if version == 1:
        pass  # SCHEMA_SQL already creates all tables
    elif version == 2:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(orders)").fetchall()}
        if "customer_email" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN customer_email TEXT")
    elif version == 3:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(orders)").fetchall()}
        if "consent_method" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN consent_method TEXT")
        if "consent_given_at" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN consent_given_at TEXT")
    elif version == 4:
        pass  # portal_token_revocations already in SCHEMA_SQL
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
        (version, name, sqlite3.Connection is not None and __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat()),
    )


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration version.

    For databases created before the schema_migrations table existed,
    detects the orders table and auto-registers as version 1.
    """
    try:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        if table_exists is None:
            # Old database without migration tracking — detect orders table
            orders_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'"
            ).fetchone()
            return 1 if orders_exists else 0
        row = conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
        ).fetchone()
        return int(row[0]) if row else 0
    except sqlite3.DatabaseError:
        return 0
