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
    changes = root / "changes"
    changes.mkdir(parents=True, exist_ok=True)
    national_payload = {
        "year": 2024,
        "version": "2024.1",
        "coverage_mode": "mvp_subset",
        "source": "教育部普通高等学校本科专业目录（人工摘录校对）",
        "source_url": "https://www.moe.gov.cn/",
        "last_verified_at": "2026-06-17",
        "majors": [],
    }
    (national / "2024.json").write_text(
        json.dumps(national_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (national / "latest.json").write_text(
        json.dumps(national_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (changes / "2024-2026.md").write_text(
        "# changes\n\n- sample\n", encoding="utf-8"
    )

    schools = root / "schools" / "2026"
    schools.mkdir(parents=True, exist_ok=True)
    school_payload = {
        "school_code": "10001",
        "school_name": "北京大学",
        "admission_year": 2026,
        "version": "2026.1",
        "province": "北京",
        "source": "学校招生章程人工摘录",
        "source_url": "https://www.pku.edu.cn/",
        "last_verified_at": "2026-06-17",
        "offerings": [
            {
                "school_code": "10001",
                "school_name": "北京大学",
                "major_code": "080901",
                "major_name": "计算机科学与技术",
                "national_major_code": "080901",
                "admission_year": 2026,
                "province": "北京",
                "duration_years": 4,
                "tuition_cny": 5000,
                "study_mode": "全日制",
                "is_new": False,
                "is_discontinued": False,
                "mapping_status": "exact",
                "source": "学校招生章程人工摘录",
                "last_verified_at": "2026-06-17",
            }
        ],
    }
    (schools / "10001.json").write_text(
        json.dumps(school_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_majors_school_status_cli_reports_school_summary(tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    result = _run_cli(
        "majors",
        "school-status",
        "--catalog-root",
        str(tmp_path),
        "--year",
        "2026",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["year"] == 2026
    assert payload["version"] == "2026.1"
    assert payload["school_count"] == 1
    assert payload["offering_count"] == 1
    assert payload["mapped_offering_count"] == 1
    assert payload["unmapped_offering_count"] == 0
    assert payload["school_codes"] == ["10001"]
    assert "changes/2024-2026.md" in payload["version_strategy"]


def test_majors_school_verify_cli_checks_year_directory(tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    result = _run_cli(
        "majors",
        "school-verify",
        "--catalog-root",
        str(tmp_path),
        "--year",
        "2026",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["missing_required_files"] == []
    assert payload["school_count"] == 1
    assert payload["version"] == "2026.1"
    assert payload["mapped_offering_count"] == 1
    assert payload["unmapped_offering_count"] == 0
    assert "changes/2024-2026.md" in payload["version_strategy"]
