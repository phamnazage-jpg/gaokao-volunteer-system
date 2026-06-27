"""用户端 Web 自助入口核心测试。"""

from __future__ import annotations

import pytest
from fastapi import HTTPException, Request

from admin.routes.web_public import (
    alipay_sim_payment_page,
    complete_alipay_sim_payment,
    complete_mock_payment,
    mock_payment_page,
    mock_payment_webhook,
)
from fastapi.testclient import TestClient
from data.orders.dao import OrdersDAO


def test_public_landing_page_served(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "高考志愿填报智能规划服务" in body
    assert "新高考志愿填报 · 志愿决策支持" in body
    assert "湖南新高考志愿填报" not in body
    assert "为什么选择我们" in body
    assert 'href="/pricing"' in body
    assert "先做快速审核" not in body
    assert "先做方案复核" in body
    assert "查看套餐" in body
    assert 'href="/review/start?source=home"' in body
    assert 'btn-primary" href="/pricing"' in body
    assert "咨询本身免费" not in body
    assert "咨询入口" not in body
    assert "复核现有方案本身免费" in body
    assert "新方案生成与深度辅导在支付后启动" in body
    assert "先免费复核一次你的现有方案" in body
    # hero 不再保留"了解服务流程"文字链
    assert "了解服务流程" not in body
    assert "获取复核与推荐" in body
    assert "方案复核（免费）" in body
    assert "深度辅导（付费）" in body
    assert "已有方案？先免费复核" in body
    assert "先告诉我们你的基本情况" not in body
    assert "先审计后规划" not in body
    assert "不会留底" in body
    assert "不会用于生成方案" in body
    assert "不会发邮件推销" in body
    assert "不会收到营销短信" in body
    assert "了解服务流程" not in body
    # hero 压缩后的新文案
    assert "最常见的不是“不会选”，而是先选错方向" in body
    assert "先看你的方案值不值得继续" in body
    assert "服务流程" in body
    assert "把风险解释清楚" in body
    assert "家长决策支持" not in body
    assert "家长联系方式" not in body
    assert "把风险解释给家长听懂" not in body
    # 首页省份必须使用下拉，不再是自由文本
    assert '<select name="province">' in body
    assert 'placeholder="例如：湖南"' not in body
    # hero 已移除三张说明卡
    assert "复核免费 / 方案付费" not in body
    assert "风险重点可解释" not in body
    assert "资料与交付站内可追踪" not in body
    # 流程编号已改为文字版
    assert ">01<" not in body
    assert ">04<" not in body
    assert "/static/portal-ui.css" in body


def test_public_pricing_page_served(client):
    resp = client.get("/pricing")
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
    assert "复核现有方案本身免费" in body
    assert "复核免费 / 方案付费" in body
    assert 'href="/#consult-box"' in body
    assert "先做一次免费复核" in body
    assert "先做付费审核" in body
    assert "支付并启动方案生成" in body
    assert "了解深度辅导" in body
    assert "先做快速审核" not in body
    assert "立即开始完整规划" not in body
    assert "先审计再决定" not in body
    assert "快速校验" not in body
    assert "复核是免费的吗？包含什么？" in body
    assert "还没决定" in body
    assert "/static/portal-ui.css" in body


def test_public_checkout_page_served(client):
    resp = client.get("/checkout/standard")
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
    assert "/static/portal-ui.css" in body


def test_public_create_order_endpoint(client, app):
    resp = client.post(
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
    with OrdersDAO.connect(app.state.settings.orders_db_path) as dao:
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

    with TestClient(app) as client:
        resp = client.post(
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


def test_public_create_order_rejects_missing_minimal_fields(client):
    resp = client.post(
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


def test_public_create_order_rejects_price_tampering(client):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "audit",
            "amount_cents": 4999,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert any(
        "amount_cents 与套餐价格不一致" in field["reason"]
        for field in body["detail"]["fields"]
    )


def test_public_create_order_persists_candidate_province(client, app):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "audit",
            "amount_cents": 4900,
            "customer_name": "李家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "广东",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    with OrdersDAO.connect(app.state.settings.orders_db_path) as dao:
        created = dao.get(body["order_id"])
    assert created.candidate_province == "广东"


def test_public_create_order_rejects_unsupported_province(client):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "李家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "内蒙古",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert "candidate_province" in resp.text


def test_public_create_order_supports_optional_contact_email(client, app):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "李家长",
            "customer_phone": "13800138000",
            "customer_email": "guardian@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    with OrdersDAO.connect(app.state.settings.orders_db_path) as dao:
        created = dao.get(body["order_id"])
    assert created.customer_email == "guardian@example.com"


def test_public_checkout_page_renders_audit_package(client):
    resp = client.get("/checkout/audit")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "49元 AI方案审核" in body
    assert "适合已经拿到其他方案、希望先快速校验风险的家庭。" in body
    assert "当前建议" in body
    assert "当前这一步只收会影响下单与后续联系的必要信息" in body
    assert "支付成功后，再进入资料向导补充分数、位次、偏好和已有方案附件。" in body
    assert "service_version: 'audit'" in body
    assert "amount_cents: 4900" in body


def test_public_checkout_page_renders_premium_package(client):
    resp = client.get("/checkout/premium")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "199元 深度辅导版" in body
    assert "适合需要更多沟通、补充说明与深度修订支持的家庭。" in body
    assert "199元 深度辅导版" in body
    assert "service_version: 'premium'" in body
    assert "amount_cents: 19900" in body


def test_public_create_order_rejects_unknown_service_version(client):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "unknown",
            "amount_cents": 9999,
            "customer_name": "李家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert any(
        field["field"] == "body.service_version" for field in body["detail"]["fields"]
    )


def test_public_payment_flow_returns_payment_success_page(client, settings):
    create_resp = client.post(
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
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]

    complete = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert complete.status_code == 303, complete.text
    assert complete.headers["location"].endswith("/payment-success")
    token = (
        complete.headers["location"].split("/portal/")[1].split("/payment-success")[0]
    )

    page = client.get(f"/portal/{token}/payment-success")
    assert page.status_code == 200, page.text
    assert "订单已创建，下一步继续补资料" in page.text
    assert "支付状态：paid" in page.text
    assert "立即补充资料" in page.text
    assert "查看订单进度" in page.text


def test_payment_success_page_shows_audit_copy_for_audit_orders(client, settings):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "audit",
            "amount_cents": 4900,
            "customer_phone": "13800138000",
            "candidate_name": "李同学",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    complete = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert complete.status_code == 303, complete.text
    assert complete.headers["location"].endswith("/payment-success")
    token = (
        complete.headers["location"].split("/portal/")[1].split("/payment-success")[0]
    )

    page = client.get(f"/portal/{token}/payment-success")
    assert page.status_code == 200, page.text
    assert "订单已创建，下一步继续补资料" in page.text
    assert "补充基础信息" in page.text
    assert "填写偏好目标" in page.text
    assert "持续查看进度" in page.text


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
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "prod-secret-ok-123456")
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "prod-portal-secret-ok-1234567890")
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv("GAOKAO_PAYMENT_BASE_URL", "http://testserver")

    from admin.config import load_settings

    settings = load_settings()
    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/api/public/payments/mock/webhook",
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    })

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

    with TestClient(app) as client:
        resp = client.post(
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


def test_my_orders_page_served(client):
    """我的订单页必须存在且可访问。"""
    resp = client.get("/my-orders")
    assert resp.status_code == 200, resp.text
    assert "我的订单" in resp.text
    assert "手机号" in resp.text


def test_my_orders_lookup_by_phone(client, settings):
    """C 方案：手机号直查已废弃，凭手机号访问 /my-orders 应显示引导说明而非订单列表。"""
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

    # 手机号查询不再返回订单列表，而是显示引导说明
    resp = client.get("/my-orders?phone=13800138000")
    assert resp.status_code == 200, resp.text
    assert "请通过订单链接进入" in resp.text


def test_my_reports_page_served(client):
    """C 方案：我的报告页存在但不再显示手机号查询表单。"""
    resp = client.get("/my-reports")
    assert resp.status_code == 200, resp.text
    assert "我的报告" in resp.text
    assert "请通过订单链接进入" in resp.text
