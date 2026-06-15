from __future__ import annotations

import json
import subprocess
from pathlib import Path

from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _seed_order(
    db_path: str,
    order_id: str = "GKO-20260614-DISPATCH",
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


def _attach_ready_delivery(settings, tmp_path: Path, order_id: str) -> None:
    report_path = tmp_path / f"{order_id}-report.html"
    pdf_path = tmp_path / f"{order_id}-report.pdf"
    report_path.write_text("<h1>ready</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nready\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order_id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order_id, "serving", actor="test", reason="processing")
        dao.transition_status(
            order_id, "delivered", actor="test", reason="report_ready"
        )


def test_dispatch_ready_station_event_marks_sent(settings, tmp_path):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    from data.notifications.dispatcher import DeliveryDispatcher

    dispatcher = DeliveryDispatcher.for_db(settings.orders_db_path)
    try:
        result = dispatcher.dispatch_ready_events(channel="station")
    finally:
        dispatcher.close()

    assert result.processed == 1
    assert result.sent == 1
    assert result.failed == 0

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        event = notification_service.list_events(order.id)[0]
    finally:
        notification_service.close()
    assert event.status == "sent"
    assert event.attempt_count == 1
    payload = json.loads(event.payload_json)
    station_notice = payload.get("station_notice")
    assert station_notice is not None
    assert station_notice["title"] == "报告已就绪"
    assert order.id in station_notice["body"]
    assert station_notice["sent_at"] == event.last_attempt_at


class _FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send_report_ready(
        self, *, recipient: str, order_id: str, subject: str, body: str
    ) -> dict[str, str]:
        payload = {
            "recipient": recipient,
            "order_id": order_id,
            "subject": subject,
            "body": body,
        }
        self.sent.append(payload)
        return payload


def test_dispatch_ready_email_event_marks_sent(settings, tmp_path):
    order = _seed_order(
        settings.orders_db_path,
        order_id="GKO-20260614-DISPATCH-EMAIL",
        customer_email="parent@example.com",
    )
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    from data.notifications.dispatcher import DeliveryDispatcher

    email_sender = _FakeEmailSender()
    dispatcher = DeliveryDispatcher.for_db(
        settings.orders_db_path,
        email_sender=email_sender,
    )
    try:
        result = dispatcher.dispatch_ready_events(channel="email")
    finally:
        dispatcher.close()

    assert result.processed == 1
    assert result.sent == 1
    assert result.failed == 0
    assert len(email_sender.sent) == 1
    assert email_sender.sent[0]["recipient"] == "parent@example.com"

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        event = notification_service.list_events(order.id, channel="email")[0]
    finally:
        notification_service.close()
    assert event.status == "sent"
    payload = json.loads(event.payload_json)
    email_notice = payload.get("email_notice")
    assert email_notice is not None
    assert email_notice["recipient"] == "parent@example.com"
    assert email_notice["subject"]


def test_dispatch_ready_station_event_marks_failed_when_pdf_missing(settings, tmp_path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-DISPATCH-FAIL")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        current = dao.get(order.id)
    assert current.pdf_path is not None
    Path(current.pdf_path).unlink()

    from data.notifications.dispatcher import DeliveryDispatcher

    dispatcher = DeliveryDispatcher.for_db(settings.orders_db_path)
    try:
        result = dispatcher.dispatch_ready_events(channel="station")
    finally:
        dispatcher.close()

    assert result.processed == 1
    assert result.sent == 0
    assert result.failed == 1

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        failed_event = notification_service.list_events(order.id)[0]
    finally:
        notification_service.close()
    assert failed_event.status == "failed"
    assert failed_event.attempt_count == 2
    assert failed_event.failure_reason == "delivery artifact missing"


def test_delivery_dispatch_script_prints_summary(settings, tmp_path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-DISPATCH-CLI")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    env = {
        **__import__("os").environ,
        "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path,
    }
    proc = subprocess.run(
        ["python3", "scripts/gaokao-delivery-dispatch.py", "--channel", "station"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert '"processed": 1' in proc.stdout
    assert '"sent": 1' in proc.stdout


def test_delivery_watchdog_exits_zero_when_no_failures(settings, tmp_path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WATCHDOG-OK")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    env = {
        **__import__("os").environ,
        "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path,
    }
    proc = subprocess.run(
        ["python3", "scripts/gaokao-delivery-watchdog.py", "--channel", "station"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert '"failed": 0' in proc.stdout


def test_delivery_watchdog_exits_nonzero_when_failures_detected(settings, tmp_path):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WATCHDOG-FAIL")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        current = dao.get(order.id)
    assert current.pdf_path is not None
    Path(current.pdf_path).unlink()

    env = {
        **__import__("os").environ,
        "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path,
    }
    proc = subprocess.run(
        ["python3", "scripts/gaokao-delivery-watchdog.py", "--channel", "station"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert '"failed": 1' in proc.stdout
