"""X-06: dev-verify.sh 必须是稳定可调的本地一键验证入口。

锁死:
1. ``--help`` 退出码为 0, 输出包含“Usage”。
2. ``--skip-pre-existing`` 是合法 flag, 默认行为不变。
3. flag 拼写错误不会被悄悄忽略(返回 1 + usage)。
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dev-verify.sh"
BASH = shutil.which("bash") or "/usr/bin/bash"


def test_dev_verify_help_exits_zero_with_usage():
    proc = subprocess.run(
        [BASH, str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"dev-verify --help failed (rc={proc.returncode})\nstderr:\n{proc.stderr}"
    )
    combined = proc.stdout + proc.stderr
    assert "Usage" in combined


def test_dev_verify_rejects_unknown_flag():
    proc = subprocess.run(
        [BASH, str(SCRIPT), "--definitely-not-a-flag"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 1
    combined = proc.stdout + proc.stderr
    assert "unexpected argument" in combined


def test_dev_verify_skip_pre_existing_is_a_real_flag():
    """``--skip-pre-existing`` 必须被 ``--help`` 文档化, 否则
    调用者会不知道存在该 flag。"""
    proc = subprocess.run(
        [BASH, str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert "--skip-pre-existing" in combined
    assert "--skip-install" in combined


def test_dev_verify_ensure_venv_recovers_when_venv_exists_without_pip(tmp_path: Path):
    broken_venv = tmp_path / ".venv"
    subprocess.run(
        ["python3", "-m", "venv", "--without-pip", str(broken_venv)],
        check=True,
        text=True,
        capture_output=True,
    )

    probe = f"""
set -euo pipefail
export GAOKAO_SOURCE_ONLY=1
source {SCRIPT}
VENV_DIR={broken_venv}
PYTHON_BIN=python3
ensure_venv
\"$VENV_DIR/bin/python\" -m pip --version
"""
    proc = subprocess.run(
        [BASH, "-lc", probe],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"ensure_venv failed to self-heal broken venv (rc={proc.returncode})\n"
        f"stdout:\n{proc.stdout}\n"
        f"stderr:\n{proc.stderr}"
    )
    combined = proc.stdout + proc.stderr
    assert "pip" in combined
