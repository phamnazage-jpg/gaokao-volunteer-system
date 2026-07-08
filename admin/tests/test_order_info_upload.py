from __future__ import annotations


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
        files=[
            ("files", ("qianwen-plan.txt", "高校A\n专业B\n建议".encode("utf-8"), "text/plain")),
            ("files", ("doubao-plan.json", b'{"plan": true}', "application/json")),
        ],
    )
    assert upload.status_code == 200, upload.text
    body = upload.json()
    assert body["order_id"] == order.id
    assert body["stage"] == "info_required"
    metas = body["attachments"]
    assert len(metas) == 2
    assert metas[0]["original_name"] == "qianwen-plan.txt"
    assert metas[1]["original_name"] == "doubao-plan.json"
    for meta in metas:
        assert meta["size_bytes"] > 0
        assert "storage_path" not in meta



def test_portal_attachment_response_does_not_expose_storage_path(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260624-UPLOAD-HIDE")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"files": ("a.txt", b"alpha", "text/plain")},
    )
    assert upload.status_code == 200, upload.text
    meta = upload.json()["attachments"][0]
    assert "storage_path" not in meta



def test_portal_attachment_upload_rejects_before_payment(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-UPLOAD-BLOCK")
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"files": ("plan.txt", b"draft", "text/plain")},
    )
    assert upload.status_code == 409
    assert "payment required" in upload.text



def test_portal_attachment_upload_rejects_png_extension_with_text_payload(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260705-UPLOAD-MAGIC")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"files": ("fake.png", b"not a real png", "image/png")},
    )

    assert upload.status_code == 415
    assert "attachment content does not match extension" in upload.text


def test_portal_attachment_upload_accepts_real_png_magic_bytes(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260705-UPLOAD-PNG")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)
    png_payload = b"\x89PNG\r\n\x1a\n" + b"minimal-png-smoke"

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"files": ("real.png", png_payload, "image/png")},
    )

    assert upload.status_code == 200, upload.text
    meta = upload.json()["attachments"][0]
    assert meta["original_name"] == "real.png"
    assert meta["content_type"] == "image/png"


def test_portal_attachment_upload_rejects_unsupported_type(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-UPLOAD-TYPE")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    upload = client.post(
        f"/portal/{token}/attachments",
        files={"files": ("plan.exe", b"MZ...", "application/octet-stream")},
    )
    assert upload.status_code == 415
    assert "unsupported attachment type" in upload.text


def test_portal_attachment_upload_rejects_when_exceeding_max_files(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260615-UPLOAD-MAX")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    first = client.post(
        f"/portal/{token}/attachments",
        files=[
            ("files", ("a.txt", b"a", "text/plain")),
            ("files", ("b.txt", b"b", "text/plain")),
            ("files", ("c.txt", b"c", "text/plain")),
            ("files", ("d.txt", b"d", "text/plain")),
            ("files", ("e.txt", b"e", "text/plain")),
        ],
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/portal/{token}/attachments",
        files={"files": ("overflow.txt", b"z", "text/plain")},
    )
    assert second.status_code == 413
    assert "too many attachments" in second.text
