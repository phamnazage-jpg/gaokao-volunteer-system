"""T3.2 溯源字段查询 + 验证 测试

覆盖：
1. 27省全部 validate_all 通过（errors=0），usable=1（仅湖南）
2. validate_province(hunan) — ok + is_usable=True + summary 7 字段齐全
3. validate_province(guizhou) — ok + is_usable=False + 1 warning (low_confidence)
4. validate_provenance(None) — 报 load_failed error
5. validate_provenance({}) — 报 7 missing_field
6. validate_provenance 边界：confidence 越界、source_type 非法、data_year 类型错、date 格式错
7. filter_provinces 多维过滤：source_type / min_confidence / max_confidence / data_year / updated_since / only_usable
8. filter_provinces 组合：min + max confidence 区间
9. get_provenance_report: 统计字段（total/usable_count/failed_count/by_source_type）
10. 错误省份输入：未知省份返回 load_failed
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
    """usable 省份应当仅含湖南 (confidence 0.85)"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    results = loader.validate_all()
    usable = [p for p, v in results.items() if v.is_usable]
    assert usable == ["湖南"], f"expected ['湖南'], got {usable}"


def test_validate_all_warnings_low_confidence():
    """低 confidence 的 26 省均应有 low_confidence warning"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    results = loader.validate_all()
    low_warn = [
        p for p, v in results.items() if any("low_confidence" in w for w in v.warnings)
    ]
    assert len(low_warn) == 26, (
        f"expected 26 low_confidence warnings, got {len(low_warn)}"
    )


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


def test_validate_province_guizhou_low_confidence():
    """贵州：ok + is_usable=False + 1 low_confidence warning"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    v = loader.validate_province("贵州")
    assert v.ok is True
    assert v.is_usable is False
    assert any("low_confidence" in w for w in v.warnings)
    assert v.summary["confidence"] == 0.45


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
    """only_usable=True → 仅 湖南"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(only_usable=True)
    assert result == ["湖南"]


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
    """min_confidence=0.5 → 仅 湖南"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(min_confidence=0.5)
    assert result == ["湖南"]


def test_filter_provinces_max_confidence():
    """max_confidence=0.5 → 26 省（0.45 全在范围内）"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(max_confidence=0.5)
    assert len(result) == 26
    assert "湖南" not in result


def test_filter_provinces_confidence_range():
    """min=0.4 max=0.5 → 26 省（仅 0.45 落在区间）"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(min_confidence=0.4, max_confidence=0.5)
    assert len(result) == 26
    assert "湖南" not in result


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
    """组合：only_usable=True + data_year=2025 → 仅 湖南"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(only_usable=True, data_year=2025)
    assert result == ["湖南"]


def test_filter_provinces_preserves_map_order():
    """返回顺序按 PROVINCE_FILE_MAP"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    result = loader.filter_provinces(max_confidence=0.5)
    expected_first = "北京"  # map 中第一个低 confidence 的省
    assert result[0] == expected_first
    # 数量与 PROVINCE_FILE_MAP 一致（不含湖南）
    assert len(result) == 26


# ------------------------------------------------------------------ #
# 5. get_provenance_report
# ------------------------------------------------------------------ #


def test_get_provenance_report_total():
    """report: total=27, usable_count=1, failed_count=0"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report()
    assert r["total"] == 27
    assert r["usable_count"] == 1
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
    """only_usable=True 时 items 仅 1 个湖南"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    r = loader.get_provenance_report(only_usable=True)
    assert r["total"] == 1
    assert r["usable_count"] == 1
    assert r["items"][0]["province"] == "湖南"


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
