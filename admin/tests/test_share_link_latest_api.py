from __future__ import annotations

from pathlib import Path

from admin.tests.order_test_helpers import _mark_paid, _seed_order, _seed_review_result
from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO


def test_admin_latest_share_link_returns_stats_payload(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260630-SHARE-LATEST")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    _seed_review_result(settings, token)

    created = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={
            "result_type": "review_result",
            "target_token": token,
            "permission": "read",
            "ttl_days": 7,
        },
    )
    assert created.status_code == 201, created.text

    latest = client.get(
        "/api/share-link/latest",
        headers=auth_headers,
        params={"result_type": "review_result", "target_token": token},
    )
    assert latest.status_code == 200, latest.text
    body = latest.json()
    assert body["result_type"] == "review_result"
    assert body["target_type"] == "review_result"
    assert body["stats"]["access_count"] == 0
    assert body["share_url"].startswith("http://testserver/s/")


def test_admin_latest_share_link_report_returns_stats_payload(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260630-SHARE-LATEST-REPORT")
    _mark_paid(settings, order)
    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "latest-share-report.html"
    pdf_path = report_root / "latest-share-report.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nlatest-share\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(order.id, "delivered", actor="test", reason="report_ready")

    token = issue_portal_token(order.id, settings.portal_token_secret)
    created = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={
            "result_type": "report",
            "target_token": token,
            "permission": "read",
            "ttl_days": 7,
        },
    )
    assert created.status_code == 201, created.text

    latest = client.get(
        "/api/share-link/latest",
        headers=auth_headers,
        params={"result_type": "report", "target_token": token},
    )
    assert latest.status_code == 200, latest.text
    body = latest.json()
    assert body["result_type"] == "report"
    assert body["target_type"] == "report"
    assert body["stats"]["access_count"] == 0
    assert body["share_url"].startswith("http://testserver/s/")
