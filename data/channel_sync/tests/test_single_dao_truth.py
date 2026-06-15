"""P2-2: ``channel_sync`` 必须把 upsert 真相收敛到 ``OrdersDAO``.

历史:
- 2026-06-14 严格复审指明
  ``data/channel_sync/webhook_server.py`` 与
  ``data/channel_sync/poller.py`` 仍在直接调用
  ``data/channel_sync/dao_extension.upsert_by_external_id``。
- 当时设计思路是 “dao_extension 退化为兼容层, 全部委托给
  ``OrdersDAO.upsert_by_external_id``”。
- 本测试锁定以下不变量:
  1. ``dao_extension.upsert_by_external_id`` 行为与
     ``OrdersDAO.upsert_by_external_id`` 完全一致(没有第二份实现)。
  2. ``dao_extension.insert_status_history`` 也必须走
     ``OrdersDAO._insert_status_history``。
  3. ``webhook_server`` 与 ``poller`` 不允许再写裸 SQL 写订单。
"""

from __future__ import annotations

import inspect
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHANNEL_SYNC_DIR = REPO_ROOT / "data" / "channel_sync"
PROJECT_ROOT = REPO_ROOT  # alias used by tests below


def test_dao_extension_upsert_delegates_to_orders_dao():
    """``dao_extension.upsert_by_external_id`` 必须是
    ``OrdersDAO.upsert_by_external_id`` 的薄壳, 不能有第二份实现。"""
    from data.channel_sync import dao_extension

    src = inspect.getsource(dao_extension.upsert_by_external_id)
    assert "OrdersDAO" in src, (
        "dao_extension.upsert_by_external_id 必须委托给 OrdersDAO"
    )
    assert "upsert_by_external_id" in src
    # 确认 dao_extension 没有自带任何 SQL 字符串(没有第二份实现)。
    assert "INSERT INTO" not in src.upper()
    assert "UPDATE " not in src.upper()
    # 顺手验证: dao_extension.upsert_by_external_id 函数体应
    # 真的调用 OrdersDAO.upsert_by_external_id。
    assert (
        "OrdersDAO(conn).upsert_by_external_id" in src
        or "OrdersDAO(conn, autocommit=False).upsert_by_external_id" in src
    )


def test_dao_extension_insert_status_history_delegates_to_orders_dao():
    from data.channel_sync import dao_extension

    src = inspect.getsource(dao_extension.insert_status_history)
    assert "OrdersDAO" in src
    assert "_insert_status_history" in src
    # 不允许自带 SQL 写状态历史。
    assert "INSERT INTO" not in src.upper()


def test_channel_sync_runtime_does_not_write_raw_orders_sql():
    """``channel_sync`` 业务模块(``webhook_server`` /
    ``poller``) 不允许再写裸 ``INSERT INTO orders`` /
    ``UPDATE orders`` / ``UPDATE payments`` 等写订单主表的 SQL。

    只允许:
    - 通过 ``OrdersDAO`` 调用
    - 读路径 SQL(``SELECT``)
    - ``delivery_notifications`` 之类的旁路表
    """
    forbidden = (
        "INSERT INTO orders",
        "UPDATE orders",
        "INSERT INTO payments",
        "UPDATE payments",
    )

    runtime_targets = [
        PROJECT_ROOT / "data" / "channel_sync" / "webhook_server.py",
        PROJECT_ROOT / "data" / "channel_sync" / "poller.py",
    ]
    for path in runtime_targets:
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden:
            assert snippet not in text, (
                f"{path.name} still writes {snippet!r}; it must go through OrdersDAO"
            )


def test_channel_sync_runtime_does_not_import_dao_extension_directly():
    """``webhook_server`` / ``poller`` 不应再 import
    ``data.channel_sync.dao_extension``; 兼容层只允许测试与
    旧脚本使用。"""
    runtime_targets = [
        PROJECT_ROOT / "data" / "channel_sync" / "webhook_server.py",
        PROJECT_ROOT / "data" / "channel_sync" / "poller.py",
    ]
    for path in runtime_targets:
        text = path.read_text(encoding="utf-8")
        assert "from data.channel_sync import dao_extension" not in text
        assert "from data.channel_sync.dao_extension" not in text
        assert "import data.channel_sync.dao_extension" not in text
