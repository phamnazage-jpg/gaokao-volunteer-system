"""Channel Sync 与 OrdersDAO 兼容层。

历史上 T8.1 为避免阻塞，先在本模块内实现了独立的 upsert/status_history 逻辑。
T4.2 完成后，订单真相已经迁移到 ``data.orders.dao.OrdersDAO``，本文件只保留
向后兼容入口，避免 channel_sync / 旧测试继续绕过主 DAO。
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from data.orders.dao import OrdersDAO, UpsertResult
from data.orders.models import Order, utc_now_iso


def upsert_by_external_id(
    conn: sqlite3.Connection,
    order: Order,
    *,
    actor: str = "xianyu_webhook",
    reason: Optional[str] = None,
) -> UpsertResult:
    """兼容旧调用，统一委托给 OrdersDAO.upsert_by_external_id。"""
    return OrdersDAO(conn).upsert_by_external_id(order, actor=actor, reason=reason)


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
    """兼容旧调用，统一走 OrdersDAO 的状态历史写入口。"""
    return OrdersDAO(conn)._insert_status_history(
        order_id=order_id,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        reason=reason,
        changed_at=changed_at or utc_now_iso(),
    )


__all__ = ["UpsertResult", "upsert_by_external_id", "insert_status_history"]
