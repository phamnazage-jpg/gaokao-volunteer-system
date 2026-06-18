from __future__ import annotations

import json
from pathlib import Path


from data.majors_catalog.loader import MajorsCatalogLoader


def _write_catalog(root: Path) -> None:
    national = root / "national"
    national.mkdir(parents=True, exist_ok=True)
    changes = root / "changes"
    changes.mkdir(parents=True, exist_ok=True)
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
    (changes / "2024-2026.md").write_text(
        "# changes\n\n- sample\n", encoding="utf-8"
    )


def test_majors_catalog_loader_reads_latest_and_supports_lookup(tmp_path: Path) -> None:
    _write_catalog(tmp_path)

    loader = MajorsCatalogLoader.from_catalog_root(tmp_path)
    by_name = loader.lookup("计算机科学与技术")
    by_code = loader.lookup("020101")
    status = loader.build_status()

    assert by_name is not None
    assert by_name.code == "080901"
    assert by_name.discipline == "工学"
    assert by_code is not None
    assert by_code.name == "经济学"
    assert status.year == 2024
    assert status.version == "2024.1"
    assert status.major_count == 3
    assert status.change_count == 1
    assert status.risky_major_count == 1
    assert status.coverage_mode == "mvp_subset"
    assert "changes/2024-2026.md" in status.version_strategy
    assert by_name.risk_tags == []


def test_majors_catalog_loader_lists_changes_for_non_active_majors(
    tmp_path: Path,
) -> None:
    _write_catalog(tmp_path)

    loader = MajorsCatalogLoader.from_catalog_root(tmp_path)
    changed = loader.list_changes()

    assert len(changed) == 1
    assert changed[0].code == "120201K"
    assert changed[0].status == "renamed"
    assert changed[0].risk_tags == ["non_active", "removed_in_last_2y"]
