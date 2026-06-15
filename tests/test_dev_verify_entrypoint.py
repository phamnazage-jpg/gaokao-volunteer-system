"""X-06: dev-verify.sh 必须是稳定可调的本地一键验证入口。

锁死:
1. ``--help`` 退出码为 0, 输出包含“Usage”。
2. ``--skip-pre-existing`` 是合法 flag, 默认行为不变。
3. flag 拼写错误不会被悄悄忽略(返回 1 + usage)。
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dev-verify.sh"


def test_dev_verify_help_exits_zero_with_usage():
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
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
        ["bash", str(SCRIPT), "--definitely-not-a-flag"],
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
        ["bash", str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert "--skip-pre-existing" in combined
    assert "--skip-install" in combined
