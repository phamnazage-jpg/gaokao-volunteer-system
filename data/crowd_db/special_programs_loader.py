"""特殊批次定向培养计划查询模块。

加载 data/crowd_db/special_programs.json，提供按省份/分数匹配特殊批次推荐的能力。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_SPECIAL_PROGRAMS_PATH = Path(__file__).resolve().parent / "special_programs.json"
_SPECIAL_RULES_PATH = (
    Path(__file__).resolve().parents[1] / "rules" / "special_programs_rules.json"
)


class SpecialProgramsLoader:
    """加载特殊批次定向培养计划数据。"""

    def __init__(
        self, data_path: Path | None = None, rules_path: Path | None = None
    ) -> None:
        self._data_path = data_path or _SPECIAL_PROGRAMS_PATH
        self._rules_path = rules_path or _SPECIAL_RULES_PATH
        self._data: dict[str, Any] | None = None
        self._rules: dict[str, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            self._data = json.loads(self._data_path.read_text(encoding="utf-8"))
        return self._data  # type: ignore[return-value]

    @property
    def rules(self) -> dict[str, Any]:
        if self._rules is None:
            self._rules = json.loads(self._rules_path.read_text(encoding="utf-8"))
        return self._rules  # type: ignore[return-value]

    def list_programs(self) -> list[dict[str, Any]]:
        """列出全部 5 类特殊批次项目。"""
        return self.data.get("programs", [])

    def get_program(self, program_type: str) -> dict[str, Any] | None:
        """按 program_type 获取单个项目详情。"""
        for p in self.list_programs():
            if p.get("program_type") == program_type:
                return p
        return None

    def list_programs_for_province(self, province: str) -> list[dict[str, Any]]:
        """列出某省份适用的特殊批次项目。"""
        province = province.strip()
        result = []
        for p in self.list_programs():
            applicable = p.get("applicable_provinces") or []
            if "全国" in applicable or province in applicable:
                result.append(p)
        return result

    def find_matching_schools(
        self,
        province: str,
        score: int,
        *,
        program_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """根据省份和分数，匹配可捡漏的特殊批次院校。

        Args:
            province: 考试省份。
            score: 考生分数。
            program_type: 可选，限定项目类型。

        Returns:
            匹配的院校列表，每个含 school/major/score_min/program_type 等。
        """
        province = province.strip()
        program_schools = self.data.get("program_schools", {})
        results: list[dict[str, Any]] = []

        for ptype, schools in program_schools.items():
            if program_type and ptype != program_type:
                continue
            for s in schools:
                s_province = s.get("province", "")
                # "全国" 适用所有省份
                if s_province != "全国" and s_province != province:
                    continue
                score_min = s.get("score_min", 999)
                # 考生分数 >= 院校最低分 * 0.9（允许一定弹性）
                if score >= int(score_min) * 0.85:
                    results.append({
                        **s,
                        "program_type": ptype,
                        "gap": score - int(score_min),
                    })

        # 按分数差升序（越接近的越优先推荐）
        results.sort(key=lambda x: abs(x.get("gap", 0)))
        return results

    def get_applicable_rules(self, program_type: str) -> list[dict[str, Any]]:
        """获取某项目类型适用的规则列表。"""
        all_rules = self.rules.get("rules", [])
        return [r for r in all_rules if program_type in (r.get("applies_to") or [])]

    def build_recommendation_for_review(
        self,
        province: str,
        score: int,
    ) -> list[dict[str, Any]]:
        """为审核/复核场景生成特殊批次推荐摘要。

        返回格式适合直接注入 LLM prompt 或 ReviewResultContract。
        """
        programs = self.list_programs_for_province(province)
        if not programs:
            return []

        recommendations = []
        for p in programs:
            ptype = p.get("program_type", "")
            matching_schools = self.find_matching_schools(
                province, score, program_type=ptype
            )
            if not matching_schools:
                continue

            # 取最近的院校
            best_school = matching_schools[0]
            features = p.get("key_features", {})

            recommendations.append({
                "program_type": ptype,
                "program_name": p.get("program_name", ""),
                "description": p.get("description", ""),
                "batch": p.get("batch", ""),
                "best_match_school": best_school.get("school", ""),
                "best_match_major": best_school.get("major", ""),
                "best_match_score_min": best_school.get("score_min", 0),
                "tuition": features.get("tuition", ""),
                "employment": features.get("employment", ""),
                "service_years": features.get("service_years"),
                "exam_required": features.get("exam_required", False),
                "physical_check": features.get("physical_check", ""),
                "match_score": max(0, 100 - abs(best_school.get("gap", 0))),
                "warnings": p.get("warnings", []),
            })

        # 按 match_score 降序
        recommendations.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return recommendations


    def list_programs_by_batch(self, batch: str) -> list[dict[str, Any]]:
        """按批次筛选项目（如"本科提前批"/"专科提前批"/"本科批"）。"""
        return [p for p in self.list_programs() if batch in p.get("batch", "")]

    def list_programs_by_category(self, category: str) -> list[dict[str, Any]]:
        """按类别筛选规则关联的项目（如"提前批-军校"/"专项计划"）。"""
        rule_types = set()
        for r in self.rules.get("rules", []):
            if r.get("category") == category:
                pt = r.get("program_type")
                if pt:
                    rule_types.add(pt)
        return [p for p in self.list_programs() if p.get("program_type") in rule_types]

    def list_categories(self) -> list[str]:
        """列出所有规则类别。"""
        return sorted(set(
            r.get("category", "")
            for r in self.rules.get("rules", [])
            if r.get("category")
        ))

    def get_rules_by_category(self, category: str) -> list[dict[str, Any]]:
        """按类别获取规则。"""
        return [
            r for r in self.rules.get("rules", [])
            if r.get("category") == category
        ]
