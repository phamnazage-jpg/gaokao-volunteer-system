from __future__ import annotations

import subprocess
from pathlib import Path

from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.payments.service import PaymentService


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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

    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "report.html"
    pdf_path = report_root / "report.pdf"
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

    token = issue_portal_token(order.id, settings.portal_token_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "报告已就绪" in status_page.text
    assert "查看报告" in status_page.text

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 200, report_page.text
    assert "志愿方案报告" in report_page.text

    pdf_resp = client.get(f"/portal/{token}/report.pdf")
    assert pdf_resp.status_code == 200, pdf_resp.text
    assert pdf_resp.headers["content-type"].startswith("application/pdf")


def test_portal_status_page_shows_sent_station_notification(
    client, settings, tmp_path: Path
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-STATUS-NOTICE")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id, payload={"candidate_score": 578}, submit=True
    )

    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "status-notice-report.html"
    pdf_path = report_root / "status-notice-report.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nportal-notice\n")

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

    env = {
        **__import__("os").environ,
        "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path,
    }
    proc = subprocess.run(
        [
            str(PROJECT_ROOT / ".venv" / "bin" / "python"),
            "scripts/gaokao-delivery-dispatch.py",
            "--channel",
            "station",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr

    token = issue_portal_token(order.id, settings.portal_token_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "通知已发送" in status_page.text
    assert "报告已就绪" in status_page.text
    assert order.id in status_page.text


def test_delivered_without_artifacts_stays_processing_on_status_page(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-STATUS-NOART")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={"candidate_score": 578},
        submit=True,
    )

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(
            order.id, "delivered", actor="test", reason="report_ready_without_files"
        )

    token = issue_portal_token(order.id, settings.portal_token_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "处理中" in status_page.text
    assert "查看当前进度" in status_page.text
    assert "报告已就绪" not in status_page.text
    assert "报告生成中" in status_page.text


def test_info_required_status_page_emphasizes_continue_intake(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-STATUS-INFO")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "待填写资料" in status_page.text
    assert "继续补充资料" in status_page.text

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 409


def test_partial_artifacts_do_not_expose_delivery_links_before_report_ready(
    client, settings, tmp_path: Path
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-STATUS-PARTIAL")
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={"candidate_score": 578, "candidate_subjects": ["物理"]},
        submit=True,
    )

    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "partial-report.html"
    report_path.write_text("<h1>partial</h1>", encoding="utf-8")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path)},
            actor="test",
            reason="attach_partial_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(
            order.id, "delivered", actor="test", reason="report_ready_without_pdf"
        )

    token = issue_portal_token(order.id, settings.portal_token_secret)
    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "处理中" in status_page.text
    assert "查看在线报告" not in status_page.text
    assert "下载 PDF" not in status_page.text
    assert "报告生成中" in status_page.text

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 409
