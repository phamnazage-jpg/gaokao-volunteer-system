from __future__ import annotations

from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-PAY") -> Order:
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


def test_create_checkout_is_idempotent_for_pending_payment(settings):
    order = _seed_order(settings.orders_db_path)
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )

    first = service.create_checkout(order.id, portal_token="portal-token")
    second = service.create_checkout(order.id, portal_token="portal-token")

    assert first.payment_id == second.payment_id
    assert first.provider == "mock"
    assert first.checkout_url.endswith(
        f"/pay/mock/{first.payment_id}?token=portal-token"
    )

    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.status == "pending"
    assert payment.amount_cents == 9900


def test_request_refund_is_idempotent_after_payment_success(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-REFUND-SVC")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")

    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-PAID-001",
    )
    handled = service.handle_webhook(payload, headers["X-Mock-Signature"])
    assert handled.order_status == "paid"

    first = service.request_refund(order.id, reason="parent_request")
    second = service.request_refund(order.id, reason="duplicate_request")

    assert first.status == "refund_pending"
    assert second.status == "refund_pending"
    assert first.payment_id == second.payment_id
