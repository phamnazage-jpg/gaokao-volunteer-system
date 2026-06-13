from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from data.orders.models import utc_now_iso


@dataclass
class PaymentRecord:
    id: str
    order_id: str
    provider: str
    amount_cents: int
    currency: str = "CNY"
    status: str = "pending"
    provider_trade_no: Optional[str] = None
    checkout_token: Optional[str] = None
    callback_payload: Optional[str] = None
    refund_reason: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    paid_at: Optional[str] = None
    refunded_at: Optional[str] = None

    def __post_init__(self) -> None:
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class PaymentCheckout:
    payment_id: str
    provider: str
    checkout_url: str
    status: str


@dataclass
class WebhookHandleResult:
    payment_id: str
    processed: bool
    idempotent: bool
    order_status: str


@dataclass
class RefundRequestResult:
    payment_id: str
    status: str
