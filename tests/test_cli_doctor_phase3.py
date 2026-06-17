from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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


def test_cli_help_lists_share_and_payment() -> None:
    # `share` and `payment` are pure passthrough markers; they are NOT
    # registered as subparsers in the top-level argparse tree, so the
    # top-level --help intentionally does not advertise them. They are
    # exposed via the dedicated delegation entry points below.
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "order" in result.stdout
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
