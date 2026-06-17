"""Thin import shim for `scripts/gaokao-delivery-dispatch.py`."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "gaokao-delivery-dispatch.py"
)


def main(argv: list[str] | None = None) -> int:
    if not _SCRIPT_PATH.is_file():
        raise FileNotFoundError(f"gaokao-delivery-dispatch not found at {_SCRIPT_PATH}")
    previous_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT_PATH), *(argv or [])]
        runpy.run_path(str(_SCRIPT_PATH), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = previous_argv
    return 0
