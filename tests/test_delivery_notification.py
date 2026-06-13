from __future__ import annotations

from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-NOTIFY") -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张家长",
        customer_phone="13800138000",
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
    service.handle_webhook(payload, headers["X-Mock-Signature"])


def test_report_ready_transition_creates_notification_event(
    client, auth_headers, settings, tmp_path
):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )

    report_path = tmp_path / "notify-report.html"
    pdf_path = tmp_path / "notify-report.pdf"
    report_path.write_text("<h1>已生成</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nnotify\n")

    serving = client.patch(
        f"/api/orders/{order.id}",
        headers=auth_headers,
        json={"to_status": "serving", "reason": "begin_processing"},
    )
    assert serving.status_code == 200, serving.text

    delivered = client.patch(
        f"/api/orders/{order.id}",
        headers=auth_headers,
        json={
            "updates": {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            "to_status": "delivered",
            "reason": "report_ready",
        },
    )
    assert delivered.status_code == 200, delivered.text

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = notification_service.list_events(order.id)
    finally:
        notification_service.close()
    assert len(events) == 1
    assert events[0].event_type == "report_ready"
