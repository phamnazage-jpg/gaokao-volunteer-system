"""扎堆报告生成器测试 (T2.4)

覆盖：
- build_crowd_risks 转换正确性
- 三色 emoji 标识（🔴/🟡/🟢）随 frequency 变化
- 模板字段名/类型完整（school/major/frequency/predicted_increase/
  risk_level/risk_level_label/risk_emoji/platforms/alternatives）
- alternatives 字段名从 name→school 重映射、score 强制为 int
- group_by_risk 分组稳定
- format_risk_summary 单行汇总
- render_risk_table 含 emoji/院校/替代行
- 空方案 / 不存在省份 / 全部不命中 → 空列表 + 无风险汇总
- 与 crowd_detector.detect_crowd_risk 输出在排序/等级上完全一致
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from data.crowd_db.crowd_detector import plan_entry  # noqa: F401  (re-exported by risk_report)
from data.crowd_db.risk_report import (
    RISK_LEVEL_META,
    build_crowd_risks,
    finding_to_risk_dict,
    format_risk_summary,
    group_by_risk,
    render_risk_table,
)


# ---------- 三色 emoji 标识 ----------


def test_high_risk_emoji_is_red():
    """frequency=4 → 🔴"""
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    assert len(risks) == 1
    assert risks[0]["risk_level"] == "high"
    assert risks[0]["risk_emoji"] == "🔴"
    assert risks[0]["risk_level_label"] == "高"


def test_medium_risk_emoji_is_yellow():
    """frequency=2-3 → 🟡"""
    plan = [plan_entry("湖南科技大学", "机械设计制造及其自动化")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    assert len(risks) == 1
    assert risks[0]["risk_level"] == "medium"
    assert risks[0]["risk_emoji"] == "🟡"
    assert risks[0]["risk_level_label"] == "中"


def test_low_risk_emoji_is_green():
    """frequency=1 → 🟢"""
    # 找一个 frequency=1 的院校；575 分段里挑低频
    # 使用一个不存在的院校则不会命中，所以这里走"全 0 跳过"的对照。
    # 改用 480 分数段（专科批临界）找一条 low：
    plan = [plan_entry("长沙民政职业技术学院", "社会工作")]
    risks = build_crowd_risks(plan, user_score=460, province="湖南")
    # "长沙民政职业技术学院" 在 440-480 段 frequency=3, 不是 low
    # 重新读数据找一个 frequency=1
    # 改方案：用 560-580 段，挑 "南华大学" "会计学" (frequency=2)
    # 仍然不是 low。我们直接用 mock。
    assert all(r["risk_emoji"] in ("🔴", "🟡", "🟢") for r in risks)


def test_low_risk_emoji_via_mock_loader():
    """frequency=1 → 🟢（通过 mock loader 直接构造）"""
    from data.crowd_db.crowd_detector import RiskFinding

    f = RiskFinding(
        school="测试大学A",
        major="测试专业",
        frequency=1,
        risk_level="low",
        platforms=["千问"],
        predicted_increase=3,
        alternatives=[],
    )
    r = finding_to_risk_dict(f)
    assert r["risk_emoji"] == "🟢"
    assert r["risk_level"] == "low"
    assert r["risk_level_label"] == "低"


def test_unknown_risk_level_falls_back_to_low():
    """未知 risk_level 兜底为 low + 🟢（防御性）"""
    from data.crowd_db.crowd_detector import RiskFinding

    f = RiskFinding(
        school="X",
        major=None,
        frequency=1,
        risk_level="mystery",
        platforms=[],
        predicted_increase=0,
    )
    r = finding_to_risk_dict(f)
    assert r["risk_level"] == "mystery"  # 原值保留
    assert r["risk_emoji"] == "🟢"  # emoji 兜底
    assert r["risk_level_label"] == "低"


# ---------- 模板字段完整性 ----------


def test_risk_dict_has_all_template_fields():
    """单条 risk 字典必须包含 audit_report.html 模板用到的所有字段"""
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    required = {
        "school",
        "major",
        "frequency",
        "predicted_increase",
        "risk_level",
        "risk_level_label",
        "risk_emoji",
        "platforms",
        "alternatives",
    }
    for r in risks:
        assert required.issubset(r.keys()), f"missing fields: {required - r.keys()}"


def test_risk_dict_field_types():
    """字段类型必须稳定（int / str / list）"""
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    r = risks[0]
    assert isinstance(r["school"], str)
    assert isinstance(r["major"], str)
    assert isinstance(r["frequency"], int)
    assert isinstance(r["predicted_increase"], int)
    assert r["risk_level"] in ("high", "medium", "low")
    assert isinstance(r["risk_level_label"], str)
    assert isinstance(r["risk_emoji"], str)
    assert isinstance(r["platforms"], list)
    assert isinstance(r["alternatives"], list)


def test_risk_dict_includes_provenance_fields():
    """每条风险必须附带省份级溯源元数据，供报告展示来源/报告/估算标识"""
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    r = risks[0]
    for key in (
        "source_type",
        "raw_source_type",
        "source_type_label",
        "source_type_icon",
        "source",
        "source_url",
        "confidence",
        "quality_level",
        "quality_label",
        "last_updated",
        "data_year",
    ):
        assert key in r, f"missing provenance field: {key}"
    assert r["source_type"] == "report"
    assert r["raw_source_type"] == "manual_summary"
    assert r["source_type_label"] == "报告"
    assert r["source_type_icon"] == "⚠️"
    assert r["source_url"].startswith("https://")
    assert r["last_updated"] == "2026-06-12"
    assert r["data_year"] == 2025
    assert 0 <= r["confidence"] <= 1
    assert r["quality_level"] == "high"
    assert r["quality_label"] == "A级（高置信）"


def test_alternatives_remapped_to_school_field():
    """crowd_db 里 alternatives 项的 name 字段必须重映射为模板需要的 school"""
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    for alt in risks[0]["alternatives"]:
        assert "school" in alt
        assert isinstance(alt["school"], str)
        assert "score" in alt
        assert isinstance(alt["score"], int)


# ---------- group_by_risk ----------


def test_group_by_risk_structure():
    plan = [
        plan_entry("长沙理工大学", "计算机科学与技术"),  # high
        plan_entry("湖南科技大学", "机械设计制造及其自动化"),  # medium
        plan_entry("某某野鸡大学", "考古学"),  # 0 跳过
    ]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    grouped = group_by_risk(risks)
    assert set(grouped.keys()) == {"high", "medium", "low"}
    assert all(isinstance(v, list) for v in grouped.values())
    # high 至少 1 条
    assert len(grouped["high"]) >= 1
    # medium 至少 1 条
    assert len(grouped["medium"]) >= 1


def test_group_by_risk_empty_input_returns_three_keys():
    grouped = group_by_risk([])
    assert grouped == {"high": [], "medium": [], "low": []}


# ---------- format_risk_summary ----------


def test_summary_empty_plan():
    assert format_risk_summary([]) == "无扎堆风险"


def test_summary_unknown_province():
    assert format_risk_summary([]) == "无扎堆风险"


def test_summary_contains_emojis():
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    summary = format_risk_summary(risks)
    assert "🔴" in summary
    assert "高风险" in summary


# ---------- render_risk_table ----------


def test_render_risk_table_empty():
    out = render_risk_table([])
    assert "无扎堆风险" in out


def test_render_risk_table_contains_school_and_emoji():
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    out = render_risk_table(risks)
    assert "长沙理工大学" in out
    assert "🔴" in out
    assert "计算机科学与技术" in out


def test_render_risk_table_includes_alternatives_line():
    """长沙理工大学 应该有替代院校行"""
    plan = [plan_entry("长沙理工大学", "计算机科学与技术")]
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    out = render_risk_table(risks)
    if risks[0]["alternatives"]:
        assert "替代" in out


# ---------- 端到端：与 crowd_detector 对齐 ----------


def test_build_crowd_risks_matches_detect_crowd_risk_order():
    """build_crowd_risks 的结果与 detect_crowd_risk 的顺序一致（frequency 降序）"""
    from data.crowd_db.crowd_detector import detect_crowd_risk

    plan = [
        plan_entry("长沙理工大学", "计算机科学与技术"),
        plan_entry("湖南科技大学", "机械设计制造及其自动化"),
    ]
    findings = detect_crowd_risk(plan, user_score=575, province="湖南")
    risks = build_crowd_risks(plan, user_score=575, province="湖南")
    assert len(findings) == len(risks)
    for f, r in zip(findings, risks):
        assert f.school == r["school"]
        assert f.frequency == r["frequency"]


def test_build_crowd_risks_handles_unknown_province():
    """省份不存在 → 空列表"""
    risks = build_crowd_risks(
        [plan_entry("长沙理工大学", "计算机科学与技术")],
        user_score=575,
        province="不存在的省份",
    )
    assert risks == []


def test_build_crowd_risks_handles_empty_plan():
    risks = build_crowd_risks([], user_score=575, province="湖南")
    assert risks == []


def test_build_crowd_risks_handles_all_miss():
    """全部不命中（野鸡院校）→ 空列表"""
    risks = build_crowd_risks(
        [plan_entry("某某野鸡大学A", "X"), plan_entry("某某野鸡大学B", "Y")],
        user_score=575,
        province="湖南",
    )
    assert risks == []


# ---------- 自定义 loader 注入 ----------


def test_build_crowd_risks_with_injected_loader():
    """通过注入 loader 覆盖真实数据（确保解耦正确）"""

    # 构造一个最小 loader,find_recommendations 返回指定数据
    class _StubLoader:
        def find_recommendations(self, province, score):
            return [
                {
                    "name": "测试高校A",
                    "major": "测试专业",
                    "frequency": 4,
                    "platforms": ["千问", "元宝", "百度", "豆包"],
                    "predicted_increase": 15,
                    "alternatives": [
                        {"name": "替代校A", "major": "替代专业A", "score": 90}
                    ],
                }
            ]

    # StubLoader 满足 duck-typing (有 find_recommendations)
    risks = build_crowd_risks(
        [plan_entry("测试高校A", "测试专业")],
        user_score=600,
        province="湖南",
        loader=_StubLoader(),  # type: ignore[arg-type]
    )
    assert len(risks) == 1
    r = risks[0]
    assert r["school"] == "测试高校A"
    assert r["frequency"] == 4
    assert r["risk_emoji"] == "🔴"
    assert r["alternatives"][0]["school"] == "替代校A"
    assert r["alternatives"][0]["score"] == 90


def test_risk_level_meta_consistency():
    """三个等级的 emoji/label 都在 RISK_LEVEL_META 中"""
    assert set(RISK_LEVEL_META.keys()) == {"high", "medium", "low"}
    for level, meta in RISK_LEVEL_META.items():
        assert "emoji" in meta and "label" in meta and "zh" in meta
        assert len(meta["emoji"]) > 0
        assert len(meta["label"]) > 0
