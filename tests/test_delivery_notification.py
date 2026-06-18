from __future__ import annotations

import pytest

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


def test_report_ready_transition_creates_notification_event(settings, tmp_path):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )

    report_path = tmp_path / "notify-report.html"
    pdf_path = tmp_path / "notify-report.pdf"
    report_path.write_text("<h1>已生成</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nnotify\n")

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="begin_processing")
        dao.transition_status(
            order.id, "delivered", actor="test", reason="report_ready"
        )

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
    assert ("email", "report_ready") in event_types
    email_event = next(event for event in events if event.channel == "email")
    assert "parent@example.com" in email_event.payload_json


def test_delivery_notification_distinguishes_channel_in_unique_key(settings):
    order = _seed_order(
        settings.orders_db_path,
        order_id="GKO-20260617-NOTIFY-CHANNEL-UNIQUE",
        customer_email="parent@example.com",
    )
    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="station",
            payload_json='{"kind":"station"}',
        )
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="email",
            payload_json='{"kind":"email"}',
        )
        events = service.list_events(order.id)
        assert {event.channel for event in events} == {"station", "email"}
    finally:
        service.close()


def test_delivery_notification_rejects_duplicate_same_channel_same_event(settings):
    order = _seed_order(
        settings.orders_db_path,
        order_id="GKO-20260617-NOTIFY-CHANNEL-DUP",
    )
    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="station",
            payload_json='{"kind":"station"}',
        )
        with pytest.raises(ValueError):
            service.notify_event(
                order.id,
                event_type="report_ready",
                channel="station",
                payload_json='{"kind":"station-2"}',
            )
    finally:
        service.close()


def test_delivery_notification_tracks_failure_and_validated_status(settings, tmp_path):
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
        notification_service.mark_failed(order.id, "smtp timeout", channel="station")
        failed = notification_service.list_events(order.id)[0]
        assert failed.status == "failed"
        assert failed.attempt_count == 2
        assert failed.failure_reason == "smtp timeout"
        assert failed.last_attempt_at is not None

        notification_service.mark_validated(order.id, channel="station")
        validated = notification_service.list_events(order.id)[0]
        assert validated.status == "validated"
        assert validated.attempt_count == 2
        assert validated.failure_reason == "smtp timeout"
        assert validated.last_attempt_at is not None
    finally:
        notification_service.close()


def test_delivery_notification_service_excludes_sent_legacy_status():
    from data.notifications import email_service

    assert "sent" not in email_service.DELIVERY_EVENT_STATUSES
    assert not hasattr(email_service.DeliveryNotificationService, "mark_sent")
