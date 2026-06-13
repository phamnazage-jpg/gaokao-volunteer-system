from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class PortalTokenError(ValueError):
    pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def issue_portal_token(
    order_id: str, secret: str, ttl_seconds: int = 30 * 24 * 3600
) -> str:
    payload = {
        "order_id": order_id,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    payload_part = _b64url_encode(payload_raw)
    sig = hmac.new(
        secret.encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{payload_part}.{sig}"


def verify_portal_token(token: str, secret: str) -> dict[str, Any]:
    try:
        payload_part, sig = token.split(".", 1)
    except ValueError as exc:
        raise PortalTokenError("invalid portal token format") from exc
    expected = hmac.new(
        secret.encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise PortalTokenError("invalid portal token signature")
    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception as exc:  # pragma: no cover
        raise PortalTokenError("invalid portal token payload") from exc
    exp = int(payload.get("exp") or 0)
    if exp <= int(time.time()):
        raise PortalTokenError("portal token expired")
    order_id = payload.get("order_id")
    if not isinstance(order_id, str) or not order_id:
        raise PortalTokenError("portal token missing order_id")
    return payload
