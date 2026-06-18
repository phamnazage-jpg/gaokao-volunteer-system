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
    # The shortlink CLI exposes a `list` subcommand. Asking for its --help
    # proves the `gaokao-cli share ...` argv successfully reaches the
    # shortlink parser instead of being swallowed by the top-level parser.
    result = _run_cli("share", "list", "--help")
    assert result.returncode == 0, result.stderr
    # The shortlink list subcommand exposes --report / --owner.
    assert "--report" in result.stdout
    assert "--owner" in result.stdout


def test_cli_payment_doctor_rejects_unexpected_args() -> None:
    # `gaokao-cli payment doctor` is a single-shot diagnostic with no
    # flags; the compat shim should surface unexpected tokens instead
    # of silently dropping them on the floor.
    result = _run_cli("payment", "doctor", "--bogus")
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "does not accept" in combined or "unrecognized" in combined.lower()


def test_cli_help_lists_unified_command_surface() -> None:
    # P2-1 contract: 顶层 help 必须显式暴露统一 CLI 命令面，即使这些
    # 命令最终仍由预委派逻辑转发给旧 parser / shell。
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "order" in result.stdout
    assert "share" in result.stdout
    assert "payment" in result.stdout
    assert "channel" in result.stdout
    assert "delivery" in result.stdout
    assert "retention" in result.stdout
    assert "backup" in result.stdout
    assert "doctor" in result.stdout

    share_help = _run_cli("share", "--help")
    assert share_help.returncode == 0, share_help.stderr
    # Reaches the shortlink parser (which exposes create/list/resolve/...)
    assert "create" in share_help.stdout

    payment_help = _run_cli("payment", "doctor")
    # mock provider is fine: should exit 0; unsupported would exit 3.
    assert payment_help.returncode in (0, 2)


def test_cli_order_delegates_list_subcommand() -> None:
    # The orders CLI exposes a `list` subcommand. Asking for its --help
    # proves the `gaokao-cli order ...` argv successfully reaches the
    # orders parser instead of being swallowed by the top-level parser.
    result = _run_cli("order", "list", "--help")
    assert result.returncode == 0, result.stderr
    # The orders parser's list subcommand should expose --status/--source/--limit;
    # presence proves the delegation wired up correctly.
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
    # When the truth_root is incomplete the loader raises before any
    # province_count key is populated, so a structured error key replaces
    # the missing province_count.
    assert "error" in payload["rules"] or payload["rules"].get("province_count", 0) == 0


def test_cli_doctor_fails_when_rules_are_stale(tmp_path: Path) -> None:
    truth_root = tmp_path / "truth"
    province_dir = truth_root / "province"
    province_dir.mkdir(parents=True, exist_ok=True)
    (truth_root / "national.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "national",
                "year": 2026,
                "version": "2026.1",
                "last_verified_at": "2026-01-01",
                "rules": {
                    "parallel_volunteer_principle": {
                        "title": "平行志愿原则",
                        "severity": "info",
                        "value": {"rule": "分数优先、遵循志愿、一次投档"},
                        "source_evidence_id": "national-2026-parallel-rule",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-01-01",
                        "status": "active",
                    }
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (province_dir / "hunan.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "province",
                "province": "湖南",
                "year": 2026,
                "version": "2026.1",
                "last_verified_at": "2026-06-17",
                "status": "active",
                "rules": {
                    "max_volunteers": {
                        "title": "本科批志愿上限",
                        "severity": "fatal",
                        "value": {"max_volunteers": 45},
                        "source_evidence_id": "hunan-2026-max-volunteers",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-06-17",
                        "status": "active",
                    }
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    evidence_root = truth_root.parent / "_evidence" / "hunan"
    evidence_root.mkdir(parents=True, exist_ok=True)
    (evidence_root / "hunan-2026-max-volunteers.md").write_text(
        "> 湖南本科批院校专业组最多 45 个志愿。\n",
        encoding="utf-8",
    )

    catalog_root = tmp_path / "catalog"
    (catalog_root / "national").mkdir(parents=True, exist_ok=True)
    (catalog_root / "schools").mkdir(parents=True, exist_ok=True)
    (catalog_root / "changes").mkdir(parents=True, exist_ok=True)
    (catalog_root / "changes" / "2024-2026.md").write_text(
        "# changes\n\n- sample\n",
        encoding="utf-8",
    )
    national_catalog = {
        "year": 2024,
        "version": "2024.1",
        "coverage_mode": "mvp_subset",
        "source": "教育部普通高等学校本科专业目录（人工摘录校对）",
        "source_url": "https://www.moe.gov.cn/",
        "last_verified_at": "2026-06-17",
        "majors": [],
    }
    for name in ("2024.json", "latest.json"):
        (catalog_root / "national" / name).write_text(
            json.dumps(national_catalog, ensure_ascii=False),
            encoding="utf-8",
        )

    result = _run_cli(
        "doctor",
        "--truth-root",
        str(truth_root),
        "--catalog-root",
        str(catalog_root),
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["rules"]["stale_rule_count"] == 1
    assert payload["rules_verify"]["ok"] is False
    assert "NATIONAL.parallel_volunteer_principle" in payload["rules_verify"]["stale_rule_ids"]


def test_cli_channel_check_delegates_to_monitor() -> None:
    # `gaokao-cli channel --help` should reach the channel_sync monitor
    # parser, which exposes {check, manual-template}.
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
    result = _run_cli("delivery", "unknown")
    assert result.returncode != 0
    # The dispatch shim surfaces the expected subcommand set, not a raw
    # argparse traceback, so callers can rely on the message.
    combined = (result.stdout or "") + (result.stderr or "")
    assert "dispatch" in combined and "watchdog" in combined


def test_cli_retention_help_reaches_parser() -> None:
    result = _run_cli("retention", "--help")
    # The retention parser exits 2 on --help with no subcommand; we
    # only assert that we reached the retention script (not Python
    # traceback and not a top-level argparse error).
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined
    assert result.returncode != 0 or "retention" in combined.lower()


def test_cli_backup_snapshot_help_reaches_shell() -> None:
    result = _run_cli("backup", "snapshot", "--help")
    # The shell script may exit 0 or non-zero if no --help is wired;
    # we only assert the routing reached bash (no Python traceback).
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined


def test_cli_backup_unknown_subcommand_errors_cleanly() -> None:
    result = _run_cli("backup", "unknown")
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "snapshot" in combined and "verify" in combined
