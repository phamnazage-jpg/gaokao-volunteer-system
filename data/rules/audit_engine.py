from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data.majors_catalog.loader import MajorsCatalogLoader

from .loader import RuleLoader
from .models import LoadedRule


@dataclass(frozen=True)
class ProvinceRuleSnapshot:
    province: str
    mode: str | None
    max_volunteers: int | None
    retrieval_rule: str | None
    rule_count: int
    rules: list[LoadedRule]


class AuditEngine:
    def __init__(
        self,
        loader: RuleLoader,
        *,
        majors_loader: MajorsCatalogLoader | None = None,
    ) -> None:
        self._loader = loader
        self._majors_loader = majors_loader

    def get_province_snapshot(self, province: str) -> ProvinceRuleSnapshot:
        rules = self._loader.list_province_rules(province)
        as_map = {rule.rule_id.split(".", 1)[1]: rule for rule in rules}
        return ProvinceRuleSnapshot(
            province=province,
            mode=_scalar(as_map.get("mode"), "mode"),
            max_volunteers=_scalar(as_map.get("max_volunteers"), "max_volunteers"),
            retrieval_rule=_scalar(as_map.get("retrieval_rule"), "retrieval_rule"),
            rule_count=len(rules),
            rules=rules,
        )

    def audit_plan(self, province: str, plan: dict[str, Any]) -> dict[str, object]:
        issues: list[dict[str, object]] = []
        if self._majors_loader is not None:
            issues.extend(self._validate_majors(plan))
        return {
            "province": province,
            "overall_pass": not issues,
            "issues": issues,
        }

    def _validate_majors(self, plan: dict[str, Any]) -> list[dict[str, object]]:
        if self._majors_loader is None:
            return []

        issues: list[dict[str, object]] = []
        for item in plan.get("items", []):
            school_name = item.get("school_name") or "未知院校"
            for major_name in item.get("major_names", []):
                major = self._majors_loader.lookup(str(major_name))
                if major is None:
                    issues.append({
                        "rule_id": "MAJORS.not_found",
                        "severity": "warning",
                        "title": f"专业未在国家级目录中找到: {major_name}",
                        "message": f"{school_name} / {major_name} 未命中国家级目录",
                        "suggestion": "请人工核对专业名称或补充目录数据",
                    })
                    continue
                if major.status != "active":
                    issues.append({
                        "rule_id": "MAJORS.non_active",
                        "severity": "critical",
                        "title": f"专业状态不是 active: {major.name}",
                        "message": f"{school_name} / {major.name} 当前状态为 {major.status}",
                        "suggestion": "请改用仍在招生/有效的专业，并核对最新目录",
                    })
        return issues


def _scalar(rule: LoadedRule | None, key: str):
    if rule is None:
        return None
    return rule.value.get(key)
