from __future__ import annotations

from pathlib import Path

from admin.tests.test_order_status_page import _mark_paid, _seed_order
from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO


def test_review_result_page_renders_share_status_panel(client, auth_headers, settings):
    order = _seed_order(
        settings.orders_db_path, order_id="GKO-20260629-SHARE-REVIEW-PANEL"
    )
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text
    create = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={
            "result_type": "review_result",
            "target_token": token,
            "permission": "read",
            "ttl_days": 7,
        },
    )
    assert create.status_code == 201, create.text

    resp = client.get(f"/review/start?source=status&token={token}")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "当前分享状态" in body
    assert "复制正式分享链接" in body
    assert "重新生成分享链接" in body
    assert "撤销当前分享链接" in body
    assert "/portal/share-link/latest?result_type=review_result" in body
    assert "/portal/share-link" in body
    assert "/revoke" in body


def test_report_ready_status_page_renders_share_status_panel(
    client, auth_headers, settings
):
    order = _seed_order(
        settings.orders_db_path, order_id="GKO-20260629-SHARE-STATUS-PANEL"
    )
    _mark_paid(settings, order)
    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "share-status-panel-report.html"
    pdf_path = report_root / "share-status-panel-report.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nshare-status-panel\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(
            order.id, "delivered", actor="test", reason="report_ready"
        )

    token = issue_portal_token(order.id, settings.portal_token_secret)
    create = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={
            "result_type": "report",
            "target_token": token,
            "permission": "read",
            "ttl_days": 7,
        },
    )
    assert create.status_code == 201, create.text

    resp = client.get(f"/portal/{token}/status")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "当前分享状态" in body
    assert "复制正式分享链接" in body
    assert "重新生成分享链接" in body
    assert "撤销当前分享链接" in body
    assert "最近一次分享：read" in body
    assert "/portal/share-link/latest?result_type=report" in body


def test_portal_review_share_link_lifecycle(client, settings):
    order = _seed_order(
        settings.orders_db_path, order_id="GKO-20260629-SHARE-PORTAL-LIFECYCLE"
    )
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text

    latest_missing = client.get(
        "/portal/share-link/latest",
        params={"result_type": "review_result", "target_token": token},
    )
    assert latest_missing.status_code == 404

    create = client.post(
        "/portal/share-link",
        json={
            "result_type": "review_result",
            "target_token": token,
            "permission": "read",
            "ttl_days": 7,
        },
    )
    assert create.status_code == 201, create.text
    created = create.json()
    code = created["share_url"].rsplit("/", 1)[1]

    latest = client.get(
        "/portal/share-link/latest",
        params={"result_type": "review_result", "target_token": token},
    )
    assert latest.status_code == 200, latest.text
    latest_body = latest.json()
    assert latest_body["code"] == code
    assert latest_body["stats"]["access_count"] == 0
    assert latest_body["permission"] == "read"

    revoke = client.post(
        f"/portal/share-link/{code}/revoke",
        json={"result_type": "review_result", "target_token": token},
    )
    assert revoke.status_code == 200, revoke.text
    revoke_body = revoke.json()
    assert revoke_body["code"] == code
    assert revoke_body["revoked"] is True

    shared_page = client.get(f"/s/{code}")
    assert shared_page.status_code == 410
    assert "分享已撤销" in shared_page.text
