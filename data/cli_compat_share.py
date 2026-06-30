"""Compat entrypoint for `gaokao-cli share ...`.

Rules:
- `share poster ...` → route to the new poster CLI
- all other `share ...` subcommands → keep delegating to legacy shortlink CLI
"""

from __future__ import annotations

from pathlib import Path
import runpy
import sys

_SHORTLINK_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "gaokao-shortlink"
_POSTER_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "gaokao-poster"


def _run_script(script_path: Path, argv: list[str] | None = None) -> int:
    if not script_path.is_file():
        raise FileNotFoundError(f"script not found at {script_path}")
    previous_argv = sys.argv
    try:
        if argv is None:
            sys.argv = [str(script_path), *previous_argv[1:]]
        else:
            sys.argv = [str(script_path), *argv]
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = previous_argv
    return 0


def main(argv: list[str] | None = None) -> int:
    tokens = list(sys.argv[1:]) if argv is None else list(argv)
    if not tokens or tokens in (["--help"], ["-h"]):
        from data.cli_compat_gaokao_shortlink import _build_parser as _shortlink_help_parser

        parser = _shortlink_help_parser()
        parser.prog = "gaokao-cli share"
        parser.description = "T7 分享命令面：短链接与海报生成"
        sub = parser._subparsers._group_actions[0]  # type: ignore[attr-defined]
        sub.add_parser("poster", help="生成分享海报")
        parser.print_help()
        return 0
    if tokens[0] == "poster":
        return _run_script(_POSTER_SCRIPT, tokens[1:])
    return _run_script(_SHORTLINK_SCRIPT, tokens)
