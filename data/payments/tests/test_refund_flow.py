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


def test_refund_request_marks_portal_as_refund_pending(client, settings):
    order = _seed_order(settings.orders_db_path)
    service = _mark_paid(settings, order)

    first = service.request_refund(order.id, reason="parent_request")
    second = service.request_refund(order.id, reason="duplicate_request")

    assert first.status == "refund_pending"
    assert second.status == "refund_pending"

    token = issue_portal_token(order.id, settings.jwt_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "退款申请中" in status_page.text
