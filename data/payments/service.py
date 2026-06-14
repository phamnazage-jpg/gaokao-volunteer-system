from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Optional

from data.orders.dao import OrdersDAO
from data.payments.dao import PaymentDAO
from data.payments.models import (
    PaymentCheckout,
    PaymentRecord,
    RefundRequestResult,
    WebhookHandleResult,
)
from data.payments.provider_requirements import build_provider_readiness_report
from data.payments.providers.alipay import AlipayProvider
from data.payments.providers.alipay_sim import AlipaySimProvider
from data.payments.providers.mock_gateway import MockPaymentProvider


class PaymentError(ValueError):
    pass


def _build_provider(
    *,
    provider_name: str,
    base_url: str,
    webhook_secret: str,
    notify_url: str = "",
    return_url: str = "",
    app_id: str = "",
    private_key_path: str = "",
    alipay_public_key_path: str = "",
):
    normalized = (provider_name or "mock").strip().lower()
    if normalized == "mock":
        return MockPaymentProvider(base_url=base_url, secret=webhook_secret)
    if normalized == "alipay_sim":
        return AlipaySimProvider(base_url=base_url, secret=webhook_secret)
    if normalized == "alipay":
        report = build_provider_readiness_report(
            "alipay",
            env={
                "GAOKAO_PAYMENT_APP_ID": app_id,
                "GAOKAO_PAYMENT_PRIVATE_KEY_PATH": private_key_path,
                "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH": alipay_public_key_path,
                "GAOKAO_PAYMENT_NOTIFY_URL": notify_url,
                "GAOKAO_PAYMENT_RETURN_URL": return_url,
                "GAOKAO_PAYMENT_WEBHOOK_SECRET": webhook_secret,
            },
        )
        if not report.ready:
            details: list[str] = []
            if report.missing_env_vars:
                details.append(
                    "missing env vars: " + ", ".join(report.missing_env_vars)
                )
            if report.missing_files:
                details.append("missing files: " + ", ".join(report.missing_files))
            raise PaymentError("alipay provider not ready: " + "; ".join(details))
        return AlipayProvider(
            app_id=app_id,
            private_key_path=private_key_path,
            alipay_public_key_path=alipay_public_key_path,
            notify_url=notify_url,
            return_url=return_url,
        )
    raise PaymentError(f"unsupported payment provider: {normalized}")


@dataclass
class ProviderBundle:
    provider: MockPaymentProvider


class PaymentService:
    def __init__(
        self,
        *,
        db_path: str,
        base_url: str,
        webhook_secret: str,
        provider_name: str = "mock",
        notify_url: str = "",
        return_url: str = "",
        app_id: str = "",
        private_key_path: str = "",
        alipay_public_key_path: str = "",
    ) -> None:
        self.db_path = db_path
        self.base_url = base_url
        self.provider = _build_provider(
            provider_name=provider_name,
            base_url=base_url,
            webhook_secret=webhook_secret,
            notify_url=notify_url,
            return_url=return_url,
            app_id=app_id,
            private_key_path=private_key_path,
            alipay_public_key_path=alipay_public_key_path,
        )

    @classmethod
    def for_db(
        cls,
        db_path: str,
        *,
        base_url: str,
        webhook_secret: str = "dev-mock-payment-secret",
        provider_name: str = "mock",
        notify_url: str = "",
        return_url: str = "",
        app_id: str = "",
        private_key_path: str = "",
        alipay_public_key_path: str = "",
    ) -> "PaymentService":
        return cls(
            db_path=db_path,
            base_url=base_url,
            webhook_secret=webhook_secret,
            provider_name=provider_name,
            notify_url=notify_url,
            return_url=return_url,
            app_id=app_id,
            private_key_path=private_key_path,
            alipay_public_key_path=alipay_public_key_path,
        )

    def create_checkout(self, order_id: str, *, portal_token: str) -> PaymentCheckout:
        with OrdersDAO.connect(self.db_path) as orders_dao:
            order = orders_dao.get(order_id)
        payments = PaymentDAO.for_db(self.db_path)
        try:
            existing = payments.get_by_order(order_id)
            if existing is not None and existing.status in {
                "pending",
                "paid",
                "refund_pending",
            }:
                return PaymentCheckout(
                    payment_id=existing.id,
                    provider=existing.provider,
                    checkout_url=self.provider.build_checkout_url(
                        existing.id,
                        portal_token,
                        amount_cents=existing.amount_cents,
                        subject=f"高考志愿服务-{order.service_version}",
                    ),
                    status=existing.status,
                )
            payment = payments.create(
                PaymentRecord(
                    id=f"pay_{secrets.token_hex(8)}",
                    order_id=order.id,
                    provider=self.provider.name,
                    amount_cents=order.amount_cents,
                    checkout_token=portal_token,
                )
            )
            return PaymentCheckout(
                payment_id=payment.id,
                provider=payment.provider,
                checkout_url=self.provider.build_checkout_url(
                    payment.id,
                    portal_token,
                    amount_cents=payment.amount_cents,
                    subject=f"高考志愿服务-{order.service_version}",
                ),
                status=payment.status,
            )
        finally:
            payments.close()

    def get_payment(self, payment_id: str) -> Optional[PaymentRecord]:
        payments = PaymentDAO.for_db(self.db_path)
        try:
            return payments.get(payment_id)
        finally:
            payments.close()

    def get_payment_by_order(self, order_id: str) -> Optional[PaymentRecord]:
        payments = PaymentDAO.for_db(self.db_path)
        try:
            return payments.get_by_order(order_id)
        finally:
            payments.close()

    def handle_webhook(self, payload: dict, signature: str) -> WebhookHandleResult:
        if not self.provider.verify_signature(payload, signature):
            raise PaymentError("invalid payment signature")
        normalized_payload = self.provider.normalize_webhook_payload(payload)
        payment_id = str(normalized_payload.get("payment_id") or "")
        if not payment_id:
            raise PaymentError("missing payment_id")

        with OrdersDAO.connect(self.db_path) as orders_dao:
            payments = PaymentDAO.from_connection(orders_dao.conn)
            with orders_dao.transaction():
                payment = payments.get(payment_id)
                if payment is None:
                    raise PaymentError("payment not found")
                if (
                    int(normalized_payload.get("amount_cents") or -1)
                    != payment.amount_cents
                ):
                    raise PaymentError("payment amount mismatch")
                if payment.status == "paid":
                    order = orders_dao.get(payment.order_id)
                    return WebhookHandleResult(
                        payment_id=payment.id,
                        processed=True,
                        idempotent=True,
                        order_status=order.status,
                    )
                updated = payments.update_status(
                    payment.id,
                    status="paid",
                    provider_trade_no=str(
                        normalized_payload.get("provider_trade_no")
                        or payment.provider_trade_no
                        or ""
                    ),
                    callback_payload=payload,
                )
                order = orders_dao.get(updated.order_id)
                if order.status == "pending":
                    order = orders_dao.transition_status(
                        updated.order_id,
                        "paid",
                        actor="payment_webhook",
                        reason="payment_paid",
                    )
        return WebhookHandleResult(
            payment_id=updated.id,
            processed=True,
            idempotent=False,
            order_status=order.status,
        )

    def request_refund(self, order_id: str, *, reason: str) -> RefundRequestResult:
        payments = PaymentDAO.for_db(self.db_path)
        try:
            payment = payments.get_by_order(order_id)
            if payment is None:
                raise PaymentError("payment not found for order")
            if payment.status in {"refund_pending", "refunded"}:
                return RefundRequestResult(payment_id=payment.id, status=payment.status)
            if payment.status != "paid":
                raise PaymentError("payment is not refundable")
            updated = payments.update_status(
                payment.id,
                status="refund_pending",
                refund_reason=reason,
            )
            return RefundRequestResult(payment_id=updated.id, status=updated.status)
        finally:
            payments.close()
