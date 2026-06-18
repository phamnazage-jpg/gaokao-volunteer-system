from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "gaokao-cli"


def _load_migrate_module():
    loader = SourceFileLoader(
        "migrate_province_rules_to_truth",
        str(PROJECT_ROOT / "scripts" / "migrate_province_rules_to_truth.py"),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_rules_status_cli_reports_truth_root_summary(tmp_path: Path) -> None:
    migrate = _load_migrate_module()

    migrate.migrate_legacy_rules_to_truth(output_root=tmp_path)

    result = _run_cli("rules", "status", "--truth-root", str(tmp_path), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["province_count"] == 27
    assert payload["national_rule_count"] == 1
    assert payload["national_version"] == "2026.1"
    assert payload["active_rule_count"] >= 27
    assert payload["stale_rule_max_age_days"] == 90
    assert payload["stale_rule_count"] == 0
    assert payload["stale_rule_ids"] == []
    assert "湖南" in payload["active_provinces"]


def test_rules_verify_cli_confirms_truth_tree_is_valid(tmp_path: Path) -> None:
    migrate = _load_migrate_module()

    migrate.migrate_legacy_rules_to_truth(output_root=tmp_path)

    result = _run_cli("rules", "verify", "--truth-root", str(tmp_path), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["province_count"] == 27
    assert payload["missing_required_files"] == []
    assert payload["stale_rule_count"] == 0
    assert payload["missing_evidence_rule_count"] >= 0


def test_rules_list_cli_returns_rule_metadata_for_province() -> None:
    result = _run_cli("rules", "list", "--province", "湖南", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["rule_count"] >= 1
    first = payload["rules"][0]
    assert first["rule_id"].startswith("HUNAN.")
    assert first["version"] == "2026.1"
    assert "last_verified_at" in first


def test_rules_explain_cli_returns_bound_evidence_excerpt() -> None:
    result = _run_cli("rules", "explain", "HUNAN.max_volunteers", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["rule"]["rule_id"] == "HUNAN.max_volunteers"
    assert payload["rule"]["source_evidence_id"] == "hunan-2026-max_volunteers"
    assert payload["rule"]["evidence_exists"] is True
    assert payload["evidence_excerpt"]


def test_rules_scaffold_evidence_cli_generates_draft_templates(tmp_path: Path) -> None:
    migrate = _load_migrate_module()
    migrate.migrate_legacy_rules_to_truth(output_root=tmp_path)

    result = _run_cli(
        "rules",
        "scaffold-evidence",
        "--truth-root",
        str(tmp_path),
        "--province",
        "湖南",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["province"] == "湖南"
    assert payload["created_rule_count"] >= 11
    index_path = tmp_path.parent / "_evidence" / "hunan" / "INDEX.md"
    assert index_path.is_file()
    text = index_path.read_text(encoding="utf-8")
    assert "待补摘录" in text
    template_path = tmp_path.parent / "_evidence" / "hunan" / "hunan-2026-mode.md"
    assert template_path.is_file()
    assert "TODO_OFFICIAL_EXCERPT" in template_path.read_text(encoding="utf-8")
