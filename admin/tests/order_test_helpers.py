from __future__ import annotations

from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-STATUS") -> Order:
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
    handled = service.handle_webhook(payload, headers["X-Mock-Signature"])
    assert handled.order_status == "paid"


def _seed_review_result(settings, token: str):
    from admin.routes.web_public import _start_review_result

    return _start_review_result(
        source="status",
        token=token,
        settings=settings,
        review_input_summary="测试复核结果",
        review_constraints={
            "candidate_province": "湖南",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学"],
        },
    )

