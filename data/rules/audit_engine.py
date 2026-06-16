from __future__ import annotations

from dataclasses import dataclass

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
    def __init__(self, loader: RuleLoader) -> None:
        self._loader = loader

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


def _scalar(rule: LoadedRule | None, key: str):
    if rule is None:
        return None
    return rule.value.get(key)
