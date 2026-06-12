"""T2.4 端到端集成验证脚本

模拟 audit_report.html 模板实际渲染时使用的 crowd_risks 字典，
确认 build_crowd_risks 输出的字段与模板期望完全一致。

跑法：python3 scripts/verify_t2_4_e2e.py
"""

import sys
from pathlib import Path

# 让 data/ 与 skills/ 模块可导入
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402

from data.crowd_db.risk_report import (  # noqa: E402
    build_crowd_risks,
    format_risk_summary,
    group_by_risk,
)


def main() -> int:
    # 1) 真实场景：湖南 575 分，扎堆样本方案
    plan = [
        {"school": "长沙理工大学", "major": "计算机科学与技术"},  # frequency=4 → high
        {
            "school": "湖南科技大学",
            "major": "机械设计制造及其自动化",
        },  # frequency=2 → medium
        {"school": "某某野鸡大学", "major": "考古学"},  # 0 → 跳过
    ]
    crowd_risks = build_crowd_risks(plan, user_score=575, province="湖南")
    print(f"✅ build_crowd_risks 输出 {len(crowd_risks)} 条风险")
    print(f"   汇总：{format_risk_summary(crowd_risks)}")
    grouped = group_by_risk(crowd_risks)
    print(
        f"   分组: high={len(grouped['high'])} medium={len(grouped['medium'])} low={len(grouped['low'])}"
    )

    # 2) 模板字段完整性逐项断言
    required_fields = {
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
    for r in crowd_risks:
        missing = required_fields - r.keys()
        assert not missing, f"missing fields: {missing} in {r}"
    print(f"✅ 模板必需字段全部存在（{len(required_fields)} 个）")

    # 3) alternatives 字段名重映射检查
    for r in crowd_risks:
        for alt in r["alternatives"]:
            assert "school" in alt, f"alternative missing 'school' key: {alt}"
            assert "score" in alt, f"alternative missing 'score' key: {alt}"
            assert isinstance(alt["score"], int), f"score not int: {alt}"
    print("✅ alternatives 字段名重映射正确（name→school，score 为 int）")

    # 4) 三色 emoji 检查
    emojis = {r["risk_emoji"] for r in crowd_risks}
    assert emojis.issubset({"🔴", "🟡", "🟢"}), f"unexpected emojis: {emojis}"
    print(f"✅ 三色 emoji 标识正常：{emojis}")

    # 5) 真实模板渲染（不修改模板，使用当前 crowd_risks 数据）
    template_path = ROOT / "skills" / "gaokao-audit" / "templates" / "audit_report.html"
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("audit_report.html")

    mock_payload = {
        "source": "端到端测试",
        "candidate_info": "湖南 575分 物化生",
        "audit_time": "2026-06-12 17:00",
        "report_id": "AUDIT-T24-E2E",
        "overall_score": 70,
        "fatal_count": 0,
        "warning_count": len(crowd_risks),
        "info_count": 0,
        "policy_errors": [],
        "crowd_risks": crowd_risks,
        "data_issues": [],
        "suggestions": [],
    }
    rendered = template.render(**mock_payload)

    # 渲染输出必须包含每个风险院校名 + emoji
    for r in crowd_risks:
        assert r["school"] in rendered, f"school not in rendered: {r['school']}"
        assert r["risk_emoji"] in rendered, f"emoji not in rendered: {r['risk_emoji']}"
    print(f"✅ 真实模板渲染成功，{len(rendered)} chars")

    # 6) 三色 emoji 在渲染输出中可见性
    assert "🔴" in rendered or "🟡" in rendered or "🟢" in rendered, (
        "no risk emoji found in rendered output"
    )
    print("✅ 风险 emoji 已渲染到 HTML 中")

    print("\n🎯 T2.4 端到端集成验证全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
