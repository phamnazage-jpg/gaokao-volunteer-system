from __future__ import annotations

from pathlib import Path

from admin.tests.order_test_helpers import _mark_paid, _seed_order, _seed_review_result
from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.share.short_link import ShortLinkService


def test_share_link_requires_auth(client):
    resp = client.post(
        "/api/share-link",
        json={"result_type": "review_result", "target_token": "fake", "permission": "read", "ttl_days": 7},
    )
    assert resp.status_code == 401



def test_viewer_cannot_create_share_link(client, viewer_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260629-SHARE-VIEWER")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    resp = client.post(
        "/api/share-link",
        headers=viewer_headers,
        json={"result_type": "review_result", "target_token": token, "permission": "read", "ttl_days": 7},
    )
    assert resp.status_code == 403, resp.text



def test_admin_can_create_review_result_share_link(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260629-SHARE-REVIEW")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    _seed_review_result(settings, token)

    resp = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={"result_type": "review_result", "target_token": token, "permission": "read", "ttl_days": 7},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["share_url"].startswith("http://testserver/s/")
    assert body["permission"] == "read"
    assert body["result_type"] == "review_result"
    assert body["target_type"] == "review_result"
    assert body["expires_at_iso"] is not None

    code = body["share_url"].rsplit("/", 1)[1]
    svc = ShortLinkService(db_path=settings.share_db_path)
    link = svc.get(code)
    assert link is not None
    assert link.permission == "read"
    assert link.expires_at is not None

    shared_page = client.get(f"/s/{code}")
    assert shared_page.status_code == 200, shared_page.text
    assert "权限：read" in shared_page.text
    assert "分享链接：" in shared_page.text



def test_admin_can_create_report_share_link(client, auth_headers, settings, tmp_path: Path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260629-SHARE-REPORT")
    _mark_paid(settings, order)
    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "share-report.html"
    pdf_path = report_root / "share-report.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nshare\n")
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

    resp = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={"result_type": "report", "target_token": token, "permission": "read", "ttl_days": 7},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["result_type"] == "report"
    assert body["target_type"] == "report"
    assert body["share_url"].startswith("http://testserver/s/")



def test_admin_can_revoke_share_link(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260629-SHARE-REVOKE")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    _seed_review_result(settings, token)

    created = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={"result_type": "review_result", "target_token": token, "permission": "read", "ttl_days": 7},
    )
    assert created.status_code == 201, created.text
    code = created.json()["share_url"].rsplit("/", 1)[1]

    revoke = client.post(f"/api/share-link/{code}/revoke", headers=auth_headers)
    assert revoke.status_code == 200, revoke.text
    body = revoke.json()
    assert body["code"] == code
    assert body["revoked"] is True

    shared_page = client.get(f"/s/{code}")
    assert shared_page.status_code == 410
    assert "分享已撤销" in shared_page.text
