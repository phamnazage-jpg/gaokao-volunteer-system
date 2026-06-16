"""用户端 Web 自助入口页面测试（T12.2/T12.3）。"""

from __future__ import annotations

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
    assert "先做快速审核" in body
    assert "了解服务流程" in body
    assert "最常见的不是“不会选”，而是先选错方向" in body
    assert "先把方案看清，再决定要不要重做" in body
    assert "我们先把现有方案看明白" in body
    assert "服务流程" in body
    assert "把风险解释清楚" in body
    assert "先审计后规划" in body
    assert "风险重点可解释" in body
    assert "进度站内可查" in body
    assert "隐私与删除入口可见" in body
    assert "01" in body
    assert "04" in body
    assert "家长决策支持" not in body
    assert "家长联系方式" not in body
    assert "把风险解释给家长听懂" not in body

    assert '/static/portal-ui.css' in body


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
    assert "支付接入建设中" not in body
    assert "先做快速审核" in body
    assert "立即开始完整规划" in body
    assert "了解深度辅导" in body
    assert "先审计再决定" in body
    assert '/static/portal-ui.css' in body


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
    assert '/static/portal-ui.css' in body


def test_public_create_order_endpoint(client):
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
    with OrdersDAO.connect(client.app.state.settings.orders_db_path) as dao:
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


def test_mock_payment_complete_rejects_wrong_portal_token(client):
    create_resp = client.post(
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

    resp = client.post(f"/pay/mock/{payment_id}/complete?token=wrong-token")
    assert resp.status_code == 401 or resp.status_code == 403


def test_payment_return_redirects_to_portal_status(client):
    create_resp = client.post(
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
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    resp = client.get(f"/portal/payment-return?token={token}", follow_redirects=False)
    assert resp.status_code == 303, resp.text
    assert resp.headers["location"] == f"/portal/{token}/status"


def test_public_pages_include_privacy_and_deletion_links(client):
    landing = client.get("/")
    assert landing.status_code == 200, landing.text
    assert 'href="/privacy"' in landing.text
    assert 'href="/service-terms"' in landing.text
    assert 'href="/deletion-policy"' in landing.text

    pricing = client.get("/pricing")
    assert pricing.status_code == 200, pricing.text
    assert 'href="/privacy"' in pricing.text
    assert 'href="/service-terms"' in pricing.text
    assert 'href="/deletion-policy"' in pricing.text


def test_privacy_and_deletion_pages_are_served(client):
    privacy = client.get("/privacy")
    assert privacy.status_code == 200, privacy.text
    assert "隐私政策" in privacy.text
    assert "隐私说明" in privacy.text
    assert '/static/portal-ui.css' in privacy.text

    terms = client.get("/service-terms")
    assert terms.status_code == 200, terms.text
    assert "服务说明与免责声明" in terms.text
    assert "服务边界" in terms.text
    assert '/static/portal-ui.css' in terms.text

    deletion = client.get("/deletion-policy")
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

    def _boom(self, order_id: str, *, portal_token: str):
        raise PaymentError("checkout transport failed")

    monkeypatch.setattr(PaymentService, "create_checkout", _boom)

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

    monkeypatch.setattr(PaymentService, "create_checkout", original)
    assert resp.status_code == 503, resp.text
    assert "payment checkout unavailable" in resp.text
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        assert dao.count() == 0
