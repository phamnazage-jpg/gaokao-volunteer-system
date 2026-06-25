"""FastAPI app 启动 + Swagger 测试 (T6.1).

验证:
- app 工厂可用
- lifespan 触发 bootstrap
- /openapi.json 含所有路由
- /docs 返回 HTML
"""

from __future__ import annotations

import sqlite3

import pytest


def test_create_app_runs_lifespan(client):
    """TestClient 上下文会触发 lifespan,验证 bootstrap 完成。"""
    # 客户端创建时 lifespan 已运行 → 已有 admin 用户
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("checks", {}).get("db_writable") is True
    assert body.get("checks", {}).get("disk_writable") is True
    assert body.get("checks", {}).get("settings_valid") is True


def test_openapi_json_exposes_all_routes(client):
    """/openapi.json 含所有 T6.1 路由。"""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = set(schema["paths"].keys())

    expected = {
        "/health",
        "/api/auth/login",
        "/api/auth/me",
        "/api/orders",
        "/api/orders/{order_id}",
        "/api/stats/dashboard",
        "/api/stats/orders",
        "/api/meta",
    }
    missing = expected - paths
    assert not missing, f"OpenAPI 缺失路径: {missing}"


def test_docs_serves_swagger_ui(client):
    """/docs 返回 HTML(200 + 含 swagger-ui 字样)。"""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text.lower()
    assert "swagger" in body or "openapi" in body


def test_redoc_served(client):
    """/redoc 也可用。"""
    resp = client.get("/redoc")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_dashboard_page_served(client, auth_headers):
    """/dashboard 需要鉴权,鉴权后返回运营后台页面骨架。"""
    resp = client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "运营总览" in body
    assert "核心经营指标" in body
    assert "/static/dashboard.js" in body
    assert "/static/portal-ui.css" in body
    assert 'id="trend-chart"' in body
    assert 'id="status-chart"' in body
    assert 'id="source-chart"' in body
    assert 'id="service-chart"' in body
    assert 'id="range-7d"' in body
    assert 'id="range-30d"' in body
    assert 'id="system-status"' in body
    assert 'id="pending-orders"' in body
    assert 'id="pending-overdue-24h"' in body
    assert 'id="pending-missing-intake"' in body
    assert 'id="pending-breakdown"' in body
    assert 'id="pending-overdue-tag"' in body
    assert 'id="pending-missing-tag"' in body
    assert "pending-tag-overdue" in body
    assert "pending-tag-missing" in body
    assert 'id="orders-spark"' in body
    assert 'id="revenue-spark"' in body
    assert 'id="status-title"' in body
    assert 'id="quick-refresh-btn"' in body
    assert 'id="quick-logout-btn"' in body
    assert 'id="dev-seed-panel"' in body
    assert 'id="dev-seed-overdue-btn"' in body
    assert 'id="dev-seed-clean-btn"' in body
    assert 'id="dashboard-title"' in body
    assert 'id="login-form"' in body
    assert 'id="quick-links"' in body
    assert 'class="card empty"' in body
    assert 'class="chart-empty"' in body
    assert 'data-card="orders"' in body
    assert 'data-card="revenue"' in body
    assert 'data-card="users"' in body
    assert 'data-card="pending"' in body
    assert "尚未连接" in body
    assert "立即刷新" in body
    assert "退出登录" in body
    assert "等待加载状态分布" in body
    assert "等待加载来源分布" in body
    assert "等待加载服务版本分布" in body
    assert "登录后展示订单与收入趋势" in body
    assert "/static/vendor/echarts.min.js" in body
    assert "jsdelivr.net" not in body
    assert "最小仪表盘" not in body
    assert "admin_users 总数" not in body
    assert "接口: <code>/api/stats/dashboard</code>" not in body



def test_dashboard_static_js_served(client):
    """前端脚本包含趋势切换与 3 张分布图渲染逻辑。"""
    resp = client.get("/static/dashboard.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers["content-type"]
    body = resp.text
    assert "renderSummary" in body
    assert "/api/stats/dashboard" in body
    assert "status-chart" in body
    assert "source-chart" in body
    assert "service-chart" in body
    assert 'range: "7d"' in body
    assert "trends?.[state.range]" in body
    assert "sessionStorage" in body
    assert "localStorage" not in body
    assert "admin_users 总数" not in body
    assert "setStatus" in body
    assert "setChartEmpty" in body
    assert "pending-orders" in body
    assert "pending-overdue-24h" in body
    assert "pending-missing-intake" in body
    assert "setChartEmpty" in body
    assert "pending-breakdown" in body
    assert "postDevSeed" in body
    assert "dev-seed-panel" in body
    assert "/api/admin/orders/dev-seed" in body


def test_bootstrap_admin_only_once(client, settings):
    """lifespan 已 bootstrap 后,再次调用应报告已存在,不再创建。"""
    from admin.db import AdminUserRepo, bootstrap_admin

    # client fixture 已触发 lifespan → 已有 bootstrap 用户
    created1, msg1 = bootstrap_admin(settings)
    assert created1 is False
    assert "已存在" in msg1

    repo = AdminUserRepo(settings.db_path)
    assert repo.count() == 1


def test_default_admin_login_works(client, settings):
    """默认 admin/admin123 (此处覆写为 test-pass-123) 可登录。"""
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-pass-123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.jwt_expire_minutes * 60
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 20


def test_create_app_bootstraps_orders_schema(tmp_path, monkeypatch):
    """真实启动流程会顺手初始化 orders DB，fresh app 的 dashboard 空库可用。"""
    db_path = tmp_path / "admin.db"
    orders_db_path = tmp_path / "orders.db"
    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(db_path))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db_path))
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")

    from fastapi.testclient import TestClient

    from admin.app import create_app
    from admin.config import load_settings

    app = create_app(load_settings())
    with TestClient(app) as client:
        login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-pass-123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        resp = client.get(
            "/api/stats/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["summary"] == {
            "total_orders": 0,
            "total_revenue_cents": 0,
            "total_users": 1,
            "pending_orders": 0,
            "pending_overdue_24h": 0,
            "pending_missing_intake": 0,
            "orders_today": 0,
            "orders_7d": 0,
            "orders_30d": 0,
            "revenue_today_cents": 0,
            "revenue_7d_cents": 0,
            "revenue_30d_cents": 0,
        }

    with sqlite3.connect(orders_db_path) as conn:
        orders_row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        ).fetchone()
        intake_row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='order_intakes'"
        ).fetchone()
    assert orders_row is not None
    assert intake_row is not None


def test_prod_rejects_default_admin_password(tmp_path, monkeypatch):
    db_path = tmp_path / "admin.db"
    orders_db_path = tmp_path / "orders.db"
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(db_path))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db_path))
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "admin123")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    # 显式提供合规 webhook secret,避免被 P2-5 fail-closed 提前拦截,
    # 让本测试聚焦于管理员密码策略。
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)

    from admin.app import _validate_and_log_settings
    from admin.config import load_settings

    with pytest.raises(
        RuntimeError, match="GAOKAO_ADMIN_PASS invalid in prod|默认管理员密码"
    ):
        _validate_and_log_settings(load_settings())
