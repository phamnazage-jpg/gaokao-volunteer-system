from __future__ import annotations

from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


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


def test_mock_payment_webhook_marks_order_paid_and_is_idempotent(client, settings):
    order = _seed_order(settings.orders_db_path)
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url="http://testserver",
        webhook_secret=settings.jwt_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-ORDER-001",
    )

    first = client.post(
        "/api/public/payments/mock/webhook", json=payload, headers=headers
    )
    assert first.status_code == 200, first.text
    assert first.json()["processed"] is True
    assert first.json()["idempotent"] is False

    second = client.post(
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


def test_mock_payment_webhook_rejects_amount_mismatch(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-WEBHOOK-AMOUNT")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url="http://testserver",
        webhook_secret=settings.jwt_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=1,
        provider_trade_no="MOCK-AMOUNT-WRONG",
    )

    resp = client.post(
        "/api/public/payments/mock/webhook", json=payload, headers=headers
    )
    assert resp.status_code == 409, resp.text

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        unchanged = dao.get(order.id)
    assert unchanged.status == "pending"
