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



def test_public_landing_route_is_registered_in_real_app(client):
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    assert "审核优先" in resp.text or "先复核" in resp.text


def test_review_action_accepts_browser_form_post(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260623-REVIEW-FORM")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text

    resp = client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert resp.status_code == 303, resp.text
    assert resp.headers["location"].endswith(f"/portal/{token}/cwb")


def test_real_app_registers_public_entry_and_form_review_routes(app):
    from fastapi.routing import APIRoute

    routes = {
        route.path: route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path in {"/", "/review/action"}
    }
    assert "/" in routes
    assert routes["/"].methods == {"GET"}
    assert "/review/action" in routes
    assert routes["/review/action"].methods == {"POST"}
    assert [param.name for param in routes["/review/action"].dependant.body_params] == ["token", "action"]


def test_real_client_landing_page_exposes_review_first_entry(client):
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert 'href="/review/start?source=home"' in body
    assert 'form action="/review/start" method="get"' in body
    assert 'name="source" value="home"' in body
    assert "复核免费 / 方案付费" in body


def test_real_client_policy_and_same_score_pages_render_trust_and_navigation(client):
    policy = client.get("/policy-center?province=湖南")
    assert policy.status_code == 200, policy.text
    assert "可信度说明" in policy.text
    assert "/same-score-reference?province=湖南" in policy.text and "score=0" in policy.text

    same_score = client.get("/same-score-reference?province=湖南&score=575")
    assert same_score.status_code == 200, same_score.text
    assert "非高置信数据不得作为强推荐依据" in same_score.text
    assert "/policy-center?province=湖南" in same_score.text


def test_real_client_review_flow_redirects_to_cwb_page(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260623-REAL-CWB")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text
    assert "方案复核入口" in start.text

    action = client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text
    assert action.headers["location"].endswith(f"/portal/{token}/cwb")
    cwb = client.get(action.headers["location"])

    assert cwb.status_code == 200, cwb.text
    assert "冲稳保建议页" in cwb.text
    assert "当前建议" in cwb.text
    assert "冲刺建议" in cwb.text
    assert "稳妥建议" in cwb.text
    assert "保底建议" in cwb.text


def test_real_client_review_flow_redirects_to_full_plan_page(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload

    order = _seed_order(settings.orders_db_path, order_id="GKO-20260623-REAL-FULLPLAN")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            family_background="家长更希望省内优先",
            interest_assessment_type="mbti",
            interest_assessment_result="INTJ",
            interest_assessment_notes="只作辅助，不作唯一判断",
        ),
        settings,
    )

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text

    action = client.post(
        "/review/action",
        data={"token": token, "action": "full_plan"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text
    assert action.headers["location"].endswith(f"/portal/{token}/full-plan")
    full_plan = client.get(action.headers["location"])

    assert full_plan.status_code == 200, full_plan.text
    assert "完整规划建议页" in full_plan.text
    assert "方案优先级" in full_plan.text
    assert "版本历史" in full_plan.text
    assert "辅助判断因子" in full_plan.text
    assert "INTJ" in full_plan.text


def test_real_client_review_action_rejects_missing_action_field(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260623-REVIEW-MISSING")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    resp = client.post(
        "/review/action",
        data={"token": token},
        follow_redirects=False,
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert any(
        field["field"] == "body.action" for field in body["detail"]["fields"]
    )


def test_real_client_review_action_rejects_invalid_literal_action(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260623-REVIEW-BADACT")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    resp = client.post(
        "/review/action",
        data={"token": token, "action": "bad"},
        follow_redirects=False,
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert any(
        field["field"] == "body.action" for field in body["detail"]["fields"]
    )


def test_real_client_review_action_rejects_json_body_for_form_route(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260623-REVIEW-JSON")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    resp = client.post(
        "/review/action",
        json={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    missing_fields = {field["field"] for field in body["detail"]["fields"]}
    assert "body.token" in missing_fields
    assert "body.action" in missing_fields


def test_payment_return_does_not_issue_portal_token_before_paid(client, settings):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    payment_id = create_resp.json()["checkout_url"].split("/pay/mock/")[1].split("?")[0]

    resp = client.get(f"/portal/payment-return?payment_id={payment_id}", follow_redirects=False)
    assert resp.status_code in {401, 403, 409}


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
