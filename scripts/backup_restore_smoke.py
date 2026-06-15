#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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


def _choose_restore_file(backup_dir: Path, suffix: str) -> Path | None:
    candidates = sorted(
        path
        for path in (backup_dir / "files").rglob(f"*{suffix}")
        if path.is_file() and "__pycache__" not in path.parts
    )
    return candidates[0] if candidates else None


def _ensure_smoke_artifacts(backup_dir: Path) -> tuple[Path, Path]:
    smoke_dir = backup_dir / "files" / "_restore_smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)

    html = _choose_restore_file(backup_dir, ".html")
    pdf = _choose_restore_file(backup_dir, ".pdf")

    if html is None:
        html = smoke_dir / "restore-smoke-report.html"
        html.write_text(
            "<h1>备份恢复演练报告</h1><p>restore smoke generated</p>",
            encoding="utf-8",
        )
    if pdf is None:
        pdf = smoke_dir / "restore-smoke-report.pdf"
        pdf.write_bytes(b"%PDF-1.4\nrestore-smoke\n")
    return html, pdf


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
    from fastapi.testclient import TestClient

    from admin.app import create_app
    from admin.config import load_settings
    from data.customer_portal.token import issue_portal_token
    from data.orders.dao import OrdersDAO
    from data.orders.models import Order
    from data.payments.service import PaymentService

    root = Path(backup_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"backup dir not found: {root}")

    db_dir = root / "db"
    admin_db = db_dir / "admin.db"
    orders_db = db_dir / "orders.db"
    share_db = db_dir / "short_links.db"
    share_report_dir = root / "files" / "reports"
    if not share_report_dir.exists():
        share_report_dir = root / "files"

    html_path, pdf_path = _ensure_smoke_artifacts(root)
    order_id = f"GKO-BACKUP-SMOKE-{uuid.uuid4().hex[:8].upper()}"

    overrides = {
        "GAOKAO_ENV": os.environ.get("GAOKAO_ENV", "dev"),
        "GAOKAO_DB_PATH": str(admin_db),
        "GAOKAO_ORDERS_DB_PATH": str(orders_db),
        "GAOKAO_SHARE_DB_PATH": str(share_db),
        "GAOKAO_SHARE_REPORT_DIR": str(share_report_dir),
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
        app = create_app(settings)
        with TestClient(app) as client:
            health = client.get("/health")
            if health.status_code != 200:
                raise RuntimeError(f"health failed: {health.status_code} {health.text}")

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
                dao.create(
                    order, actor="backup_restore_smoke", reason="seed_pending_order"
                )

            payment_service = PaymentService.for_db(
                settings.orders_db_path,
                base_url=settings.payment_base_url,
                webhook_secret=settings.payment_webhook_secret,
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
            status_page = client.get(f"/portal/{token}/status")
            if status_page.status_code != 200 or "报告已就绪" not in status_page.text:
                raise RuntimeError(
                    f"portal status failed: {status_page.status_code} {status_page.text}"
                )

            report_page = client.get(f"/portal/{token}/report")
            if report_page.status_code != 200:
                raise RuntimeError(
                    f"portal report failed: {report_page.status_code} {report_page.text}"
                )

            pdf_resp = client.get(f"/portal/{token}/report.pdf")
            if pdf_resp.status_code != 200:
                raise RuntimeError(
                    f"portal pdf failed: {pdf_resp.status_code} {pdf_resp.text}"
                )
            if not pdf_resp.headers.get("content-type", "").startswith(
                "application/pdf"
            ):
                raise RuntimeError(
                    f"portal pdf content-type invalid: {pdf_resp.headers.get('content-type')}"
                )
            if not pdf_resp.content.startswith(b"%PDF-"):
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
        "pdf_bytes": len(pdf_resp.content),
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

    result = run_restore_smoke(args.backup_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
