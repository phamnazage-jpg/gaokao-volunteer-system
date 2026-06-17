from __future__ import annotations

import json
from pathlib import Path

from data.majors_catalog.loader import MajorsCatalogLoader


def _write_catalog(root: Path) -> None:
    national = root / "national"
    national.mkdir(parents=True, exist_ok=True)
    national_payload = {
        "year": 2024,
        "version": "2024.1",
        "coverage_mode": "mvp_subset",
        "source": "教育部普通高等学校本科专业目录（人工摘录校对）",
        "source_url": "https://www.moe.gov.cn/",
        "last_verified_at": "2026-06-17",
        "majors": [
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
            }
        ],
    }
    (national / "2024.json").write_text(
        json.dumps(national_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (national / "latest.json").write_text(
        json.dumps(national_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    schools = root / "schools" / "2026"
    schools.mkdir(parents=True, exist_ok=True)
    school_payload = {
        "school_code": "10001",
        "school_name": "北京大学",
        "admission_year": 2026,
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
                "admission_year": 2026,
                "province": "北京",
                "duration_years": 4,
                "tuition_cny": 5000,
                "study_mode": "全日制",
                "is_new": False,
                "is_discontinued": False,
                "source": "学校招生章程人工摘录",
                "last_verified_at": "2026-06-17",
            }
        ],
    }
    (schools / "10001.json").write_text(
        json.dumps(school_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_majors_catalog_loader_reads_school_offerings_status(tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    loader = MajorsCatalogLoader.from_catalog_root(tmp_path)

    status = loader.build_school_status(2026)
    offerings = loader.list_school_offerings(2026, "10001")

    assert status.year == 2026
    assert status.school_count == 1
    assert status.offering_count == 1
    assert status.school_codes == ["10001"]
    assert len(offerings) == 1
    assert offerings[0].school_name == "北京大学"
    assert offerings[0].major_code == "080901"


def test_majors_catalog_loader_school_verify_detects_missing_year_dir(
    tmp_path: Path,
) -> None:
    _write_catalog(tmp_path)
    loader = MajorsCatalogLoader.from_catalog_root(tmp_path)

    payload = loader.verify_school_catalog(2027)

    assert payload["ok"] is False
    assert payload["missing_required_files"] == ["schools/2027/"]
