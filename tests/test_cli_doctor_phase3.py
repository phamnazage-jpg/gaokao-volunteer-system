from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml  # type: ignore[import-untyped]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI = PROJECT_ROOT / "scripts" / "gaokao-cli"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


def test_cli_share_delegates_list_subcommand() -> None:
    result = _run_cli("share", "list", "--help")
    assert result.returncode == 0, result.stderr
    assert "--report" in result.stdout
    assert "--owner" in result.stdout


def test_cli_share_poster_help_reaches_parser() -> None:
    result = _run_cli("share", "poster", "--help")
    assert result.returncode == 0, result.stderr
    assert "--report-json" in result.stdout
    assert "--code" in result.stdout
    assert "--output" in result.stdout


def test_cli_payment_doctor_rejects_unexpected_args() -> None:
    result = _run_cli("payment", "doctor", "--bogus")
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "does not accept" in combined or "unrecognized" in combined.lower()


def test_cli_help_lists_unified_command_surface() -> None:
    result = _run_cli("--help")
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "rules" in combined
    assert "majors" in combined
    assert "audit" in combined
    assert "share" in combined
    assert "payment" in combined
    assert "channel" in combined
    assert "delivery" in combined
    assert "retention" in combined
    assert "backup" in combined
    assert "doctor" in combined

    share_help = _run_cli("share", "--help")
    assert share_help.returncode == 0, share_help.stderr
    assert "create" in share_help.stdout

def test_cli_share_help_lists_poster_subcommand() -> None:
    result = _run_cli("share", "--help")
    assert result.returncode == 0, result.stderr
    assert "poster" in result.stdout

    payment_help = _run_cli("payment", "doctor")
    assert payment_help.returncode in (0, 2)


def test_cli_order_delegates_list_subcommand() -> None:
    result = _run_cli("order", "list", "--help")
    assert result.returncode == 0, result.stderr
    assert "--status" in result.stdout
    assert "--limit" in result.stdout


def test_cli_doctor_returns_ok_json(tmp_path: Path) -> None:
    result = _run_cli("doctor", "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["rules"]["province_count"] >= 27
    assert payload["rules"]["national_rule_count"] >= 0
    assert payload["rules"]["stale_rule_count"] == 0
    assert payload["rules_verify"]["ok"] is True
    assert payload["majors"]["ok"] is True
    assert payload["majors_verify"]["ok"] is True


def test_cli_doctor_fails_on_empty_truth_root(tmp_path: Path) -> None:
    empty_truth = tmp_path / "truth"
    empty_truth.mkdir()
    empty_catalog = tmp_path / "catalog"
    empty_catalog.mkdir()
    (empty_catalog / "national").mkdir()
    (empty_catalog / "schools").mkdir()
    (empty_catalog / "national" / "2024.json").write_text(
        json.dumps({"year": 2024, "majors": []}),
        encoding="utf-8",
    )
    (empty_catalog / "national" / "latest.json").write_text(
        json.dumps({"year": 2024, "majors": []}),
        encoding="utf-8",
    )
    result = _run_cli(
        "doctor",
        "--truth-root",
        str(empty_truth),
        "--catalog-root",
        str(empty_catalog),
        "--json",
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["rules"].get("province_count", 0) == 0
def test_cli_doctor_fails_when_rules_are_stale(tmp_path: Path) -> None:
    import shutil

    truth_root = tmp_path / "truth"
    shutil.copytree(PROJECT_ROOT / "rules" / "_truth", truth_root)

    stale_rule = truth_root / "province" / "hunan.yaml"
    stale_doc = yaml.safe_load(stale_rule.read_text(encoding="utf-8"))
    stale_doc["last_verified_at"] = "2020-01-01"
    stale_rule.write_text(
        yaml.safe_dump(stale_doc, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    result = _run_cli(
        "rules",
        "verify",
        "--truth-root",
        str(truth_root),
        "--json",
        "--max-rule-age-days",
        "365",
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["stale_rule_count"] > 0


def test_cli_channel_check_delegates_to_monitor() -> None:
    result = _run_cli("channel", "--help")
    assert result.returncode == 0, result.stderr
    assert "check" in result.stdout
    assert "manual-template" in result.stdout


def test_cli_delivery_dispatch_help_reaches_parser() -> None:
    result = _run_cli("delivery", "dispatch", "--help")
    assert result.returncode == 0, result.stderr
    assert "--channel" in result.stdout
    assert "--limit" in result.stdout


def test_cli_delivery_unknown_subcommand_errors_cleanly() -> None:
    result = _run_cli("delivery", "bogus-subcommand")
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "watchdog" in combined.lower() or "dispatch" in combined.lower()
    assert "Traceback" not in combined


def test_cli_retention_help_reaches_parser() -> None:
    result = _run_cli("retention", "--help")
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined
    assert "cleanup" in combined.lower() or "retention" in combined.lower()


def test_cli_backup_snapshot_help_reaches_shell() -> None:
    result = _run_cli("backup", "snapshot", "--help")
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined


def test_cli_backup_unknown_subcommand_errors_cleanly() -> None:
    result = _run_cli("backup", "definitely-bogus")
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "snapshot" in combined.lower() or "verify" in combined.lower()
    assert "Traceback" not in combined
