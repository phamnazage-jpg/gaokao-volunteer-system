from __future__ import annotations

from pathlib import Path

from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
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


def test_order_status_page_and_report_download(client, settings, tmp_path: Path):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学"],
        },
        submit=True,
    )

    report_path = tmp_path / "report.html"
    pdf_path = tmp_path / "report.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nportal-report\n")

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="attach_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(
            order.id, "delivered", actor="test", reason="report_ready"
        )

    token = issue_portal_token(order.id, settings.jwt_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "报告已就绪" in status_page.text

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 200, report_page.text
    assert "志愿方案报告" in report_page.text

    pdf_resp = client.get(f"/portal/{token}/report.pdf")
    assert pdf_resp.status_code == 200, pdf_resp.text
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert pdf_resp.content.startswith(b"%PDF-1.4")
