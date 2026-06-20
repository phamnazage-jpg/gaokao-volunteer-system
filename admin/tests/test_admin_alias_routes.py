from __future__ import annotations


def test_admin_dashboard_alias_served(client):
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    assert "仪表盘" in resp.text
    assert "/static/dashboard.js" in resp.text


def test_admin_orders_alias_list_and_detail(client, auth_headers):
    created = client.post(
        "/api/admin/orders",
        headers=auth_headers,
        json={
            "source": "web",
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
            # A-2 (2026-06-20): 后台补录路径强制要求 consent 块
            "consent": {
                "consent_method": "verbal_chat",
                "consent_note": "alias route test",
            },
        },
    )
    assert created.status_code == 201, created.text
    order_id = created.json()["order"]["id"]

    listed = client.get("/api/admin/orders", headers=auth_headers)
    assert listed.status_code == 200, listed.text
    assert any(item["id"] == order_id for item in listed.json())

    detail = client.get(f"/api/admin/orders/{order_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["order"]["id"] == order_id


def test_admin_cases_alias_crud(client, auth_headers):
    created = client.post(
        "/api/admin/cases",
        headers=auth_headers,
        json={
            "title": "后台别名案例",
            "category": "success",
            "summary": "别名路径创建",
            "content": "别名路径正文",
            "tags": ["alias"],
        },
    )
    assert created.status_code == 201, created.text
    case_id = created.json()["id"]

    listed = client.get("/api/admin/cases", headers=auth_headers)
    assert listed.status_code == 200, listed.text
    assert any(item["id"] == case_id for item in listed.json()["items"])

    detail = client.get(f"/api/admin/cases/{case_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["id"] == case_id


def test_admin_stats_aliases(client, auth_headers):
    dashboard = client.get("/api/admin/stats/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200, dashboard.text
    assert "summary" in dashboard.json()

    orders = client.get("/api/admin/stats/orders", headers=auth_headers)
    assert orders.status_code == 200, orders.text
    assert "total_orders" in orders.json()
