from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from data.orders.dao import OrdersDAO
from data.orders.models import Order

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _seed_old_completed_order(
    db_path: str, order_id: str = "GKO-20250101-RETENTION"
) -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="completed",
        customer_name="张家长",
        customer_phone="13800138000",
        customer_wechat="wx-retention",
        candidate_name="张三",
        candidate_province="湖南",
        notes="old completed order",
        created_at="2025-01-01T00:00:00+00:00",
        completed_at="2025-01-02T00:00:00+00:00",
        status_updated_at="2025-01-02T00:00:00+00:00",
    )
    with OrdersDAO.connect(db_path) as dao:
        return dao.create(order, actor="test", reason="seed_old_completed")


def test_retention_cleanup_dry_run_reports_candidates(settings):
    _seed_old_completed_order(settings.orders_db_path)

    from data.orders.retention_cleanup import run_cleanup

    result = run_cleanup(
        settings.orders_db_path,
        cutoff_iso="2025-06-30T00:00:00+00:00",
        apply=False,
    )
    assert result.scanned >= 1
    assert result.candidates == 1
    assert result.anonymized == 0


def test_retention_cleanup_apply_anonymizes_old_completed_order(settings):
    _seed_old_completed_order(
        settings.orders_db_path, order_id="GKO-20250101-RETENTION-APPLY"
    )

    from data.orders.retention_cleanup import run_cleanup

    result = run_cleanup(
        settings.orders_db_path,
        cutoff_iso="2025-06-30T00:00:00+00:00",
        apply=True,
    )
    assert result.candidates == 1
    assert result.anonymized == 1

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order = dao.get("GKO-20250101-RETENTION-APPLY")
    assert order.customer_phone is None
    assert order.customer_name == "已匿名化"


def test_retention_cleanup_script_prints_summary(settings):
    _seed_old_completed_order(
        settings.orders_db_path, order_id="GKO-20250101-RETENTION-CLI"
    )
    env = {**os.environ, "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path}
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/gaokao-retention-cleanup.py",
            "--cutoff",
            "2025-06-30T00:00:00+00:00",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert '"cutoff_iso": "2025-06-30T00:00:00+00:00"' in proc.stdout
    assert '"dry_run": true' in proc.stdout
    assert '"candidates": 1' in proc.stdout


def test_retention_cleanup_script_supports_retention_days(settings):
    _seed_old_completed_order(
        settings.orders_db_path, order_id="GKO-20250101-RETENTION-DAYS"
    )
    env = {**os.environ, "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path}
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/gaokao-retention-cleanup.py",
            "--retention-days",
            "180",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert '"cutoff_iso":' in proc.stdout
    assert '"dry_run": true' in proc.stdout
    assert '"candidates": 1' in proc.stdout


def test_retention_cleanup_apply_anonymizes_multiple_old_orders_in_sequence(
    settings,
) -> None:
    """T12-D regression: 服务持有 conn 时，连续 anonymize 多笔订单必须全部成功。

    历史 bug: ``deletion_service.anonymize_order`` 把 ``self._conn`` 包成
    ``OrdersDAO(self._conn)`` 走 with-block，而 ``OrdersDAO.__exit__`` 不区分
    conn 所有权，一律 close。第一个订单执行完就把 service 持有的连接关掉，
    第二个订单开始全部 ``Cannot operate on a closed database``。
    """
    from data.orders.retention_cleanup import run_cleanup

    order_ids = [
        "GKO-20250101-RETENTION-MULTI-A",
        "GKO-20250101-RETENTION-MULTI-B",
        "GKO-20250101-RETENTION-MULTI-C",
    ]
    for idx, oid in enumerate(order_ids, start=1):
        _seed_old_completed_order(settings.orders_db_path, order_id=oid)
        # 给每个订单一点时间间隔，确保 status_updated_at 不完全相同
        # （cleanup 按 cutoff 命中即可，无需显式 sleep）

    result = run_cleanup(
        settings.orders_db_path,
        cutoff_iso="2025-06-30T00:00:00+00:00",
        apply=True,
    )

    assert result.scanned >= 3
    assert result.candidates == 3
    assert result.anonymized == 3, (
        f"连续多笔订单应全部匿名化，实际 anonymized={result.anonymized} "
        f"（历史 bug: 第一个 anonymize 关闭 service.conn 后后续全部失败）"
    )

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        for oid in order_ids:
            order = dao.get(oid)
            assert order.customer_phone is None, f"{oid} phone 未被清空"
            assert order.customer_name == "已匿名化", (
                f"{oid} name 未被替换为'已匿名化'，实际={order.customer_name!r}"
            )


def test_retention_cleanup_underscore_script_alias_works(settings):
    _seed_old_completed_order(
        settings.orders_db_path, order_id="GKO-20250101-RETENTION-ALIAS"
    )
    env = {**os.environ, "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path}
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/gaokao_retention_cleanup.py",
            "--cutoff",
            "2025-06-30T00:00:00+00:00",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert '"candidates": 1' in proc.stdout
