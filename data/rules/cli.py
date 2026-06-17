from __future__ import annotations

import argparse
import json
from pathlib import Path

from data.majors_catalog.cli import (
    DEFAULT_CATALOG_ROOT,
    build_changes_payload,
    build_lookup_payload,
    build_school_status_payload,
    build_school_verify_payload,
    build_status_payload as build_majors_status_payload,
    build_verify_payload as build_majors_verify_payload,
)
from data.majors_catalog.loader import MajorsCatalogLoader
from data.rules.audit_engine import AuditEngine
from data.rules.loader import RuleLoader


DEFAULT_RULES_TRUTH_ROOT = Path(__file__).resolve().parents[2] / "rules" / "_truth"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gaokao-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rules_parser = subparsers.add_parser("rules", help="rules truth source commands")
    rules_sub = rules_parser.add_subparsers(dest="rules_command", required=True)

    status_parser = rules_sub.add_parser("status", help="show rules truth status")
    status_parser.add_argument("--truth-root", default=str(DEFAULT_RULES_TRUTH_ROOT))
    status_parser.add_argument("--json", action="store_true")

    verify_parser = rules_sub.add_parser("verify", help="verify rules truth tree")
    verify_parser.add_argument("--truth-root", default=str(DEFAULT_RULES_TRUTH_ROOT))
    verify_parser.add_argument("--json", action="store_true")

    majors_parser = subparsers.add_parser(
        "majors", help="national majors catalog commands"
    )
    majors_sub = majors_parser.add_subparsers(dest="majors_command", required=True)

    majors_status = majors_sub.add_parser("status", help="show majors catalog status")
    majors_status.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    majors_status.add_argument("--json", action="store_true")

    majors_lookup = majors_sub.add_parser(
        "lookup", help="lookup a major by code or name"
    )
    majors_lookup.add_argument("name_or_code")
    majors_lookup.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    majors_lookup.add_argument("--json", action="store_true")

    majors_verify = majors_sub.add_parser(
        "verify", help="verify majors catalog structure"
    )
    majors_verify.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    majors_verify.add_argument("--json", action="store_true")

    majors_changes = majors_sub.add_parser(
        "changes", help="list non-active major records"
    )
    majors_changes.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    majors_changes.add_argument("--json", action="store_true")

    school_status = majors_sub.add_parser(
        "school-status", help="show school catalog summary for a year"
    )
    school_status.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    school_status.add_argument("--year", required=True, type=int)
    school_status.add_argument("--json", action="store_true")

    school_verify = majors_sub.add_parser(
        "school-verify", help="verify school catalog structure for a year"
    )
    school_verify.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    school_verify.add_argument("--year", required=True, type=int)
    school_verify.add_argument("--json", action="store_true")

    audit_parser = subparsers.add_parser("audit", help="structured audit commands")
    audit_sub = audit_parser.add_subparsers(dest="audit_command", required=True)
    audit_run = audit_sub.add_parser("run", help="run structured audit on JSON plan")
    audit_run.add_argument("--province", required=True)
    audit_run.add_argument("--plan", required=True)
    audit_run.add_argument("--truth-root", default=str(DEFAULT_RULES_TRUTH_ROOT))
    audit_run.add_argument("--catalog-root", default=str(DEFAULT_CATALOG_ROOT))
    audit_run.add_argument("--json", action="store_true")

    return parser


def _emit(payload: dict[str, object], json_output: bool) -> int:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(payload)
    return 0 if bool(payload.get("ok", payload.get("overall_pass", True))) else 1


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
        truth_root = Path(args.truth_root)
        if not (truth_root / "national.yaml").is_file():
            missing_required_files.append("national.yaml")
        if not (truth_root / "province").is_dir():
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

    if args.command == "majors" and args.majors_command == "status":
        payload = build_majors_status_payload(Path(args.catalog_root))
        return _emit(payload, args.json)

    if args.command == "majors" and args.majors_command == "lookup":
        payload = build_lookup_payload(Path(args.catalog_root), args.name_or_code)
        return _emit(payload, args.json)

    if args.command == "majors" and args.majors_command == "verify":
        payload = build_majors_verify_payload(Path(args.catalog_root))
        return _emit(payload, args.json)

    if args.command == "majors" and args.majors_command == "changes":
        payload = build_changes_payload(Path(args.catalog_root))
        return _emit(payload, args.json)

    if args.command == "majors" and args.majors_command == "school-status":
        payload = build_school_status_payload(Path(args.catalog_root), args.year)
        return _emit(payload, args.json)

    if args.command == "majors" and args.majors_command == "school-verify":
        payload = build_school_verify_payload(Path(args.catalog_root), args.year)
        return _emit(payload, args.json)

    if args.command == "audit" and args.audit_command == "run":
        truth_loader = RuleLoader.from_truth_root(Path(args.truth_root))
        majors_loader = MajorsCatalogLoader.from_catalog_root(Path(args.catalog_root))
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        payload = AuditEngine(truth_loader, majors_loader=majors_loader).audit_plan(
            args.province, plan
        )
        return _emit(payload, args.json)

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
