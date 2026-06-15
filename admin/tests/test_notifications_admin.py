from __future__ import annotations

from data.notifications.email_service import DeliveryNotificationService
from data.orders.dao import OrdersDAO
from data.orders.models import Order


def _seed_order(db_path: str, order_id: str = "GKO-20260615-ADMIN-NOTIFY") -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张家长",
        customer_phone="13800138000",
        customer_email="parent@example.com",
        candidate_name="张三",
        candidate_province="湖南",
    )
    with OrdersDAO.connect(db_path) as dao:
        created = dao.create(order, actor="test", reason="seed")
        dao.transition_status(created.id, "paid", actor="test", reason="seed_pay")
        dao.transition_status(created.id, "serving", actor="test", reason="seed_processing")
        dao.transition_status(created.id, "delivered", actor="test", reason="seed_ready")
        return dao.get(created.id)


def test_admin_notification_list_api_filters_by_status_and_channel(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path)
    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="station",
            payload_json='{"kind":"station"}',
        )
        service.mark_validated(order.id, event_type="report_ready", payload_json='{"kind":"station"}')
        service.notify_event(
            order.id,
            event_type="report_ready_email",
            channel="email",
            payload_json='{"kind":"email"}',
        )
        service.mark_delivered(order.id, event_type="report_ready_email", payload_json='{"kind":"email"}')
    finally:
        service.close()

    resp = client.get(
        "/api/admin/notifications?status=delivered&channel=email",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["channel"] == "email"
    assert body["items"][0]["status"] == "delivered"


def test_admin_notification_audit_page_renders_table(client, auth_headers, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-ADMIN-NOTIFY-PAGE")
    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        service.notify_event(
            order.id,
            event_type="report_ready",
            channel="station",
            payload_json='{"kind":"station"}',
        )
    finally:
        service.close()

    resp = client.get(f"/admin/notifications?order_id={order.id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert "后台通知审计" in resp.text
    assert order.id in resp.text
    assert "station" in resp.text
    assert "report_ready" in resp.text
