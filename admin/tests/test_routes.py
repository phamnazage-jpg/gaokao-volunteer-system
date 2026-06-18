"""路由层测试 (T6.1).

覆盖:
- /health 公开
- /api/auth/login 错凭证 401 + 不区分用户名密码
- /api/orders 无 token 401 + 有效 token 返回 []
- /api/orders/{id} 不存在 404
- /api/stats/orders 鉴权
- /api/meta 鉴权 + 内容
"""

from __future__ import annotations


# ---------------- health ----------------


def test_health_public(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok"}


# ---------------- auth ----------------


def test_login_wrong_password_returns_401(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "WRONG"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "E01101"
    # 必须泛化错误信息,避免账户枚举
    assert body["message"] == "用户名或密码不正确"
    assert "detail" not in body


def test_login_unknown_user_returns_401(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "anything"},
    )
    assert resp.status_code == 401


def test_login_rate_limited_after_repeated_failures(client):
    resp = None
    for _ in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "WRONG"},
        )

    assert resp is not None
    assert resp.status_code == 429
    body = resp.json()
    assert body["code"] == "E02501"
    assert body["message"] == "请求过于频繁"
    assert body["detail"]["retry_after_seconds"] >= 1


def test_login_missing_fields_rejected(client):
    resp = client.post("/api/auth/login", json={"username": ""})
    assert resp.status_code == 422  # pydantic 校验


# ---------------- orders ----------------


def test_orders_requires_auth(client):
    resp = client.get("/api/orders")
    assert resp.status_code == 401


def test_orders_returns_empty_list_with_auth(client, auth_headers):
    resp = client.get("/api/orders", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_orders_supports_limit_offset(client, auth_headers):
    resp = client.get(
        "/api/orders",
        params={"limit": 10, "offset": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_orders_rejects_invalid_limit(client, auth_headers):
    resp = client.get("/api/orders", params={"limit": 0}, headers=auth_headers)
    assert resp.status_code == 422


def test_order_detail_404_for_unknown(client, auth_headers):
    resp = client.get("/api/orders/GKO-20260612-XXXX", headers=auth_headers)
    assert resp.status_code == 404


def test_order_detail_requires_auth(client):
    resp = client.get("/api/orders/anything")
    assert resp.status_code == 401


def test_dev_seed_requires_auth(client):
    resp = client.post("/api/admin/orders/dev-seed", json={"scenario": "overdue_pending_once"})
    assert resp.status_code == 401


def test_dev_seed_create_and_cleanup(client, auth_headers):
    create = client.post(
        "/api/admin/orders/dev-seed",
        headers=auth_headers,
        json={"scenario": "overdue_pending_once"},
    )
    assert create.status_code == 200, create.text
    created = create.json()
    assert created["action"] == "created"
    assert len(created["created_ids"]) == 1

    dashboard = client.get("/api/stats/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200, dashboard.text
    summary = dashboard.json()["summary"]
    assert summary["pending_orders"] == 1
    assert summary["pending_overdue_24h"] == 1
    assert summary["pending_missing_intake"] == 1

    cleanup = client.post(
        "/api/admin/orders/dev-seed",
        headers=auth_headers,
        json={"scenario": "cleanup_demo_seed"},
    )
    assert cleanup.status_code == 200, cleanup.text
    cleaned = cleanup.json()
    assert cleaned["action"] == "cleaned"
    assert cleaned["detail"]["deleted_count"] == 1

    dashboard_after = client.get("/api/stats/dashboard", headers=auth_headers)
    assert dashboard_after.status_code == 200, dashboard_after.text
    summary_after = dashboard_after.json()["summary"]
    assert summary_after["pending_orders"] == 0
    assert summary_after["pending_overdue_24h"] == 0
    assert summary_after["pending_missing_intake"] == 0


# ---------------- stats ----------------


def test_stats_orders_requires_auth(client):
    resp = client.get("/api/stats/orders")
    assert resp.status_code == 401


def test_stats_orders_real_shape(client, auth_headers):
    """T6.2: /api/stats/orders 接入真实 SQL 聚合。

    - 字段集沿用 T6.1 stub 形状 (5 字段)
    - 移除 _stub 标记
    - 空库时所有计数为 0
    """
    resp = client.get("/api/stats/orders", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_orders"] == 0
    assert body["total_revenue_cents"] == 0
    # 6 态全 0 填充
    assert body["by_status"] == {
        "pending": 0,
        "paid": 0,
        "serving": 0,
        "delivered": 0,
        "completed": 0,
        "refunded": 0,
    }
    assert body["by_source"] == {"xianyu": 0, "wechat": 0, "web": 0, "school": 0}
    assert body["by_service_version"] == {
        "audit": 0,
        "basic": 0,
        "standard": 0,
        "premium": 0,
    }
    assert "_stub" not in body


# ---------------- meta ----------------


def test_meta_requires_auth(client):
    resp = client.get("/api/meta")
    assert resp.status_code == 401


def test_meta_full_enums(client, auth_headers):
    resp = client.get("/api/meta", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["supported_provinces"]) >= 27
    assert "湖南" in body["supported_provinces"]

    assert set(body["order_statuses"]) == {
        "pending",
        "paid",
        "serving",
        "delivered",
        "completed",
        "refunded",
    }
    assert set(body["order_sources"]) == {"xianyu", "wechat", "web", "school"}
    assert set(body["service_versions"]) == {"audit", "basic", "standard", "premium"}
