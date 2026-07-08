from __future__ import annotations

from pathlib import Path

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

