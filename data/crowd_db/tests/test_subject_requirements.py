"""选科匹配度验证测试（Phase 0 - P0 级风险修复）。

目的：
- 锁死 7 个新高考 S 级省的 subject_requirements 覆盖率 100%
- 验证字段结构正确（preferred_subject / reselect_subject / note）
- 防止未来数据回退导致推荐错误

新高考 S 级省：湖南/广东/江苏/山东/河北/浙江/福建
"""

from __future__ import annotations

import pytest

from data.crowd_db.loader import CrowdDBLoader


NEW_GAOKAO_S_PROVINCES = frozenset({
    "湖南",
    "广东",
    "江苏",
    "山东",
    "河北",
    "浙江",
    "福建",
})

VALID_PREFERRED_SUBJECTS = {"物理", "历史"}
VALID_RESELECT_SUBJECTS = {"化学", "生物", "政治", "地理"}


@pytest.fixture(scope="module")
def loader() -> CrowdDBLoader:
    return CrowdDBLoader(warn_low_confidence=False)


def _all_recommendations(data: dict):
    for sr in data.get("score_ranges", []):
        for rec in sr.get("recommendations", []):
            yield rec


def test_new_gaokao_s_provinces_have_full_subject_requirements_coverage(
    loader: CrowdDBLoader,
):
    """7 个新高考 S 级省 100% recs 必须有 subject_requirements。"""
    for province in NEW_GAOKAO_S_PROVINCES:
        data = loader.load_province(province)
        assert data is not None, f"{province} 数据不存在"
        recs = list(_all_recommendations(data))
        assert recs, f"{province} 无推荐数据"
        missing = [rec for rec in recs if rec.get("subject_requirements") is None]
        assert missing == [], (
            f"{province} 存在 {len(missing)} 条 rec 缺失 subject_requirements，"
            f"应 100% 覆盖。"
        )


def test_subject_requirements_structure_is_valid(loader: CrowdDBLoader):
    """subject_requirements 结构必须完整且取值合法。"""
    for province in NEW_GAOKAO_S_PROVINCES:
        data = loader.load_province(province)
        assert data is not None
        for rec in _all_recommendations(data):
            sr = rec.get("subject_requirements")
            assert isinstance(sr, dict), (
                f"{province}/{rec.get('name')}/{rec.get('major')} subject_requirements 应为 dict"
            )
            assert sr.get("preferred_subject") in VALID_PREFERRED_SUBJECTS, (
                f"{province}/{rec.get('name')}/{rec.get('major')} preferred_subject="
                f"{sr.get('preferred_subject')} 非法"
            )
            reselect = sr.get("reselect_subject")
            assert isinstance(reselect, list), (
                f"{province}/{rec.get('name')}/{rec.get('major')} reselect_subject 应为 list"
            )
            invalid = [s for s in reselect if s not in VALID_RESELECT_SUBJECTS]
            assert invalid == [], (
                f"{province}/{rec.get('name')}/{rec.get('major')} reselect_subject "
                f"含非法值: {invalid}"
            )
            note = sr.get("note")
            assert isinstance(note, str) and note.strip(), (
                f"{province}/{rec.get('name')}/{rec.get('major')} note 应为非空字符串"
            )


def test_program_type_placeholder_exists(loader: CrowdDBLoader):
    """为后续 Phase 1 预铺：7 省所有 rec 都应存在 program_type 字段（可为 null）。"""
    for province in NEW_GAOKAO_S_PROVINCES:
        data = loader.load_province(province)
        assert data is not None
        for rec in _all_recommendations(data):
            assert "program_type" in rec, (
                f"{province}/{rec.get('name')}/{rec.get('major')} 缺失 program_type 字段"
            )


def test_business_rule_history_subjects_not_marked_physics(loader: CrowdDBLoader):
    """关键业务规则：文史类专业不得错误标为物理优先。"""
    historical_majors = {
        "社会工作",
        "会计学",
        "汉语言文学",
        "法学",
        "历史学",
        "英语",
        "教育学",
    }
    for province in NEW_GAOKAO_S_PROVINCES:
        data = loader.load_province(province)
        assert data is not None
        for rec in _all_recommendations(data):
            major = rec.get("major", "")
            if major in historical_majors:
                sr = rec.get("subject_requirements") or {}
                assert sr.get("preferred_subject") == "历史", (
                    f"{province}/{rec.get('name')}/{major} 应标为历史优先，"
                    f"实际 {sr.get('preferred_subject')}"
                )
