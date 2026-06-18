from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class AlipaySimProvider:
    name = "alipay_sim"

    def __init__(self, *, base_url: str, secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.secret = secret

    def build_checkout_url(
        self,
        payment_id: str,
        portal_token: str,
        *,
        amount_cents: int | None = None,
        subject: str | None = None,
    ) -> str:
        return f"/pay/alipay-sim/{payment_id}"

    def build_webhook_request(
        self,
        *,
        payment_id: str,
        amount_cents: int,
        provider_trade_no: str,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        payload = {
            "out_trade_no": payment_id,
            "trade_no": provider_trade_no,
            "total_amount": self._format_amount(amount_cents),
            "trade_status": "TRADE_SUCCESS",
        }
        sig = self.sign_payload(payload)
        return payload, {"X-Alipay-Sim-Signature": sig}

    def normalize_webhook_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        total_amount = str(payload.get("total_amount") or "0")
        amount_cents = int(
            (
                Decimal(total_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                * 100
            )
        )
        return {
            "payment_id": str(payload.get("out_trade_no") or ""),
            "amount_cents": amount_cents,
            "provider_trade_no": str(payload.get("trade_no") or ""),
            "status": str(payload.get("trade_status") or "TRADE_SUCCESS"),
        }

    def sign_payload(self, payload: dict[str, Any]) -> str:
        body = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hmac.new(
            self.secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, payload: dict[str, Any], signature: str) -> bool:
        expected = self.sign_payload(payload)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def _format_amount(amount_cents: int) -> str:
        return f"{Decimal(amount_cents) / Decimal(100):.2f}"
