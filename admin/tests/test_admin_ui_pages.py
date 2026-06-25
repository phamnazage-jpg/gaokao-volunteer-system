from __future__ import annotations


def test_admin_new_order_page_renders(client, auth_headers):
    resp = client.get("/admin/orders/new", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert "后台手动添加订单" in resp.text
    assert "/api/orders" in resp.text
    assert "人工补录更直接" in resp.text
    assert '/static/portal-ui.css' in resp.text
    assert "考试省份" in resp.text


def test_admin_new_order_page_includes_required_consent_fields(client, auth_headers):
    resp = client.get("/admin/orders/new", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "consent_method" in body
    assert "consent_note" in body
    assert 'consent:' in body



def test_admin_new_order_page_minimal_payload_matches_create_order_contract(client, auth_headers):
    from admin.routes.orders import CreateOrderRequest

    resp = client.get("/admin/orders/new", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "source: form.get('source')" in body
    assert "service_version: form.get('service_version')" in body
    assert "amount_cents: Number(form.get('amount_cents') || 0)" in body
    assert "candidate_name: form.get('candidate_name') || null" in body
    assert "candidate_province: form.get('candidate_province') || null" in body
    assert "consent_method: form.get('consent_method') || 'verbal_chat'" in body
    assert "consent_note: form.get('consent_note') || null" in body

    payload = {
        "source": "wechat",
        "service_version": "standard",
        "amount_cents": 9900,
        "customer_name": "张家长",
        "customer_phone": "13800138000",
        "candidate_name": "张三",
        "candidate_province": "湖南",
        "notes": None,
        "consent": {
            "consent_method": "verbal_chat",
            "consent_note": None,
        },
    }
    model = CreateOrderRequest.model_validate(payload)
    assert model.consent.consent_method == "verbal_chat"


def test_dashboard_page_requires_auth(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 401


def test_admin_new_order_page_requires_auth(client):
    resp = client.get("/admin/orders/new")
    assert resp.status_code == 401





def test_dashboard_exposes_admin_quick_links(client, auth_headers):
    resp = client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert "/admin/orders/new" in resp.text
    assert "/admin/notifications" in resp.text
    assert "/admin/ops-alerts" in resp.text
    assert 'id="dashboard-title"' in resp.text
    assert 'id="dev-seed-panel"' in resp.text
    assert 'id="dev-seed-overdue-btn"' in resp.text
    assert 'id="dev-seed-clean-btn"' in resp.text
    assert '?seed-tools=1' in resp.text
