from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from data.payments.providers.alipay import AlipayProvider


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


def _provider(tmp_path: Path) -> AlipayProvider:
    private_path, public_path = _write_keypair(tmp_path)
    return AlipayProvider(
        app_id="20260001",
        merchant_id="2088123412341234",
        private_key_path=str(private_path),
        alipay_public_key_path=str(public_path),
        notify_url="https://example.com/api/public/payments/alipay/notify",
        return_url="https://example.com/portal/payment-return",
    )


def test_alipay_checkout_url_contains_signed_gateway_params(tmp_path):
    provider = _provider(tmp_path)

    checkout_url = provider.build_checkout_url(
        "pay_123",
        "portal-token",
        amount_cents=9900,
        subject="高考志愿标准版",
    )

    parsed = urlparse(checkout_url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "openapi.alipay.com"
    assert parsed.path == "/gateway.do"
    assert query["app_id"] == ["20260001"]
    assert query["method"] == ["alipay.trade.page.pay"]
    assert query["sign_type"] == ["RSA2"]
    assert query["notify_url"] == [
        "https://example.com/api/public/payments/alipay/notify"
    ]
    assert query["return_url"] == [
        "https://example.com/portal/payment-return?payment_id=pay_123"
    ]
    biz_content = unquote(query["biz_content"][0])
    assert '"out_trade_no":"pay_123"' in biz_content
    assert '"total_amount":"99.00"' in biz_content
    assert query["sign"][0]


def test_alipay_provider_verifies_signed_webhook_payload(tmp_path):
    provider = _provider(tmp_path)
    payload, signature = provider.build_webhook_request(
        payment_id="pay_123",
        amount_cents=9900,
        provider_trade_no="ALI-TRADE-001",
    )

    assert provider.verify_signature(payload, signature) is True

    tampered = dict(payload)
    tampered["total_amount"] = "1.00"
    assert provider.verify_signature(tampered, signature) is False

    normalized = provider.normalize_webhook_payload(payload)
    assert normalized == {
        "payment_id": "pay_123",
        "amount_cents": 9900,
        "provider_trade_no": "ALI-TRADE-001",
        "status": "TRADE_SUCCESS",
        "app_id": "20260001",
        "notify_id": "notify_pay_123",
        "merchant_id": "2088123412341234",
    }


def test_alipay_provider_normalizes_seller_id(tmp_path):
    provider = _provider(tmp_path)
    payload, _signature = provider.build_webhook_request(
        payment_id="pay_merchant",
        amount_cents=9900,
        provider_trade_no="ALI-TRADE-MERCHANT",
    )
    payload["seller_id"] = "2088123412341234"

    normalized = provider.normalize_webhook_payload(payload)
    assert normalized["merchant_id"] == "2088123412341234"
