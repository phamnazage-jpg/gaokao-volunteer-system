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


def test_dev_verify_excludes_test_packages_from_coverage_args():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "--cov=." not in script
    assert "--cov=tests" not in script
    assert "--cov=admin/tests" not in script
    assert "--cov=admin" in script
    assert "--cov=data" in script


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


def test_dev_verify_skip_install_does_not_upgrade_pip(tmp_path: Path):
    venv_dir = tmp_path / ".venv"
    subprocess.run(
        ["python3", "-m", "venv", str(venv_dir)],
        check=True,
        text=True,
        capture_output=True,
    )

    python_bin = venv_dir / "bin" / "python"
    real_python = venv_dir / "bin" / "python-real"
    python_bin.rename(real_python)
    python_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "-m" && "${2:-}" == "pip" && "${3:-}" == "install" ]]; then
  echo "unexpected pip install" >&2
  exit 99
fi
exec "$(dirname "$0")/python-real" "$@"
""",
        encoding="utf-8",
    )
    python_bin.chmod(0o755)

    probe = f"""
set -euo pipefail
export GAOKAO_SOURCE_ONLY=1
source {SCRIPT}
VENV_DIR={venv_dir}
PYTHON_BIN=python3
SKIP_INSTALL=1
ensure_venv
"""
    proc = subprocess.run(
        [BASH, "-lc", probe],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"ensure_venv should not upgrade pip when skip-install is enabled (rc={proc.returncode})\n"
        f"stdout:\n{proc.stdout}\n"
        f"stderr:\n{proc.stderr}"
    )
    assert "unexpected pip install" not in (proc.stdout + proc.stderr)


def test_dev_verify_pre_existing_ignores_only_keeps_locust_probe():
    probe = f"""
set -euo pipefail
export GAOKAO_SOURCE_ONLY=1
source {SCRIPT}
printf '%s\n' "${{PRE_EXISTING_IGNORES[@]}}"
"""
    proc = subprocess.run(
        [BASH, "-lc", probe],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    ignores = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    assert ignores == [
        "tests/test_t5_performance.py::test_admin_locust_10_concurrency_success_rate_above_95"
    ]


def test_dev_verify_detects_python_bin_drift(tmp_path: Path):
    venv_dir = tmp_path / ".venv"
    subprocess.run(
        ["python3", "-m", "venv", str(venv_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    fake_python = tmp_path / "python-fake"
    fake_python.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ \"${1:-}\" == \"--version\" ]]; then
  echo \"Python 9.9.9\"
  exit 0
fi
exec /usr/bin/python3 \"$@\"
""",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    probe = f"""
set -euo pipefail
export GAOKAO_SOURCE_ONLY=1
source {SCRIPT}
VENV_DIR={venv_dir}
PYTHON_BIN={fake_python}
ensure_venv
"""
    proc = subprocess.run(
        [BASH, "-lc", probe],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "python bin drift" in combined
