from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _evidence_root() -> Path:
    return PROJECT_ROOT / "rules" / "_evidence"


def test_evidence_layer_readme_exists() -> None:
    readme = _evidence_root() / "README.md"
    assert readme.is_file(), "rules/_evidence/README.md must exist"
    text = readme.read_text(encoding="utf-8")
    # README must explain the directory contract.
    assert "<prov-slug>" in text
    assert "<source_evidence_id>" in text
    assert "evidence 摘录模板" in text


def test_hunan_evidence_covers_every_active_rule() -> None:
    """Every source_evidence_id declared in rules/_truth/province/hunan.yaml
    must have a matching evidence file under rules/_evidence/hunan/.
    """
    import yaml  # type: ignore[import-untyped]

    truth_path = PROJECT_ROOT / "rules" / "_truth" / "province" / "hunan.yaml"
    truth = yaml.safe_load(truth_path.read_text(encoding="utf-8")) or {}
    rules = truth.get("rules", {}) or {}
    expected_ids = {
        payload["source_evidence_id"]
        for payload in rules.values()
        if payload.get("status", "active") == "active"
    }
    assert expected_ids, "hunan.yaml must declare at least one rule"

    evidence_dir = _evidence_root() / "hunan"
    missing: list[str] = []
    for evidence_id in sorted(expected_ids):
        if not (evidence_dir / f"{evidence_id}.md").is_file():
            missing.append(evidence_id)
    assert not missing, f"missing evidence files for: {missing}"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("hunan-2026-mode", ["院校专业组", "湖南省"]),
        ("hunan-2026-batch", ["本科批", "湖南省"]),
        ("hunan-2026-max_volunteers", ["45", "院校专业组"]),
        ("hunan-2026-max_majors_per_group", ["6", "专业"]),
        ("hunan-2026-has_adjustment", ["调剂", "院校专业组"]),
        ("hunan-2026-adjustment_scope", ["组内专业", "调剂"]),
        ("hunan-2026-retrieval_rule", ["分数优先", "一次投档"]),
        ("hunan-2026-collection_count", ["2", "征集"]),
        ("hunan-2026-subject_mode", ["3+1+2"]),
        ("hunan-2026-official_url", ["jyt.hunan.gov.cn"]),
        ("hunan-2026-exam_subject_total", ["750"]),
    ],
)
def test_hunan_evidence_files_contain_required_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "hunan" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


def test_evidence_files_have_strict_template_sections() -> None:
    """Every evidence file must include the four required sections."""
    for path in sorted((_evidence_root() / "hunan").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for section in (
            "## 1. 官方原文摘录",
            "## 2. 转写为机读规则",
            "## 3. 关键边界与例外",
            "## 4. 后续维护",
        ):
            assert section in text, f"{path.name} missing section: {section}"


def test_no_orphan_evidence_files() -> None:
    """Every evidence file under rules/_evidence/hunan/ must be referenced
    by some hunan.yaml rule. Prevents stale/orphan摘录.
    """
    import yaml  # type: ignore[import-untyped]

    truth_path = PROJECT_ROOT / "rules" / "_truth" / "province" / "hunan.yaml"
    truth = yaml.safe_load(truth_path.read_text(encoding="utf-8")) or {}
    declared = {
        payload["source_evidence_id"]
        for payload in (truth.get("rules", {}) or {}).values()
        if "source_evidence_id" in payload
    }
    evidence_files = {p.stem for p in (_evidence_root() / "hunan").glob("*.md")}
    orphans = evidence_files - declared
    assert not orphans, (
        f"orphan evidence files (not referenced by hunan.yaml): {orphans}"
    )
