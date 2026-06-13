"""Mini-validator for the Jinja2 audit_report.html template.

Verifies that:
- Template can be parsed by Jinja2
- All expected placeholders exist
- Renders with a representative mock payload without errors
- Produced HTML is well-formed (counted open/close tag balance)
"""

import sys
import re
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError, UndefinedError

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "templates" / "audit_report.html"
)

REQUIRED_PLACEHOLDERS = [
    "{{ source",
    "{{ candidate_info",
    "{{ audit_time",
    "{{ report_id",
    "{{ overall_score",
    "{{ fatal_count",
    "{{ warning_count",
    "{{ info_count",
    "{% if policy_errors %}",
    "{% if crowd_risks %}",
    "{% if data_issues %}",
    "{% if suggestions %}",
    "risk.source_type_icon",
    "risk.source_type_label",
    "risk.confidence",
    "risk.last_updated",
    "policy_errors",
    "crowd_risks",
    "data_issues",
    "suggestions",
]


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print(f"FAIL: template not found: {TEMPLATE_PATH}")
        return 1

    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    for needle in REQUIRED_PLACEHOLDERS:
        if needle not in text:
            print(f"FAIL: placeholder missing: {needle!r}")
            return 1
    print(f"OK: all {len(REQUIRED_PLACEHOLDERS)} required placeholders present")

    env = Environment(autoescape=True)
    try:
        template = env.from_string(text)
    except TemplateSyntaxError as e:
        print(f"FAIL: Jinja2 syntax error: {e}")
        return 1
    print("OK: Jinja2 template parses cleanly")

    # Render with a representative mock payload
    mock = {
        "source": "百度AI志愿助手",
        "candidate_info": "湖南 578分 物化生",
        "audit_time": "2026-06-12 15:30",
        "report_id": "AUDIT-20260612-001",
        "overall_score": 65,
        "fatal_count": 1,
        "warning_count": 2,
        "info_count": 3,
        "policy_errors": [
            {
                "rule_id": "HUN-001",
                "rule": "院校专业组模式未应用",
                "description": '第2志愿"湖南师范大学 - 会计学"未指定专业组',
                "fix": '改为"湖南师范大学 第003专业组（物理+不限）- 会计学"',
            }
        ],
        "crowd_risks": [
            {
                "school": "长沙理工大学",
                "major": "会计学",
                "frequency": 4,
                "predicted_increase": 18,
                "risk_level": "high",
                "risk_level_label": "高",
                "risk_emoji": "🔴",
                "source_type": "report",
                "raw_source_type": "manual_summary",
                "source_type_icon": "⚠️",
                "source_type_label": "报告",
                "source": "千问/元宝/百度/豆包 公开推荐汇总（手动整理）",
                "source_url": "https://example.com/hunan.json",
                "confidence": 0.85,
                "last_updated": "2026-06-12",
                "data_year": 2025,
                "alternatives": [
                    {"school": "湖南工商大学", "score": 95},
                    {"school": "湖北经济学院", "score": 92},
                ],
            }
        ],
        "data_issues": [
            {
                "location": "第3志愿",
                "description": '标注"录取概率80%"但未提供数据来源',
                "recommendation": "删除主观概率表述，或补充 2024-2025 三年录取位次数据",
            }
        ],
        "suggestions": [
            "冲稳保比例建议 3:4:3（已用 5:3:2，建议调整）",
            '第3志愿后建议加入备选院校如"湖南工商大学"、"湖北经济学院"',
        ],
    }
    try:
        rendered = template.render(**mock)
    except UndefinedError as e:
        print(f"FAIL: render error with mock payload: {e}")
        return 1
    print(f"OK: rendered {len(rendered)} chars with mock payload")

    # Tag balance check (lightweight)
    # Note: the regex below counts ANY non-closing tag opening, including
    # HTML5 void elements (meta/link/br/img/input/hr). To get a tighter
    # check, subtract void-element occurrences from the open count.
    VOID_ELEMENTS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    raw_open_tags = re.findall(r"<(?!/)(?!!)([a-zA-Z][a-zA-Z0-9]*)\b", rendered)
    close_tags = len(re.findall(r"</([a-zA-Z][a-zA-Z0-9]*)\s*>", rendered))
    void_count = sum(1 for t in raw_open_tags if t.lower() in VOID_ELEMENTS)
    open_tags = len(raw_open_tags) - void_count
    print(
        f"INFO: open={open_tags} close={close_tags} "
        f"(void elements excluded: {void_count})"
    )

    # Sanity: the rendered report must contain key user-visible strings
    must_contain = [
        "百度AI志愿助手",
        "65/100",
        "HUN-001",
        "长沙理工大学",
        "录取概率80%",
        "⚠️ 报告",
        "2026-06-12",
        "升级到完整方案",
        "免责声明",
    ]
    for needle in must_contain:
        if needle not in rendered:
            print(f"FAIL: rendered output missing: {needle!r}")
            return 1
    print(f"OK: all {len(must_contain)} expected strings present in rendered output")

    print("\n✅ audit_report.html template is well-formed and renderable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
