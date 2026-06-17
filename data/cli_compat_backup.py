"""Thin import shim for the `scripts/backup_snapshot.sh` / `backup_verify.sh` shells."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

_SHELL_TARGETS = {
    "snapshot": _SCRIPTS_DIR / "backup_snapshot.sh",
    "verify": _SCRIPTS_DIR / "backup_verify.sh",
}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] not in _SHELL_TARGETS:
        valid = ", ".join(sorted(_SHELL_TARGETS))
        raise SystemExit(f"gaokao-cli backup expects one of [{valid}]; got: {argv!r}")
    subcommand = argv[0]
    target = _SHELL_TARGETS[subcommand]
    if not target.is_file():
        raise FileNotFoundError(f"backup script not found at {target}")
    completed = subprocess.run(
        ["bash", str(target), *argv[1:]],
        check=False,
    )
    return completed.returncode
