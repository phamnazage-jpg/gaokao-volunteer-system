#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DEFAULT_JWT_SECRET = "backup-restore-smoke-secret-0123456789abcdef0123456789abcdef"
DEFAULT_FERNET_SECRET = "backup-restore-smoke-fernet-secret"
DEFAULT_ADMIN_PASSWORD = "backup-restore-pass-123"


class RestorePreconditionError(RuntimeError):
    """恢复演练缺少关键前置条件时抛出。"""


def _choose_restore_file(backup_dir: Path, suffix: str) -> Path | None:
    search_roots = [
        backup_dir / "files" / "order_artifacts",
        backup_dir / "files" / "reports",
        backup_dir / "files",
    ]
    seen: set[Path] = set()
    candidates: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob(f"*{suffix}")):
            if not path.is_file() or "__pycache__" in path.parts or path in seen:
                continue
            seen.add(path)
            candidates.append(path)
    return candidates[0] if candidates else None


def _require_file(path: Path, relative_name: str) -> None:
    if not path.is_file():
        raise RestorePreconditionError(f"missing required file: {relative_name}")


def _read_table_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {str(row[0]) for row in rows}
    finally:
        conn.close()


def _require_tables(db_path: Path, required_tables: set[str], relative_name: str) -> None:
    tables = _read_table_names(db_path)
    missing = sorted(required_tables - tables)
    if missing:
        raise RestorePreconditionError(
            f"{relative_name} missing required tables: {', '.join(missing)}"
        )


def _resolve_restore_inputs(
    backup_dir: Path,
) -> tuple[Path, Path, Path, Path, Path | None]:
    db_dir = backup_dir / "db"
    admin_db = db_dir / "admin.db"
    orders_db = db_dir / "orders.db"
    share_db = db_dir / "short_links.db"

    _require_file(admin_db, "db/admin.db")
    _require_file(orders_db, "db/orders.db")
    _require_tables(admin_db, {"admin_users"}, "db/admin.db")
    _require_tables(orders_db, {"orders", "order_status_history"}, "db/orders.db")

    html = _choose_restore_file(backup_dir, ".html")
    pdf = _choose_restore_file(backup_dir, ".pdf")
    if html is None:
        raise RestorePreconditionError("missing report html under files/")
    if pdf is None:
        raise RestorePreconditionError("missing report pdf under files/")

    resolved_share_db = share_db if share_db.is_file() else None
    return admin_db, orders_db, html, pdf, resolved_share_db


@contextmanager
def _patched_env(overrides: dict[str, str]) -> Iterator[None]:
    original = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        yield
    finally:
        for key, old_value in original.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def run_restore_smoke(backup_dir: str | Path) -> dict[str, object]:
    from admin.app import _setup_database, _validate_and_log_settings
    from admin.config import load_settings
    from admin.routes.health import health
    from admin.routes.web_public import (
        order_status_page,
        report_pdf_download,
        report_view_page,
    )
    from data.customer_portal.token import issue_portal_token
    from data.orders.dao import OrdersDAO
    from data.orders.models import Order
    from data.payments.service import PaymentService

    root = Path(backup_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"backup dir not found: {root}")

    admin_db, orders_db, html_path, pdf_path, share_db = _resolve_restore_inputs(root)
    share_report_dir = root / "files" / "reports"
    if not share_report_dir.exists():
        share_report_dir = root / "files"

    order_id = f"GKO-BACKUP-SMOKE-{uuid.uuid4().hex[:8].upper()}"

    overrides = {
        "GAOKAO_ENV": os.environ.get("GAOKAO_ENV", "dev"),
        "GAOKAO_DB_PATH": str(admin_db),
        "GAOKAO_ORDERS_DB_PATH": str(orders_db),
        "GAOKAO_SHARE_DB_PATH": str(share_db or (root / "db" / "short_links.db")),
        "GAOKAO_SHARE_REPORT_DIR": str(share_report_dir),
        "GAOKAO_PORTAL_UPLOAD_DIR": str(root / "files" / "portal_uploads"),
        "GAOKAO_ORDERS_FERNET_KEY": os.environ.get(
            "GAOKAO_ORDERS_FERNET_KEY", DEFAULT_FERNET_SECRET
        ),
        "GAOKAO_JWT_SECRET": os.environ.get("GAOKAO_JWT_SECRET", DEFAULT_JWT_SECRET),
        "GAOKAO_ADMIN_USER": os.environ.get("GAOKAO_ADMIN_USER", "admin"),
        "GAOKAO_ADMIN_PASS": os.environ.get(
            "GAOKAO_ADMIN_PASS", DEFAULT_ADMIN_PASSWORD
        ),
        "GAOKAO_PAYMENT_PROVIDER": "mock",
        "GAOKAO_PAYMENT_BASE_URL": "http://testserver",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": os.environ.get(
            "GAOKAO_PAYMENT_WEBHOOK_SECRET", "backup-restore-smoke-payment-secret"
        ),
    }

    with _patched_env(overrides):
        settings = load_settings()
        _validate_and_log_settings(settings)
        _setup_database(settings)

        health_payload = health(settings)
        if health_payload.get("status") != "ok":
            raise RuntimeError(f"health failed: {health_payload}")

        order = Order(
            id=order_id,
            source="web",
            service_version="standard",
            amount_cents=9900,
            status="pending",
            customer_name="备份演练家长",
            customer_phone="13800138000",
            candidate_name="恢复演练考生",
            candidate_province="湖南",
        )
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            dao.create(order, actor="backup_restore_smoke", reason="seed_pending_order")

        payment_service = PaymentService.for_db(
            settings.orders_db_path,
            base_url=settings.payment_base_url,
            webhook_secret=settings.payment_webhook_secret,
            provider_name=settings.payment_provider,
        )
        checkout = payment_service.create_checkout(
            order.id, portal_token="backup-smoke-token"
        )
        payload, headers = payment_service.provider.build_webhook_request(
            payment_id=checkout.payment_id,
            amount_cents=order.amount_cents,
            provider_trade_no=f"SMOKE-{order.id}",
        )
        payment_service.handle_webhook(payload, headers.get("X-Mock-Signature", ""))

        with OrdersDAO.connect(settings.orders_db_path) as dao:
            dao.update(
                order.id,
                {"audit_report": str(html_path), "pdf_path": str(pdf_path)},
                actor="backup_restore_smoke",
                reason="attach_restore_artifacts",
            )
            dao.transition_status(
                order.id,
                "serving",
                actor="backup_restore_smoke",
                reason="processing",
            )
            dao.transition_status(
                order.id,
                "delivered",
                actor="backup_restore_smoke",
                reason="report_ready",
            )

        token = issue_portal_token(order.id, settings.portal_token_secret)
        status_page = order_status_page(token, settings)
        status_body = bytes(status_page.body).decode("utf-8")
        if status_page.status_code != 200 or "报告已就绪" not in status_body:
            raise RuntimeError(
                f"portal status failed: {status_page.status_code} {status_body}"
            )

        report_page = report_view_page(token, settings)
        report_body = bytes(report_page.body).decode("utf-8")
        if report_page.status_code != 200 or not report_body.strip():
            raise RuntimeError(
                f"portal report failed: {report_page.status_code} {report_body}"
            )

        pdf_resp = report_pdf_download(token, settings)
        if pdf_resp.status_code != 200:
            raise RuntimeError(f"portal pdf failed: {pdf_resp.status_code}")
        if pdf_resp.media_type != "application/pdf":
            raise RuntimeError(
                f"portal pdf content-type invalid: {pdf_resp.media_type}"
            )
        pdf_response_path = Path(pdf_resp.path)
        if not pdf_response_path.is_file():
            raise RuntimeError(f"portal pdf path missing: {pdf_response_path}")
        pdf_bytes = pdf_response_path.read_bytes()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise RuntimeError("portal pdf payload is not a PDF header")

    result = {
        "backup_dir": str(root),
        "admin_db": str(admin_db),
        "orders_db": str(orders_db),
        "report_html": str(html_path),
        "report_pdf": str(pdf_path),
        "smoke_order_id": order_id,
        "health_status": 200,
        "portal_status": 200,
        "portal_report": 200,
        "portal_pdf": 200,
        "pdf_bytes": len(pdf_bytes),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run restore smoke test against a staged backup directory"
    )
    parser.add_argument(
        "--backup-dir",
        required=True,
        help="staged backup directory containing db/ and files/",
    )
    args = parser.parse_args(argv)

    try:
        result = run_restore_smoke(args.backup_dir)
    except RestorePreconditionError as exc:
        print(f"restore precondition failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
