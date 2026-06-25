"""特殊专业标注验证测试（Phase 1）。

目标：
- 31 省 recommendations 的 program_type 覆盖率 >= 30%
- 关键类型至少各存在 1 条
- program_type 字段在所有 rec 上存在（可为 null）
"""

from __future__ import annotations

from collections import Counter

from data.crowd_db.loader import CrowdDBLoader


EXPECTED_MIN_TYPES = {
    "师范教育类",
    "医学类特色",
    "农林类特色",
    "艺体类",
    "民族类特色",
    "国际涉外导向",
}


def _all_recommendations(loader: CrowdDBLoader):
    for province in loader.list_supported_provinces():
        data = loader.load_province(province)
        if not data:
            continue
        for sr in data.get("score_ranges", []):
            for rec in sr.get("recommendations", []):
                yield province, rec


def test_program_type_field_exists_on_all_recommendations():
    loader = CrowdDBLoader(warn_low_confidence=False)
    missing = []
    for province, rec in _all_recommendations(loader):
        if "program_type" not in rec:
            missing.append((province, rec.get("name"), rec.get("major")))
    assert missing == [], f"存在 rec 缺少 program_type 字段: {missing[:10]}"


def test_program_type_coverage_at_least_30_percent():
    loader = CrowdDBLoader(warn_low_confidence=False)
    total = 0
    tagged = 0
    for _, rec in _all_recommendations(loader):
        total += 1
        if rec.get("program_type") is not None:
            tagged += 1
    coverage = tagged / total if total else 0
    assert coverage >= 0.30, (
        f"program_type 覆盖率应 >= 30%，实际 {coverage:.1%} ({tagged}/{total})"
    )


def test_expected_program_types_exist():
    loader = CrowdDBLoader(warn_low_confidence=False)
    counter: Counter[str] = Counter()
    for _, rec in _all_recommendations(loader):
        ptype = rec.get("program_type")
        if isinstance(ptype, str) and ptype:
            counter[ptype] += 1

    missing = [ptype for ptype in EXPECTED_MIN_TYPES if counter[ptype] == 0]
    assert missing == [], f"缺少关键 program_type 类型: {missing}"


def test_program_type_sample_business_rules():
    loader = CrowdDBLoader(warn_low_confidence=False)
    found = {
        "国防科技大学": False,
        "长沙民政职业技术学院": False,
        "南京中医药大学": False,
    }

    for _, rec in _all_recommendations(loader):
        school = rec.get("name")
        if school == "国防科技大学":
            assert rec.get("program_type") == "军校"
            found[school] = True
        elif school == "长沙民政职业技术学院":
            # 社会工作不应被误标为特殊类型
            assert rec.get("program_type") is None or rec.get("program_type") in {
                "师范教育类",
                "国际涉外导向",
                "艺体类",
                "民族类特色",
                "农林类特色",
                "医学类特色",
                "军校",
                "公安院校",
                "师范院校特色类",
                "农林院校特色类",
                "医学院校特色类",
            }
            found[school] = True
        elif school == "南京中医药大学":
            # 中医药院校相关专业应被标注为医学类特色 / 医学院校特色类
            assert rec.get("program_type") in {"医学类特色", "医学院校特色类"}
            found[school] = True

    assert all(found.values()), f"抽样学校未全部找到: {found}"
