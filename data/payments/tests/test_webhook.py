from __future__ import annotations

from typing import Any, cast

import pytest
from starlette.requests import Request

from admin.routes.web_public import mock_payment_webhook
from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentError, PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-WEBHOOK") -> Order:
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


def test_mock_payment_webhook_marks_order_paid_and_is_idempotent(
    route_client, settings
):
    order = _seed_order(settings.orders_db_path)
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-ORDER-001",
    )

    first = route_client.post(
        "/api/public/payments/mock/webhook", json=payload, headers=headers
    )
    assert first.status_code == 200, first.text
    assert first.json()["processed"] is True
    assert first.json()["idempotent"] is False

    second = route_client.post(
        "/api/public/payments/mock/webhook", json=payload, headers=headers
    )
    assert second.status_code == 200, second.text
    assert second.json()["processed"] is True
    assert second.json()["idempotent"] is True

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        updated = dao.get(order.id)
        history = dao.get_status_history(order.id)
    assert updated.status == "paid"
    assert [item.to_status for item in history] == ["pending", "paid"]


def test_mock_payment_webhook_rejects_amount_mismatch(route_client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WEBHOOK-AMOUNT")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=1,
        provider_trade_no="MOCK-AMOUNT-WRONG",
    )

    resp = route_client.post(
        "/api/public/payments/mock/webhook", json=payload, headers=headers
    )
    assert resp.status_code == 409, resp.text

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        unchanged = dao.get(order.id)
    assert unchanged.status == "pending"


def test_handle_webhook_persists_failed_status(settings):
    """6/19: 失败 webhook 必须持久化 payment.status='failed', 不再只抛 PaymentError.

    之前的契约 (test_handle_webhook_rejects_non_success_status) 让失败 webhook 抛 PaymentError,
    导致 portal/admin 看 payment 仍为 pending, 用户/客服无法判断真实支付状态.
    """
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260619-WEBHOOK-FAILED")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-FAILED-001",
    )
    payload = cast(dict[str, Any], payload)
    headers = cast(dict[str, str], headers)
    payload["status"] = "TRADE_CLOSED"
    payload["failure_reason"] = "buyer_closed_payment"
    headers["X-Mock-Signature"] = service.provider.sign_payload(payload)

    result = service.handle_webhook(payload, headers["X-Mock-Signature"])

    assert result.processed is True
    assert result.idempotent is False
    assert result.payment_id == checkout.payment_id

    # 订单保持 pending (失败支付不应该推进订单状态机)
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        kept = dao.get(order.id)
    assert kept.status == "pending"

    # 关键: payment 行已持久化为 failed, 留有 callback_payload + failure_reason
    payment = service.get_payment_by_order(order.id)
    assert payment is not None
    assert payment.status == "failed"
    assert payment.provider_trade_no == "MOCK-FAILED-001"
    assert payment.callback_payload is not None
    assert "TRADE_CLOSED" in payment.callback_payload
    # 新加字段: failed_at 与 failure_reason
    assert getattr(payment, "failed_at", None) is not None
    assert getattr(payment, "failure_reason", None) == "buyer_closed_payment"


def test_handle_webhook_rejects_app_id_mismatch(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WEBHOOK-APPID")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    setattr(service.provider, "app_id", "expected-app-id")
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-APPID-001",
    )
    payload = cast(dict[str, Any], payload)
    headers = cast(dict[str, str], headers)
    payload["app_id"] = "wrong-app-id"
    payload["notify_id"] = "notify-001"
    headers["X-Mock-Signature"] = service.provider.sign_payload(payload)

    with pytest.raises(PaymentError, match="payment app_id mismatch"):
        service.handle_webhook(payload, headers["X-Mock-Signature"])

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        unchanged = dao.get(order.id)
    assert unchanged.status == "pending"


def test_handle_webhook_rejects_missing_notify_id_for_bound_provider(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WEBHOOK-NOTIFY")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    setattr(service.provider, "app_id", "expected-app-id")
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-NOTIFY-001",
    )
    payload = cast(dict[str, Any], payload)
    headers = cast(dict[str, str], headers)
    payload["app_id"] = "expected-app-id"
    headers["X-Mock-Signature"] = service.provider.sign_payload(payload)

    with pytest.raises(PaymentError, match="payment notify_id missing"):
        service.handle_webhook(payload, headers["X-Mock-Signature"])

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        unchanged = dao.get(order.id)
    assert unchanged.status == "pending"


def test_handle_webhook_rejects_merchant_id_mismatch(settings):
    order = _seed_order(
        settings.orders_db_path, order_id="GKO-20260615-WEBHOOK-MERCHANT"
    )
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    setattr(service.provider, "app_id", "expected-app-id")
    setattr(service.provider, "merchant_id", "expected-merchant")
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-MERCHANT-001",
    )
    payload = cast(dict[str, Any], payload)
    headers = cast(dict[str, str], headers)
    payload["app_id"] = "expected-app-id"
    payload["notify_id"] = "notify-merchant-001"
    payload["seller_id"] = "wrong-merchant"
    headers["X-Mock-Signature"] = service.provider.sign_payload(payload)

    with pytest.raises(PaymentError, match="payment merchant_id mismatch"):
        service.handle_webhook(payload, headers["X-Mock-Signature"])

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        unchanged = dao.get(order.id)
    assert unchanged.status == "pending"


def test_mock_payment_webhook_keeps_refunded_payment_terminal_state(settings):
    order = _seed_order(
        settings.orders_db_path, order_id="GKO-20260617-WEBHOOK-REFUND-REPLAY"
    )
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-WEBHOOK-REFUND-001",
    )

    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/api/public/payments/mock/webhook",
        "headers": [
            (
                b"x-mock-signature",
                headers["X-Mock-Signature"].encode("utf-8"),
            )
        ],
    })

    first = mock_payment_webhook(payload, request, settings)
    assert first.idempotent is False

    refund = service.request_refund(order.id, reason="parent_request")
    assert refund.status == "refunded"

    replay = mock_payment_webhook(payload, request, settings)
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
