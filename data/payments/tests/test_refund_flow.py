from __future__ import annotations

from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-REFUND") -> Order:
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


def _mark_paid(settings, order: Order) -> PaymentService:
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
    return service


def test_refund_request_marks_portal_as_refunded(client, settings):
    order = _seed_order(settings.orders_db_path)
    service = _mark_paid(settings, order)

    first = service.request_refund(order.id, reason="parent_request")
    second = service.request_refund(order.id, reason="duplicate_request")

    assert first.status == "refunded"
    assert second.status == "refunded"

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        reloaded = dao.get(order.id)
    assert reloaded.status == "refunded", (
        "refund request must close the order side of the loop as well"
    )

    token = issue_portal_token(order.id, settings.portal_token_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "已退款" in status_page.text
    assert "退款申请中" not in status_page.text


def test_refund_pending_legacy_status_is_removed():
    from data.payments import dao as payment_dao

    assert "refund_pending" not in payment_dao.SCHEMA_SQL
