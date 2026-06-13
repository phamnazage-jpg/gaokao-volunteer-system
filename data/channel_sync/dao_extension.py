"""订单 DAO 扩展 (T8.1 配套)

T4.2 主 DAO 仍为 ``todo``；为不阻塞 T8.1，本模块在
``data/orders/schema.py`` 既有 ``orders`` / ``order_status_history`` 表
之上提供 Channel Sync 直接需要的两个能力:

- :func:`upsert_by_external_id` — 按 ``(source, external_id)`` 唯一索引幂等写入
- :func:`insert_status_history` — 状态机转换历史

依赖:

- :class:`data.orders.models.Order`
- :class:`data.orders.state_machine.is_valid_transition` / :class:`InvalidStateTransition`

T4.2 落地后，本模块可删除并由 T4.2 接管。
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

from data.orders.models import Order
from data.orders.state_machine import (
    InvalidStateTransition,
    assert_valid_transition,
)


@dataclass
class UpsertResult:
    """upsert 的返回结构。"""

    order_id: str
    action: str  # 'inserted' | 'updated' | 'unchanged' | 'illegal_transition'
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    error: Optional[str] = None


def _row_to_dict(row) -> dict:
    """把 fetchone() 拿到的 tuple 转成 dict，用 cursor.description 取列名。"""
    if row is None:
        return {}
    if hasattr(row, "keys"):
        return dict(row)
    # 普通 tuple：依赖调用方已设 row_factory 或我们用 description 拼
    cur = getattr(_row_to_dict, "_last_cur", None)
    if cur is None or cur.description is None:
        raise RuntimeError(
            "row is a plain tuple but no cursor.description is available; "
            "set conn.row_factory = sqlite3.Row before querying"
        )
    return dict(zip([d[0] for d in cur.description], row))


def _row_to_order(row) -> Order:
    """把数据库行转换为 Order（借助 from_db_row 解析加密字段）。"""
    if row is None:
        raise ValueError("cannot convert None row to Order")
    if hasattr(row, "keys"):
        return Order.from_db_row(dict(row))
    # tuple: 需要列名
    cur = getattr(_row_to_order, "_last_cur", None)
    if cur is None or cur.description is None:
        raise RuntimeError(
            "row is a plain tuple but no cursor.description available; "
            "set conn.row_factory = sqlite3.Row before querying"
        )
    return Order.from_db_row(dict(zip([d[0] for d in cur.description], row)))


def _coerce_value(key: str, value: Any) -> Any:
    """保证 tags / candidate_subjects 落盘为 JSON 字符串。"""
    if key in ("tags", "candidate_subjects") and isinstance(value, (list, tuple)):
        return json.dumps(list(value), ensure_ascii=False)
    return value


def _column_list() -> str:
    """``orders`` 表的可写列清单（与 schema.py 对齐）。"""
    return (
        "id, source, external_id, service_version, amount_cents, status, "
        "status_updated_at, customer_name, customer_phone_enc, "
        "customer_phone_hash, customer_wechat, candidate_name, "
        "candidate_id_card_enc, candidate_province, candidate_score, "
        "candidate_rank, candidate_subjects, candidate_interests, "
        "candidate_strong_subjects, candidate_weak_subjects, "
        "candidate_family, assigned_consultant, plan_file, audit_report, "
        "pdf_path, created_at, paid_at, started_at, delivered_at, "
        "completed_at, notes, tags, upgrade_from"
    )


def upsert_by_external_id(
    conn: sqlite3.Connection,
    order: Order,
    *,
    actor: str = "xianyu_webhook",
    reason: Optional[str] = None,
) -> UpsertResult:
    """按 (source, external_id) 唯一索引写入或更新订单。

    行为:

    - **不存在** → 插入新行 + 写 status_history(from=None → status)
    - **已存在且状态可推进** → 更新 status / status_updated_at + 写 status_history
    - **已存在且状态非法转换** → 不写库，返回 ``action='illegal_transition'``
    - **已存在且状态不变** → ``action='unchanged'``，不写 status_history

    入参:
        conn: 启用了 ``PRAGMA foreign_keys = ON`` 的 sqlite3 连接
        order: 待写入的 Order；id 与外部订单号会用于查重
        actor: 操作者标签（写入 status_history）
        reason: 可选原因描述
    """
    if not order.external_id:
        return UpsertResult(
            order_id=order.id,
            action="illegal_transition",
            error="external_id 缺失，无法做幂等 upsert",
        )

    # 1) 查询是否已存在（统一用 sqlite3.Row 工厂）
    prior_factory = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE source=? AND external_id=? LIMIT 1",
            (order.source, order.external_id),
        ).fetchone()
    finally:
        conn.row_factory = prior_factory

    if row is None:
        # INSERT
        db_row = order.to_db_row()
        # 过滤掉 schema 中不存在的列（防御性）
        valid_cols = set(_column_list().split(", "))
        db_row = {k: _coerce_value(k, v) for k, v in db_row.items() if k in valid_cols}
        cols = list(db_row.keys())
        placeholders = ",".join("?" for _ in cols)
        values = [db_row[c] for c in cols]
        conn.execute(
            f"INSERT INTO orders ({','.join(cols)}) VALUES ({placeholders})",
            values,
        )
        insert_status_history(
            conn,
            order_id=order.id,
            from_status=None,
            to_status=order.status,
            actor=actor,
            reason=reason or "channel_sync_upsert_insert",
        )
        conn.commit()
        return UpsertResult(
            order_id=order.id,
            action="inserted",
            old_status=None,
            new_status=order.status,
        )

    # 2) 已存在：判断状态转换
    existing = _row_to_order(row)
    old_status = existing.status
    if old_status == order.status:
        # 状态未变：可选择更新业务字段（amount / 客户信息）
        # 但 Channel Sync 场景下避免覆盖人工录入的字段，只更新可空字段
        return UpsertResult(
            order_id=existing.id,
            action="unchanged",
            old_status=old_status,
            new_status=order.status,
        )
    try:
        assert_valid_transition(old_status, order.status)
    except InvalidStateTransition as e:
        conn.commit()
        return UpsertResult(
            order_id=existing.id,
            action="illegal_transition",
            old_status=old_status,
            new_status=order.status,
            error=str(e),
        )

    # 3) 合法的状态推进
    conn.execute(
        """
        UPDATE orders SET
            status=?,
            status_updated_at=?,
            paid_at = COALESCE(paid_at, ?),
            completed_at = COALESCE(completed_at, ?)
        WHERE id=?
        """,
        (
            order.status,
            order.status_updated_at or order.created_at,
            order.paid_at,
            order.completed_at,
            existing.id,
        ),
    )
    insert_status_history(
        conn,
        order_id=existing.id,
        from_status=old_status,
        to_status=order.status,
        actor=actor,
        reason=reason or f"channel_sync_update_{order.source}",
    )
    conn.commit()
    return UpsertResult(
        order_id=existing.id,
        action="updated",
        old_status=old_status,
        new_status=order.status,
    )


def insert_status_history(
    conn: sqlite3.Connection,
    *,
    order_id: str,
    from_status: Optional[str],
    to_status: str,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    changed_at: Optional[str] = None,
) -> int:
    """插入一条 order_status_history 记录，返回 rowid。"""
    from data.orders.models import utc_now_iso  # local import 避免循环

    if changed_at is None:
        changed_at = utc_now_iso()
    cur = conn.execute(
        """
        INSERT INTO order_status_history(
            order_id, from_status, to_status, actor, reason, changed_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (order_id, from_status, to_status, actor, reason, changed_at),
    )
    # 不在此处 commit，由调用方统一事务
    return int(cur.lastrowid or 0)
