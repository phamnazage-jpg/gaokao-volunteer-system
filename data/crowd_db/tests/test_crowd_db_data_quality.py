"""crowd_db 数据质量契约测试 (6/20 Q-A 闭环).

CROWD_DB_DATA_QUALITY.md §7 承诺的锁死文件, 实际仓库中缺失。
本测试锁住以下契约:
- 27 省总数 (23 省 + 4 直辖市, 不含 5 自治区/港澳台)
- 湖南为 high (A级) 数据, confidence >= 0.8
- 其它 26 省质量分级不超过 skeleton (C级) 或 usable (B级)
- 高考生源大省 (广东/江苏/北京/上海/山东/河南/四川) 不在 high 集合
- 新增 high 省份必须显式更新本测试, 避免"小变化悄悄升级"

Q-A 审计依据: reports/QA_CROWD_DB_NON_HUNAN_DENSITY_AUDIT.md (6/20)
"""

from __future__ import annotations

import pytest

from data.crowd_db.quality_summary import build_quality_summary
from data.crowd_db.loader import CrowdDBLoader


# 高考生源大省 (按历年统计 top 8) — 6/20 Q-A 审计明确这些省当前都是 skeleton
# 任何升级到 usable / high 必须显式更新本测试, 避免回归到"27 省高置信"假象
HIGH_POPULATION_PROVINCES = frozenset({
    "广东",
    "江苏",
    "北京",
    "上海",
    "山东",
    "河南",
    "四川",
    "湖北",
})


@pytest.fixture(scope="module")
def summary():
    return build_quality_summary(CrowdDBLoader(warn_low_confidence=False))


def test_total_provinces_is_27(summary):
    """6/20 真相: 27 个 JSON (23 省 + 4 直辖市), 不含 5 自治区/港澳台。"""
    assert summary["total_provinces"] == 27
    assert len(summary["provinces"]) == 27


def test_hunan_is_the_only_high_quality_province(summary):
    """湖南是唯一 high 级 (A级) 数据, 其它 26 省不能跳跃升级。

    锁住这一点防止:
    1. 有人手工把 0.45 的省标成 high (合规/对外口径风险)
    2. 后续数据补充时静默升级 (CROWD_DB_DATA_QUALITY §2 明确要求分级流程)
    """
    high_provinces = [
        p["province"] for p in summary["provinces"] if p["quality_level"] == "high"
    ]
    assert high_provinces == ["湖南"], (
        f"预期仅湖南为 high, 实际: {high_provinces}。"
        "新增 high 省份必须显式更新本测试, 避免'27 省高置信'假象。"
    )


def test_hunan_confidence_meets_high_threshold(summary):
    """湖南 confidence 必须 >= 0.8 (high 入门门槛, 见 quality_summary.py)。"""
    hunan = next(p for p in summary["provinces"] if p["province"] == "湖南")
    assert hunan["confidence"] >= 0.8, (
        f"湖南 confidence={hunan['confidence']} 不满足 high 门槛 >= 0.8"
    )
    assert hunan["quality_level"] == "high"


def test_non_hunan_provinces_not_high(summary):
    """非湖南 26 省 quality_level 不能是 high。

    显式枚举, 不依赖 quality_level 集合是否包含 high (避免有人偷偷改白名单)。
    """
    non_hunan = [p for p in summary["provinces"] if p["province"] != "湖南"]
    assert len(non_hunan) == 26
    leaked = [p["province"] for p in non_hunan if p["quality_level"] == "high"]
    assert leaked == [], (
        f"以下省份被错标为 high (仅湖南应为 high): {leaked}。"
        "如需新增 high, 同步更新 test_hunan_is_the_only_high_quality_province"
    )


def test_high_population_provinces_acknowledged_as_skeleton_or_lower(summary):
    """广东/江苏/北京/上海/山东/河南/四川/湖北 8 个高考生源大省当前都是 skeleton/usable,
    不在 high 集合。

    Q-A 审计发现这些省当前 confidence=0.45 / 1-3 分数段 / 2-8 条推荐, 不构成强推荐。
    后续扩到 usable/high 必须显式更新本测试, 防止"静默升级"。
    """
    by_name = {p["province"]: p for p in summary["provinces"]}
    for province in HIGH_POPULATION_PROVINCES:
        p = by_name.get(province)
        assert p is not None, f"高考生源大省 {province} 不在 27 省列表内"
        assert p["quality_level"] != "high", (
            f"{province} 当前被标为 high, 与 Q-A 6/20 审计事实不符。"
            "如数据已升级, 同步更新 test_hunan_is_the_only_high_quality_province"
            " 并补充 Q-A 复审报告。"
        )


def test_quality_levels_are_valid_enum(summary):
    """所有 province 的 quality_level 必须是 high / usable / skeleton 之一。"""
    valid_levels = {"high", "usable", "skeleton"}
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
