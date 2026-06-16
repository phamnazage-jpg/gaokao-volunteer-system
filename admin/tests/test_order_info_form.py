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


def test_order_info_form_accepts_draft_and_submit(client, settings):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    page = client.get(f"/portal/{token}/info")
    assert page.status_code == 200, page.text
    assert "资料填写向导" in page.text
    assert "四步资料向导" in page.text
    assert "当前资料状态" in page.text
    assert '/static/portal-ui.css' in page.text
    assert "目标城市" in page.text
    assert "目标专业" in page.text
    assert "已有方案说明" in page.text
    assert "基础信息" in page.text
    assert "偏好与目标" in page.text
    assert "已有方案与附件" in page.text
    assert "确认并提交" in page.text
    assert "提交确认" not in page.text

    assert page.text.count("<form") == 1
    assert 'id="attachment-form"' not in page.text
    assert "wizard-actions" in page.text

    draft = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "draft",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "candidate_interests": "计算机",
            "target_cities": ["长沙", "上海"],
            "target_majors": ["计算机科学与技术", "自动化"],
            "university_preferences": "更偏向 985 / 211，接受省内优先",
            "existing_plan_summary": "已有一份千问方案，需要人工校验是否扎堆",
            "guardian_notes": "更看重省内城市",
            "consent_version": "t12-web-mvp-v1",
            "consent_scope": "web-self-service-order-intake",
            "privacy_accepted": False,
            "service_terms_accepted": False,
            "guardian_confirmed": False,
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
            "target_cities": ["长沙", "上海"],
            "target_majors": ["计算机科学与技术", "自动化"],
            "university_preferences": "更偏向 985 / 211，接受省内优先",
            "existing_plan_summary": "已有一份千问方案，需要人工校验是否扎堆",
            "guardian_notes": "更看重省内城市",
            "consent_version": "t12-web-mvp-v1",
            "consent_scope": "web-self-service-order-intake",
            "privacy_accepted": True,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        },
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["intake_status"] == "submitted"
    assert submit.json()["stage"] == "processing"

    status_page = client.get(f"/portal/{token}/status")
    assert status_page.status_code == 200, status_page.text
    assert "订单进度总览" in status_page.text
    assert '/static/portal-ui.css' in status_page.text
    assert "处理中" in status_page.text
    assert "当前资料摘要" in status_page.text
    assert "下一步建议" in status_page.text
    assert "长沙,上海" in status_page.text
    assert "计算机科学与技术,自动化" in status_page.text
    assert "已有一份千问方案" in status_page.text


def test_order_info_form_becomes_read_only_after_report_ready(
    client, settings, tmp_path
):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-INFO-LOCK")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

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
            "candidate_interests": "数学",
            "consent_version": "t12-web-mvp-v1",
            "consent_scope": "web-self-service-order-intake",
            "privacy_accepted": True,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        },
    )
    assert resp.status_code == 409


def test_submit_requires_consent_fields(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260614-INFO-CONSENT")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    resp = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "submit",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "consent_version": "t12-web-mvp-v1",
            "consent_scope": "web-self-service-order-intake",
            "privacy_accepted": False,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        },
    )
    assert resp.status_code == 422
    assert "privacy_accepted" in resp.text


def test_submit_requires_at_least_one_target_preference(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-INFO-TARGET")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    resp = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "submit",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "candidate_interests": None,
            "target_cities": [],
            "target_majors": [],
            "university_preferences": None,
            "consent_version": "t12-web-mvp-v1",
            "consent_scope": "web-self-service-order-intake",
            "privacy_accepted": True,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        },
    )
    assert resp.status_code == 422
    assert "至少填写一个偏好与目标字段" in resp.text


def test_order_info_page_exposes_policy_and_deletion_links(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-INFO-LINKS")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    page = client.get(f"/portal/{token}/info")
    assert page.status_code == 200, page.text
    assert f'/privacy?token={token}' in page.text
    assert f'/service-terms?token={token}' in page.text
    assert f'/portal/{token}/deletion-request' in page.text


def test_portal_deletion_request_is_logged_and_visible_in_admin(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-DELETE-REQ")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    form_page = client.get(f"/portal/{token}/deletion-request")
    assert form_page.status_code == 200, form_page.text
    assert "删除申请" in form_page.text
    assert "提交删除申请" in form_page.text
    assert '/static/portal-ui.css' in form_page.text

    submit = client.post(
        f"/portal/{token}/deletion-request",
        json={
            "requester_name": "张家长",
            "requester_contact": "parent@example.com",
            "reason": "需要撤回资料并删除附件",
            "scope": "order_and_attachments",
            "confirm_guardian": True,
        },
    )
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["order_id"] == order.id
    assert body["request_logged"] is True

    admin_page = client.get(
        f"/admin/deletion-requests?order_id={order.id}", headers=auth_headers
    )
    assert admin_page.status_code == 200, admin_page.text

    assert order.id in admin_page.text
    assert "需要撤回资料并删除附件" in admin_page.text
    assert "parent@example.com" in admin_page.text


def test_order_info_page_uses_checkbox_checked_state_for_submit(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-INFO-CHECKED")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    page = client.get(f"/portal/{token}/info")
    assert page.status_code == 200, page.text
    assert 'document.querySelector(\'input[name="privacy_accepted"]\')?.checked' in page.text
    assert "form.get('privacy_accepted') === 'on'" not in page.text
    assert "form.get('service_terms_accepted') === 'on'" not in page.text
    assert "form.get('guardian_confirmed') === 'on'" not in page.text