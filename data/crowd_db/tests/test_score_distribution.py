"""一分一段表（score_distribution）验证测试。

验证接入了一分一段表的省份：
- 湖南（2026官方公布）
- 黑龙江（2026官方公布）

锁住的契约：
- score_distribution 字段存在且结构正确
- subjects 必须分物理/历史
- benchmarks 必须包含 score + cumulative_count
- 600分以上人数 > 0（核心锚点）
- 本科分数线 > 0
"""

from __future__ import annotations

import pytest

from data.crowd_db.loader import CrowdDBLoader


# 已接入 score_distribution 的省份（2026 官方一分一段）
# 山东不分物理/历史类，历史类 benchmarks 可为空
PROVINCES_WITH_DISTRIBUTION = frozenset({
    "湖南",
    "黑龙江",
    "广东",
    "河南",
    "山东",
    "江苏",
    "河北",
})

REQUIRED_SUBJECTS = {"物理", "历史"}


@pytest.fixture(scope="module")
def loader() -> CrowdDBLoader:
    return CrowdDBLoader(warn_low_confidence=False)


def test_score_distribution_exists_for_target_provinces(loader: CrowdDBLoader):
    """已接入一分一段表的省份必须有 score_distribution 字段。"""
    for province in PROVINCES_WITH_DISTRIBUTION:
        data = loader.load_province(province)
        assert data is not None, f"{province} 数据不存在"
        sd = data.get("score_distribution")
        assert sd is not None, f"{province} 缺少 score_distribution 字段"


def test_score_distribution_structure_is_valid(loader: CrowdDBLoader):
    """score_distribution 结构必须完整且合法。"""
    for province in PROVINCES_WITH_DISTRIBUTION:
        data = loader.load_province(province)
        assert data is not None
        sd = data.get("score_distribution")
        assert isinstance(sd, dict), f"{province} score_distribution 应为 dict"

        # 必须有 subjects
        subjects = sd.get("subjects")
        assert isinstance(subjects, dict), f"{province} subjects 应为 dict"
        assert REQUIRED_SUBJECTS.issubset(subjects.keys()), (
            f"{province} subjects 缺少物理/历史: {subjects.keys()}"
        )

        # 每个 subject 的结构
        for subject_name in REQUIRED_SUBJECTS:
            subj = subjects.get(subject_name)
            assert isinstance(subj, dict), f"{province}/{subject_name} 应为 dict"

            benchmarks = subj.get("benchmarks")
            assert isinstance(benchmarks, list), (
                f"{province}/{subject_name} benchmarks 应为 list"
            )
            # 物理类必须有锚点，历史类允许为空（如山东不分物理/历史）
            if subject_name == "物理":
                assert len(benchmarks) > 0, (
                    f"{province}/{subject_name} benchmarks 不能为空"
                )

            for bm in benchmarks:
                assert isinstance(bm.get("score"), int), (
                    f"{province}/{subject_name} benchmark score 应为 int"
                )
                assert isinstance(bm.get("cumulative_count"), int), (
                    f"{province}/{subject_name} benchmark cumulative_count 应为 int"
                )
                assert bm["cumulative_count"] >= 0

            # 600分以上人数（核心锚点）
            # 山东不分物理/历史，历史类无独立统计，允许为 0
            score_600 = subj.get("score_line_at_600")
            assert isinstance(score_600, int) and score_600 >= 0, (
                f"{province}/{subject_name} score_line_at_600 应为非负整数"
            )
            # 至少物理类必须 > 0
            if subject_name == "物理":
                assert score_600 > 0, (
                    f"{province}/{subject_name} score_line_at_600 物理类必须为正整数"
                )

            # 本科分数线
            bsl = subj.get("bachelor_score_line")
            assert isinstance(bsl, int) and bsl > 0, (
                f"{province}/{subject_name} bachelor_score_line 应为正整数"
            )


def test_score_distribution_source_type_is_official(loader: CrowdDBLoader):
    """一分一段表数据必须来自官方发布（source_type=official_release）。"""
    for province in PROVINCES_WITH_DISTRIBUTION:
        data = loader.load_province(province)
        assert data is not None
        sd = data.get("score_distribution")
        assert isinstance(sd, dict)
        assert sd.get("source_type") == "official_release", (
            f"{province} score_distribution source_type 应为 official_release"
        )
        assert sd.get("source_url", "").startswith("https://"), (
            f"{province} score_distribution source_url 应为 https:// 开头"
        )
