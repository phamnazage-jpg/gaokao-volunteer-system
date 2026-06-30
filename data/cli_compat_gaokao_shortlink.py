"""Thin import shim for the legacy `gaokao-shortlink` script.

The share command surface now includes two lanes:
- `gaokao-cli share poster ...` routes to the dedicated poster CLI
- all other `gaokao-cli share ...` subcommands route to this shortlink CLI
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

from data.share.short_link import DEFAULT_DB_PATH

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "gaokao-shortlink"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaokao-cli share",
        description="T7 分享命令面：短链接与海报生成",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite 数据库路径 (默认: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="用于构造 /s/{code} 完整 URL (默认 http://localhost:8000)",
    )
    parser.add_argument(
        "--human", action="store_true", help="人类可读输出 (默认 JSON)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    create = sub.add_parser("create", help="创建一条短链接")
    create.add_argument("--report-id")
    create.add_argument("--owner")
    create.add_argument("--permission")
    create.add_argument("--password")
    create.add_argument("--ttl-seconds")
    create.add_argument("--ttl-days")
    create.add_argument("--length")
    create.add_argument("--note")

    resolve = sub.add_parser("resolve", help="解析短链接")
    resolve.add_argument("code")
    resolve.add_argument("--password")
    resolve.add_argument("--dry-run", action="store_true")

    revoke = sub.add_parser("revoke", help="撤销短链接")
    revoke.add_argument("code")
    revoke.add_argument("--owner")

    revoke_report = sub.add_parser("revoke-report", help="按 report 批量撤销短链接")
    revoke_report.add_argument("--report-id")
    revoke_report.add_argument("--owner")

    listing = sub.add_parser("list", help="列出某报告/某用户的链接")
    listing.add_argument("--report")
    listing.add_argument("--owner")
    listing.add_argument("--limit")

    stats = sub.add_parser("stats", help="查看短链接统计")
    stats.add_argument("code")
    stats.add_argument("--days")

    stats_report = sub.add_parser("stats-report", help="查看报告级分享统计")
    stats_report.add_argument("--report-id")
    stats_report.add_argument("--owner")
    stats_report.add_argument("--days")

    return parser


def main(argv: list[str] | None = None) -> int:
    tokens = list(sys.argv[1:]) if argv is None else list(argv)
    if tokens == ["--help"] or tokens == ["-h"]:
        _build_parser().print_help()
        return 0
    if not _SCRIPT_PATH.is_file():
        raise FileNotFoundError(f"gaokao-shortlink not found at {_SCRIPT_PATH}")
    previous_argv = sys.argv
    try:
        if argv is None:
            sys.argv = [str(_SCRIPT_PATH), *previous_argv[1:]]
        else:
            sys.argv = [str(_SCRIPT_PATH), *argv]
        runpy.run_path(str(_SCRIPT_PATH), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = previous_argv
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gaokao-shortlink compat entrypoint")
    parser.parse_args()
    raise SystemExit(main(sys.argv[1:]))
