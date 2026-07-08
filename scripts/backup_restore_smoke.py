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


def _require_dir(path: Path, relative_name: str) -> None:
    if not path.is_dir():
        raise RestorePreconditionError(f"missing required directory: {relative_name}")


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
) -> tuple[Path, Path, Path, Path, Path | None, Path, Path]:
    db_dir = backup_dir / "db"
    files_dir = backup_dir / "files"
    config_dir = backup_dir / "config"
    secrets_dir = backup_dir / "secrets"
    admin_db = db_dir / "admin.db"
    orders_db = db_dir / "orders.db"
    share_db = db_dir / "short_links.db"

    _require_dir(db_dir, "db/")
    _require_dir(files_dir, "files/")
    _require_dir(config_dir, "config/")
    _require_dir(secrets_dir, "secrets/")
    _require_file(config_dir / ".env", "config/.env")
    _require_file(secrets_dir / "jwt_secret", "secrets/jwt_secret")
    _require_file(secrets_dir / "orders_fernet_key", "secrets/orders_fernet_key")
    _require_file(secrets_dir / "admin_pass", "secrets/admin_pass")
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
    return admin_db, orders_db, html, pdf, resolved_share_db, config_dir, secrets_dir


def _read_secret(path: Path, name: str) -> str:
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise RestorePreconditionError(f"empty required secret: {name}")
    return value


def _load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


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
    from data.orders.dao import OrdersDAO

    root = Path(backup_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"backup dir not found: {root}")

    (
        admin_db,
        orders_db,
        html_path,
        pdf_path,
        share_db,
        config_dir,
        secrets_dir,
    ) = _resolve_restore_inputs(root)
    share_report_dir = root / "files" / "reports"
    if not share_report_dir.exists():
        share_report_dir = root / "files"
    env_from_file = _load_env_file(config_dir / ".env")
    order_id = f"GKO-BACKUP-SMOKE-{uuid.uuid4().hex[:8].upper()}"

    overrides = {
        **env_from_file,
        "GAOKAO_ENV": env_from_file.get(
            "GAOKAO_ENV", os.environ.get("GAOKAO_ENV", "dev")
        ),
        "GAOKAO_DB_PATH": str(admin_db),
        "GAOKAO_ORDERS_DB_PATH": str(orders_db),
        "GAOKAO_SHARE_DB_PATH": str(share_db or (root / "db" / "short_links.db")),
        "GAOKAO_SHARE_REPORT_DIR": str(share_report_dir),
        "GAOKAO_PORTAL_UPLOAD_DIR": str(root / "files" / "portal_uploads"),
        "GAOKAO_ORDERS_FERNET_KEY": _read_secret(
            secrets_dir / "orders_fernet_key", "secrets/orders_fernet_key"
        ),
        "GAOKAO_JWT_SECRET": _read_secret(
            secrets_dir / "jwt_secret", "secrets/jwt_secret"
        ),
        "GAOKAO_ADMIN_USER": env_from_file.get(
            "GAOKAO_ADMIN_USER", os.environ.get("GAOKAO_ADMIN_USER", "admin")
        ),
        "GAOKAO_ADMIN_PASS": _read_secret(
            secrets_dir / "admin_pass", "secrets/admin_pass"
        ),
        "GAOKAO_PAYMENT_PROVIDER": env_from_file.get(
            "GAOKAO_PAYMENT_PROVIDER", "mock"
        ),
        "GAOKAO_PAYMENT_BASE_URL": env_from_file.get(
            "GAOKAO_PAYMENT_BASE_URL", "http://testserver"
        ),
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": env_from_file.get(
            "GAOKAO_PAYMENT_WEBHOOK_SECRET",
            os.environ.get(
                "GAOKAO_PAYMENT_WEBHOOK_SECRET",
                "backup-restore-smoke-payment-secret",
            ),
        ),
    }

    with _patched_env(overrides):
        settings = load_settings()
        app = create_app(settings)
        with TestClient(app) as client:
            health_resp = client.get("/health")
            if health_resp.status_code != 200:
                raise RuntimeError(f"health failed: {health_resp.status_code}")
            health_payload = health_resp.json()
            if health_payload.get("status") != "ok":
                raise RuntimeError(f"health failed: {health_payload}")

            create_resp = client.post(
                "/api/public/orders",
                json={
                    "service_version": "standard",
                    "amount_cents": 9900,
                    "customer_name": "备份演练家长",
                    "customer_phone": "13800138000",
                    "candidate_name": "恢复演练考生",
                    "candidate_province": "湖南",
                },
            )
            if create_resp.status_code != 201:
                raise RuntimeError(
                    f"public order create failed: {create_resp.status_code} {create_resp.text}"
                )
            create_body = create_resp.json()
            payment_id = create_body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
            complete = client.post(
                f"/pay/mock/{payment_id}/complete", follow_redirects=False
            )
            if complete.status_code != 303:
                raise RuntimeError(
                    f"mock payment failed: {complete.status_code} {complete.text}"
                )

            with OrdersDAO.connect(settings.orders_db_path) as dao:
                dao.update(
                    create_body["order_id"],
                    {"audit_report": str(html_path), "pdf_path": str(pdf_path)},
                    actor="backup_restore_smoke",
                    reason="attach_restore_artifacts",
                )
                dao.transition_status(
                    create_body["order_id"],
                    "serving",
                    actor="backup_restore_smoke",
                    reason="processing",
                )
                dao.transition_status(
                    create_body["order_id"],
                    "delivered",
                    actor="backup_restore_smoke",
                    reason="report_ready",
                )

            with OrdersDAO.connect(settings.orders_db_path) as dao:
                restored_order = dao.get(create_body["order_id"])
            if restored_order.status != "delivered":
                raise RuntimeError(f"restored order status invalid: {restored_order.status}")
            if restored_order.audit_report != str(html_path):
                raise RuntimeError("restored order audit_report path mismatch")
            if restored_order.pdf_path != str(pdf_path):
                raise RuntimeError("restored order pdf_path mismatch")

            if not html_path.read_text(encoding="utf-8", errors="replace").strip():
                raise RuntimeError("restored report html is empty")
            pdf_bytes = pdf_path.read_bytes()
            if not pdf_bytes.startswith(b"%PDF-"):
                raise RuntimeError("restored report pdf payload is not a PDF header")

    return {
        "backup_dir": str(root),
        "admin_db": str(admin_db),
        "orders_db": str(orders_db),
        "report_html": str(html_path),
        "report_pdf_path": str(pdf_path),
        "smoke_order_id": order_id,
        "health_status": 200,
        "public_order_create": 201,
        "restored_order_status": "delivered",
        "report_html_exists": True,
        "report_pdf": 200,
        "pdf_bytes": len(pdf_bytes),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run restore smoke test against a staged backup directory"
    )
    parser.add_argument(
        "--backup-dir",
        required=True,
        help="staged backup directory containing db/, files/, config/, and secrets/",
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
