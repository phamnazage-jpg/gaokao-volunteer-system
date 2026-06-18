from __future__ import annotations

import threading

import pytest

from data.orders.dao import OrdersDAO
from data.payments.dao import PaymentDAO
from data.orders.models import Order
from data.payments.models import PaymentRecord
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
    assert first.checkout_url == f"/pay/mock/{first.payment_id}"

    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.status == "pending"
    assert payment.amount_cents == 9900


def test_create_checkout_returns_same_payment_for_paid_order(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260617-PAID-REUSE")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )

    first = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=first.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-PAID-REUSE-001",
    )
    service.handle_webhook(payload, headers["X-Mock-Signature"])

    second = service.create_checkout(order.id, portal_token="portal-token")

    assert first.payment_id == second.payment_id
    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.status == "paid"

    payments = PaymentDAO.for_db(settings.orders_db_path)
    try:
        all_payments = payments.list_by_order(order.id)
    finally:
        payments.close()
    assert [item.id for item in all_payments] == [first.payment_id]


def test_payment_does_not_persist_plain_portal_token(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260618-TOKEN-STORAGE")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )

    service.create_checkout(order.id, portal_token="portal-token")

    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.checkout_token != "portal-token"


def test_create_checkout_is_serialized_to_single_pending_payment(
    settings, monkeypatch: pytest.MonkeyPatch
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260617-CONCURRENT-PAY")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )

    original_create = PaymentDAO.create

    def slow_create(self, payment):
        import time

        time.sleep(0.1)
        return original_create(self, payment)

    monkeypatch.setattr(PaymentDAO, "create", slow_create)

    results: list[str] = []
    errors: list[BaseException] = []

    def worker() -> None:
        local_service = PaymentService.for_db(
            settings.orders_db_path,
            base_url=settings.payment_base_url,
            webhook_secret=settings.payment_webhook_secret,
        )
        try:
            checkout = local_service.create_checkout(order.id, portal_token="portal-token")
            results.append(checkout.payment_id)
        except BaseException as exc:  # pragma: no cover - 调试兜底
            errors.append(exc)

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    second.start()
    first.join()
    second.join()

    assert not errors
    assert len(results) == 2
    assert len(set(results)) == 1

    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.status == "pending"
    payments = PaymentDAO.for_db(settings.orders_db_path)
    try:
        all_payments = payments.list_by_order(order.id)
    finally:
        payments.close()
    assert len(all_payments) == 1
    assert all_payments[0].status == "pending"


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


def test_handle_webhook_keeps_refunded_payment_terminal_state(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260617-REFUND-REPLAY")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-REFUND-REPLAY-001",
    )

    first = service.handle_webhook(payload, headers["X-Mock-Signature"])
    assert first.idempotent is False
    refund = service.request_refund(order.id, reason="parent_request")
    assert refund.status == "refunded"

    replay = service.handle_webhook(payload, headers["X-Mock-Signature"])
    assert replay.idempotent is True
    assert replay.order_status == "refunded"

    payment = service.get_payment(checkout.payment_id)
    assert payment is not None
    assert payment.status == "refunded"

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        refunded_order = dao.get(order.id)
        history = dao.get_status_history(order.id)
    assert refunded_order.status == "refunded"
    assert [item.to_status for item in history] == ["pending", "paid", "refunded"]


def test_failed_payment_state_is_not_rendered_as_portal_stage(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260618-PAYMENT-FAILED")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )

    checkout = service.create_checkout(order.id)
    payment = service.get_payment(checkout.payment_id)
    assert payment is not None

    from admin.routes.web_public import _build_portal_context

    failed_payment = PaymentRecord(
        id=payment.id,
        order_id=payment.order_id,
        provider=payment.provider,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
        status="failed",
        checkout_token=payment.checkout_token,
        callback_payload=payment.callback_payload,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )
    dao = PaymentDAO.for_db(settings.orders_db_path)
    try:
        dao.update_status(payment.id, status="failed")
    finally:
        dao.close()

    order = OrdersDAO.connect(settings.orders_db_path).get(order.id)
    assert order is not None
    context = _build_portal_context(order, settings)
    assert context["stage"] != "payment_failed"
