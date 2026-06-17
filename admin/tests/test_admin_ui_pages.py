from __future__ import annotations


def test_admin_new_order_page_renders(client):
    resp = client.get("/admin/orders/new")
    assert resp.status_code == 200, resp.text
    assert "后台手动添加订单" in resp.text
    assert "/api/orders" in resp.text
    assert "人工补录更直接" in resp.text
    assert '/static/portal-ui.css' in resp.text
    assert "考试省份" in resp.text


def test_dashboard_exposes_admin_quick_links(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200, resp.text
    assert "/admin/orders/new" in resp.text
    assert "/admin/notifications" in resp.text
    assert "/admin/ops-alerts" in resp.text
    assert 'id="dashboard-title"' in resp.text
    assert 'id="dev-seed-panel"' in resp.text
    assert 'id="dev-seed-overdue-btn"' in resp.text
    assert 'id="dev-seed-clean-btn"' in resp.text
    assert '?seed-tools=1' in resp.text
