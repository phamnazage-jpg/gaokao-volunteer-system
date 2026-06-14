from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient


def _write_keypair(tmp_path: Path) -> tuple[Path, Path]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_path = tmp_path / "alipay_private.pem"
    public_path = tmp_path / "alipay_public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


def test_alipay_notify_marks_order_paid_and_is_idempotent(tmp_path, monkeypatch):
    admin_db = tmp_path / "admin.db"
    orders_db = tmp_path / "orders.db"
    share_db = tmp_path / "share.db"
    share_reports = tmp_path / "share_reports"
    share_reports.mkdir()
    private_path, public_path = _write_keypair(tmp_path)

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
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "alipay-independent-secret")
    monkeypatch.setenv(
        "GAOKAO_PAYMENT_NOTIFY_URL",
        "https://example.com/api/public/payments/alipay/notify",
    )
    monkeypatch.setenv(
        "GAOKAO_PAYMENT_RETURN_URL",
        "https://example.com/portal/payment-return",
    )
    monkeypatch.setenv("GAOKAO_PAYMENT_APP_ID", "20260001")
    monkeypatch.setenv("GAOKAO_PAYMENT_PRIVATE_KEY_PATH", str(private_path))
    monkeypatch.setenv("GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH", str(public_path))

    from admin.app import create_app
    from admin.config import load_settings
    from data.orders.dao import OrdersDAO
    from data.payments.providers.alipay import AlipayProvider
    from data.payments.service import PaymentService

    settings = load_settings()
    app = create_app(settings)

    with TestClient(app) as client:
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
        created = create_resp.json()
        assert created["checkout_url"].startswith(
            "https://openapi.alipay.com/gateway.do?"
        )

        service = PaymentService.for_db(
            settings.orders_db_path,
            base_url=settings.payment_base_url,
            webhook_secret=settings.payment_webhook_secret,
            provider_name="alipay",
            notify_url=settings.payment_notify_url,
            return_url=settings.payment_return_url,
            app_id=settings.payment_app_id,
            private_key_path=settings.payment_private_key_path,
            alipay_public_key_path=settings.payment_alipay_public_key_path,
        )
        payment = service.get_payment_by_order(created["order_id"])
        assert payment is not None

        provider = AlipayProvider(
            app_id=settings.payment_app_id,
            private_key_path=settings.payment_private_key_path,
            alipay_public_key_path=settings.payment_alipay_public_key_path,
            notify_url=settings.payment_notify_url,
            return_url=settings.payment_return_url,
        )
        payload, signature = provider.build_webhook_request(
            payment_id=payment.id,
            amount_cents=payment.amount_cents,
            provider_trade_no="ALI-ORDER-001",
        )

        first = client.post(
            "/api/public/payments/alipay/notify",
            data={**payload, "sign": signature, "sign_type": "RSA2"},
        )
        assert first.status_code == 200, first.text
        assert first.text == "success"

        second = client.post(
            "/api/public/payments/alipay/notify",
            data={**payload, "sign": signature, "sign_type": "RSA2"},
        )
        assert second.status_code == 200, second.text
        assert second.text == "success"

        with OrdersDAO.connect(settings.orders_db_path) as dao:
            updated = dao.get(created["order_id"])
            history = dao.get_status_history(created["order_id"])
        assert updated.status == "paid"
        assert [item.to_status for item in history] == ["pending", "paid"]
