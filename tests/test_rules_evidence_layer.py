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
    assert "draft_template" in text


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
        if path.name == "INDEX.md":
            continue
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
    evidence_files = {
        p.stem for p in (_evidence_root() / "hunan").glob("*.md") if p.name != "INDEX.md"
    }
    orphans = evidence_files - declared
    assert not orphans, (
        f"orphan evidence files (not referenced by hunan.yaml): {orphans}"
    )


def test_hunan_index_file_tracks_evidence_completion() -> None:
    index_path = _evidence_root() / "hunan" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/hunan/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "| rule_id | source_evidence_id | 状态 |" in text
    assert "HUNAN.max_volunteers" in text
    assert "已完成" in text


def test_beijing_index_file_tracks_completion() -> None:
    index_path = _evidence_root() / "beijing" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/beijing/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "BEIJING.mode" in text
    assert "BEIJING.collection_count" in text
    assert "| `BEIJING.mode` | `beijing-2026-mode` | 已完成 |" in text
    assert "| `BEIJING.subject_mode` | `beijing-2026-subject_mode` | 已完成 |" in text
    assert "| `BEIJING.exam_subject_total` | `beijing-2026-exam_subject_total` | 已完成 |" in text
    assert "| `BEIJING.collection_count` | `beijing-2026-collection_count` | 已完成 |" in text


def test_jiangsu_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "jiangsu" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/jiangsu/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "JIANGSU.mode" in text
    assert "JIANGSU.max_majors_per_group" in text
    assert "| `JIANGSU.mode` | `jiangsu-2026-mode` | 已完成 |" in text
    assert "| `JIANGSU.collection_count` | `jiangsu-2026-collection_count` | 已完成 |" in text
    assert "| `JIANGSU.max_majors_per_group` | `jiangsu-2026-max_majors_per_group` | 已完成 |" in text
    assert "| `JIANGSU.exam_subject_total` | `jiangsu-2026-exam_subject_total` | 已完成 |" in text


def test_zhejiang_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "zhejiang" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/zhejiang/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "ZHEJIANG.mode" in text
    assert "ZHEJIANG.collection_count" in text
    assert "| `ZHEJIANG.mode` | `zhejiang-2026-mode` | 已完成 |" in text
    assert (
        "| `ZHEJIANG.collection_count` | `zhejiang-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `ZHEJIANG.max_majors_per_group` | `zhejiang-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `ZHEJIANG.exam_subject_total` | `zhejiang-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_shanghai_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "shanghai" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/shanghai/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "SHANGHAI.mode" in text
    assert "SHANGHAI.collection_count" in text
    assert "| `SHANGHAI.mode` | `shanghai-2026-mode` | 已完成 |" in text
    assert (
        "| `SHANGHAI.collection_count` | `shanghai-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `SHANGHAI.max_majors_per_group` | `shanghai-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `SHANGHAI.exam_subject_total` | `shanghai-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_anhui_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "anhui" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/anhui/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "ANHUI.mode" in text
    assert "ANHUI.collection_count" in text
    assert "| `ANHUI.mode` | `anhui-2026-mode` | 已完成 |" in text
    assert (
        "| `ANHUI.collection_count` | `anhui-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `ANHUI.max_majors_per_group` | `anhui-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `ANHUI.exam_subject_total` | `anhui-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_shandong_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "shandong" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/shandong/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "SHANDONG.mode" in text
    assert "SHANDONG.collection_count" in text
    assert "| `SHANDONG.mode` | `shandong-2026-mode` | 已完成 |" in text
    assert (
        "| `SHANDONG.collection_count` | `shandong-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `SHANDONG.max_majors_per_group` | `shandong-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `SHANDONG.exam_subject_total` | `shandong-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_guangdong_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "guangdong" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/guangdong/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "GUANGDONG.mode" in text
    assert "GUANGDONG.collection_count" in text
    assert "| `GUANGDONG.mode` | `guangdong-2026-mode` | 已完成 |" in text
    assert (
        "| `GUANGDONG.collection_count` | `guangdong-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `GUANGDONG.max_majors_per_group` | `guangdong-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `GUANGDONG.exam_subject_total` | `guangdong-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_hubei_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "hubei" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/hubei/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "HUBEI.mode" in text
    assert "HUBEI.collection_count" in text
    assert "| `HUBEI.mode` | `hubei-2026-mode` | 已完成 |" in text
    assert "| `HUBEI.collection_count` | `hubei-2026-collection_count` | 已完成 |" in text
    assert (
        "| `HUBEI.max_majors_per_group` | `hubei-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `HUBEI.exam_subject_total` | `hubei-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_hebei_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "hebei" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/hebei/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "HEBEI.mode" in text
    assert "HEBEI.retrieval_rule" in text
    assert "| `HEBEI.mode` | `hebei-2026-mode` | 已完成 |" in text
    assert "| `HEBEI.collection_count` | `hebei-2026-collection_count` | 已完成 |" in text
    assert (
        "| `HEBEI.max_majors_per_group` | `hebei-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `HEBEI.subject_mode` | `hebei-2026-subject_mode` | 已完成 |" in text
    )
    assert (
        "| `HEBEI.exam_subject_total` | `hebei-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_hainan_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "hainan" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/hainan/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "HAINAN.mode" in text
    assert "HAINAN.collection_count" in text
    assert "| `HAINAN.mode` | `hainan-2026-mode` | 已完成 |" in text
    assert "| `HAINAN.collection_count` | `hainan-2026-collection_count` | 已完成 |" in text
    assert (
        "| `HAINAN.max_volunteers` | `hainan-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `HAINAN.subject_mode` | `hainan-2026-subject_mode` | 已完成 |" in text
    )
    assert (
        "| `HAINAN.exam_subject_total` | `hainan-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_fujian_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "fujian" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/fujian/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "FUJIAN.mode" in text
    assert "FUJIAN.collection_count" in text
    assert "| `FUJIAN.mode` | `fujian-2026-mode` | 已完成 |" in text
    assert "| `FUJIAN.collection_count` | `fujian-2026-collection_count` | 已完成 |" in text
    assert (
        "| `FUJIAN.max_volunteers` | `fujian-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `FUJIAN.subject_mode` | `fujian-2026-subject_mode` | 已完成 |" in text
    )
    assert (
        "| `FUJIAN.exam_subject_total` | `fujian-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_sichuan_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "sichuan" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/sichuan/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "SICHUAN.mode" in text
    assert "SICHUAN.collection_count" in text
    assert "| `SICHUAN.mode` | `sichuan-2026-mode` | 已完成 |" in text
    assert "| `SICHUAN.collection_count` | `sichuan-2026-collection_count` | 已完成 |" in text
    assert (
        "| `SICHUAN.max_volunteers` | `sichuan-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `SICHUAN.subject_mode` | `sichuan-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `SICHUAN.exam_subject_total` | `sichuan-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_jiangxi_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "jiangxi" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/jiangxi/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "JIANGXI.mode" in text
    assert "JIANGXI.collection_count" in text
    assert "| `JIANGXI.mode` | `jiangxi-2026-mode` | 已完成 |" in text
    assert "| `JIANGXI.collection_count` | `jiangxi-2026-collection_count` | 已完成 |" in text
    assert (
        "| `JIANGXI.max_volunteers` | `jiangxi-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `JIANGXI.subject_mode` | `jiangxi-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `JIANGXI.exam_subject_total` | `jiangxi-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_gansu_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "gansu" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/gansu/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "GANSU.mode" in text
    assert "GANSU.collection_count" in text
    assert "| `GANSU.mode` | `gansu-2026-mode` | 已完成 |" in text
    assert "| `GANSU.collection_count` | `gansu-2026-collection_count` | 已完成 |" in text
    assert (
        "| `GANSU.max_majors_per_group` | `gansu-2026-max_majors_per_group` | 已完成 |"
        in text
    )
    assert (
        "| `GANSU.exam_subject_total` | `gansu-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_yunnan_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "yunnan" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/yunnan/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "YUNNAN.mode" in text
    assert "YUNNAN.collection_count" in text
    assert "| `YUNNAN.mode` | `yunnan-2026-mode` | 已完成 |" in text
    assert "| `YUNNAN.batch` | `yunnan-2026-batch` | 已完成 |" in text
    assert (
        "| `YUNNAN.max_volunteers` | `yunnan-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `YUNNAN.collection_count` | `yunnan-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `YUNNAN.subject_mode` | `yunnan-2026-subject_mode` | 已完成 |" in text
    )
    assert (
        "| `YUNNAN.exam_subject_total` | `yunnan-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_guizhou_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "guizhou" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/guizhou/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "GUIZHOU.mode" in text
    assert "GUIZHOU.collection_count" in text
    assert "| `GUIZHOU.mode` | `guizhou-2026-mode` | 已完成 |" in text
    assert "| `GUIZHOU.batch` | `guizhou-2026-batch` | 已完成 |" in text
    assert (
        "| `GUIZHOU.max_volunteers` | `guizhou-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `GUIZHOU.collection_count` | `guizhou-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `GUIZHOU.subject_mode` | `guizhou-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `GUIZHOU.exam_subject_total` | `guizhou-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_liaoning_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "liaoning" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/liaoning/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "LIAONING.mode" in text
    assert "LIAONING.collection_count" in text
    assert "| `LIAONING.mode` | `liaoning-2026-mode` | 已完成 |" in text
    assert "| `LIAONING.batch` | `liaoning-2026-batch` | 已完成 |" in text
    assert (
        "| `LIAONING.max_volunteers` | `liaoning-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `LIAONING.collection_count` | `liaoning-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `LIAONING.subject_mode` | `liaoning-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `LIAONING.exam_subject_total` | `liaoning-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_jilin_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "jilin" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/jilin/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "JILIN.mode" in text
    assert "JILIN.collection_count" in text
    assert "| `JILIN.mode` | `jilin-2026-mode` | 已完成 |" in text
    assert "| `JILIN.batch` | `jilin-2026-batch` | 已完成 |" in text
    assert (
        "| `JILIN.max_volunteers` | `jilin-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `JILIN.collection_count` | `jilin-2026-collection_count` | 已完成 |"
        in text
    )
    assert "| `JILIN.subject_mode` | `jilin-2026-subject_mode` | 已完成 |" in text
    assert (
        "| `JILIN.exam_subject_total` | `jilin-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_heilongjiang_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "heilongjiang" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/heilongjiang/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "HEILONGJIANG.mode" in text
    assert "HEILONGJIANG.collection_count" in text
    assert "| `HEILONGJIANG.mode` | `heilongjiang-2026-mode` | 已完成 |" in text
    assert (
        "| `HEILONGJIANG.batch` | `heilongjiang-2026-batch` | 已完成 |"
        in text
    )
    assert (
        "| `HEILONGJIANG.max_volunteers` | `heilongjiang-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `HEILONGJIANG.collection_count` | `heilongjiang-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `HEILONGJIANG.subject_mode` | `heilongjiang-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `HEILONGJIANG.exam_subject_total` | `heilongjiang-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_guangxi_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "guangxi" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/guangxi/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "GUANGXI.mode" in text
    assert "GUANGXI.collection_count" in text
    assert "| `GUANGXI.mode` | `guangxi-2026-mode` | 已完成 |" in text
    assert "| `GUANGXI.batch` | `guangxi-2026-batch` | 已完成 |" in text
    assert (
        "| `GUANGXI.max_volunteers` | `guangxi-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `GUANGXI.collection_count` | `guangxi-2026-collection_count` | 已完成 |"
        in text
    )
    assert "| `GUANGXI.subject_mode` | `guangxi-2026-subject_mode` | 已完成 |" in text
    assert (
        "| `GUANGXI.exam_subject_total` | `guangxi-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_qinghai_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "qinghai" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/qinghai/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "QINGHAI.mode" in text
    assert "QINGHAI.collection_count" in text
    assert "| `QINGHAI.mode` | `qinghai-2026-mode` | 已完成 |" in text
    assert (
        "| `QINGHAI.collection_count` | `qinghai-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `QINGHAI.max_volunteers` | `qinghai-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `QINGHAI.subject_mode` | `qinghai-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `QINGHAI.exam_subject_total` | `qinghai-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_xizang_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "xizang" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/xizang/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "XIZANG.mode" in text
    assert "XIZANG.collection_count" in text
    assert "| `XIZANG.mode` | `xizang-2026-mode` | 已完成 |" in text
    assert (
        "| `XIZANG.collection_count` | `xizang-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `XIZANG.max_volunteers` | `xizang-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `XIZANG.subject_mode` | `xizang-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `XIZANG.exam_subject_total` | `xizang-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_xinjiang_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "xinjiang" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/xinjiang/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "XINJIANG.mode" in text
    assert "XINJIANG.collection_count" in text
    assert "| `XINJIANG.mode` | `xinjiang-2026-mode` | 已完成 |" in text
    assert (
        "| `XINJIANG.collection_count` | `xinjiang-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `XINJIANG.max_volunteers` | `xinjiang-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `XINJIANG.subject_mode` | `xinjiang-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `XINJIANG.exam_subject_total` | `xinjiang-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_tianjin_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "tianjin" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/tianjin/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "TIANJIN.mode" in text
    assert "TIANJIN.collection_count" in text
    assert "| `TIANJIN.mode` | `tianjin-2026-mode` | 已完成 |" in text
    assert (
        "| `TIANJIN.collection_count` | `tianjin-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `TIANJIN.max_volunteers` | `tianjin-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `TIANJIN.subject_mode` | `tianjin-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `TIANJIN.exam_subject_total` | `tianjin-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_henan_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "henan" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/henan/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "HENAN.mode" in text
    assert "HENAN.collection_count" in text
    assert "| `HENAN.mode` | `henan-2026-mode` | 已完成 |" in text
    assert (
        "| `HENAN.collection_count` | `henan-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `HENAN.max_volunteers` | `henan-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `HENAN.subject_mode` | `henan-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `HENAN.exam_subject_total` | `henan-2026-exam_subject_total` | 已完成 |"
        in text
    )


def test_chongqing_index_file_tracks_full_completion() -> None:
    index_path = _evidence_root() / "chongqing" / "INDEX.md"
    assert index_path.is_file(), "rules/_evidence/chongqing/INDEX.md must exist"
    text = index_path.read_text(encoding="utf-8")
    assert "CHONGQING.mode" in text
    assert "CHONGQING.collection_count" in text
    assert "| `CHONGQING.mode` | `chongqing-2026-mode` | 已完成 |" in text
    assert (
        "| `CHONGQING.collection_count` | `chongqing-2026-collection_count` | 已完成 |"
        in text
    )
    assert (
        "| `CHONGQING.max_volunteers` | `chongqing-2026-max_volunteers` | 已完成 |"
        in text
    )
    assert (
        "| `CHONGQING.subject_mode` | `chongqing-2026-subject_mode` | 已完成 |"
        in text
    )
    assert (
        "| `CHONGQING.exam_subject_total` | `chongqing-2026-exam_subject_total` | 已完成 |"
        in text
    )


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("xinjiang-2026-mode", ["文科综合/理科综合", "mode: 传统"]),
        ("xinjiang-2026-batch", ["本科一批次", "batch: 本科一批"]),
        ("xinjiang-2026-max_volunteers", ["18个平行志愿", "max_volunteers: 18"]),
        ("xinjiang-2026-max_majors_per_group", ["可填报6个专业", "max_majors_per_group: 6"]),
        ("xinjiang-2026-has_adjustment", ["“服从 / 不服从”", "has_adjustment: true"]),
        ("xinjiang-2026-adjustment_scope", ["统招调剂 / 定向调剂", "adjustment_scope: 全部专业"]),
        ("xinjiang-2026-retrieval_rule", ["分数优先，遵循志愿", "一次性投档"]),
        ("xinjiang-2026-collection_count", ["各安排一次征集志愿", "collection_count: 1"]),
        ("xinjiang-2026-subject_mode", ["文史类 / 理工类", "subject_mode: 传统"]),
        ("xinjiang-2026-exam_subject_total", ["总分750分", "exam_subject_total: 750"]),
        ("xinjiang-2026-official_url", ["https://www.xjzk.gov.cn/", "新疆教育考试院官网"]),
    ],
)
def test_xinjiang_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "xinjiang" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("tianjin-2026-mode", ["院校专业组", "mode: 院校专业组"]),
        ("tianjin-2026-batch", ["普通本科批次（含A、B阶段）", "batch: 本科批"]),
        ("tianjin-2026-max_volunteers", ["50个院校专业组", "max_volunteers: 50"]),
        ("tianjin-2026-max_majors_per_group", ["6个专业志愿", "max_majors_per_group: 6"]),
        ("tianjin-2026-has_adjustment", ["服从调剂专业志愿", "has_adjustment: true"]),
        ("tianjin-2026-adjustment_scope", ["院校专业组", "adjustment_scope: 组内专业"]),
        (
            "tianjin-2026-retrieval_rule",
            ["一次投档、不再补档", "retrieval_rule: 分数优先、遵循志愿、一次投档"],
        ),
        ("tianjin-2026-collection_count", ["两次填报、四次征询", "collection_count: 2"]),
        ("tianjin-2026-subject_mode", ["统一高考科目为语文、数学、外语3门", "subject_mode: 3+3"]),
        ("tianjin-2026-exam_subject_total", ["高考总成绩满分值为750分", "exam_subject_total: 750"]),
        ("tianjin-2026-official_url", ["www.zhaokao.net", "官方信息"]),
    ],
)
def test_tianjin_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "tianjin" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("henan-2026-mode", ["院校专业组平行志愿", "mode: 院校专业组"]),
        ("henan-2026-batch", ["普通本科批", "batch: 本科批"]),
        ("henan-2026-max_volunteers", ["48个院校专业组志愿", "max_volunteers: 48"]),
        ("henan-2026-max_majors_per_group", ["6个专业志愿", "max_majors_per_group: 6"]),
        ("henan-2026-has_adjustment", ["是否同意专业调剂选项", "has_adjustment: true"]),
        ("henan-2026-adjustment_scope", ["院校专业组", "adjustment_scope: 组内专业"]),
        ("henan-2026-retrieval_rule", ["分数优先、遵循志愿、一轮投档", "retrieval_rule: 分数优先、遵循志愿、一次投档"]),
        ("henan-2026-collection_count", ["公开征集志愿", "collection_count: null"]),
        ("henan-2026-subject_mode", ["从历史和物理2门首选科目中任选1门", "subject_mode: 3+1+2"]),
        ("henan-2026-exam_subject_total", ["满分750分", "exam_subject_total: 750"]),
        ("henan-2026-official_url", ["https://www.haeea.cn", "正式填报志愿时"]),
    ],
)
def test_henan_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "henan" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("chongqing-2026-mode", ["专业平行志愿以", "mode: 专业+学校"]),
        ("chongqing-2026-batch", ["本科批", "batch: 本科批"]),
        ("chongqing-2026-max_volunteers", ["96个专业平行志愿", "max_volunteers: 96"]),
        ("chongqing-2026-max_majors_per_group", ["1个专业（类）+1个学校", "max_majors_per_group: 1"]),
        ("chongqing-2026-has_adjustment", ["是否服从专业调剂选项", "has_adjustment: false"]),
        ("chongqing-2026-adjustment_scope", ["是否服从专业调剂选项", "adjustment_scope: 无"]),
        (
            "chongqing-2026-retrieval_rule",
            ["分数优先、遵循志愿、一轮投档", "retrieval_rule: 分数优先、遵循志愿、一次投档"],
        ),
        ("chongqing-2026-collection_count", ["各批次未完成招生计划并组织进行征集志愿", "collection_count: null"]),
        ("chongqing-2026-subject_mode", ["物理、历史为首选科目", "subject_mode: 3+1+2"]),
        ("chongqing-2026-exam_subject_total", ["总分满分为 750 分", "exam_subject_total: 750"]),
        ("chongqing-2026-official_url", ["指定网站", "www.cqksy.cn"]),
    ],
)
def test_chongqing_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "chongqing" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("beijing-2026-mode", ["院校专业组", "选考科目"]),
        ("beijing-2026-batch", ["本科普通批", "统考考生"]),
        ("beijing-2026-max_volunteers", ["30个志愿", "本科普通批"]),
        ("beijing-2026-max_majors_per_group", ["6个志愿专业", "专业6"]),
        ("beijing-2026-has_adjustment", ["是否服从", "调剂"]),
        ("beijing-2026-adjustment_scope", ["专业组内调剂", "院校内专业调剂"]),
        ("beijing-2026-retrieval_rule", ["分数优先", "一次性投档"]),
        ("beijing-2026-collection_count", ["动态安排", "下一批次录取开始前"]),
        ("beijing-2026-subject_mode", ["自主选择3门", "语文、数学、外语3门"]),
        ("beijing-2026-exam_subject_total", ["750分", "每科目满分100分"]),
        ("beijing-2026-official_url", ["www.bjeea.cn", "北京教育考试院"]),
    ],
)
def test_beijing_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "beijing" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("hainan-2026-mode", ["院校专业组", "基本单位"]),
        ("hainan-2026-batch", ["本科批次", "本科普通部分"]),
        ("hainan-2026-max_volunteers", ["30个院校专业组志愿", "本科普通批"]),
        ("hainan-2026-max_majors_per_group", ["6个专业志愿", "服从专业调剂志愿"]),
        ("hainan-2026-has_adjustment", ["服从专业调剂志愿", "是否愿意服从"]),
        ("hainan-2026-adjustment_scope", ["院校专业组的其他专业", "组内专业"]),
        ("hainan-2026-retrieval_rule", ["从高分到低分", "不再进行检索和投档"]),
        ("hainan-2026-collection_count", ["二轮征集志愿", "collection_count: 2"]),
        ("hainan-2026-subject_mode", ["语文、数学、外语3个科目", "选择性考试3个科目"]),
        ("hainan-2026-exam_subject_total", ["高考文化课成绩/900", "exam_subject_total: 900"]),
        ("hainan-2026-official_url", ["ea.hainan.gov.cn", "海南省考试局"]),
    ],
)
def test_hainan_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "hainan" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("fujian-2026-mode", ["院校专业组平行志愿投档模式", "院校专业组"]),
        ("fujian-2026-batch", ["普通类。设本科提前批、本科批", "本科批"]),
        ("fujian-2026-max_volunteers", ["50个平行且有顺序排列的院校专业组志愿", "max_volunteers: 50"]),
        ("fujian-2026-max_majors_per_group", ["6个专业志愿", "是否服从专业调剂栏目"]),
        ("fujian-2026-has_adjustment", ["是否服从专业调剂栏目", "has_adjustment: true"]),
        ("fujian-2026-adjustment_scope", ["院校专业组志愿", "组内专业"]),
        ("fujian-2026-retrieval_rule", ["高考总成绩从高分到低分", "一经投档、录取"]),
        ("fujian-2026-collection_count", ["2次征求志愿", "collection_count: 2"]),
        ("fujian-2026-subject_mode", ["首选科目（物理或历史）", "再选科目单科次高成绩"]),
        ("fujian-2026-exam_subject_total", ["文考总分满分750分", "exam_subject_total: 750"]),
        ("fujian-2026-official_url", ["eeafj.cn", "福建省教育考试院"]),
    ],
)
def test_fujian_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "fujian" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("sichuan-2026-mode", ["院校专业组方式设置志愿", "一个独立的志愿"]),
        ("sichuan-2026-batch", ["普通类共设置4个批次", "本科批次"]),
        ("sichuan-2026-max_volunteers", ["设置45个院校专业组志愿", "max_volunteers: 45"]),
        ("sichuan-2026-max_majors_per_group", ["6个专业志愿", "是否服从专业调剂选项"]),
        ("sichuan-2026-has_adjustment", ["是否服从专业调剂选项", "has_adjustment: true"]),
        ("sichuan-2026-adjustment_scope", ["一个院校专业组即为一个独立的志愿", "组内专业"]),
        ("sichuan-2026-retrieval_rule", ["位次优先、遵循志愿、一轮投档", "平行志愿只实行一轮投档"]),
        ("sichuan-2026-collection_count", ["collection_count: null", "征集志愿的填报办法根据录取实际情况另文通知"]),
        ("sichuan-2026-subject_mode", ["“3+1+2”模式", "首选科目"]),
        ("sichuan-2026-exam_subject_total", ["满分750分", "每门满分150分"]),
        ("sichuan-2026-official_url", ["sceea.cn", "四川省教育考试院"]),
    ],
)
def test_sichuan_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "sichuan" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("jiangxi-2026-mode", ["院校专业组", "一个独立的志愿"]),
        ("jiangxi-2026-batch", ["提前本科批次", "高职（专科）批次"]),
        ("jiangxi-2026-max_volunteers", ["45个“院校专业组”", "max_volunteers: 45"]),
        ("jiangxi-2026-max_majors_per_group", ["6个专业志愿", "max_majors_per_group: 6"]),
        ("jiangxi-2026-has_adjustment", ["是否服从专业调剂", "has_adjustment: true"]),
        ("jiangxi-2026-adjustment_scope", ["每个组内包含数量不等的专业", "组内专业"]),
        ("jiangxi-2026-retrieval_rule", ["平行志愿投档的统一录取模式", "分数优先、遵循志愿、一次投档"]),
        ("jiangxi-2026-collection_count", ["安排2次征集志愿", "collection_count: 2"]),
        ("jiangxi-2026-subject_mode", ["“3+1+2”的模式", "首选科目历史、物理"]),
        ("jiangxi-2026-exam_subject_total", ["总分为750分", "exam_subject_total: 750"]),
        ("jiangxi-2026-official_url", ["jxeea.cn", "江西省教育考试院"]),
    ],
)
def test_jiangxi_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "jiangxi" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("gansu-2026-mode", ["院校专业组", "首选科目为物理"]),
        ("gansu-2026-batch", ["本科批", "高职（专科）批"]),
        ("gansu-2026-max_volunteers", ["45个院校专业组志愿", "max_volunteers: 45"]),
        ("gansu-2026-max_majors_per_group", ["6个专业选项", "max_majors_per_group: 6"]),
        ("gansu-2026-has_adjustment", ["服从专业调剂选项", "has_adjustment: true"]),
        ("gansu-2026-adjustment_scope", ["每个院校专业组内", "组内专业"]),
        ("gansu-2026-retrieval_rule", ["分数优先，遵循志愿，一轮投档", "首选科目单科成绩"]),
        ("gansu-2026-collection_count", ["征集2次", "collection_count: 2"]),
        ("gansu-2026-subject_mode", ["3+1+2", "首选科目"]),
        ("gansu-2026-exam_subject_total", ["exam_subject_total: 750", "再选科目"]),
        ("gansu-2026-official_url", ["ganseea.cn", "甘肃省教育考试院"]),
    ],
)
def test_gansu_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "gansu" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("jiangsu-2026-mode", ["院校专业组", "选考科目要求"]),
        ("jiangsu-2026-batch", ["本科院校专业组志愿", "普通类本科批次"]),
        ("jiangsu-2026-max_volunteers", ["20或40个院校专业组志愿", "40"]),
        ("jiangsu-2026-max_majors_per_group", ["6个专业志愿", "专业服从调剂志愿"]),
        ("jiangsu-2026-has_adjustment", ["1个专业服从调剂志愿", "调剂"]),
        ("jiangsu-2026-adjustment_scope", ["院校专业组内", "不会被录取到其他院校专业组"]),
        ("jiangsu-2026-retrieval_rule", ["按分排序", "不再补投"]),
        ("jiangsu-2026-collection_count", ["collection_count: null", "专科补录"]),
        ("jiangsu-2026-subject_mode", ["3+1+2", "首选科目"]),
        ("jiangsu-2026-official_url", ["https://www.jseea.cn/", "江苏省教育考试院"]),
        ("jiangsu-2026-exam_subject_total", ["750分", "每门150分"]),
    ],
)
def test_jiangsu_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "jiangsu" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("guizhou-2026-mode", ["专业（类）平行志愿", "1个专业（类）+1个院校"]),
        ("guizhou-2026-batch", ["本科批", "设置本科提前批、本科批"]),
        ("guizhou-2026-max_volunteers", ["设置96个专业（类）平行志愿", "max_volunteers: 96"]),
        ("guizhou-2026-max_majors_per_group", ["1个专业（类）+1个院校", "max_majors_per_group: 1"]),
        ("guizhou-2026-has_adjustment", ["不设是否服从专业调剂选项", "has_adjustment: false"]),
        ("guizhou-2026-adjustment_scope", ["不设是否服从专业调剂选项", "adjustment_scope: 无"]),
        ("guizhou-2026-retrieval_rule", ["分数优先、遵循志愿、一轮投档", "一次投档"]),
        ("guizhou-2026-collection_count", ["本科批第2次征集志愿", "collection_count: 3"]),
        ("guizhou-2026-subject_mode", ["3+1+2", "物理、历史2门科目中选择1门首选科目"]),
        ("guizhou-2026-exam_subject_total", ["×750", "exam_subject_total: 750"]),
        ("guizhou-2026-official_url", ["https://zsksy.guizhou.gov.cn/", "贵州省招生考试院"]),
    ],
)
def test_guizhou_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "guizhou" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("liaoning-2026-mode", ["专业平行志愿", "专业+学校"]),
        ("liaoning-2026-batch", ["本科批", "普通类录取批次划分为"]),
        ("liaoning-2026-max_volunteers", ["112个“专业+学校”志愿", "max_volunteers: 112"]),
        ("liaoning-2026-max_majors_per_group", ["1个“专业+学校”为1个志愿", "max_majors_per_group: 1"]),
        ("liaoning-2026-has_adjustment", ["不存在专业服从调剂", "has_adjustment: false"]),
        ("liaoning-2026-adjustment_scope", ["取消了专业调剂", "adjustment_scope: 无"]),
        ("liaoning-2026-retrieval_rule", ["分数优先、遵循志愿、一轮投档", "一次投档"]),
        ("liaoning-2026-collection_count", ["第二次“征集志愿”投档最低分", "collection_count: 2"]),
        ("liaoning-2026-subject_mode", ["3+1+2", "历史、物理2门科目中自主选择1门"]),
        ("liaoning-2026-exam_subject_total", ["总分为 750分", "exam_subject_total: 750"]),
        ("liaoning-2026-official_url", ["https://www.lnzsks.com/", "唯一网站"]),
    ],
)
def test_liaoning_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "liaoning" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("jilin-2026-mode", ["院校专业组平行志愿", "mode: 院校专业组"]),
        ("jilin-2026-batch", ["普通类分为提前批、本科批及专科批三个批次", "batch: 本科批"]),
        ("jilin-2026-max_volunteers", ["本科批设50个院校专业组平行志愿", "max_volunteers: 50"]),
        ("jilin-2026-max_majors_per_group", ["设置6个专业志愿", "max_majors_per_group: 6"]),
        ("jilin-2026-has_adjustment", ["是否服从专业调剂选项", "has_adjustment: true"]),
        ("jilin-2026-adjustment_scope", ["该专业组内所有专业均可接受", "adjustment_scope: 组内专业"]),
        ("jilin-2026-retrieval_rule", ["平行志愿实行一轮投档", "一次投档"]),
        ("jilin-2026-collection_count", ["本科批征集志愿（第二轮）考生须知", "collection_count: 2"]),
        ("jilin-2026-subject_mode", ["物理、历史2门科目中自主选择1门", "subject_mode: 3+1+2"]),
        ("jilin-2026-exam_subject_total", ["以750分为高考满分计算", "exam_subject_total: 750"]),
        ("jilin-2026-official_url", ["https://www.jleea.com.cn/", "吉林省教育考试院"]),
    ],
)
def test_jilin_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "jilin" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("heilongjiang-2026-mode", ["院校专业组", "mode: 院校专业组"]),
        ("heilongjiang-2026-batch", ["合并为普通本科批", "batch: 本科批"]),
        ("heilongjiang-2026-max_volunteers", ["设40个院校专业组志愿", "max_volunteers: 40"]),
        ("heilongjiang-2026-max_majors_per_group", ["下设6个专业志愿", "max_majors_per_group: 6"]),
        ("heilongjiang-2026-has_adjustment", ["是否服从专业调剂选项", "has_adjustment: true"]),
        ("heilongjiang-2026-adjustment_scope", ["院校专业组内未录满专业", "adjustment_scope: 组内专业"]),
        ("heilongjiang-2026-retrieval_rule", ["分数优先、遵循志愿", "一次性投档"]),
        ("heilongjiang-2026-collection_count", ["普通本科批第二次征集志愿", "collection_count: 2"]),
        ("heilongjiang-2026-subject_mode", ["“3+1+2”模式", "subject_mode: 3+1+2"]),
        ("heilongjiang-2026-exam_subject_total", ["满分750分", "exam_subject_total: 750"]),
        ("heilongjiang-2026-official_url", ["https://www.lzk.hl.cn/", "黑龙江省招生考试信息港"]),
    ],
)
def test_heilongjiang_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "heilongjiang" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("guangxi-2026-mode", ["院校专业组", "mode: 院校专业组"]),
        ("guangxi-2026-batch", ["本科普通批", "batch: 本科批"]),
        ("guangxi-2026-max_volunteers", ["设置40个院校专业组志愿", "max_volunteers: 40"]),
        ("guangxi-2026-max_majors_per_group", ["设置20个专业", "max_majors_per_group: 20"]),
        ("guangxi-2026-has_adjustment", ["是否服从专业组内专业调剂", "has_adjustment: true"]),
        ("guangxi-2026-adjustment_scope", ["院校专业组内未录满专业", "adjustment_scope: 组内专业"]),
        ("guangxi-2026-retrieval_rule", ["分数优先、遵循志愿", "1：1的比例"]),
        ("guangxi-2026-collection_count", ["根据录取时计划完成情况确定是否征集志愿", "collection_count: null"]),
        ("guangxi-2026-subject_mode", ["“3+1+2”模式", "subject_mode: 3+1+2"]),
        ("guangxi-2026-exam_subject_total", ["满分750分", "exam_subject_total: 750"]),
        ("guangxi-2026-official_url", ["https://www.gxeea.cn/", "填报志愿的唯一网站"]),
    ],
)
def test_guangxi_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "guangxi" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("qinghai-2026-mode", ["专业（类）+院校", "mode: 专业+学校"]),
        ("qinghai-2026-batch", ["本科批次", "batch: 本科批"]),
        ("qinghai-2026-max_volunteers", ["填报96个专业（类）平行志愿", "max_volunteers: 96"]),
        (
            "qinghai-2026-max_majors_per_group",
            ["1个专业（类）+1个院校", "max_majors_per_group: 1"],
        ),
        ("qinghai-2026-has_adjustment", ["不设是否服从院校专业调剂选项", "has_adjustment: false"]),
        ("qinghai-2026-adjustment_scope", ["不设是否服从院校专业调剂选项", "adjustment_scope: 无"]),
        ("qinghai-2026-retrieval_rule", ["分数优先、遵循志愿、一轮投档", "一次投档"]),
        ("qinghai-2026-collection_count", ["可实行多次志愿征集", "collection_count: null"]),
        ("qinghai-2026-subject_mode", ["“3+1+2”考试模式", "subject_mode: 3+1+2"]),
        ("qinghai-2026-exam_subject_total", ["满分750分", "exam_subject_total: 750"]),
        ("qinghai-2026-official_url", ["https://www.qhjyks.com/", "唯一网站"]),
    ],
)
def test_qinghai_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "qinghai" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("xizang-2026-mode", ["3＋文科综合/理科综合", "mode: 传统"]),
        ("xizang-2026-batch", ["本科二批", "batch: 本科二批"]),
        ("xizang-2026-max_volunteers", ["共 10 个并列的院校志愿", "max_volunteers: 10"]),
        ("xizang-2026-max_majors_per_group", ["每个院校设置 4 个专业志愿", "max_majors_per_group: 4"]),
        ("xizang-2026-has_adjustment", ["专业服从调剂志愿", "has_adjustment: true"]),
        ("xizang-2026-adjustment_scope", ["不设院校服从调剂志愿", "adjustment_scope: 全部专业"]),
        ("xizang-2026-retrieval_rule", ["投档原则为“分数优先，遵循志愿”", "一次投档"]),
        ("xizang-2026-collection_count", ["视情况进行一次或多次", "collection_count: null"]),
        ("xizang-2026-subject_mode", ["文史类", "subject_mode: 传统"]),
        ("xizang-2026-exam_subject_total", ["高考卷面总分 750 分", "exam_subject_total: 750"]),
        ("xizang-2026-official_url", ["http://zsks.edu.xizang.gov.cn/", "西藏教育考试院网址"]),
    ],
)
def test_xizang_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "xizang" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("zhejiang-2026-mode", ["专业平行志愿", "1所学校的1个专业"]),
        ("zhejiang-2026-batch", ["普通类分提前录取和平行录取", "普通类第一段平行志愿"]),
        ("zhejiang-2026-max_volunteers", ["80个志愿", "每段均可填报不超过80个志愿"]),
        ("zhejiang-2026-max_majors_per_group", ["1个专业（类）", "1个独立的志愿单位"]),
        ("zhejiang-2026-has_adjustment", ["不存在专业服从调剂", "调剂"]),
        (
            "zhejiang-2026-adjustment_scope",
            ["不存在专业服从调剂", "其他专业平行志愿也不能再投档"],
        ),
        ("zhejiang-2026-retrieval_rule", ["分数优先、遵循志愿", "一轮投档"]),
        ("zhejiang-2026-collection_count", ["8月3日8:30—17:30", "征求志愿"]),
        ("zhejiang-2026-subject_mode", ["3门必考科目和3门选考科目", "选择3门"]),
        ("zhejiang-2026-official_url", ["www.zjzs.net", "唯一网站"]),
        ("zhejiang-2026-exam_subject_total", ["考生满分750分", "每门满分150分"]),
    ],
)
def test_zhejiang_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "zhejiang" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("shanghai-2026-mode", ["院校专业组", "本科阶段"]),
        ("shanghai-2026-batch", ["本科阶段志愿", "普通批次"]),
        ("shanghai-2026-max_volunteers", ["24个平行志愿", "本科普通批次"]),
        ("shanghai-2026-max_majors_per_group", ["4个专业志愿", "院校专业组志愿"]),
        ("shanghai-2026-has_adjustment", ["愿否服从专业志愿调剂", "调剂"]),
        ("shanghai-2026-adjustment_scope", ["院校专业组内", "专业调剂录取"]),
        ("shanghai-2026-retrieval_rule", ["分数优先", "一轮投档"]),
        ("shanghai-2026-collection_count", ["两次征求志愿", "collection_count: 2"]),
        ("shanghai-2026-subject_mode", ["语文、数学、外语3门", "自主选择3门"]),
        ("shanghai-2026-official_url", ["www.shmeea.edu.cn", "上海招考热线"]),
        ("shanghai-2026-exam_subject_total", ["总成绩为660分", "每门满分70分"]),
    ],
)
def test_shanghai_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "shanghai" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("anhui-2026-mode", ["院校专业组", "基本单位"]),
        ("anhui-2026-batch", ["普通本科批次", "本科批"]),
        ("anhui-2026-max_volunteers", ["45个院校专业组志愿", "普通本科批次"]),
        ("anhui-2026-max_majors_per_group", ["6个专业志愿", "专业服从志愿"]),
        ("anhui-2026-has_adjustment", ["专业服从志愿", "普通本科批次"]),
        ("anhui-2026-adjustment_scope", ["院校专业组内", "可调剂录取"]),
        ("anhui-2026-retrieval_rule", ["从高到低排序", "可视情进行多轮次投档"]),
        ("anhui-2026-collection_count", ["collection_count: 1", "7月31日10:00至16:00"]),
        ("anhui-2026-subject_mode", ["3+1+2", "首选科目"]),
        ("anhui-2026-official_url", ["www.ahzsks.cn", "安徽省教育招生考试院"]),
        ("anhui-2026-exam_subject_total", ["满分为750分", "选考科目满分均为100分"]),
    ],
)
def test_anhui_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "anhui" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("shandong-2026-mode", ["专业（专业类）+学校", "平行志愿模式"]),
        ("shandong-2026-batch", ["普通类分为提前批和常规批", "常规批"]),
        ("shandong-2026-max_volunteers", ["96个", "每次填报志愿"]),
        ("shandong-2026-max_majors_per_group", ["1个“专业（专业类）+学校”", "1个志愿"]),
        ("shandong-2026-has_adjustment", ["无调剂", "专业服从调剂"]),
        ("shandong-2026-adjustment_scope", ["组内专业调剂", "无"]),
        ("shandong-2026-retrieval_rule", ["分数优先", "志愿顺序前者优先投档"]),
        ("shandong-2026-collection_count", ["安排3次志愿填报", "collection_count: 2"]),
        ("shandong-2026-subject_mode", ["3+3", "夏季高考"]),
        ("shandong-2026-official_url", ["山东省教育招生考试院官网", "sdzk.cn"]),
        ("shandong-2026-exam_subject_total", ["总成绩为750分", "750分"]),
    ],
)
def test_shandong_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "shandong" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("guangdong-2026-mode", ["院校专业组模式", "组内专业志愿"]),
        ("guangdong-2026-batch", ["本科和专科录取批次", "本科批"]),
        ("guangdong-2026-max_volunteers", ["45 个院校专业组志愿", "普通类"]),
        ("guangdong-2026-max_majors_per_group", ["6 个专业志愿", "是否服从专业调剂"]),
        ("guangdong-2026-has_adjustment", ["是否服从专业调剂选项", "has_adjustment: true"]),
        ("guangdong-2026-adjustment_scope", ["组内专业", "其他院校专业组无效"]),
        ("guangdong-2026-retrieval_rule", ["分数优先、遵循志愿", "一次性投档"]),
        ("guangdong-2026-collection_count", ["collection_count: null", "多次征集志愿"]),
        ("guangdong-2026-subject_mode", ["3+1+2", "选择性考试科目"]),
        ("guangdong-2026-official_url", ["广东省教育考试院", "https://eea.gd.gov.cn/"]),
        ("guangdong-2026-exam_subject_total", ["750 分", "高考文化总成绩卷面满分值"]),
    ],
)
def test_guangdong_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "guangdong" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("hubei-2026-mode", ["院校专业组", "高考志愿设置"]),
        ("hubei-2026-batch", ["本科普通批", "本科批"]),
        ("hubei-2026-max_volunteers", ["45个院校专业组志愿", "本科普通批"]),
        ("hubei-2026-max_majors_per_group", ["不超过6个专业", "是否服从专业调剂"]),
        ("hubei-2026-has_adjustment", ["是否服从专业调剂", "has_adjustment: true"]),
        (
            "hubei-2026-adjustment_scope",
            ["只能在这个院校专业组所包含的专业中进行调剂", "不能跨院校专业组调剂专业"],
        ),
        (
            "hubei-2026-retrieval_rule",
            ["分数优先、遵循志愿、一次投档、不再补档", "只能参加征集志愿或后续批次录取"],
        ),
        ("hubei-2026-collection_count", ["本科普通批（第一次）", "collection_count: 2"]),
        ("hubei-2026-subject_mode", ["3+1+2", "“1+2”"]),
        ("hubei-2026-official_url", ["湖北省教育考试院", "https://www.hbea.edu.cn/"]),
        ("hubei-2026-exam_subject_total", ["满分750分", "每科满分150分"]),
    ],
)
def test_hubei_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "hubei" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"


@pytest.mark.parametrize(
    "evidence_id,expected_keywords",
    [
        ("hebei-2026-mode", ["专业（类）+学校", "平行志愿模式"]),
        ("hebei-2026-batch", ["本科批", "普通类本科批"]),
        ("hebei-2026-max_volunteers", ["96 个“院校+专业（类）”", "max_volunteers: 96"]),
        ("hebei-2026-max_majors_per_group", ["院校代号及名称", "max_majors_per_group: 1"]),
        ("hebei-2026-has_adjustment", ["专业调剂", "has_adjustment: false"]),
        ("hebei-2026-adjustment_scope", ["专业调剂", "adjustment_scope: 无"]),
        ("hebei-2026-collection_count", ["本科批第一次志愿征集", "collection_count: 2"]),
        ("hebei-2026-official_url", ["http://www.hebeea.edu.cn", "河北省教育考试院"]),
        ("hebei-2026-retrieval_rule", ["分数优先、遵循志愿、一次投档、不再补档", "一旦投档"]),
        ("hebei-2026-subject_mode", ["统一高考", "再选科目（化学、地理、生物、思想政治）"]),
        ("hebei-2026-exam_subject_total", ["高考文化总成绩", "×750"]),
    ],
)
def test_hebei_completed_evidence_files_contain_expected_keywords(
    evidence_id: str, expected_keywords: list[str]
) -> None:
    path = _evidence_root() / "hebei" / f"{evidence_id}.md"
    assert path.is_file(), f"missing evidence file: {path}"
    text = path.read_text(encoding="utf-8")
    for keyword in expected_keywords:
        assert keyword in text, f"{evidence_id}.md must mention '{keyword}'"
