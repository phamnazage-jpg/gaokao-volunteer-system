from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from data.orders.models import utc_now_iso
from data.orders.schema import apply_schema
from data.payments.models import PaymentRecord


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
    currency TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','paid','failed','refunded')),
    provider_trade_no TEXT,
    checkout_token TEXT,
    callback_payload TEXT,
    refund_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    paid_at TEXT,
    refunded_at TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
"""


class PaymentDAO:
    def __init__(self, conn: sqlite3.Connection, *, autocommit: bool = True) -> None:
        self._conn = conn
        self._autocommit = autocommit

    @classmethod
    def for_db(cls, db_path: str | Path) -> "PaymentDAO":
        conn = apply_schema(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        return cls(conn, autocommit=True)

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "PaymentDAO":
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        return cls(conn, autocommit=False)

    def close(self) -> None:
        self._conn.close()

    def create(self, payment: PaymentRecord) -> PaymentRecord:
        self._conn.execute(
            """
            INSERT INTO payments(id, order_id, provider, amount_cents, currency, status, provider_trade_no,
                                 checkout_token, callback_payload, refund_reason, created_at, updated_at, paid_at, refunded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payment.id,
                payment.order_id,
                payment.provider,
                payment.amount_cents,
                payment.currency,
                payment.status,
                payment.provider_trade_no,
                payment.checkout_token,
                payment.callback_payload,
                payment.refund_reason,
                payment.created_at,
                payment.updated_at,
                payment.paid_at,
                payment.refunded_at,
            ),
        )
        if self._autocommit:
            self._conn.commit()
        created = self.get(payment.id)
        assert created is not None
        return created

    def get(self, payment_id: str) -> Optional[PaymentRecord]:
        row = self._conn.execute(
            "SELECT * FROM payments WHERE id=?",
            (payment_id,),
        ).fetchone()
        return self._row_to_payment(row) if row is not None else None

    def get_by_order(self, order_id: str) -> Optional[PaymentRecord]:
        row = self._conn.execute(
            "SELECT * FROM payments WHERE order_id=? ORDER BY created_at DESC LIMIT 1",
            (order_id,),
        ).fetchone()
        return self._row_to_payment(row) if row is not None else None

    def update_status(
        self,
        payment_id: str,
        *,
        status: str,
        provider_trade_no: Optional[str] = None,
        callback_payload: Optional[dict] = None,
        refund_reason: Optional[str] = None,
    ) -> PaymentRecord:
        now = utc_now_iso()
        payment = self.get(payment_id)
        if payment is None:
            raise LookupError(f"payment not found: {payment_id}")
        payload_json = payment.callback_payload
        if callback_payload is not None:
            payload_json = json.dumps(callback_payload, ensure_ascii=False)
        paid_at = payment.paid_at
        refunded_at = payment.refunded_at
        if status == "paid" and paid_at is None:
            paid_at = now
        if status == "refunded" and refunded_at is None:
            refunded_at = now
        self._conn.execute(
            """
            UPDATE payments
            SET status=?, provider_trade_no=?, callback_payload=?, refund_reason=?, updated_at=?, paid_at=?, refunded_at=?
            WHERE id=?
            """,
            (
                status,
                provider_trade_no or payment.provider_trade_no,
                payload_json,
                refund_reason or payment.refund_reason,
                now,
                paid_at,
                refunded_at,
                payment_id,
            ),
        )
        if self._autocommit:
            self._conn.commit()
        updated = self.get(payment_id)
        assert updated is not None
        return updated

    @staticmethod
    def _row_to_payment(row: sqlite3.Row) -> PaymentRecord:
        return PaymentRecord(
            id=row["id"],
            order_id=row["order_id"],
            provider=row["provider"],
            amount_cents=int(row["amount_cents"]),
            currency=row["currency"],
            status=row["status"],
            provider_trade_no=row["provider_trade_no"],
            checkout_token=row["checkout_token"],
            callback_payload=row["callback_payload"],
            refund_reason=row["refund_reason"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            paid_at=row["paid_at"],
            refunded_at=row["refunded_at"],
        )
