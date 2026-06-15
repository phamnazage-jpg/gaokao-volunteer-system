from __future__ import annotations

import base64
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey


class AlipayProvider:
    name = "alipay"
    gateway_url = "https://openapi.alipay.com/gateway.do"

    def __init__(
        self,
        *,
        app_id: str,
        merchant_id: str,
        private_key_path: str,
        alipay_public_key_path: str,
        notify_url: str,
        return_url: str,
    ) -> None:
        self.app_id = app_id.strip()
        self.merchant_id = merchant_id.strip()
        self.notify_url = notify_url.strip()
        self.return_url = return_url.strip()
        self.private_key_path = Path(private_key_path)
        self.alipay_public_key_path = Path(alipay_public_key_path)
        loaded_private = serialization.load_pem_private_key(
            self.private_key_path.read_bytes(), password=None
        )
        loaded_public = serialization.load_pem_public_key(
            self.alipay_public_key_path.read_bytes()
        )
        if not isinstance(loaded_private, RSAPrivateKey):
            raise ValueError("alipay private key must be RSA")
        if not isinstance(loaded_public, RSAPublicKey):
            raise ValueError("alipay public key must be RSA")
        self._private_key = cast(RSAPrivateKey, loaded_private)
        self._public_key = cast(RSAPublicKey, loaded_public)

    def build_checkout_url(
        self,
        payment_id: str,
        portal_token: str,
        *,
        amount_cents: int | None = None,
        subject: str | None = None,
    ) -> str:
        if amount_cents is None:
            raise ValueError("alipay checkout requires amount_cents")
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": self.notify_url,
            "return_url": self._append_query_param(
                self.return_url, "token", portal_token
            ),
            "biz_content": json.dumps(
                {
                    "out_trade_no": payment_id,
                    "product_code": "FAST_INSTANT_TRADE_PAY",
                    "total_amount": self._format_amount(amount_cents),
                    "subject": subject or f"高考志愿服务-{payment_id}",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
        params["sign"] = self.sign_payload(params)
        return f"{self.gateway_url}?{urlencode(params)}"

    def build_webhook_request(
        self,
        *,
        payment_id: str,
        amount_cents: int,
        provider_trade_no: str,
    ) -> tuple[dict[str, Any], str]:
        payload = {
            "app_id": self.app_id,
            "seller_id": self.merchant_id,
            "notify_id": f"notify_{payment_id}",
            "out_trade_no": payment_id,
            "trade_no": provider_trade_no,
            "total_amount": self._format_amount(amount_cents),
            "trade_status": "TRADE_SUCCESS",
        }
        return payload, self.sign_payload(payload)

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
            "app_id": str(payload.get("app_id") or ""),
            "notify_id": str(payload.get("notify_id") or ""),
            "merchant_id": str(payload.get("seller_id") or payload.get("merchant_id") or ""),
        }

    def sign_payload(self, payload: dict[str, Any]) -> str:
        content = self._canonical_payload(payload).encode("utf-8")
        signature = self._private_key.sign(
            content,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def verify_signature(self, payload: dict[str, Any], signature: str) -> bool:
        try:
            raw = base64.b64decode(signature)
        except Exception:
            return False
        try:
            self._public_key.verify(
                raw,
                self._canonical_payload(payload).encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception:
            return False
        return True

    @staticmethod
    def _format_amount(amount_cents: int) -> str:
        return f"{Decimal(amount_cents) / Decimal(100):.2f}"

    @staticmethod
    def _canonical_payload(payload: dict[str, Any]) -> str:
        pairs: list[tuple[str, str]] = []
        for key, value in payload.items():
            if key in {"sign", "sign_type"}:
                continue
            if value is None or value == "":
                continue
            pairs.append((str(key), str(value)))
        pairs.sort(key=lambda item: item[0])
        return "&".join(f"{key}={value}" for key, value in pairs)

    @staticmethod
    def _append_query_param(url: str, key: str, value: str) -> str:
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.append((key, value))
        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        ))
