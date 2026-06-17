from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "gaokao-cli"


def _write_catalog(root: Path) -> None:
    national = root / "national"
    national.mkdir(parents=True, exist_ok=True)
    payload = {
        "year": 2024,
        "version": "2024.1",
        "coverage_mode": "mvp_subset",
        "source": "教育部普通高等学校本科专业目录（人工摘录校对）",
        "source_url": "https://www.moe.gov.cn/",
        "last_verified_at": "2026-06-17",
        "majors": [
            {
                "code": "020101",
                "name": "经济学",
                "discipline": "经济学",
                "category": "经济学类",
                "degree": "经济学学士",
                "is_directional": False,
                "status": "active",
                "year_added": 1998,
                "year_removed": None,
                "notes": None,
            },
            {
                "code": "080901",
                "name": "计算机科学与技术",
                "discipline": "工学",
                "category": "计算机类",
                "degree": "工学学士",
                "is_directional": False,
                "status": "active",
                "year_added": 1998,
                "year_removed": None,
                "notes": None,
            },
            {
                "code": "120201K",
                "name": "工商管理",
                "discipline": "管理学",
                "category": "工商管理类",
                "degree": "管理学学士",
                "is_directional": True,
                "status": "renamed",
                "year_added": 1998,
                "year_removed": 2024,
                "notes": "示例改名专业",
            },
        ],
    }
    (national / "2024.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (national / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_majors_status_cli_reports_catalog_summary(tmp_path: Path) -> None:
    _write_catalog(tmp_path)

    result = _run_cli("majors", "status", "--catalog-root", str(tmp_path), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["year"] == 2024
    assert payload["major_count"] == 3
    assert payload["coverage_mode"] == "mvp_subset"


def test_majors_lookup_cli_supports_name_and_code(tmp_path: Path) -> None:
    _write_catalog(tmp_path)

    result = _run_cli(
        "majors", "lookup", "经济学", "--catalog-root", str(tmp_path), "--json"
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["major"]["code"] == "020101"

    result = _run_cli(
        "majors", "lookup", "080901", "--catalog-root", str(tmp_path), "--json"
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["major"]["name"] == "计算机科学与技术"


def test_majors_verify_cli_checks_required_national_files(tmp_path: Path) -> None:
    _write_catalog(tmp_path)

    result = _run_cli("majors", "verify", "--catalog-root", str(tmp_path), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["missing_required_files"] == []
    assert payload["major_count"] == 3


def test_majors_lookup_cli_returns_business_error_when_missing(tmp_path: Path) -> None:
    _write_catalog(tmp_path)

    result = _run_cli(
        "majors", "lookup", "不存在的专业", "--catalog-root", str(tmp_path), "--json"
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["code"] == "E_MAJORS_NOT_FOUND"


def test_majors_changes_cli_lists_non_active_majors(tmp_path: Path) -> None:
    _write_catalog(tmp_path)

    result = _run_cli("majors", "changes", "--catalog-root", str(tmp_path), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["change_count"] == 1
    assert payload["changes"][0]["code"] == "120201K"
    assert payload["changes"][0]["status"] == "renamed"
