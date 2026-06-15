"""P1-8: 备份恢复必须升级到服务级验证。

历史:
- ``backup_verify.sh`` 之前只复制文件,然后验证 SQLite 文件能打开。
- 2026-06-14 严格复审判定这只是“文件级验证”,不构成“系统可恢复”。
- 修复后:
  1. ``backup_verify.sh`` 优先调用 venv python
  2. ``backup_restore_smoke.py`` 真的把 admin/orders DB 喂回 FastAPI TestClient
  3. 真实执行 /api/public/orders 等关键端点,确认恢复后系统可用
- 本测试锁定该行为,使未来回归(例如换成 ``python3``)立刻失败。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _prepare_backup_dir(staging: Path) -> None:
    staging.mkdir(parents=True, exist_ok=True)
    db_dir = staging / "db"
    files_dir = staging / "files"
    db_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)

    src_orders = REPO_ROOT / "data" / "orders.db"
    src_share = REPO_ROOT / "data" / "share" / "short_links.db"
    src_admin = REPO_ROOT / "data" / "orders" / "admin.db"
    if src_orders.exists():
        shutil.copy(src_orders, db_dir / "orders.db")
    if src_share.exists():
        shutil.copy(src_share, db_dir / "short_links.db")
    if src_admin.exists():
        shutil.copy(src_admin, db_dir / "admin.db")

    src_reports = REPO_ROOT / "data" / "share" / "reports"
    if src_reports.exists():
        shutil.copytree(src_reports, files_dir / "reports")


def test_backup_verify_uses_venv_python_for_service_level_restore(tmp_path):
    staging = tmp_path / "backup"
    _prepare_backup_dir(staging)

    env = os.environ.copy()
    env.pop("GAOKAO_PYTHON_BIN", None)
    # Force the shell script to fall back to its own venv detection
    # logic by hiding any caller-provided PYTHON_BIN.
    env.pop("PYTHON_BIN", None)
    # Ensure no GAOKAO_DB_PATH override leaks in from the test env.

    proc = subprocess.run(
        ["bash", str(SCRIPTS_DIR / "backup_verify.sh"), "--from-backup", str(staging)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, (
        f"backup_verify.sh failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    # The smoke output should be a JSON block with a 200 health_status.
    # That is the contract that distinguishes service-level from
    # file-level recovery.
    assert '"health_status": 200' in proc.stdout
    assert '"smoke_order_id"' in proc.stdout
    # Venv python must be used; if the script ever silently falls
    # back to ``python3``, a developer without the admin dependencies
    # installed globally will see the same ModuleNotFoundError that
    # motivated this regression lock.
    assert "ModuleNotFoundError" not in proc.stderr
    assert "ModuleNotFoundError" not in proc.stdout
