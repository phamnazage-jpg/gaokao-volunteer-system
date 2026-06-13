"""渠道兜底巡检 CLI tests (T8.4)."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from data.channel_sync.audit import apply_audit_schema
from data.channel_sync.monitor import main as cli_main, summarize_channel_health
from data.channel_sync.poller import apply_poller_schema
from data.orders.schema import apply_schema

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "gaokao-channel-fallback"


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    db = tmp_path / "orders.db"
    conn = apply_schema(db)
    apply_audit_schema(conn)
    apply_poller_schema(conn)
    conn.close()
    return db


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )


def test_summarize_channel_health_warns_when_no_runtime_signal(
    tmp_db_path: Path,
) -> None:
    payload = summarize_channel_health(str(tmp_db_path), source="xianyu")
    assert payload["status"] == "warn"
    assert any("链路可能未启动" in item for item in payload["findings"])
    assert any(
        "gaokao-order-manager" in item for item in payload["recommended_actions"]
    )


def test_summarize_channel_health_critical_when_poller_has_errors(
    tmp_db_path: Path,
) -> None:
    with _connect(tmp_db_path) as conn:
        conn.execute(
            """
            INSERT INTO poller_state(source, last_cursor, last_run_at, last_error, run_count, error_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "xianyu",
                "2026-06-12T10:00:00+00:00",
                "2026-06-12T10:05:00+00:00",
                "TimeoutError: upstream timeout",
                8,
                3,
            ),
        )
        conn.execute(
            """
            INSERT INTO poller_run(
                source, started_at, finished_at, fetched, inserted, updated, unchanged,
                rejected, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "xianyu",
                "2026-06-12T10:00:00+00:00",
                "2026-06-12T10:05:00+00:00",
                0,
                0,
                0,
                0,
                0,
                "TimeoutError: upstream timeout",
            ),
        )
        conn.commit()

    payload = summarize_channel_health(
        str(tmp_db_path),
        source="xianyu",
        now=None,
        poller_error_warn_threshold=3,
    )
    assert payload["status"] == "critical"
    assert any("连续错误计数=3" in item for item in payload["findings"])


def test_cli_manual_template_and_check_exit_codes(
    tmp_db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manual_code = cli_main(
        [
            "--db",
            str(tmp_db_path),
            "manual-template",
            "--source",
            "wechat",
            "--human",
        ]
    )
    out = capsys.readouterr().out
    assert manual_code == 0
    assert "gaokao-order-manager" in out
    assert "status: warn" in out
    assert "recommended_actions:" in out

    result = _run_cli("--db", str(tmp_db_path), "check", "--source", "xianyu")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "warn"
    assert payload["source"] == "xianyu"
