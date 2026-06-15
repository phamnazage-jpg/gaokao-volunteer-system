from __future__ import annotations

from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(
    db_path: str,
    order_id: str = "GKO-20260614-NOTIFY",
    *,
    customer_email: str | None = None,
) -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张家长",
        customer_phone="13800138000",
        customer_email=customer_email,
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
    assert events[0].status == "ready"
    assert events[0].attempt_count == 1
    assert events[0].failure_reason is None


def test_dao_delivered_transition_also_creates_notification_event(settings, tmp_path):
    order = _seed_order(
        settings.orders_db_path,
        order_id="GKO-20260614-NOTIFY-DAO",
        customer_email="parent@example.com",
    )
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )

    report_path = tmp_path / "dao-report.html"
    pdf_path = tmp_path / "dao-report.pdf"
    report_path.write_text("<h1>dao</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\ndao\n")

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

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = notification_service.list_events(order.id)
    finally:
        notification_service.close()
    assert len(events) == 2
    event_types = {(event.channel, event.event_type) for event in events}
    assert ("station", "report_ready") in event_types
    assert ("email", "report_ready_email") in event_types
    email_event = next(event for event in events if event.channel == "email")
    assert "parent@example.com" in email_event.payload_json


def test_delivery_notification_tracks_failure_and_sent_status(settings, tmp_path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-NOTIFY-STATUS")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )

    report_path = tmp_path / "status-report.html"
    pdf_path = tmp_path / "status-report.pdf"
    report_path.write_text("<h1>status</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nstatus\n")

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

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        notification_service.mark_failed(order.id, "smtp timeout")
        failed = notification_service.list_events(order.id)[0]
        assert failed.status == "failed"
        assert failed.attempt_count == 2
        assert failed.failure_reason == "smtp timeout"
        assert failed.last_attempt_at is not None

        notification_service.mark_sent(order.id)
        sent = notification_service.list_events(order.id)[0]
        assert sent.status == "sent"
        assert sent.attempt_count == 2
        assert sent.failure_reason is None
        assert sent.last_attempt_at is not None
    finally:
        notification_service.close()
