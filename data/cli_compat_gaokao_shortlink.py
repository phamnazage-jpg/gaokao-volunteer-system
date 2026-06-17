"""Thin import shim for the legacy `gaokao-shortlink` script.

The script is shipped as a top-level module under `scripts/`. It uses
argparse directly and does not expose a stable Python entrypoint, so
we exec it via `runpy` and forward `main(argv)`.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "gaokao-shortlink"


def main(argv: list[str] | None = None) -> int:
    if not _SCRIPT_PATH.is_file():
        raise FileNotFoundError(f"gaokao-shortlink not found at {_SCRIPT_PATH}")
    previous_argv = sys.argv
    try:
        if argv is None:
            sys.argv = [str(_SCRIPT_PATH), *previous_argv[1:]]
        else:
            sys.argv = [str(_SCRIPT_PATH), *argv]
        # run_path returns the script's global namespace; we rely on
        # `if __name__ == "__main__"` running main() and raising SystemExit.
        runpy.run_path(str(_SCRIPT_PATH), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = previous_argv
    # If the script didn't call sys.exit (unlikely), surface 0.
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gaokao-shortlink compat entrypoint")
    parser.parse_args()
    raise SystemExit(main(sys.argv[1:]))
