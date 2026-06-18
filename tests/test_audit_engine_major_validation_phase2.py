from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from data.majors_catalog.loader import MajorsCatalogLoader
from data.rules.audit_engine import AuditEngine
from data.rules.loader import RuleLoader


def _write_truth_and_catalog(
    root: Path,
    *,
    max_volunteers_status: str = "active",
    max_volunteers_severity: str = "fatal",
    max_volunteers_title: str = "志愿上限",
) -> tuple[Path, Path, Path]:
    truth_root = root / "truth"
    province_dir = truth_root / "province"
    province_dir.mkdir(parents=True, exist_ok=True)
    (truth_root / "national.yaml").write_text(
        "scope: national\nyear: 2026\nversion: '2026.1'\nrules: {}\n",
        encoding="utf-8",
    )
    (province_dir / "hunan.yaml").write_text(
        (
            "scope: province\nprovince: 湖南\nyear: 2026\nversion: '2026.1'\n"
            "status: active\nrules:\n  max_volunteers:\n"
            f"    title: {max_volunteers_title}\n"
            f"    severity: {max_volunteers_severity}\n"
            "    value:\n      max_volunteers: 45\n"
            "    source_evidence_id: hunan-2026-max-volunteers\n"
            "    effective_date: '2026-01-01'\n"
            f"    status: {max_volunteers_status}\n"
        ),
        encoding="utf-8",
    )

    catalog_root = root / "catalog"
    national = catalog_root / "national"
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
                "status": "deprecated",
                "year_added": 1998,
                "year_removed": 2024,
                "notes": "示例停用",
            },
        ],
    }
    for name in ("2024.json", "latest.json"):
        (national / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    plan_path = root / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "province": "湖南",
                "items": [
                    {
                        "school_name": "北京大学",
                        "major_names": ["计算机科学与技术", "不存在专业", "工商管理"],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return truth_root, catalog_root, plan_path


def test_audit_engine_major_validation_marks_missing_and_non_active_majors(
    tmp_path: Path,
) -> None:
    truth_root, catalog_root, plan_path = _write_truth_and_catalog(tmp_path)
    loader = RuleLoader.from_truth_root(truth_root)
    catalog = MajorsCatalogLoader.from_catalog_root(catalog_root)
    engine = AuditEngine(loader, majors_loader=catalog)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    result = engine.audit_plan("湖南", plan)
    issues = cast(list[dict[str, Any]], result["issues"])

    rule_ids = {issue["rule_id"] for issue in issues}
    assert "MAJORS.not_found" in rule_ids
    assert "MAJORS.non_active" in rule_ids
    assert result["overall_pass"] is False


def test_audit_engine_major_validation_passes_when_all_majors_are_active(
    tmp_path: Path,
) -> None:
    truth_root, catalog_root, _ = _write_truth_and_catalog(tmp_path)
    loader = RuleLoader.from_truth_root(truth_root)
    catalog = MajorsCatalogLoader.from_catalog_root(catalog_root)
    engine = AuditEngine(loader, majors_loader=catalog)

    result = engine.audit_plan(
        "湖南",
        {
            "province": "湖南",
            "items": [{"school_name": "北京大学", "major_names": ["计算机科学与技术"]}],
        },
    )

    assert result["issues"] == []
    assert result["overall_pass"] is True


def test_audit_engine_fails_when_volunteer_count_exceeds_province_limit(
    tmp_path: Path,
) -> None:
    truth_root, catalog_root, _ = _write_truth_and_catalog(tmp_path)
    loader = RuleLoader.from_truth_root(truth_root)
    catalog = MajorsCatalogLoader.from_catalog_root(catalog_root)
    engine = AuditEngine(loader, majors_loader=catalog)

    result = engine.audit_plan(
        "湖南",
        {
            "province": "湖南",
            "items": [
                {"school_name": f"学校{i}", "major_names": []}
                for i in range(46)
            ],
        },
    )

    issues = cast(list[dict[str, Any]], result["issues"])
    issue = next(issue for issue in issues if issue["rule_id"] == "RULES.max_volunteers")

    assert result["overall_pass"] is False
    assert issue["severity"] == "fatal"
    assert issue["title"] == "志愿上限"
    assert issue["message"] == "当前方案包含 46 个志愿单位，已超过湖南规则上限 45"
    assert issue["suggestion"] == "请减少到不超过 45 个志愿单位后重新审计"


def test_audit_engine_skips_non_active_max_volunteers_rule(tmp_path: Path) -> None:
    truth_root, catalog_root, _ = _write_truth_and_catalog(
        tmp_path,
        max_volunteers_status="draft",
    )
    loader = RuleLoader.from_truth_root(truth_root)
    catalog = MajorsCatalogLoader.from_catalog_root(catalog_root)
    engine = AuditEngine(loader, majors_loader=catalog)

    result = engine.audit_plan(
        "湖南",
        {
            "province": "湖南",
            "items": [
                {"school_name": f"学校{i}", "major_names": []}
                for i in range(46)
            ],
        },
    )

    issues = cast(list[dict[str, Any]], result["issues"])
    assert all(issue["rule_id"] != "RULES.max_volunteers" for issue in issues)
    assert result["overall_pass"] is True


def test_audit_engine_allows_volunteer_count_equal_to_province_limit(
    tmp_path: Path,
) -> None:
    truth_root, catalog_root, _ = _write_truth_and_catalog(tmp_path)
    loader = RuleLoader.from_truth_root(truth_root)
    catalog = MajorsCatalogLoader.from_catalog_root(catalog_root)
    engine = AuditEngine(loader, majors_loader=catalog)

    result = engine.audit_plan(
        "湖南",
        {
            "province": "湖南",
            "items": [
                {"school_name": f"学校{i}", "major_names": []}
                for i in range(45)
            ],
        },
    )

    issues = cast(list[dict[str, Any]], result["issues"])
    assert all(issue["rule_id"] != "RULES.max_volunteers" for issue in issues)
    assert result["overall_pass"] is True
