#!/usr/bin/env python3
"""Validate LLM prompt special-program coverage against data/rules files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "data" / "llm" / "prompts.py"
DATA = ROOT / "data" / "crowd_db" / "special_programs.json"
RULES = ROOT / "data" / "rules" / "special_programs_rules.json"

REQUIRED_COVERAGE: list[tuple[str, tuple[str, ...]]] = [
    ("公费农科生", ("公费农科生", "public_agriculture")),
    ("定向基层医疗", ("定向基层医疗", "农村订单定向免费医学生", "免费医学定向", "rural_medical")),
    ("公费消防", ("公费消防", "消防", "fire_rescue")),
    ("司法", ("司法", "judicial_directed")),
    ("公费师范", ("公费师范", "public_teacher")),
    ("定向培养军士", ("定向培养军士", "军士", "military_nco")),
    ("铁路", ("铁路", "railway_directed")),
    ("订单班", ("订单班", "enterprise_order")),
    ("预科", ("预科", "ethnic_preparatory")),
    ("专项计划", ("专项计划", "special_plan")),
    ("定向西藏", ("定向西藏", "tibet_directed")),
    ("军校", ("军校", "police_military")),
    ("强基", ("强基", "strong_foundation")),
]


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def main() -> int:
    prompt_text = PROMPTS.read_text(encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    combined = json.dumps(data, ensure_ascii=False) + chr(10) + json.dumps(rules, ensure_ascii=False)
    missing_prompt = [prompt_kw for prompt_kw, _ in REQUIRED_COVERAGE if prompt_kw not in prompt_text]
    missing_data = [prompt_kw for prompt_kw, synonyms in REQUIRED_COVERAGE if not _has_any(combined, synonyms)]
    program_count = len(data.get("programs", []))
    school_groups = len(data.get("program_schools", {}))
    rule_count = len(rules.get("rules", []))
    if missing_prompt or missing_data or program_count < 12 or school_groups < 12 or rule_count < 12:
        print({
            "missing_prompt": missing_prompt,
            "missing_data": missing_data,
            "program_count": program_count,
            "school_groups": school_groups,
            "rule_count": rule_count,
        })
        return 1
    print(f"llm domain data coverage ok: programs={program_count} school_groups={school_groups} rules={rule_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
