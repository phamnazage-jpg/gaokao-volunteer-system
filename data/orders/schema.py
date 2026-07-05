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
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        if "customer_email" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN customer_email TEXT")
        # A-2 (2026-06-20) — 后台/外部渠道补录同意审计统一化
        # consent_method 记录采集方式(verbal_chat/phone_recording/screenshot/
        # written_form/self_declared), consent_given_at 记录采集时间。
        # 两个字段都冗余落库, 避免每次列表 join order_intakes。
        if "consent_method" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN consent_method TEXT")
        if "consent_given_at" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN consent_given_at TEXT")
        conn.commit()
    except Exception:
        conn.close()
        raise
    return conn


def get_schema_version(conn: sqlite3.Connection) -> int:
    """读取当前 schema 版本号（首次运行返回 0）。后续迁移将引入 schema_version 表。"""
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'"
        ).fetchone()
        return 1 if row else 0
    except sqlite3.DatabaseError:
        return 0
