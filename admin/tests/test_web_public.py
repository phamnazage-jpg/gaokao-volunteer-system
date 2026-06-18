"""用户端 Web 自助入口页面测试（T12.2/T12.3）。"""

from __future__ import annotations

import pytest

from admin.tests.conftest import RouteClient
from data.orders.dao import OrdersDAO


def test_public_landing_page_served(route_client):
    resp = route_client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "高考志愿填报智能规划服务" in body
    assert "新高考志愿填报 · 志愿决策支持" in body
    assert "湖南新高考志愿填报" not in body
    assert "为什么选择我们" in body
    assert 'href="/pricing"' in body
    # Plan B: hero CTAs 改成 "立即咨询 / 查看套餐" 两个主 CTA
    assert "先做快速审核" not in body
    assert "立即咨询" in body
    assert "查看套餐" in body
    assert 'btn-primary" href="#consult-box"' in body
    assert 'btn-primary" href="/pricing"' in body
    # 业务铁律: 复核免费 / 方案付费 — 旧"咨询本身免费"已被替换
    assert "咨询本身免费" not in body
    assert "咨询入口" not in body  # 不应再承诺"咨询免费"
    assert "复核现有方案本身免费" in body
    assert "新方案生成与深度辅导在支付后启动" in body
    # hero-trust 1 号卡片: 复核免费 / 方案付费
    assert "复核免费 / 方案付费" in body
    # 复核/付费套餐按钮
    assert "获取复核与推荐" in body
    assert "直接看付费套餐" in body
    # 服务流程 01 步: 明确标注复核免费 / 方案付费
    assert "方案复核（免费）" in body
    assert "深度辅导（付费）" in body
    # 底部 CTA: 区分复核路径与付费路径
    assert "已有方案？先免费复核" in body
    assert "先告诉我们你的基本情况" not in body  # 旧标题已替换
    assert "告诉我们你的基本情况" in body  # 新标题存在
    # 旧 CTA/按钮文案不应再出现
    assert "获取推荐路径" not in body
    assert "直接看套餐</a>" not in body
    assert "先看套餐，再决定是否立即下单" not in body
    assert "先审计后规划" not in body
    # 咨询表单隐私说明 (输入仅用于判断, 不留底)
    assert "不会留底" in body
    assert "不会用于生成方案" in body
    assert "不会发邮件推销" in body
    assert "不会收到营销短信" in body
    # 还保留的核心元素
    assert "为什么选择我们" in body
    assert "了解服务流程" in body
    assert "最常见的不是“不会选”，而是先选错方向" in body
    assert "先把方案看清，再决定要不要重做" in body
    assert "我们先把现有方案看明白" in body
    assert "服务流程" in body
    assert "把风险解释清楚" in body
    assert "风险重点可解释" in body
    assert "进度站内可查" in body
    assert "隐私与删除入口可见" in body
    assert "01" in body
    assert "04" in body
    assert "家长决策支持" not in body
    assert "家长联系方式" not in body
    assert "把风险解释给家长听懂" not in body

    assert '/static/portal-ui.css' in body


def test_public_pricing_page_served(route_client):
    resp = route_client.get("/pricing")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "服务套餐" in body
    assert "49元 AI方案审核" in body
    assert "99元 完整志愿方案" in body
    assert "199元 深度辅导版" in body
    assert 'data-package="audit"' in body
    assert 'data-package="standard"' in body
    assert 'data-package="premium"' in body
    assert "推荐方案" in body
    assert "你可以先从 99 元完整志愿方案开始" in body
    assert "支付接入建设中" not in body
    # 业务铁律: 套餐页口径与首页一致 — 复核免费 / 方案付费
    assert "复核现有方案本身免费" in body
    assert "复核免费 / 方案付费" in body
    # 套餐页应有 1 处明确引导回首页做免费复核
    assert 'href="/#consult-box"' in body
    assert "先做一次免费复核" in body
    # 49/99/199 三档文案
    assert "先做付费审核" in body  # 49 元档 CTA
    assert "支付并启动方案生成" in body  # 99 元档 CTA
    assert "了解深度辅导" in body  # 199 元档 CTA
    # 旧 CTA/文案已替换
    assert "先做快速审核" not in body
    assert "立即开始完整规划" not in body
    assert "先审计再决定" not in body
    assert "快速校验" not in body
    # FAQ 加了"复核是免费的吗"
    assert "复核是免费的吗？包含什么？" in body
    # notice 提示明确引导免费复核
    assert "还没决定" in body
    assert '/static/portal-ui.css' in body


def test_public_checkout_page_served(route_client):
    resp = route_client.get("/checkout/standard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "完整志愿方案" in body
    assert "订单摘要" in body
    assert "服务保障" in body
    assert "立即支付" in body
    assert "状态站内可追踪" in body
    assert "当前建议" in body
    assert "交付方式" in body
    assert "最小下单" not in body
    assert '/static/portal-ui.css' in body


def test_public_create_order_endpoint(route_client):
    resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["order_id"].startswith("GKO-")
    assert body["source"] == "web"
    assert body["status"] == "pending"
    assert body["service_version"] == "standard"
    assert body["amount_cents"] == 9900
    assert body["next_step"] == "payment"
    assert body["checkout_url"].startswith("/pay/mock/")
    assert "/portal/" in body["portal_status_url"]
    with OrdersDAO.connect(route_client.app.state.settings.orders_db_path) as dao:
        created = dao.get(body["order_id"])
    assert created.customer_email == "parent@example.com"
    assert created.candidate_name == "张三"


def test_public_create_order_returns_503_with_friendly_message_when_encryption_key_missing(
    tmp_path, monkeypatch
):
    admin_db = tmp_path / "admin.db"
    orders_db = tmp_path / "orders.db"
    share_db = tmp_path / "share.db"
    share_reports = tmp_path / "share_reports"
    share_reports.mkdir()

    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(admin_db))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db))
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", str(share_db))
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", str(share_reports))
    monkeypatch.delenv("GAOKAO_ORDERS_FERNET_KEY", raising=False)
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")

    from admin.app import create_app
    from admin.config import load_settings
    from data.orders import crypto

    crypto.get_fernet.cache_clear()

    settings = load_settings()
    app = create_app(settings)

    with RouteClient(app) as route_client:
        resp = route_client.post(
            "/api/public/orders",
            json={
                "service_version": "standard",
                "amount_cents": 9900,
                "customer_phone": "13800138000",
                "candidate_name": "张三",
                "candidate_province": "湖南",
            },
        )

    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert "当前暂时无法创建订单" in body["detail"]["reason"]


def test_public_create_order_rejects_missing_minimal_fields(route_client):
    resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "audit",
            "amount_cents": 4900,
            "customer_name": "李家长",
            "candidate_province": "广东",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert any(
        field["field"] in {"body.customer_phone", "body.candidate_name"}
        for field in body["detail"]["fields"]
    )


def test_public_create_order_rejects_price_tampering(route_client):
    resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 1,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert (
        body["detail"]["fields"][0]["reason"]
        == "Value error, amount_cents 与套餐价格不一致"
    )


def test_checkout_url_does_not_expose_portal_token_in_query(route_client):
    create_resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()

    assert "token=" not in body["checkout_url"]


def test_payment_return_redirects_to_payment_success_page(route_client):
    create_resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]

    route_client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    resp = route_client.get(
        f"/portal/payment-return?payment_id={payment_id}", follow_redirects=False
    )
    assert resp.status_code == 303, resp.text
    assert resp.headers["location"].startswith("/portal/")
    assert resp.headers["location"].endswith("/payment-success")


def test_payment_success_page_served_after_paid_order(route_client, settings):
    create_resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    complete = route_client.post(
        f"/pay/mock/{payment_id}/complete", follow_redirects=False
    )
    assert complete.status_code == 303, complete.text
    assert complete.headers["location"] == f"/portal/{token}/payment-success"

    page = route_client.get(f"/portal/{token}/payment-success")
    assert page.status_code == 200, page.text
    assert "支付成功" in page.text
    assert "订单已创建，下一步继续补资料" in page.text
    assert "立即补充资料" in page.text


def test_portal_report_rejects_untrusted_report_path(route_client, settings):
    from data.orders.dao import OrdersDAO
    from data.orders.models import Order
    from data.customer_portal.token import issue_portal_token

    order = Order(
        id="GKO-20260614-TRUST",
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张家长",
        customer_phone="13800138000",
        candidate_name="张三",
        candidate_province="湖南",
        audit_report="/etc/hosts",
        pdf_path="/etc/hosts",
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.create(order, actor="test", reason="seed")
    token = issue_portal_token(order.id, settings.portal_token_secret)

    report_page = route_client.get(f"/portal/{token}/report")
    assert report_page.status_code == 409
    assert "report not ready" in report_page.text

    pdf_resp = route_client.get(f"/portal/{token}/report.pdf")
    assert pdf_resp.status_code == 409
    assert "report not ready" in pdf_resp.text


def test_portal_status_page_does_not_fall_back_to_pending_after_paid_order(
    route_client, settings
):
    from data.payments.service import PaymentService

    create_resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]
    order_id = body["order_id"]

    complete = route_client.post(
        f"/pay/mock/{payment_id}/complete", follow_redirects=False
    )
    assert complete.status_code == 303, complete.text

    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    redundant = service.create_checkout(order_id)
    assert redundant.payment_id == payment_id

    page = route_client.get(f"/portal/{token}/status")
    assert page.status_code == 200, page.text
    assert "待填写资料" in page.text
    assert "待支付" not in page.text


def test_prod_hides_simulated_payment_entrypoints(tmp_path, monkeypatch):
    admin_db = tmp_path / "admin.db"
    orders_db = tmp_path / "orders.db"
    share_db = tmp_path / "share.db"
    share_reports = tmp_path / "share_reports"
    share_reports.mkdir()

    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(admin_db))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db))
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", str(share_db))
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", str(share_reports))
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "Prod-pass-123!")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)

    from admin.config import load_settings
    from admin.routes.web_public import (
        alipay_sim_payment_page,
        complete_alipay_sim_payment,
        complete_mock_payment,
        mock_payment_page,
        mock_payment_webhook,
    )
    from fastapi import HTTPException
    from starlette.requests import Request

    settings = load_settings()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/public/payments/mock/webhook",
            "headers": [],
        }
    )

    for route_call in (
        lambda: mock_payment_page("pay_123", settings),
        lambda: complete_mock_payment("pay_123", settings),
        lambda: alipay_sim_payment_page("pay_123", settings),
        lambda: complete_alipay_sim_payment("pay_123", settings),
        lambda: mock_payment_webhook({}, request, settings),
    ):
        with pytest.raises(HTTPException) as exc_info:
            route_call()
        assert exc_info.value.status_code == 404


def test_public_pages_include_privacy_and_deletion_links(route_client):
    landing = route_client.get("/")
    assert landing.status_code == 200, landing.text
    assert 'href="/privacy"' in landing.text
    assert 'href="/service-terms"' in landing.text
    assert 'href="/deletion-policy"' in landing.text

    pricing = route_client.get("/pricing")
    assert pricing.status_code == 200, pricing.text
    assert 'href="/privacy"' in pricing.text
    assert 'href="/service-terms"' in pricing.text
    assert 'href="/deletion-policy"' in pricing.text


def test_privacy_and_deletion_pages_are_served(route_client):
    privacy = route_client.get("/privacy")
    assert privacy.status_code == 200, privacy.text
    assert "隐私政策" in privacy.text
    assert "隐私说明" in privacy.text
    assert '/static/portal-ui.css' in privacy.text

    terms = route_client.get("/service-terms")
    assert terms.status_code == 200, terms.text
    assert "服务说明与免责声明" in terms.text
    assert "服务边界" in terms.text
    assert '/static/portal-ui.css' in terms.text

    deletion = route_client.get("/deletion-policy")
    assert deletion.status_code == 200, deletion.text
    assert "删除申请" in deletion.text
    assert "数据删除" in deletion.text
    assert '/static/portal-ui.css' in deletion.text


def test_public_create_order_returns_503_without_creating_orphan_order_when_provider_unavailable(
    tmp_path, monkeypatch
):
    admin_db = tmp_path / "admin.db"
    orders_db = tmp_path / "orders.db"
    share_db = tmp_path / "share.db"
    share_reports = tmp_path / "share_reports"
    share_reports.mkdir()

    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(admin_db))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db))
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", str(share_db))
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", str(share_reports))
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv("GAOKAO_PAYMENT_BASE_URL", "http://testserver")
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "missing-real-provider-env")

    from admin.app import create_app
    from admin.config import load_settings

    settings = load_settings()
    app = create_app(settings)

    with RouteClient(app) as route_client:
        resp = route_client.post(
            "/api/public/orders",
            json={
                "service_version": "standard",
                "amount_cents": 9900,
                "customer_name": "张家长",
                "customer_phone": "13800138000",
                "candidate_name": "张三",
                "candidate_province": "湖南",
            },
        )

    assert resp.status_code == 503, resp.text
    assert "payment provider unavailable" in resp.text
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        assert dao.count() == 0


def test_public_create_order_returns_503_without_creating_orphan_order_when_checkout_fails(
    tmp_path, monkeypatch
):
    admin_db = tmp_path / "admin.db"
    orders_db = tmp_path / "orders.db"
    share_db = tmp_path / "share.db"
    share_reports = tmp_path / "share_reports"
    share_reports.mkdir()

    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(admin_db))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db))
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", str(share_db))
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", str(share_reports))
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("GAOKAO_PAYMENT_BASE_URL", "http://testserver")
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "test-payment-secret")

    from admin.app import create_app
    from admin.config import load_settings
    from data.payments.service import PaymentError, PaymentService

    original = PaymentService.create_checkout

    def _boom(self, order_id: str, *, portal_token: str | None = None):
        raise PaymentError("checkout transport failed")

    monkeypatch.setattr(PaymentService, "create_checkout", _boom)

    settings = load_settings()
    app = create_app(settings)

    with RouteClient(app) as route_client:
        resp = route_client.post(
            "/api/public/orders",
            json={
                "service_version": "standard",
                "amount_cents": 9900,
                "customer_name": "张家长",
                "customer_phone": "13800138000",
                "candidate_name": "张三",
                "candidate_province": "湖南",
            },
        )

    monkeypatch.setattr(PaymentService, "create_checkout", original)
    assert resp.status_code == 503, resp.text
    assert "payment checkout unavailable" in resp.text
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        assert dao.count() == 0
def test_public_pricing_page_shows_consult_recommendation(route_client):
    resp = route_client.get(
        "/pricing?province=%E6%B9%96%E5%8D%97&score=578&goal=%E5%85%88%E5%AE%A1%E6%A0%B8&consult=%E5%B7%B2%E6%9C%89%E4%B8%80%E7%89%88%E6%96%B9%E6%A1%88"
    )
    assert resp.status_code == 200, resp.text
    assert "更适合先做 49 元方案审核" in resp.text
    assert "湖南 578 先审核" in resp.text


def test_info_page_wizard_actions_outside_form_for_sticky_bottom(route_client, settings):
    """资料页移动端关键操作按钮必须放在 form 之外, 才能让
    `position: sticky; bottom: 0` 跨越整个表单区域在视口持续可见。"""
    from data.orders.dao import OrdersDAO
    from data.orders.public_flow import PublicOrderCreate, create_public_order
    from data.customer_portal.token import issue_portal_token

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order = create_public_order(
            dao,
            PublicOrderCreate(
                service_version="standard",
                amount_cents=9900,
                customer_name="Sticky 用户",
                customer_phone="13800138000",
                candidate_name="Sticky-User",
                candidate_province="湖南",
            ),
        )
    token = issue_portal_token(order.id, settings.portal_token_secret)
    resp = route_client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    body = resp.text
    # 关键断言: wizard-actions 必须出现在 </form> 之后
    form_end = body.find("</form>")
    wizard_start = body.find('<div class="wizard-actions">')
    assert form_end > 0, "should have </form> closing tag"
    assert wizard_start > 0, "should have wizard-actions div"
    assert wizard_start > form_end, (
        "wizard-actions must be a sibling of <form>, not nested inside it "
        "(so position: sticky works across all step-panels)"
    )
    # 同时确认主操作按钮文案都还在
    for label in ["保存草稿", "下一步", "上一步", "确认并提交资料"]:
        assert label in body, f"missing wizard button label: {label}"
    # 移动端 safe-area 适配
    assert "safe-area-inset-bottom" in body, "should reserve safe-area for notched devices"
