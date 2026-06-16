from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from data.rules.loader import PROVINCE_SLUGS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEGACY_CHECKER_PATH = PROJECT_ROOT / "scripts" / "gaokao-checker"

RULE_FIELD_METADATA = {
    "mode": ("志愿模式", "fatal"),
    "batch": ("批次名称", "info"),
    "max_volunteers": ("志愿上限", "fatal"),
    "max_majors_per_group": ("每组专业上限", "warning"),
    "has_adjustment": ("是否允许调剂", "warning"),
    "adjustment_scope": ("调剂范围", "fatal"),
    "retrieval_rule": ("投档原则", "critical"),
    "collection_count": ("征集志愿次数", "warning"),
    "subject_mode": ("选科模式", "warning"),
    "official_url": ("官方来源链接", "info"),
    "exam_subject_total": ("总分", "info"),
}


def _load_legacy_checker_module():
    loader = SourceFileLoader("legacy_gaokao_checker", str(LEGACY_CHECKER_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load legacy checker from {LEGACY_CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_national_truth() -> dict[str, Any]:
    return {
        "scope": "national",
        "year": 2026,
        "version": "2026.1",
        "rules": {
            "parallel_volunteer_principle": {
                "title": "平行志愿原则",
                "severity": "info",
                "value": {"rule": "分数优先、遵循志愿、一次投档"},
                "source_evidence_id": "national-2026-parallel-volunteer-principle",
                "effective_date": "2026-01-01",
                "status": "active",
            }
        },
    }


def _build_province_truth(province: str, payload: dict[str, Any]) -> dict[str, Any]:
    rules: dict[str, Any] = {}
    for key, value in payload.items():
        title, severity = RULE_FIELD_METADATA.get(key, (key, "info"))
        rules[key] = {
            "title": title,
            "severity": severity,
            "value": {key: value},
            "source_evidence_id": f"{PROVINCE_SLUGS[province]}-2026-{key}",
            "effective_date": "2026-01-01",
            "status": "active",
        }
    return {
        "scope": "province",
        "province": province,
        "year": 2026,
        "version": "2026.1",
        "status": "active",
        "rules": rules,
    }


def migrate_legacy_rules_to_truth(output_root: Path | str) -> dict[str, int]:
    legacy = _load_legacy_checker_module()
    target_root = Path(output_root)
    province_dir = target_root / "province"
    province_dir.mkdir(parents=True, exist_ok=True)

    national_truth = _build_national_truth()
    (target_root / "national.yaml").write_text(
        yaml.safe_dump(national_truth, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    for province, payload in sorted(legacy.PROVINCE_RULES.items()):
        slug = PROVINCE_SLUGS.get(province)
        if not slug:
            raise KeyError(f"missing province slug mapping for {province}")
        truth_doc = _build_province_truth(province, payload)
        (province_dir / f"{slug}.yaml").write_text(
            yaml.safe_dump(truth_doc, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    return {
        "province_count": len(legacy.PROVINCE_RULES),
        "national_rule_count": len(national_truth["rules"]),
    }


def main() -> int:
    output_root = PROJECT_ROOT / "rules" / "_truth"
    summary = migrate_legacy_rules_to_truth(output_root=output_root)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
