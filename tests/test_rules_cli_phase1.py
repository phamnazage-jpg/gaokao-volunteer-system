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
