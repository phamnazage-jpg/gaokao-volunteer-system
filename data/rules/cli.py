from __future__ import annotations

import argparse
import json
from pathlib import Path

from data.rules.loader import RuleLoader


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gaokao-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rules_parser = subparsers.add_parser("rules", help="rules truth source commands")
    rules_sub = rules_parser.add_subparsers(dest="rules_command", required=True)

    status_parser = rules_sub.add_parser("status", help="show rules truth status")
    status_parser.add_argument("--truth-root", required=True)
    status_parser.add_argument("--json", action="store_true")

    verify_parser = rules_sub.add_parser("verify", help="verify rules truth tree")
    verify_parser.add_argument("--truth-root", required=True)
    verify_parser.add_argument("--json", action="store_true")

    return parser


def _emit(payload: dict, json_output: bool) -> int:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload.get("ok", True) else 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "rules" and args.rules_command == "status":
        loader = RuleLoader.from_truth_root(Path(args.truth_root))
        status = loader.build_status()
        return _emit(
            {
                "ok": True,
                "province_count": status.province_count,
                "national_rule_count": status.national_rule_count,
                "active_provinces": status.active_provinces,
            },
            args.json,
        )

    if args.command == "rules" and args.rules_command == "verify":
        loader = RuleLoader.from_truth_root(Path(args.truth_root))
        status = loader.build_status()
        missing_required_files: list[str] = []
        if not (Path(args.truth_root) / "national.yaml").is_file():
            missing_required_files.append("national.yaml")
        if not (Path(args.truth_root) / "province").is_dir():
            missing_required_files.append("province/")
        return _emit(
            {
                "ok": not missing_required_files,
                "province_count": status.province_count,
                "national_rule_count": status.national_rule_count,
                "missing_required_files": missing_required_files,
            },
            args.json,
        )

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
