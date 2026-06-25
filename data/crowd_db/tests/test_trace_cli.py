"""gaokao-data-trace CLI tests (T3.4)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from data.crowd_db.cli import main as cli_main

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "gaokao-data-trace"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_trace_cli_json_output_contains_matches() -> None:
    result = _run_cli("长沙理工大学")
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["query"] == "长沙理工大学"
    assert payload["match_count"] >= 1
    assert any(match["school"] == "长沙理工大学" for match in payload["matches"])

    hunan_match = next(
        match for match in payload["matches"] if match["province"] == "湖南"
    )
    assert hunan_match["data_year"] in (2025, 2026)  # 过渡期：湖南已切到 2026
    assert hunan_match["source_url"].startswith("https://")
    assert 0 <= hunan_match["confidence"] <= 1
    assert hunan_match["source_type"] == "report"
    assert hunan_match["raw_source_type"] == "manual_summary"


def test_trace_cli_human_output_contains_required_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_main(["--human", "长沙理工大学"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "query: 长沙理工大学" in captured.out
    assert "湖南 / 2026年数据 / 长沙理工大学 / 会计学" in captured.out
    assert "source_url: https://" in captured.out
    assert "confidence: 0.85" in captured.out
    assert "quality_level: high (A级（高置信）)" in captured.out


def test_trace_cli_missing_school_returns_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_main(["不存在的测试院校XYZ"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "不存在的测试院校XYZ" in captured.err
