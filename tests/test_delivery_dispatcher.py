from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService

from data.notifications.dispatcher import DeliveryDispatcher



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


def test_dispatch_ready_station_event_validates_persisted_payload(
    settings, tmp_path
):
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
    # station channel is local render only; ``delivered`` must be 0.
    assert result.delivered == 0
    assert result.validated == 1
    assert result.failed == 0
    assert not hasattr(result, "sent")

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        event = notification_service.list_events(order.id)[0]
    finally:
        notification_service.close()
    assert event.status == "validated"
    assert event.attempt_count == 1
    payload = json.loads(event.payload_json)
    # The portal page consumes ``station_notice`` from the persisted
    # payload even though ``station`` does not transition to
    # ``delivered``; the dispatcher stashes it during ``mark_validated``.
    station_notice = payload.get("station_notice")
    assert station_notice is not None
    assert station_notice["title"] == "报告已就绪"
    assert order.id in station_notice["body"]

def test_dispatch_station_marks_validated_then_delivered(settings, tmp_path):
    """P2-3 lock: ``station`` channel cannot be reported as ``delivered``.

    The lifecycle is now ``ready`` -> ``validated``.  ``delivered`` is
    reserved for channels that actually push the notice externally
    (today: ``email``).  This test re-asserts the new chain so future
    regressions that flatten the lifecycle back to a single ``sent``
    step will fail.
    """
    order = _seed_order(
        settings.orders_db_path,
        order_id="GKO-20260614-DISPATCH-STATION-DELIVERED",
    )
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )
    _attach_ready_delivery(settings, tmp_path, order.id)

    dispatcher = DeliveryDispatcher.for_db(settings.orders_db_path)
    try:
        result = dispatcher.dispatch_ready_events(channel="station")
    finally:
        dispatcher.close()

    assert result.processed == 1
    assert result.validated == 1
    assert result.delivered == 0
    assert result.failed == 0
    assert not hasattr(result, "sent")

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        event = notification_service.list_events(order.id)[0]
    finally:
        notification_service.close()
    assert event.status == "validated"


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
    assert result.delivered == 1
    assert result.failed == 0
    assert len(email_sender.sent) == 1
    assert email_sender.sent[0]["recipient"] == "parent@example.com"

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        event = notification_service.list_events(order.id, channel="email")[0]
    finally:
        notification_service.close()
    assert event.status == "delivered"
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
    assert result.failed == 1
    assert result.validated == 0
    assert result.delivered == 0

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
        [sys.executable, "scripts/gaokao-delivery-dispatch.py", "--channel", "station"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert '"processed": 1' in proc.stdout
    assert '"validated": 1' in proc.stdout
    assert '"delivered": 0' in proc.stdout


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
        [sys.executable, "scripts/gaokao-delivery-watchdog.py", "--channel", "station"],
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
        [sys.executable, "scripts/gaokao-delivery-watchdog.py", "--channel", "station"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert '"failed": 1' in proc.stdout


def test_retention_cleanup_scrubs_notification_payload_for_expired_orders(settings):
    from data.orders.retention_cleanup import run_cleanup

    order = Order(
        id="GKO-20250101-RETENTION-NOTIFY",
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="completed",
        customer_name="张家长",
        customer_phone="13800138000",
        candidate_name="张三",
        candidate_province="湖南",
        created_at="2025-01-01T00:00:00+00:00",
        completed_at="2025-01-02T00:00:00+00:00",
        status_updated_at="2025-01-02T00:00:00+00:00",
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.create(order, actor="test", reason="seed_old_completed")

    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="email",
            payload_json='{"customer_email":"parent@example.com","detail":"keep"}',
        )
    finally:
        service.close()

    result = run_cleanup(
        settings.orders_db_path,
        cutoff_iso="2025-06-30T00:00:00+00:00",
        apply=True,
    )

    assert result.anonymized == 1
    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = service.list_events(order.id)
    finally:
        service.close()
    assert len(events) == 1
    assert events[0].payload_json == "{}"


def test_share_access_events_have_retention_cleanup(settings):
    from data.orders.retention_cleanup import run_cleanup
    from data.share.short_link import ShortLinkService

    order = Order(
        id="GKO-20250101-RETENTION-SHARE",
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="completed",
        customer_name="张家长",
        customer_phone="13800138000",
        candidate_name="张三",
        candidate_province="湖南",
        created_at="2025-01-01T00:00:00+00:00",
        completed_at="2025-01-02T00:00:00+00:00",
        status_updated_at="2025-01-02T00:00:00+00:00",
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.create(order, actor="test", reason="seed_old_completed")

    share = ShortLinkService(db_path=settings.share_db_path)
    link = share.create(report_id=order.id)
    share.resolve(link.code, visitor_token="visitor-1")

    result = run_cleanup(
        settings.orders_db_path,
        cutoff_iso="2025-06-30T00:00:00+00:00",
        apply=True,
        share_db_path=settings.share_db_path,
    )

    assert result.anonymized == 1
    with share._connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM share_link_access_events WHERE code=?",
            (link.code,),
        ).fetchone()
    assert row is not None
    assert int(row[0]) == 0
