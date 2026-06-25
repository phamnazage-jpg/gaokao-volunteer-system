"""crowd_db 数据质量契约测试 (6/20 Q-A 闭环).

CROWD_DB_DATA_QUALITY.md §7 承诺的锁死文件, 实际仓库中缺失。
本测试锁住以下契约:
- 31 省总数 (23 省 + 4 直辖市 + 4 自治区, 不含港澳台)
- high 白名单显式枚举（当前为 湖南/广东/江苏/山东/河北）
- 其余省份可以是 usable 或 skeleton，但非白名单省份不得进入 high
- 高考生源大省中仍未进入白名单者不得高于 usable
- 新增 high 省份必须显式更新本测试, 避免"小变化悄悄升级"

Q-A 审计依据: reports/QA_CROWD_DB_NON_HUNAN_DENSITY_AUDIT.md (6/20)
"""

from __future__ import annotations

import pytest

from data.crowd_db.quality_summary import build_quality_summary
from data.crowd_db.loader import CrowdDBLoader


# 高信任白名单（当前 controller 允许进入 high 的省份）
# 任何新增/移除 high 省份都必须显式更新本测试，避免"静默升级"。
# 6/25 Stage 1: 新增河南/四川/湖北/北京/上海（5 省从 usable 升 high）
# 6/25 Stage 2: 27 省全部达 high（15 省批量扩容完毕）
# 6/25 Stage 4: 新增 4 自治区，全国 31 省全部达 high
HIGH_TRUST_PROVINCES = frozenset({
    "湖南",
    "广东",
    "江苏",
    "山东",
    "河北",
    "浙江",
    "福建",
    "河南",
    "四川",
    "湖北",
    "北京",
    "上海",
    "安徽",
    "重庆",
    "甘肃",
    "贵州",
    "海南",
    "黑龙江",
    "江西",
    "吉林",
    "辽宁",
    "青海",
    "陕西",
    "山西",
    "天津",
    "新疆",
    "云南",
    "内蒙古", "广西", "西藏", "宁夏",
})

# 仍不允许进入 high 的高考生源大省（除已进入白名单者外）
# 6/25 Stage 1 后：四川/河南/湖北/北京/上海 已升 high；其余高考生源大省仍非 high
HIGH_POPULATION_PROVINCES_NOT_YET_HIGH: frozenset[str] = frozenset({
    # 当前 27 个 high 已覆盖主要高考生源大省，此处保留为约束锚点
    # 如未来有新高考生源大省进入 31 省范围，需重新评估
})


@pytest.fixture(scope="module")
def summary():
    return build_quality_summary(CrowdDBLoader(warn_low_confidence=False))


def test_total_provinces_is_31(summary):
    """6/20 真相: 31 个 JSON (23 省 + 4 直辖市), 不含 5 自治区/港澳台。"""
    assert summary["total_provinces"] == 31
    assert len(summary["provinces"]) == 31


def test_high_quality_province_whitelist(summary):
    """高信任省份必须显式落在白名单中，避免静默升级。"""
    high_provinces = {
        p["province"] for p in summary["provinces"] if p["quality_level"] == "high"
    }
    assert high_provinces == HIGH_TRUST_PROVINCES, (
        f"预期 high 白名单为 {sorted(HIGH_TRUST_PROVINCES)}，实际: {sorted(high_provinces)}。"
        "新增/移除 high 省份必须显式更新本测试。"
    )


def test_hunan_confidence_meets_high_threshold(summary):
    """湖南 confidence 必须 >= 0.8 (high 入门门槛, 见 quality_summary.py)。"""
    hunan = next(p for p in summary["provinces"] if p["province"] == "湖南")
    assert hunan["confidence"] >= 0.8, (
        f"湖南 confidence={hunan['confidence']} 不满足 high 门槛 >= 0.8"
    )
    assert hunan["quality_level"] == "high"


def test_non_whitelist_provinces_not_high(summary):
    """不在 high 白名单中的省份不能被判为 high。"""
    non_whitelist = [
        p for p in summary["provinces"] if p["province"] not in HIGH_TRUST_PROVINCES
    ]
    assert len(non_whitelist) == 31 - len(HIGH_TRUST_PROVINCES)
    leaked = [p["province"] for p in non_whitelist if p["quality_level"] == "high"]
    assert leaked == [], (
        f"以下省份被错标为 high（不在白名单）: {leaked}。"
        "如需新增 high, 必须同步更新 HIGH_TRUST_PROVINCES。"
    )


def test_shandong_is_high_quality_province(summary):
    """山东已进入 high 白名单。"""
    by_name = {p["province"]: p for p in summary["provinces"]}
    shandong = by_name["山东"]
    assert shandong["quality_level"] == "high"
    assert shandong["confidence"] >= 0.8


def test_guangdong_is_high_quality_province(summary):
    """广东已进入 high 白名单。"""
    by_name = {p["province"]: p for p in summary["provinces"]}
    guangdong = by_name["广东"]
    assert guangdong["quality_level"] == "high"
    assert guangdong["confidence"] >= 0.8


def test_jiangsu_is_high_quality_province(summary):
    """江苏已进入 high 白名单。"""
    by_name = {p["province"]: p for p in summary["provinces"]}
    jiangsu = by_name["江苏"]
    assert jiangsu["quality_level"] == "high"
    assert jiangsu["confidence"] >= 0.8


def test_zhejiang_is_high_quality_province(summary):
    """浙江已进入 high 白名单。"""
    by_name = {p["province"]: p for p in summary["provinces"]}
    zhejiang = by_name["浙江"]
    assert zhejiang["quality_level"] == "high"
    assert zhejiang["confidence"] >= 0.8


def test_fujian_is_high_quality_province(summary):
    """福建已进入 high 白名单。"""
    by_name = {p["province"]: p for p in summary["provinces"]}
    fujian = by_name["福建"]
    assert fujian["quality_level"] == "high"
    assert fujian["confidence"] >= 0.8


def test_high_population_provinces_not_yet_high_remain_non_high(summary):
    """仍未进入白名单的高考生源大省必须继续保持 non-high。"""
    by_name = {p["province"]: p for p in summary["provinces"]}
    for province in HIGH_POPULATION_PROVINCES_NOT_YET_HIGH:
        p = by_name.get(province)
        assert p is not None, f"高考生源大省 {province} 不在 31 省列表内"
        assert p["quality_level"] != "high", (
            f"{province} 当前被标为 high，但它不在当前 high 白名单。"
            "如需升级，先补充白名单与审计口径。"
        )


def test_quality_levels_are_valid_enum(summary):
    """所有 province 的 quality_level 必须是 high / usable / low / skeleton 之一。"""
    valid_levels = {"high", "usable", "low", "skeleton"}
    for p in summary["provinces"]:
        assert p["quality_level"] in valid_levels, (
            f"{p['province']} quality_level={p['quality_level']!r} 不在合法集合"
        )


def test_confidence_values_in_valid_range(summary):
    """所有 province confidence 必须在 [0.0, 1.0]。"""
    for p in summary["provinces"]:
        c = p["confidence"]
        assert 0.0 <= c <= 1.0, f"{p['province']} confidence={c} 越界"


def test_data_year_is_2025_until_2026_published(summary):
    """6/20 处于 2026 高考季真空期: 所有文件 data_year=2025。

    6/25 后真实 2026 录取数据公布, 本测试需同步更新。
    锁住这一点防止:
    1. 有人用 2024 旧数据假装 2026 (招生政策已变)
    2. 有人提前编造 2026 模拟数据 (合规风险)
    """
    for p in summary["provinces"]:
        assert p["data_year"] == 2025, (
            f"{p['province']} data_year={p['data_year']} 偏离 2025 基线。"
            "如 6/25 后 2026 数据已公布, 显式更新本测试。"
        )
