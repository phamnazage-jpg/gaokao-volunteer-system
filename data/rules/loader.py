from __future__ import annotations

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


class RuleLoader:
    def __init__(self, truth_root: Path) -> None:
        self._truth_root = Path(truth_root)
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

    def build_status(self) -> RulesStatus:
        return RulesStatus(
            province_count=len(self.active_provinces()),
            national_rule_count=len(self._national_doc.get("rules", {})),
            active_provinces=self.active_provinces(),
        )

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
                )
            )
        return rules

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
