from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import yaml  # type: ignore[import-untyped]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_CHECKER_PATH = PROJECT_ROOT / "scripts" / "gaokao-checker"


def _load_legacy_checker_module():
    loader = SourceFileLoader("legacy_gaokao_checker", str(LEGACY_CHECKER_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migrate_province_rules_to_truth_exports_all_legacy_provinces(
    tmp_path: Path,
) -> None:
    legacy = _load_legacy_checker_module()

    from scripts.migrate_province_rules_to_truth import migrate_legacy_rules_to_truth

    summary = migrate_legacy_rules_to_truth(output_root=tmp_path)

    province_dir = tmp_path / "province"
    province_files = sorted(province_dir.glob("*.yaml"))

    assert summary["province_count"] == len(legacy.PROVINCE_RULES)
    assert len(province_files) == len(legacy.PROVINCE_RULES)
    assert (tmp_path / "national.yaml").is_file()

    hunan_truth = yaml.safe_load(
        (province_dir / "hunan.yaml").read_text(encoding="utf-8")
    )
    assert hunan_truth["province"] == "湖南"
    assert hunan_truth["year"] == 2026
    assert hunan_truth["status"] == "active"
    assert hunan_truth["rules"]["max_volunteers"]["value"] == {"max_volunteers": 45}
    assert hunan_truth["rules"]["max_volunteers"]["source_evidence_id"]


def test_rule_loader_reads_national_and_province_truth_tree(tmp_path: Path) -> None:
    truth_root = tmp_path
    (truth_root / "province").mkdir(parents=True, exist_ok=True)

    (truth_root / "national.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "national",
                "year": 2026,
                "version": "2026.1",
                "rules": {
                    "parallel_volunteer_principle": {
                        "title": "平行志愿原则",
                        "severity": "info",
                        "value": {"rule": "分数优先、遵循志愿、一次投档"},
                        "source_evidence_id": "national-2026-parallel-rule",
                        "effective_date": "2026-01-01",
                        "status": "active",
                    }
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    (truth_root / "province" / "hunan.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "province",
                "province": "湖南",
                "year": 2026,
                "version": "2026.1",
                "status": "active",
                "rules": {
                    "max_volunteers": {
                        "title": "本科批志愿上限",
                        "severity": "fatal",
                        "value": {"max_volunteers": 45},
                        "source_evidence_id": "hunan-2026-max-volunteers",
                        "effective_date": "2026-01-01",
                        "status": "active",
                    }
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    from data.rules.loader import RuleLoader

    loader = RuleLoader.from_truth_root(truth_root)
    status = loader.build_status()
    rules = loader.list_province_rules("湖南")
    national = loader.list_national_rules()

    assert status.province_count == 1
    assert status.national_rule_count == 1
    assert status.active_provinces == ["湖南"]
    assert rules[0].rule_id == "HUNAN.max_volunteers"
    assert rules[0].value["max_volunteers"] == 45
    assert national[0].rule_id == "NATIONAL.parallel_volunteer_principle"


def test_migrated_truth_set_matches_legacy_checker_provinces(tmp_path: Path) -> None:
    legacy = _load_legacy_checker_module()

    from scripts.migrate_province_rules_to_truth import migrate_legacy_rules_to_truth
    from data.rules.loader import RuleLoader

    migrate_legacy_rules_to_truth(output_root=tmp_path)
    loader = RuleLoader.from_truth_root(tmp_path)

    assert set(loader.active_provinces()) == set(legacy.PROVINCE_RULES.keys())


def test_audit_engine_exposes_province_snapshot_from_truth(tmp_path: Path) -> None:
    from data.rules.audit_engine import AuditEngine
    from data.rules.loader import RuleLoader
    from scripts.migrate_province_rules_to_truth import migrate_legacy_rules_to_truth

    migrate_legacy_rules_to_truth(output_root=tmp_path)
    loader = RuleLoader.from_truth_root(tmp_path)
    engine = AuditEngine(loader)

    snapshot = engine.get_province_snapshot("湖南")

    assert snapshot.province == "湖南"
    assert snapshot.mode == "院校专业组"
    assert snapshot.max_volunteers == 45
    assert snapshot.retrieval_rule == "分数优先、遵循志愿、一次投档"
    assert snapshot.rule_count >= 5
