from __future__ import annotations

from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260614-INFO") -> Order:
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
        settings.orders_db_path, base_url="http://testserver"
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no=f"MOCK-{order.id}",
    )
    handled = service.handle_webhook(payload, headers["X-Mock-Signature"])
    assert handled.order_status == "paid"


def test_order_info_form_accepts_draft_and_submit(client, settings):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.jwt_secret)

    page = client.get(f"/portal/{token}/info")
    assert page.status_code == 200, page.text
    assert "考生资料填写" in page.text

    draft = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "draft",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "candidate_interests": "计算机",
            "guardian_notes": "更看重省内城市",
        },
    )
    assert draft.status_code == 200, draft.text
    assert draft.json()["intake_status"] == "draft"
    assert draft.json()["stage"] == "info_required"

    submit = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "submit",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "candidate_interests": "计算机",
            "guardian_notes": "更看重省内城市",
        },
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["intake_status"] == "submitted"
    assert submit.json()["stage"] == "info_submitted"

    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "资料已提交" in status_page.text


def test_order_info_form_becomes_read_only_after_report_ready(
    client, settings, tmp_path
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-INFO-LOCK")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.jwt_secret)

    report_path = tmp_path / "locked-report.html"
    pdf_path = tmp_path / "locked-report.pdf"
    report_path.write_text("<h1>locked</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nlocked\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(order.id, "delivered", actor="test", reason="ready")

    resp = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "submit",
            "candidate_score": 600,
            "candidate_rank": 999,
            "candidate_subjects": ["物理"],
        },
    )
    assert resp.status_code == 409
