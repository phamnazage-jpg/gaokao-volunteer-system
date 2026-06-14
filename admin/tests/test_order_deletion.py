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


def test_admin_delete_order_removes_artifacts_and_related_records(
    client, auth_headers, settings, tmp_path
):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={"candidate_score": 578, "guardian_notes": "to delete"},
        submit=True,
    )
    report_path, pdf_path = _prepare_order_with_artifacts(settings, tmp_path, order.id)

    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        assert len(notification_service.list_events(order.id)) == 1
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
    assert body["files_deleted"] == 2

    assert not report_path.exists()
    assert not pdf_path.exists()

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
    assert anonymized.candidate_name == "匿名考生"
    assert anonymized.notes == "[ANONYMIZED] retention_expired"

    deletion_service = OrderDeletionService.for_db(settings.orders_db_path)
    try:
        assert deletion_service.audit_count(order.id) == 1
    finally:
        deletion_service.close()
