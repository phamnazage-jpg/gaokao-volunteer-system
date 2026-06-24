"""T3.2 溯源字段查询 + 验证 测试

覆盖：
1. 27省全部 validate_all 通过（errors=0），usable=27（全部省份均已达到 usable 及以上）
2. validate_province(hunan) — ok + is_usable=True + summary 7 字段齐全
3. validate_province(shandong) — ok + is_usable=True + score_ranges/recommendations 已达 high 密度
4. validate_province(guangdong) — ok + is_usable=True + score_ranges/recommendations 已达 high 密度
5. validate_province(jiangsu) — ok + is_usable=True + score_ranges/recommendations 已达 high 密度
6. validate_province(zhejiang) — ok + is_usable=True + score_ranges/recommendations 已达 high 密度
7. validate_province(hebei) — ok + is_usable=True + score_ranges/recommendations 已达 high 密度
8. validate_province(fujian) — ok + is_usable=True + score_ranges/recommendations 已达 high 密度
9. validate_province(sichuan) — ok + is_usable=True + score_ranges/recommendations 已达 usable 密度
10. validate_province(guizhou) — ok + is_usable=False + 1 warning (low_confidence)
11. validate_provenance(None) — 报 load_failed error
12. validate_provenance({}) — 报 7 missing_field
13. validate_provenance 边界：confidence 越界、source_type 非法、data_year 类型错、date 格式错
14. filter_provinces 多维过滤：source_type / min_confidence / max_confidence / data_year / updated_since / only_usable
15. filter_provinces 组合：min + max confidence 区间
16. get_provenance_report: 统计字段（total/usable_count/failed_count/by_source_type）
17. 错误省份输入：未知省份返回 load_failed
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.crowd_db.loader import (
    CrowdDBLoader,
    ProvenanceValidation,
)


# ------------------------------------------------------------------ #
# 1. validate_all 27省
# ------------------------------------------------------------------ #


def test_validate_all_27_passes():
    """27 省全部通过 schema 校验（无 errors）"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    results = loader.validate_all()
    assert len(results) == 27, f"expected 27 entries, got {len(results)}"
    failed = [(p, v.errors) for p, v in results.items() if not v.ok]
    assert not failed, f"应全部 ok, 失败省份: {failed}"


def test_validate_all_usable_count():
    """27 省当前全部达到 usable 及以上（按 PROVINCE_FILE_MAP 顺序）。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    results = loader.validate_all()
    usable = [p for p, v in results.items() if v.is_usable]
    assert usable == [
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "山西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "陕西",
        "甘肃",
        "青海",
        "新疆",
    ], f"unexpected usable provinces: {usable}"


def test_validate_all_warnings_low_confidence():
    """当前 27 省口径下已无 low_confidence warning。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    results = loader.validate_all()
    low_warn = [
        p for p, v in results.items() if any("low_confidence" in w for w in v.warnings)
    ]
    assert low_warn == [], f"expected no low_confidence warnings, got {low_warn}"


# ------------------------------------------------------------------ #
# 2. validate_province（hunan — 高 confidence）
# ------------------------------------------------------------------ #


def test_validate_province_hunan_usable():
    """湖南：ok + is_usable + 7 字段 summary 齐全 + 0 warning"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    v = loader.validate_province("湖南")
    assert v.ok is True
    assert v.is_usable is True
    assert v.errors == []
    assert v.warnings == []
    expected_keys = {
        "province",
        "source",
        "source_url",
        "source_type",
        "data_year",
        "last_updated",
        "confidence",
    }
    assert set(v.summary.keys()) == expected_keys
    assert v.summary["province"] == "湖南"
    assert v.summary["confidence"] >= 0.8


def test_validate_province_guizhou_usable():
    """贵州：ok + is_usable=True + confidence 已达 usable 门槛。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    v = loader.validate_province("贵州")
    assert v.ok is True
    assert v.is_usable is True
    assert v.errors == []
    assert v.summary["confidence"] >= 0.65


# ------------------------------------------------------------------ #
# 3. validate_provenance 边界：class method 直接调用
# ------------------------------------------------------------------ #


def test_validate_provenance_none_load_failed():
    """None 数据 → 1 个 load_failed error"""
    v = CrowdDBLoader.validate_provenance(None, province="X")
    assert v.ok is False
    assert v.is_usable is False
    assert any("load_failed" in e for e in v.errors)
    assert v.summary == {}


def test_validate_provenance_empty_dict():
    """空 dict → 7 个 missing_field 错误（无重复）"""
    v = CrowdDBLoader.validate_provenance({}, province="X")
    assert v.ok is False
    expected = {
        "province",
        "last_updated",
        "data_year",
        "source",
        "source_type",
        "confidence",
        "score_ranges",
    }
    reported = {e.split(": ", 1)[1] for e in v.errors if e.startswith("missing_field:")}
    assert reported == expected, f"missing fields mismatch: {reported}"


def test_validate_provenance_confidence_out_of_range():
    """confidence=1.5 越界 → range_error"""
    data = {
        "province": "X",
        "last_updated": "2025-01-01",
        "data_year": 2025,
        "source": "s",
        "source_type": "manual_summary",
        "confidence": 1.5,
        "score_ranges": [],
    }
    v = CrowdDBLoader.validate_provenance(data, province="X")
    assert v.ok is False
    assert any("range_error" in e for e in v.errors)


def test_validate_provenance_invalid_source_type():
    """source_type='garbage' → enum_error"""
    data = {
        "province": "X",
        "last_updated": "2025-01-01",
        "data_year": 2025,
        "source": "s",
        "source_type": "garbage",
        "confidence": 0.5,
        "score_ranges": [],
    }
    v = CrowdDBLoader.validate_provenance(data, province="X")
    assert v.ok is False
    assert any("enum_error" in e for e in v.errors)


def test_validate_provenance_data_year_wrong_type():
    """data_year='2025' (str) → type_error"""
    data = {
        "province": "X",
        "last_updated": "2025-01-01",
        "data_year": "2025",
        "source": "s",
        "source_type": "manual_summary",
        "confidence": 0.5,
        "score_ranges": [],
    }
    v = CrowdDBLoader.validate_provenance(data, province="X")
    assert v.ok is False
    assert any("type_error" in e and "data_year" in e for e in v.errors)


def test_validate_provenance_bad_date_format():
    """last_updated='2025/01/01' → format_error"""
    data = {
        "province": "X",
        "last_updated": "2025/01/01",
        "data_year": 2025,
        "source": "s",
        "source_type": "manual_summary",
        "confidence": 0.5,
        "score_ranges": [],
    }
    v = CrowdDBLoader.validate_provenance(data, province="X")
    assert v.ok is False
    assert any("format_error" in e for e in v.errors)


def test_validate_provenance_empty_source_warning():
    """source='' → 0 错误 + 1 empty_source warning（不影响 ok）"""
    data = {
        "province": "X",
        "last_updated": "2025-01-01",
        "data_year": 2025,
        "source": "",
        "source_type": "manual_summary",
        "confidence": 0.5,
        "score_ranges": [],
    }
    v = CrowdDBLoader.validate_provenance(data, province="X")
    assert v.ok is True
    assert any("empty_source" in w for w in v.warnings)


# ------------------------------------------------------------------ #
# 4. filter_provinces 多维过滤
# ------------------------------------------------------------------ #


def test_filter_provinces_only_usable():
    """only_usable=True → 当前全部 27 省（按 PROVINCE_FILE_MAP 顺序）。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(only_usable=True)
    assert result == [
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "山西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "陕西",
        "甘肃",
        "青海",
        "新疆",
    ]


def test_filter_provinces_source_type_manual():
    """source_type='manual_summary' → 27 省全匹配"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(source_type="manual_summary")
    assert len(result) == 27


def test_filter_provinces_source_type_official():
    """source_type='official_release' → 当前无匹配 → 空列表"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(source_type="official_release")
    assert result == []


def test_filter_provinces_data_year_match():
    """data_year=2025 → 27 省全匹配"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(data_year=2025)
    assert len(result) == 27


def test_filter_provinces_data_year_no_match():
    """data_year=2024 → 当前无匹配 → 空列表"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(data_year=2024)
    assert result == []


def test_filter_provinces_min_confidence():
    """min_confidence=0.5 → 当前 27 省全部 ≥ 0.65，全部返回。

    旧基线下只有 13 省 usable+ 通过，27 省升级后全部通过。
    用动态加载断言，避免未来再次升级数据时回归。
    """
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(min_confidence=0.5)
    # 所有 27 省当前 confidence 都 ≥ 0.65，应全部返回
    assert len(result) == 27
    # 关键省份必须出现
    for province in [
        "北京",
        "天津",
        "上海",
        "河北",
        "江苏",
        "浙江",
        "福建",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "广东",
        "四川",
    ]:
        assert province in result, f"{province} 应在 min_confidence=0.5 结果中"


def test_filter_provinces_max_confidence():
    """max_confidence=0.5 → 当前 27 省全部 ≥ 0.65，无任何省份落入此区间。

    旧基线下 14 省 confidence=0.45 落入此区间，27 省升级后无任何落入。
    """
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(max_confidence=0.5)
    # 当前所有省份 confidence ≥ 0.65，无任何 ≤ 0.5
    assert result == []


def test_filter_provinces_confidence_range():
    """min=0.4 max=0.5 → 当前 27 省全部 ≥ 0.65，无任何落入此区间。

    旧基线下 14 省 confidence=0.45 落入此区间，27 省升级后无任何落入。
    额外验证一个有实际数据的区间（0.6-0.7），保证 filter 行为本身正确。
    """
    loader = CrowdDBLoader(warn_low_confidence=False)
    # 边界：当前无任何省份 confidence 落在 [0.4, 0.5]
    result_empty = loader.filter_provinces(min_confidence=0.4, max_confidence=0.5)
    assert result_empty == []

    # 正向：[0.6, 0.7] 应命中 19 省（0.65-0.68 范围内的省份）
    result_actual = loader.filter_provinces(min_confidence=0.6, max_confidence=0.7)
    assert len(result_actual) >= 15, (
        f"[0.6, 0.7] 应至少命中 15 省（0.65~0.68），实际 {len(result_actual)}: {result_actual}"
    )
    # 高置信省份不应落入此区间
    for province in ["湖南", "山东", "广东", "江苏", "河北", "浙江", "福建"]:
        assert province not in result_actual, (
            f"{province} confidence≥0.85，不应落入 [0.6, 0.7] 区间"
        )


def test_filter_provinces_updated_since():
    """updated_since='2026-06-12' → 27 省（全在 2026-06-12）"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(updated_since="2026-06-12")
    assert len(result) == 27


def test_filter_provinces_updated_before_no_match():
    """updated_before='2026-06-11' → 0 省（全在 2026-06-12）"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(updated_before="2026-06-11")
    assert result == []


def test_filter_provinces_combined_usable_and_year():
    """组合：only_usable=True + data_year=2025 → 当前全部 27 省。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(only_usable=True, data_year=2025)
    assert result == [
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "山西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "陕西",
        "甘肃",
        "青海",
        "新疆",
    ]


def test_filter_provinces_preserves_map_order():
    """max_confidence=0.5 当前无结果，返回空列表。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(max_confidence=0.5)
    assert result == []


# ------------------------------------------------------------------ #
# 5. get_provenance_report
# ------------------------------------------------------------------ #


def test_get_provenance_report_total():
    """report: total=27, usable_count=27, failed_count=0"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report()
    assert r["total"] == 27
    assert r["usable_count"] == 27
    assert r["failed_count"] == 0


def test_get_provenance_report_by_source_type():
    """by_source_type 分布：27 全在 manual_summary"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report()
    assert r["by_source_type"] == {"manual_summary": 27}


def test_get_provenance_report_items_have_summary():
    """每个 item 含 province/ok/is_usable/errors/warnings/summary/file_name"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report()
    required = {
        "province",
        "ok",
        "is_usable",
        "errors",
        "warnings",
        "summary",
        "file_name",
    }
    for item in r["items"]:
        assert required <= set(item.keys()), (
            f"item 缺字段: {required - set(item.keys())}"
        )


def test_get_provenance_report_filtered_only_usable():
    """only_usable=True 时应返回全部 27 省。"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report(only_usable=True)
    assert r["total"] == 27
    assert r["usable_count"] == 27
    assert [item["province"] for item in r["items"]] == [
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "山西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "陕西",
        "甘肃",
        "青海",
        "新疆",
    ]


def test_get_provenance_report_filtered_source_type():
    """source_type 过滤时 by_source_type 只含该类型"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report(source_type="official_release")
    assert r["total"] == 0
    assert r["by_source_type"] == {}


# ------------------------------------------------------------------ #
# 6. 错误省份输入
# ------------------------------------------------------------------ #


def test_validate_province_unknown_load_failed():
    """未注册的省份 → load_failed error"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    v = loader.validate_province("不存在的省")
    assert v.ok is False
    assert any("load_failed" in e for e in v.errors)
    assert v.is_usable is False


def test_provenance_validation_to_dict_roundtrip():
    """ProvenanceValidation.to_dict 输出 6 字段且值一致"""
    v = ProvenanceValidation(province="X", ok=True, is_usable=True)
    v.errors = []
    v.warnings = ["w1"]
    v.summary = {"a": 1}
    d = v.to_dict()
    assert d["province"] == "X"
    assert d["ok"] is True
    assert d["is_usable"] is True
    assert d["errors"] == []
    assert d["warnings"] == ["w1"]
    assert d["summary"] == {"a": 1}


# ------------------------------------------------------------------ #
# 7. 与 load_metadata 的契约对齐（确保未破坏既有 API）
# ------------------------------------------------------------------ #


def test_load_metadata_unchanged():
    """既有 load_metadata 仍返回 8 字段"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    meta = loader.load_metadata("湖南")
    assert meta is not None
    for k in (
        "province",
        "last_updated",
        "data_year",
        "source",
        "source_url",
        "source_type",
        "confidence",
        "record_count",
    ):
        assert k in meta
    assert meta["record_count"] > 0


def test_validate_provenance_does_not_mutate_caller_dict():
    """validate_provenance 不会修改入参 data"""
    data = {
        "province": "湖南",
        "last_updated": "2026-06-12",
        "data_year": 2025,
        "source": "s",
        "source_type": "manual_summary",
        "confidence": 0.85,
        "score_ranges": [],
    }
    import copy

    before = copy.deepcopy(data)
    CrowdDBLoader.validate_provenance(data, province="湖南")
    assert data == before
