from __future__ import annotations

import os
import subprocess
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
            "python3",
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
    assert '"candidates": 1' in proc.stdout
