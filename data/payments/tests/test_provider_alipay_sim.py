from __future__ import annotations

from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-ALIPAY-SIM") -> Order:
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


def test_alipay_sim_provider_checkout_shape_and_idempotency(settings):
    order = _seed_order(settings.orders_db_path)
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
        provider_name="alipay_sim",
    )

    first = service.create_checkout(order.id, portal_token="portal-token")
    second = service.create_checkout(order.id, portal_token="portal-token")

    assert first.payment_id == second.payment_id
    assert first.provider == "alipay_sim"
    assert first.checkout_url.endswith(
        f"/pay/alipay-sim/{first.payment_id}?token=portal-token"
    )


def test_alipay_sim_webhook_marks_order_paid(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-ALIPAY-WEBHOOK")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
        provider_name="alipay_sim",
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="ALIPAY-SIM-001",
    )

    handled = service.handle_webhook(payload, headers["X-Alipay-Sim-Signature"])
    assert handled.idempotent is False
    assert handled.order_status == "paid"

    again = service.handle_webhook(payload, headers["X-Alipay-Sim-Signature"])
    assert again.idempotent is True
