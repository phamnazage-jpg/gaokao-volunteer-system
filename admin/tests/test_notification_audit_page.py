from __future__ import annotations

from pathlib import Path

from data.customer_portal.token import issue_portal_token
from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260615-NOTIFY-AUDIT") -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张家长",
        customer_phone="13800138000",
        customer_email="parent@example.com",
        candidate_name="张三",
        candidate_province="湖南",
    )
    with OrdersDAO.connect(db_path) as dao:
        return dao.create(order, actor="test", reason="seed")


def _mark_paid(settings, order: Order) -> None:
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no=f"MOCK-{order.id}",
    )
    signature = headers.get("X-Mock-Signature", "") if isinstance(headers, dict) else ""
    handled = service.handle_webhook(payload, signature)
    assert handled.order_status == "paid"


def test_notification_audit_page_shows_station_and_email_events(client, settings, tmp_path: Path):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={"candidate_score": 578},
        submit=True,
    )

    report_path = tmp_path / "notify-audit-report.html"
    pdf_path = tmp_path / "notify-audit-report.pdf"
    report_path.write_text("<h1>report</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nnotify\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(order.id, "delivered", actor="test", reason="report_ready")

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = notification_service.list_events(order.id)
    finally:
        notification_service.close()
    assert {e.channel for e in events} == {"station", "email"}

    token = issue_portal_token(order.id, settings.portal_token_secret)
    page = client.get(f"/portal/{token}/notifications")
    assert page.status_code == 200, page.text
    assert "通知审计" in page.text
    assert '/static/portal-ui.css' in page.text
    assert "返回订单状态页" in page.text
    assert order.id in page.text
    assert "station" in page.text
    assert "email" in page.text
    assert "report_ready" in page.text
    assert "report_ready" in page.text

def test_viewer_cannot_access_notification_admin_page(client, viewer_headers, settings, tmp_path: Path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-NOTIFY-VIEWER")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )

    report_path = tmp_path / "viewer-report.html"
    pdf_path = tmp_path / "viewer-report.pdf"
    report_path.write_text("<h1>report</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nviewer\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(order.id, "delivered", actor="test", reason="report_ready")

    resp = client.get("/admin/notifications", headers=viewer_headers)
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "E01301"


def test_notification_audit_page_hides_payload_details(client, settings, tmp_path: Path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-NOTIFY-HIDE")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={"candidate_score": 578},
        submit=True,
    )

    report_path = tmp_path / "notify-hide-report.html"
    pdf_path = tmp_path / "notify-hide-report.pdf"
    report_path.write_text("<h1>report</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nnotify-hide\n")
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
    page = client.get(f"/portal/{token}/notifications")
    assert page.status_code == 200, page.text
    assert "parent@example.com" not in page.text
    assert str(report_path) not in page.text
    assert str(pdf_path) not in page.text
    assert "report_ready" in page.text


def test_notification_audit_api_masks_internal_paths_and_customer_email(
    client, auth_headers, settings, tmp_path: Path
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260618-NOTIFY-API")
    _mark_paid(settings, order)

    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="email",
            payload_json='{"kind":"email","customer_email":"parent@example.com","report_path":"/tmp/report.pdf"}',
        )
    finally:
        service.close()

    resp = client.get(f"/api/admin/notifications?order_id={order.id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"]
    payload = body["items"][0]["payload"]
    assert payload["kind"] == "email"
    assert "customer_email" not in payload
    assert "report_path" not in payload


def test_status_page_links_to_notification_audit(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-NOTIFY-LINK")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    page = client.get(f"/portal/{token}/status")
    assert page.status_code == 200, page.text
    assert f"/portal/{token}/notifications" in page.text
