from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LoadedRule:
    rule_id: str
    title: str
    severity: str
    value: dict[str, Any]
    source_evidence_id: str
    effective_date: str
    status: str
    scope: str
    province: str | None = None
    year: int = 2026
    version: str = "2026.1"


@dataclass(frozen=True)
class RulesStatus:
    province_count: int
    national_rule_count: int
    active_provinces: list[str]
