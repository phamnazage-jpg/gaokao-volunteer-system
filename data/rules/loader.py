from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .models import LoadedRule, RulesStatus


PROVINCE_SLUGS = {
    "安徽": "anhui",
    "北京": "beijing",
    "重庆": "chongqing",
    "福建": "fujian",
    "甘肃": "gansu",
    "广东": "guangdong",
    "广西": "guangxi",
    "贵州": "guizhou",
    "海南": "hainan",
    "河北": "hebei",
    "黑龙江": "heilongjiang",
    "河南": "henan",
    "湖北": "hubei",
    "湖南": "hunan",
    "吉林": "jilin",
    "江苏": "jiangsu",
    "江西": "jiangxi",
    "辽宁": "liaoning",
    "青海": "qinghai",
    "山东": "shandong",
    "山西": "shanxi",
    "上海": "shanghai",
    "四川": "sichuan",
    "天津": "tianjin",
    "西藏": "xizang",
    "新疆": "xinjiang",
    "云南": "yunnan",
    "浙江": "zhejiang",
}

SLUG_TO_PROVINCE = {value: key for key, value in PROVINCE_SLUGS.items()}
EVIDENCE_TEMPLATE_STATUS = "draft_template"
EVIDENCE_REQUIRED_SECTIONS = (
    "## 1. 官方原文摘录",
    "## 2. 转写为机读规则",
    "## 3. 关键边界与例外",
    "## 4. 后续维护",
)
EVIDENCE_TEMPLATE_SENTINELS = (
    f"证据状态: {EVIDENCE_TEMPLATE_STATUS}",
    "TODO_OFFICIAL_EXCERPT",
)


class RuleLoader:
    def __init__(self, truth_root: Path) -> None:
        self._truth_root = Path(truth_root)
        self._evidence_root = self._truth_root.parent / "_evidence"
        self._national_doc = self._read_yaml(self._truth_root / "national.yaml")
        self._province_docs = self._load_province_docs(self._truth_root / "province")

    @classmethod
    def from_truth_root(cls, truth_root: Path | str) -> "RuleLoader":
        return cls(Path(truth_root))

    def list_national_rules(self) -> list[LoadedRule]:
        return self._convert_rules(self._national_doc, scope="national", province=None)

    def list_province_rules(self, province: str) -> list[LoadedRule]:
        doc = self._province_docs[province]
        return self._convert_rules(doc, scope="province", province=province)

    def active_provinces(self) -> list[str]:
        return sorted(
            province
            for province, doc in self._province_docs.items()
            if doc.get("status", "active") == "active"
        )

    def list_all_rules(self, *, include_inactive: bool = True) -> list[LoadedRule]:
        rules = self.list_national_rules()
        for province in self.active_provinces():
            rules.extend(self.list_province_rules(province))
        if include_inactive:
            return rules
        return [rule for rule in rules if rule.status == "active"]

    def get_rule(self, rule_id: str) -> LoadedRule:
        for rule in self.list_all_rules(include_inactive=True):
            if rule.rule_id == rule_id:
                return rule
        raise KeyError(f"rule not found: {rule_id}")

    def build_status(self, *, max_rule_age_days: int = 90) -> RulesStatus:
        active_rules = self.list_all_rules(include_inactive=False)
        stale_rules = self.find_stale_rules(active_rules, max_age_days=max_rule_age_days)
        return RulesStatus(
            province_count=len(self.active_provinces()),
            national_rule_count=len(self._national_doc.get("rules", {})),
            active_provinces=self.active_provinces(),
            national_version=str(self._national_doc.get("version", "2026.1")),
            province_versions={
                province: str(self._province_docs[province].get("version", "2026.1"))
                for province in self.active_provinces()
            },
            active_rule_count=len(active_rules),
            stale_rule_max_age_days=max_rule_age_days,
            stale_rule_count=len(stale_rules),
            stale_rule_ids=[rule.rule_id for rule in stale_rules],
            evidenced_rule_count=sum(1 for rule in active_rules if rule.evidence_exists),
            missing_evidence_rule_count=sum(
                1 for rule in active_rules if not rule.evidence_exists
            ),
        )

    def build_evidence_matrix(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        rows.append(self._build_scope_row(scope="national", province=None, doc=self._national_doc))
        for province in self.active_provinces():
            rows.append(
                self._build_scope_row(
                    scope="province",
                    province=province,
                    doc=self._province_docs[province],
                )
            )
        return rows

    def find_stale_rules(
        self,
        rules: list[LoadedRule] | None = None,
        *,
        today: date | None = None,
        max_age_days: int = 90,
    ) -> list[LoadedRule]:
        baseline = today or date.today()
        stale_before = baseline - timedelta(days=max_age_days)
        candidates = rules if rules is not None else self.list_all_rules(include_inactive=False)
        stale: list[LoadedRule] = []
        for rule in candidates:
            verified = _parse_rule_date(rule.last_verified_at)
            if verified is None or verified < stale_before:
                stale.append(rule)
        return stale

    def read_evidence_excerpt(self, rule: LoadedRule) -> str | None:
        if not rule.evidence_path:
            return None
        path = Path(rule.evidence_path)
        if not _evidence_file_is_complete(path):
            return None
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(">"):
                return stripped.removeprefix(">").strip()
        return None

    def scaffold_missing_evidence(
        self,
        *,
        province: str | None = None,
    ) -> dict[str, Any]:
        rules = self._rules_for_scaffolding(province)
        created_files: list[str] = []
        existing_files: list[str] = []
        touched_indexes: list[str] = []

        for group in rules.values():
            if not group:
                continue
            rule = group[0]
            evidence_dir = self._evidence_dir_for_rule(rule)
            evidence_dir.mkdir(parents=True, exist_ok=True)
            index_path = evidence_dir / "INDEX.md"
            index_path.write_text(
                self._build_index_markdown(group),
                encoding="utf-8",
            )
            touched_indexes.append(str(index_path))

            for scoped_rule in group:
                if scoped_rule.evidence_exists:
                    existing_files.append(scoped_rule.evidence_path or scoped_rule.rule_id)
                    continue
                evidence_path = self._evidence_dir_for_rule(scoped_rule) / (
                    f"{scoped_rule.source_evidence_id}.md"
                )
                if evidence_path.exists():
                    existing_files.append(str(evidence_path))
                    continue
                evidence_path.write_text(
                    self._build_evidence_template(scoped_rule),
                    encoding="utf-8",
                )
                created_files.append(str(evidence_path))

        return {
            "ok": True,
            "province": province,
            "created_rule_count": len(created_files),
            "created_files": created_files,
            "existing_rule_count": len(existing_files),
            "existing_files": existing_files,
            "touched_index_count": len(touched_indexes),
            "touched_indexes": touched_indexes,
        }

    def verify(
        self,
        *,
        strict_evidence: bool = False,
        max_rule_age_days: int = 90,
    ) -> dict[str, Any]:
        status = self.build_status(max_rule_age_days=max_rule_age_days)
        missing_required_files: list[str] = []
        if not (self._truth_root / "national.yaml").is_file():
            missing_required_files.append("national.yaml")
        if not (self._truth_root / "province").is_dir():
            missing_required_files.append("province/")

        active_rules = self.list_all_rules(include_inactive=False)
        stale_rules = self.find_stale_rules(active_rules, max_age_days=max_rule_age_days)
        missing_evidence_rules = [rule for rule in active_rules if not rule.evidence_exists]
        ok = not missing_required_files and not stale_rules
        if strict_evidence and missing_evidence_rules:
            ok = False

        return {
            "ok": ok,
            "province_count": status.province_count,
            "national_rule_count": status.national_rule_count,
            "national_version": status.national_version,
            "active_rule_count": status.active_rule_count,
            "missing_required_files": missing_required_files,
            "strict_evidence": strict_evidence,
            "max_rule_age_days": max_rule_age_days,
            "stale_rule_count": len(stale_rules),
            "stale_rule_ids": [rule.rule_id for rule in stale_rules],
            "missing_evidence_rule_count": len(missing_evidence_rules),
            "missing_evidence_rule_ids": [
                rule.rule_id for rule in missing_evidence_rules
            ],
        }

    def _load_province_docs(self, province_dir: Path) -> dict[str, dict[str, Any]]:
        docs: dict[str, dict[str, Any]] = {}
        for path in sorted(province_dir.glob("*.yaml")):
            doc = self._read_yaml(path)
            province = doc.get("province") or SLUG_TO_PROVINCE.get(path.stem)
            if not province:
                raise ValueError(f"cannot resolve province for truth file: {path}")
            docs[province] = doc
        return docs

    def _convert_rules(
        self, doc: dict[str, Any], *, scope: str, province: str | None
    ) -> list[LoadedRule]:
        rules: list[LoadedRule] = []
        prefix = "NATIONAL" if scope == "national" else self._province_prefix(province)
        for rule_key, payload in doc.get("rules", {}).items():
            evidence_path = self._resolve_evidence_path(
                scope=scope,
                province=province,
                source_evidence_id=payload["source_evidence_id"],
            )
            rules.append(
                LoadedRule(
                    rule_id=f"{prefix}.{rule_key}",
                    title=payload["title"],
                    severity=payload["severity"],
                    value=payload["value"],
                    source_evidence_id=payload["source_evidence_id"],
                    effective_date=payload["effective_date"],
                    status=payload.get("status", "active"),
                    scope=scope,
                    province=province,
                    year=doc.get("year", 2026),
                    version=doc.get("version", "2026.1"),
                    last_verified_at=payload.get(
                        "last_verified_at",
                        doc.get("last_verified_at", "2026-06-17"),
                    ),
                    evidence_path=str(evidence_path) if evidence_path else None,
                    evidence_exists=bool(
                        evidence_path and _evidence_file_is_complete(evidence_path)
                    ),
                )
            )
        return rules

    def _rules_for_scaffolding(
        self,
        province: str | None,
    ) -> dict[str, list[LoadedRule]]:
        groups: dict[str, list[LoadedRule]] = {}
        base_rules: list[LoadedRule]
        if province is None:
            base_rules = self.list_national_rules()
            provinces = self.active_provinces()
            for active_province in provinces:
                base_rules.extend(self.list_province_rules(active_province))
        elif province == "national":
            base_rules = self.list_national_rules()
        else:
            base_rules = self.list_province_rules(province)

        for rule in base_rules:
            if rule.status != "active":
                continue
            key = rule.province or "national"
            groups.setdefault(key, []).append(rule)
        return groups

    def _evidence_dir_for_rule(self, rule: LoadedRule) -> Path:
        if rule.scope == "national":
            return self._evidence_root / "national"
        assert rule.province is not None
        slug = PROVINCE_SLUGS[rule.province]
        return self._evidence_root / slug

    def _build_index_markdown(self, rules: list[LoadedRule]) -> str:
        sample = rules[0]
        scope_label = "国家级" if sample.scope == "national" else "省级"
        province_label = sample.province or "national"
        lines = [
            f"# {province_label} evidence index",
            "",
            f"- 范围: {scope_label}",
            f"- 规则版本: {sample.version}",
            f"- 最后刷新: {date.today().isoformat()}",
            "",
            "| rule_id | source_evidence_id | 状态 |",
            "| --- | --- | --- |",
        ]
        for rule in sorted(rules, key=lambda item: item.rule_id):
            status = "已完成" if rule.evidence_exists else "待补摘录"
            lines.append(
                f"| `{rule.rule_id}` | `{rule.source_evidence_id}` | {status} |"
            )
        lines.append("")
        lines.append(
            "> 说明: `待补摘录` 表示模板已准备或证据仍缺失，不计入 CLI evidence 覆盖。"
        )
        lines.append("")
        return "\n".join(lines)

    def _build_evidence_template(self, rule: LoadedRule) -> str:
        value_yaml = yaml.safe_dump(
            {
                rule.rule_id: {
                    "severity": rule.severity,
                    "value": rule.value,
                    "effective_date": rule.effective_date,
                    "source_evidence_id": rule.source_evidence_id,
                    "status": rule.status,
                }
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip()
        scope_label = "国家级" if rule.scope == "national" else "省级"
        owner = rule.province or "national"
        return "\n".join(
            [
                f"# {rule.source_evidence_id}",
                "",
                f"> 对应规则: `{rule.rule_id}`",
                f"> 所属: {scope_label}",
                f"> 规则版本: `{rule.version}`",
                f"> 摘录时间: {date.today().isoformat()}",
                "> 摘录人: 待补充",
                f"> 证据状态: {EVIDENCE_TEMPLATE_STATUS}",
                "",
                "## 1. 官方原文摘录",
                "",
                '> "TODO_OFFICIAL_EXCERPT" —— 出处: TODO_SOURCE_TITLE, TODO_URL, TODO_PUBLISHED_DATE',
                "",
                "## 2. 转写为机读规则",
                "",
                "```yaml",
                value_yaml,
                "```",
                "",
                "## 3. 关键边界与例外",
                "",
                "- 例 1：TODO",
                "- 例 2：TODO",
                "",
                "## 4. 后续维护",
                "",
                "- 下次复核时间: TODO",
                f"- 复核来源: {owner}",
                "- 复核负责人: 待指派",
                "",
            ]
        )

    def _build_scope_row(
        self,
        *,
        scope: str,
        province: str | None,
        doc: dict[str, Any],
    ) -> dict[str, Any]:
        if scope == "national":
            rules = self.list_national_rules()
        else:
            assert province is not None
            rules = self.list_province_rules(province)
        active_rules = [rule for rule in rules if rule.status == "active"]
        missing = [rule.rule_id for rule in active_rules if not rule.evidence_exists]
        return {
            "scope": scope,
            "province": province,
            "version": str(doc.get("version", "2026.1")),
            "last_verified_at": str(doc.get("last_verified_at", "2026-06-17")),
            "active_rule_count": len(active_rules),
            "evidenced_rule_count": sum(
                1 for rule in active_rules if rule.evidence_exists
            ),
            "missing_evidence_rule_ids": missing,
        }

    def _resolve_evidence_path(
        self,
        *,
        scope: str,
        province: str | None,
        source_evidence_id: str,
    ) -> Path | None:
        if scope == "national":
            return self._evidence_root / "national" / f"{source_evidence_id}.md"
        if province is None:
            return None
        slug = PROVINCE_SLUGS.get(province)
        if not slug:
            return None
        return self._evidence_root / slug / f"{source_evidence_id}.md"

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @staticmethod
    def _province_prefix(province: str | None) -> str:
        if not province:
            return "PROVINCE"
        slug = PROVINCE_SLUGS.get(province)
        if slug:
            return slug.upper()
        return province.upper()


def _parse_rule_date(raw: str) -> date | None:
    value = str(raw or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _evidence_file_is_complete(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    for section in EVIDENCE_REQUIRED_SECTIONS:
        if section not in text:
            return False
    for sentinel in EVIDENCE_TEMPLATE_SENTINELS:
        if sentinel in text:
            return False
    return True
