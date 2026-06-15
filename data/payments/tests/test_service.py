from __future__ import annotations

import pytest

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

    assert first.status == "refunded"
    assert second.status == "refunded"
    assert first.payment_id == second.payment_id

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        reloaded = dao.get(order.id)
    assert reloaded.status == "refunded", (
        "refund request must also move the order into the refunded terminal state"
    )

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        refunded_order = dao.get(order.id)
        history = dao.get_status_history(order.id)
    assert refunded_order.status == "refunded"
    assert [item.to_status for item in history] == ["pending", "paid", "refunded"]


def test_handle_webhook_rolls_back_payment_if_order_transition_fails(
    settings, monkeypatch: pytest.MonkeyPatch
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WEBHOOK-ATOMIC")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-ATOMIC-001",
    )

    original_transition = OrdersDAO.transition_status

    def fail_transition(self, order_id, to_status, *, actor=None, reason=None):
        if order_id == order.id and to_status == "paid":
            raise RuntimeError("boom during order transition")
        return original_transition(
            self, order_id, to_status, actor=actor, reason=reason
        )

    monkeypatch.setattr(OrdersDAO, "transition_status", fail_transition)

    with pytest.raises(RuntimeError, match="boom during order transition"):
        service.handle_webhook(payload, headers["X-Mock-Signature"])

    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.status == "pending"

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        reloaded = dao.get(order.id)
        history = dao.get_status_history(order.id)
    assert reloaded.status == "pending"
    assert [item.to_status for item in history] == ["pending"]
