from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

from admin.db import ensure_schema
from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.orders.schema import apply_schema

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _bootstrap_share_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS short_links (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()


def _list_tables(db_path: Path) -> list[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def _count_rows(db_path: Path, table_name: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0])
    finally:
        conn.close()


def _prepare_backup_sources(settings, tmp_path: Path) -> dict[str, str]:
    ensure_schema(settings.db_path)
    apply_schema(settings.orders_db_path).close()
    _bootstrap_share_db(settings.share_db_path)

    share_report_dir = Path(settings.share_report_dir)
    share_report_dir.mkdir(parents=True, exist_ok=True)
    (share_report_dir / "sample-report.json").write_text("{}", encoding="utf-8")

    portal_upload_dir = Path(settings.portal_upload_dir)
    portal_upload_dir.mkdir(parents=True, exist_ok=True)
    portal_order_dir = portal_upload_dir / "ORDER-1"
    portal_order_dir.mkdir(parents=True, exist_ok=True)
    (portal_order_dir / "score.pdf").write_bytes(b"%PDF-1.4\nportal-upload\n")

    report_path = tmp_path / "delivery-report.html"
    pdf_path = tmp_path / "delivery-report.pdf"
    report_path.write_text("<h1>delivery report</h1>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\ndelivery\n")
    order = Order(
        id="ORDER-1",
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="delivered",
        customer_name="备份测试家长",
        customer_phone="13800138000",
        candidate_name="备份测试考生",
        candidate_province="湖南",
        audit_report=str(report_path),
        pdf_path=str(pdf_path),
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.create(order, actor="test", reason="seed")

    env_file = tmp_path / ".env.runtime"
    env_file.write_text("GAOKAO_ENV=dev\n", encoding="utf-8")

    config_dir = tmp_path / "deploy-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")

    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    (secrets_dir / "jwt.secret").write_text("secret", encoding="utf-8")

    return {
        "GAOKAO_DB_PATH": settings.db_path,
        "GAOKAO_ORDERS_DB_PATH": settings.orders_db_path,
        "GAOKAO_SHARE_DB_PATH": settings.share_db_path,
        "GAOKAO_SHARE_REPORT_DIR": settings.share_report_dir,
        "GAOKAO_PORTAL_UPLOAD_DIR": settings.portal_upload_dir,
        "GAOKAO_BACKUP_ENV_FILE": str(env_file),
        "GAOKAO_BACKUP_CONFIG_DIR": str(config_dir),
        "GAOKAO_BACKUP_SECRETS_DIR": str(secrets_dir),
    }


def _run_snapshot(env: dict[str, str], backup_root: Path) -> Path:
    proc = subprocess.run(
        ["bash", "scripts/backup_snapshot.sh", str(backup_root)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return Path(proc.stdout.strip().splitlines()[-1])


def test_backup_snapshot_creates_manifest_and_prunes_old_backups(settings, tmp_path):
    env = {
        **os.environ,
        **_prepare_backup_sources(settings, tmp_path),
        "GAOKAO_BACKUP_KEEP": "2",
    }
    backup_root = tmp_path / "backups"
    (backup_root / "backup-20240101T000000Z").mkdir(parents=True, exist_ok=True)
    (backup_root / "backup-20240102T000000Z").mkdir(parents=True, exist_ok=True)

    snapshot_dir = _run_snapshot(env, backup_root)

    assert snapshot_dir.is_dir()
    manifest_path = snapshot_dir / "manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_paths = {item["path"] for item in manifest["files"]}
    assert "db/admin.db" in manifest_paths
    assert "db/orders.db" in manifest_paths
    assert "db/short_links.db" in manifest_paths
    assert "config/.env" in manifest_paths
    assert "config/deploy/docker-compose.yml" in manifest_paths
    assert "secrets/jwt.secret" in manifest_paths
    assert "files/portal_uploads/ORDER-1/score.pdf" in manifest_paths
    assert any(
        path.startswith("files/order_artifacts/ORDER-1/audit_report/") for path in manifest_paths
    )
    assert any(
        path.startswith("files/order_artifacts/ORDER-1/pdf_path/") for path in manifest_paths
    )
    assert any(path.startswith("files/examples/") for path in manifest_paths)

    remaining = sorted(path.name for path in backup_root.iterdir() if path.is_dir())
    assert len(remaining) == 2
    assert "backup-20240101T000000Z" not in remaining
    assert snapshot_dir.name in remaining


def test_backup_snapshot_preserves_admin_db_contents_under_wal(tmp_path):
    admin_db = tmp_path / "admin.db"
    live_conn = sqlite3.connect(admin_db)
    try:
        journal_mode = live_conn.execute("PRAGMA journal_mode=WAL").fetchone()
        assert journal_mode is not None
        assert str(journal_mode[0]).lower() == "wal"
        live_conn.execute("PRAGMA wal_autocheckpoint = 0")
        live_conn.execute(
            "CREATE TABLE admin_users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)"
        )
        live_conn.execute(
            "INSERT INTO admin_users(username) VALUES (?)", ("snapshot-admin",)
        )
        live_conn.commit()

        wal_path = admin_db.with_name(f"{admin_db.name}-wal")
        assert wal_path.exists()

        snapshot_dir = _run_snapshot(
            {
                **os.environ,
                "GAOKAO_DB_PATH": str(admin_db),
            },
            tmp_path / "backups",
        )
    finally:
        live_conn.close()

    snapshot_admin_db = snapshot_dir / "db" / "admin.db"
    assert _list_tables(admin_db) == ["admin_users"]
    assert _count_rows(admin_db, "admin_users") == 1
    assert "admin_users" in _list_tables(snapshot_admin_db)
    assert _count_rows(snapshot_admin_db, "admin_users") == 1


def test_backup_verify_live_copy_handles_wal_sqlite(tmp_path):
    admin_db = tmp_path / "admin.db"
    verify_dir = tmp_path / "verify"
    live_conn = sqlite3.connect(admin_db)
    try:
        journal_mode = live_conn.execute("PRAGMA journal_mode=WAL").fetchone()
        assert journal_mode is not None
        assert str(journal_mode[0]).lower() == "wal"
        live_conn.execute("PRAGMA wal_autocheckpoint = 0")
        live_conn.execute(
            "CREATE TABLE admin_users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)"
        )
        live_conn.execute(
            "INSERT INTO admin_users(username) VALUES (?)", ("verify-admin",)
        )
        live_conn.commit()

        wal_path = admin_db.with_name(f"{admin_db.name}-wal")
        assert wal_path.exists()

        proc = subprocess.run(
            ["bash", "scripts/backup_verify.sh", str(verify_dir), "--skip-smoke"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "GAOKAO_DB_PATH": str(admin_db),
            },
            check=False,
        )
    finally:
        live_conn.close()

    assert proc.returncode == 0, proc.stderr
    staged_admin_db = verify_dir / "db" / "admin.db"
    assert staged_admin_db.is_file()
    assert "admin_users" in _list_tables(staged_admin_db)
    assert _count_rows(staged_admin_db, "admin_users") == 1


def test_backup_verify_runs_restore_smoke_on_snapshot(settings, tmp_path):
    env = {
        **os.environ,
        **_prepare_backup_sources(settings, tmp_path),
        "GAOKAO_PAYMENT_PROVIDER": "alipay",
    }
    backup_root = tmp_path / "backups"
    snapshot_dir = _run_snapshot(env, backup_root)

    proc = subprocess.run(
        ["bash", "scripts/backup_verify.sh", "--from-backup", str(snapshot_dir)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "manifest_ok files=" in proc.stdout
    assert '"portal_status": 200' in proc.stdout
    assert '"portal_report": 200' in proc.stdout
    assert '"portal_pdf": 200' in proc.stdout
    assert "backup verification finished" in proc.stdout


def test_backup_verify_stages_live_portal_uploads_and_order_artifacts(
    settings, tmp_path
):
    env = {
        **os.environ,
        **_prepare_backup_sources(settings, tmp_path),
    }
    verify_dir = tmp_path / "verify"

    proc = subprocess.run(
        ["bash", "scripts/backup_verify.sh", str(verify_dir), "--skip-smoke"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert (verify_dir / "files" / "portal_uploads" / "ORDER-1" / "score.pdf").is_file()
    assert any(
        path.is_file()
        for path in (verify_dir / "files" / "order_artifacts").rglob("*.html")
    )
    assert any(
        path.is_file()
        for path in (verify_dir / "files" / "order_artifacts").rglob("*.pdf")
    )
    assert "copied order artifacts:" in proc.stdout


def test_dr_drill_template_exists_and_references_target_machine_acceptance():
    report = PROJECT_ROOT / "reports" / "DR_DRILL_TEMPLATE.md"
    assert report.is_file()
    body = report.read_text(encoding="utf-8")
    assert "目标主机" in body
    assert "backup_verify.sh --from-backup" in body
    assert "portal_status" in body


def test_backup_plan_references_dr_drill_template():
    doc = (PROJECT_ROOT / "docs" / "BACKUP_AND_RECOVERY_PLAN.md").read_text(
        encoding="utf-8"
    )
    assert "reports/DR_DRILL_TEMPLATE.md" in doc
