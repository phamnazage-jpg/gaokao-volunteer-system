from __future__ import annotations

from pathlib import Path

from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.payments.service import PaymentService


def _seed_order(db_path: str, order_id: str = "GKO-20260615-UPLOAD") -> Order:
    order = Order(
        id=order_id,
        source="web",
        service_version="audit",
        amount_cents=4900,
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


def test_portal_attachment_upload_persists_metadata_and_file(client, settings):
    order = _seed_order(settings.orders_db_path)
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"file": ("qianwen-plan.txt", "高校A\n专业B\n建议".encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 200, upload.text
    body = upload.json()
    assert body["order_id"] == order.id
    assert body["stage"] == "info_required"
    meta = body["attachment"]
    assert meta["original_name"] == "qianwen-plan.txt"
    assert meta["size_bytes"] > 0
    assert Path(meta["storage_path"]).is_file()

    page = client.get(f"/portal/{token}/info")
    assert page.status_code == 200, page.text
    assert "已上传附件" in page.text
    assert "qianwen-plan.txt" in page.text


def test_portal_attachment_upload_rejects_before_payment(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-UPLOAD-BLOCK")
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"file": ("plan.txt", b"draft", "text/plain")},
    )
    assert upload.status_code == 409
    assert "payment required" in upload.text


def test_portal_attachment_upload_rejects_unsupported_type(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-UPLOAD-TYPE")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"file": ("plan.exe", b"MZ...", "application/octet-stream")},
    )
    assert upload.status_code == 415
    assert "unsupported attachment type" in upload.text
