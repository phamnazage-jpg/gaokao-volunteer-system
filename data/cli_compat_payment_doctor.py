"""Thin import shim for the legacy `payment_provider_doctor.py` script."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "payment_provider_doctor.py"
)


def main(argv: list[str] | None = None) -> int:
    if not _SCRIPT_PATH.is_file():
        raise FileNotFoundError(f"payment_provider_doctor not found at {_SCRIPT_PATH}")
    # `gaokao-cli payment doctor` arrives here as argv=["doctor"]; the
    # legacy script takes no args, so strip the leading "doctor" marker
    # (and any other unrecognised tokens) and reject them.
    if argv and argv[0] == "doctor":
        argv = argv[1:]
    if argv:
        raise SystemExit(f"payment doctor does not accept positional args; got: {argv}")
    previous_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT_PATH)]
        runpy.run_path(str(_SCRIPT_PATH), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = previous_argv
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="payment provider doctor compat entrypoint"
    )
    parser.parse_args()
    raise SystemExit(main(sys.argv[1:]))
