from __future__ import annotations

from dataclasses import dataclass, field
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
    last_verified_at: str = "2026-06-17"
    evidence_path: str | None = None
    evidence_exists: bool = False


@dataclass(frozen=True)
class RulesStatus:
    province_count: int
    national_rule_count: int
    active_provinces: list[str]
    national_version: str = "2026.1"
    province_versions: dict[str, str] = field(default_factory=dict)
    active_rule_count: int = 0
    stale_rule_max_age_days: int = 90
    stale_rule_count: int = 0
    stale_rule_ids: list[str] = field(default_factory=list)
    evidenced_rule_count: int = 0
    missing_evidence_rule_count: int = 0
