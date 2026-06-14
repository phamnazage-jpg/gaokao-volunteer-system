from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

from admin.db import ensure_schema
from data.orders.schema import apply_schema

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _bootstrap_share_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS short_links (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()


def _prepare_backup_sources(settings, tmp_path: Path) -> dict[str, str]:
    ensure_schema(settings.db_path)
    apply_schema(settings.orders_db_path).close()
    _bootstrap_share_db(settings.share_db_path)

    share_report_dir = Path(settings.share_report_dir)
    share_report_dir.mkdir(parents=True, exist_ok=True)
    (share_report_dir / "sample-report.json").write_text("{}", encoding="utf-8")

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
    assert any(path.startswith("files/examples/") for path in manifest_paths)

    remaining = sorted(path.name for path in backup_root.iterdir() if path.is_dir())
    assert len(remaining) == 2
    assert "backup-20240101T000000Z" not in remaining
    assert snapshot_dir.name in remaining


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
