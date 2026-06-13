from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


class MockPaymentProvider:
    name = "mock"

    def __init__(self, *, base_url: str, secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.secret = secret

    def build_checkout_url(self, payment_id: str, portal_token: str) -> str:
        return f"/pay/mock/{payment_id}?token={portal_token}"

    def build_webhook_request(
        self,
        *,
        payment_id: str,
        amount_cents: int,
        provider_trade_no: str,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        payload = {
            "payment_id": payment_id,
            "amount_cents": amount_cents,
            "provider_trade_no": provider_trade_no,
            "status": "paid",
        }
        sig = self.sign_payload(payload)
        return payload, {"X-Mock-Signature": sig}

    def normalize_webhook_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "payment_id": str(payload.get("payment_id") or ""),
            "amount_cents": int(payload.get("amount_cents") or 0),
            "provider_trade_no": str(payload.get("provider_trade_no") or ""),
            "status": str(payload.get("status") or "paid"),
        }

    def sign_payload(self, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        return hmac.new(
            self.secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, payload: dict[str, Any], signature: str) -> bool:
        expected = self.sign_payload(payload)
        return hmac.compare_digest(expected, signature)
