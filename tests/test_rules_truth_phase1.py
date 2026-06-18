from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import yaml  # type: ignore[import-untyped]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_CHECKER_PATH = PROJECT_ROOT / "scripts" / "gaokao-checker"


def _load_python_module(name: str, path: Path):
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    migrate = _load_python_module(
        'migrate_province_rules_to_truth',
        PROJECT_ROOT / 'scripts' / 'migrate_province_rules_to_truth.py',
    )

    summary = migrate.migrate_legacy_rules_to_truth(output_root=tmp_path)

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
                "last_verified_at": "2026-06-17",
                "rules": {
                    "parallel_volunteer_principle": {
                        "title": "平行志愿原则",
                        "severity": "info",
                        "value": {"rule": "分数优先、遵循志愿、一次投档"},
                        "source_evidence_id": "national-2026-parallel-rule",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-06-17",
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
                "last_verified_at": "2026-06-17",
                "status": "active",
                "rules": {
                    "max_volunteers": {
                        "title": "本科批志愿上限",
                        "severity": "fatal",
                        "value": {"max_volunteers": 45},
                        "source_evidence_id": "hunan-2026-max-volunteers",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-06-17",
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

    evidence_root = tmp_path.parent / "_evidence" / "hunan"
    evidence_root.mkdir(parents=True, exist_ok=True)
    (evidence_root / "hunan-2026-max-volunteers.md").write_text(
        "\n".join(
            [
                "# hunan-2026-max-volunteers",
                "",
                "> 对应规则: `HUNAN.max_volunteers`",
                "> 所属: 省级",
                "> 规则版本: `2026.1`",
                "> 摘录时间: 2026-06-17",
                "> 摘录人: pytest",
                "",
                "## 1. 官方原文摘录",
                "",
                '> "湖南本科批院校专业组最多 45 个志愿。" —— 出处: 湖南省招生规则, http://example.com, 2026-06-01',
                "",
                "## 2. 转写为机读规则",
                "",
                "```yaml",
                "HUNAN.max_volunteers:",
                "  severity: fatal",
                "  value:",
                "    max_volunteers: 45",
                "  effective_date: 2026-01-01",
                "  source_evidence_id: hunan-2026-max-volunteers",
                "  status: active",
                "```",
                "",
                "## 3. 关键边界与例外",
                "",
                "- 例 1：示例",
                "- 例 2：示例",
                "",
                "## 4. 后续维护",
                "",
                "- 下次复核时间: 2026-09-01",
                "- 复核来源: http://example.com",
                "- 复核负责人: pytest",
                "",
            ]
        ),
        encoding="utf-8",
    )

    loader = RuleLoader.from_truth_root(truth_root)
    status = loader.build_status()
    rules = loader.list_province_rules("湖南")
    national = loader.list_national_rules()

    assert status.province_count == 1
    assert status.national_rule_count == 1
    assert status.active_provinces == ["湖南"]
    assert status.national_version == "2026.1"
    assert status.stale_rule_max_age_days == 90
    assert status.stale_rule_count == 0
    assert status.stale_rule_ids == []
    assert rules[0].rule_id == "HUNAN.max_volunteers"
    assert rules[0].value["max_volunteers"] == 45
    assert rules[0].last_verified_at == "2026-06-17"
    assert rules[0].evidence_exists is True
    assert national[0].rule_id == "NATIONAL.parallel_volunteer_principle"


def test_rule_loader_verify_flags_stale_or_missing_evidence(tmp_path: Path) -> None:
    truth_root = tmp_path / "truth"
    province_dir = truth_root / "province"
    province_dir.mkdir(parents=True, exist_ok=True)
    (truth_root / "national.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "national",
                "year": 2026,
                "version": "2026.1",
                "last_verified_at": "2026-01-01",
                "rules": {
                    "parallel_volunteer_principle": {
                        "title": "平行志愿原则",
                        "severity": "info",
                        "value": {"rule": "分数优先、遵循志愿、一次投档"},
                        "source_evidence_id": "national-2026-parallel-rule",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-01-01",
                        "status": "active",
                    }
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (province_dir / "hunan.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "province",
                "province": "湖南",
                "year": 2026,
                "version": "2026.1",
                "last_verified_at": "2026-01-01",
                "status": "active",
                "rules": {
                    "max_volunteers": {
                        "title": "本科批志愿上限",
                        "severity": "fatal",
                        "value": {"max_volunteers": 45},
                        "source_evidence_id": "hunan-2026-max-volunteers",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-01-01",
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
    payload = loader.verify(strict_evidence=True, max_rule_age_days=90)

    assert payload["ok"] is False
    assert payload["stale_rule_count"] == 2
    assert "NATIONAL.parallel_volunteer_principle" in payload["stale_rule_ids"]
    assert "HUNAN.max_volunteers" in payload["stale_rule_ids"]
    assert payload["missing_evidence_rule_count"] == 2
    assert "NATIONAL.parallel_volunteer_principle" in payload["missing_evidence_rule_ids"]
    assert "HUNAN.max_volunteers" in payload["missing_evidence_rule_ids"]


def test_rule_loader_scaffold_templates_do_not_count_as_completed_evidence(
    tmp_path: Path,
) -> None:
    truth_root = tmp_path / "truth"
    province_dir = truth_root / "province"
    province_dir.mkdir(parents=True, exist_ok=True)
    (truth_root / "national.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "national",
                "year": 2026,
                "version": "2026.1",
                "last_verified_at": "2026-06-17",
                "rules": {},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (province_dir / "hunan.yaml").write_text(
        yaml.safe_dump(
            {
                "scope": "province",
                "province": "湖南",
                "year": 2026,
                "version": "2026.1",
                "last_verified_at": "2026-06-17",
                "status": "active",
                "rules": {
                    "max_volunteers": {
                        "title": "本科批志愿上限",
                        "severity": "fatal",
                        "value": {"max_volunteers": 45},
                        "source_evidence_id": "hunan-2026-max-volunteers",
                        "effective_date": "2026-01-01",
                        "last_verified_at": "2026-06-17",
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
    payload = loader.scaffold_missing_evidence(province="湖南")
    reloaded = RuleLoader.from_truth_root(truth_root)
    rules = reloaded.list_province_rules("湖南")

    assert payload["created_rule_count"] == 1
    assert payload["touched_index_count"] == 1
    evidence_path = tmp_path / "_evidence" / "hunan" / "hunan-2026-max-volunteers.md"
    assert evidence_path.is_file()
    assert "证据状态: draft_template" in evidence_path.read_text(encoding="utf-8")
    assert rules[0].evidence_exists is False


def test_migrated_truth_set_matches_legacy_checker_provinces(tmp_path: Path) -> None:
    legacy = _load_legacy_checker_module()

    migrate = _load_python_module(
        'migrate_province_rules_to_truth',
        PROJECT_ROOT / 'scripts' / 'migrate_province_rules_to_truth.py',
    )
    from data.rules.loader import RuleLoader

    migrate.migrate_legacy_rules_to_truth(output_root=tmp_path)
    loader = RuleLoader.from_truth_root(tmp_path)

    assert set(loader.active_provinces()) == set(legacy.PROVINCE_RULES.keys())


def test_audit_engine_exposes_province_snapshot_from_truth(tmp_path: Path) -> None:
    from data.rules.audit_engine import AuditEngine
    from data.rules.loader import RuleLoader
    migrate = _load_python_module(
        'migrate_province_rules_to_truth',
        PROJECT_ROOT / 'scripts' / 'migrate_province_rules_to_truth.py',
    )

    migrate.migrate_legacy_rules_to_truth(output_root=tmp_path)
    loader = RuleLoader.from_truth_root(tmp_path)
    engine = AuditEngine(loader)

    snapshot = engine.get_province_snapshot("湖南")

    assert snapshot.province == "湖南"
    assert snapshot.mode == "院校专业组"
    assert snapshot.max_volunteers == 45
    assert snapshot.retrieval_rule == "分数优先、遵循志愿、一次投档"
    assert snapshot.rule_count >= 5
