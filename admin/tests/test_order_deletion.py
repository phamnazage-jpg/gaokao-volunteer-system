from __future__ import annotations

from pathlib import Path

from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrderNotFound, OrdersDAO
from data.orders.deletion_service import OrderDeletionService
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-DELETE") -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张家长",
        customer_phone="13800138000",
        customer_wechat="wx-parent-01",
        customer_email="parent@example.com",
        candidate_name="张三",
        candidate_province="湖南",
        notes="需要删除的测试订单",
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


def _prepare_order_with_artifacts(
    settings, tmp_path: Path, order_id: str
) -> tuple[Path, Path]:
    report_path = tmp_path / f"{order_id}-report.html"
    pdf_path = tmp_path / f"{order_id}-report.pdf"
    report_path.write_text("<h1>report</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\ndelete\n")
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
    return report_path, pdf_path

def _prepare_portal_attachment(settings, order_id: str) -> Path:
    upload_dir = Path(settings.portal_upload_dir) / order_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    attachment = upload_dir / "score-sheet.pdf"
    attachment.write_bytes(b"%PDF-1.4\nportal-upload\n")
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order_id,
        payload={
            "candidate_score": 578,
            "attachments": [
                {
                    "original_name": "score-sheet.pdf",
                    "stored_name": "score-sheet.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": attachment.stat().st_size,
                    "storage_path": str(attachment),
                    "kind": "portal_attachment",
                }
            ],
        },
        submit=True,
    )
    return attachment


def test_admin_delete_order_removes_artifacts_and_related_records(
    client, auth_headers, settings, tmp_path
):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    attachment = _prepare_portal_attachment(settings, order.id)
    report_path, pdf_path = _prepare_order_with_artifacts(settings, tmp_path, order.id)

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = notification_service.list_events(order.id)
        assert {event.channel for event in events} == {"station", "email"}
    finally:
        notification_service.close()

    resp = client.delete(
        f"/api/orders/{order.id}?mode=delete&reason=user_request",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["action"] == "deleted"
    assert body["order_id"] == order.id
    assert body["files_deleted"] == 3

    assert not report_path.exists()
    assert not pdf_path.exists()
    assert not attachment.exists()
    assert not attachment.parent.exists()

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            dao.get(order.id)
        except OrderNotFound:
            pass
        else:
            raise AssertionError("order should be deleted")

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        assert notification_service.list_events(order.id) == []
    finally:
        notification_service.close()

    deletion_service = OrderDeletionService.for_db(settings.orders_db_path)
    try:
        assert deletion_service.audit_count(order.id) == 1
    finally:
        deletion_service.close()


def test_admin_anonymize_order_masks_pii_but_keeps_order(
    client, auth_headers, settings
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-ANON")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={"candidate_score": 578, "guardian_notes": "contains pii"},
        submit=True,
    )

    resp = client.delete(
        f"/api/orders/{order.id}?mode=anonymize&reason=retention_expired",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["action"] == "anonymized"
    assert body["order_id"] == order.id

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        anonymized = dao.get(order.id)
    assert anonymized.customer_name == "已匿名化"
    assert anonymized.customer_phone is None
    assert anonymized.customer_wechat is None
    assert anonymized.customer_email is None
    assert anonymized.candidate_name == "匿名考生"
    assert anonymized.notes == "[ANONYMIZED] retention_expired"

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(order.id)
    finally:
        intake_store.close()
    assert intake is not None
    assert intake.payload == {}

    payment_service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    payment = payment_service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.callback_payload is None
    assert payment.checkout_token is None

    deletion_service = OrderDeletionService.for_db(settings.orders_db_path)
    try:
        assert deletion_service.audit_count(order.id) == 1
    finally:
        deletion_service.close()


def test_admin_anonymize_order_removes_portal_attachments(
    client, auth_headers, settings
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-ANON-FILE")
    _mark_paid(settings, order)
    attachment = _prepare_portal_attachment(settings, order.id)

    resp = client.delete(
        f"/api/orders/{order.id}?mode=anonymize&reason=retention_expired",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["action"] == "anonymized"
    assert body["files_deleted"] == 1

    assert not attachment.exists()
    assert not attachment.parent.exists()

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(order.id)
    finally:
        intake_store.close()
    assert intake is not None
    assert intake.payload == {}


def test_admin_anonymize_order_scrubs_delivery_notifications_payload(
    client, auth_headers, settings
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260618-ANON-NOTIFY")
    _mark_paid(settings, order)

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        notification_service.notify_event(
            order.id,
            event_type="report_ready",
            channel="station",
            payload_json='{"customer_email":"parent@example.com","report_path":"/tmp/report.pdf"}',
        )
        notification_service.mark_delivered(
            order.id,
            channel="station",
            payload_json='{"customer_email":"parent@example.com","report_path":"/tmp/report.pdf"}',
        )
    finally:
        notification_service.close()

    resp = client.delete(
        f"/api/orders/{order.id}?mode=anonymize&reason=retention_expired",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = notification_service.list_events(order.id)
    finally:
        notification_service.close()

    assert len(events) == 1
    assert events[0].payload_json == "{}"
