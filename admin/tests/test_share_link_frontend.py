from __future__ import annotations

from admin.tests.test_order_status_page import _mark_paid, _seed_order
from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO


def test_review_result_page_no_longer_uses_window_location_for_share_buttons(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260629-SHARE-REVIEW-UI")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    resp = client.get(f"/review/start?source=status&token={token}")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "/api/share-link" in body
    assert "navigator.share" in body
    assert "target_token" in body
    assert "ttl_days: 7" in body or 'ttl_days": 7' in body or "ttl_days:7" in body
    assert "navigator.share({ title: summary, text: summary, url: url })" not in body
    assert "copy-link-btn" in body
    assert "report-share-btn" not in body



def test_report_ready_status_page_no_longer_uses_window_location_for_share_buttons(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260629-SHARE-STATUS-UI")
    _mark_paid(settings, order)
    report_root = __import__('pathlib').Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "share-status-report.html"
    pdf_path = report_root / "share-status-report.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nshare-status\n")
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
    resp = client.get(f"/portal/{token}/status")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "/api/share-link" in body
    assert "navigator.share" in body
    assert "target_token" in body
    assert "ttl_days: 7" in body or 'ttl_days": 7' in body or "ttl_days:7" in body
    assert "navigator.share({ title: '志愿报告', url: window.location.href })" not in body
    assert "report-copy-link" in body
    assert "report-share-btn" in body
