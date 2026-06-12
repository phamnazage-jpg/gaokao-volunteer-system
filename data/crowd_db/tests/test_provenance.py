"""T3.1 27省溯源数据测试

覆盖：
1. 27个省份 JSON 存在
2. 顶层溯源字段完整
3. 分数段 + 推荐条目 schema 合规
4. confidence 在 [0,1]
5. Loader: list_supported_provinces 返回 27
6. Loader: list_provinces 报告 27/27 存在
7. Loader: load_metadata 返回含 8 个元数据字段
8. Loader: load_province 在 confidence<0.5 时发出 UserWarning
9. 反扎堆检测端到端：随机抽取一省，命中一校的频次与 platforms 不空
"""

import os
import sys
import json
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.crowd_db.loader import CrowdDBLoader


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(REPO, "data", "crowd_db")


def _list_json_files():
    return sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))


def test_27_province_files_exist():
    """27 省 JSON 全部存在"""
    files = _list_json_files()
    assert len(files) == 27, f"expected 27 province JSONs, got {len(files)}"


def test_top_level_provenance_fields():
    """所有 27 个文件顶层必填字段齐全"""
    req = {
        "province",
        "last_updated",
        "data_year",
        "source",
        "source_type",
        "confidence",
        "score_ranges",
    }
    for fname in _list_json_files():
        d = json.load(open(os.path.join(DATA_DIR, fname), encoding="utf-8"))
        miss = req - set(d.keys())
        assert not miss, f"{fname} 缺字段: {miss}"


def test_score_range_schema():
    """score_ranges 每个元素含 range+recommendations 且 range 长度为 2"""
    for fname in _list_json_files():
        d = json.load(open(os.path.join(DATA_DIR, fname), encoding="utf-8"))
        for sr in d.get("score_ranges", []):
            assert isinstance(sr, dict), f"{fname}: score_range 必须是 dict"
            assert (
                "range" in sr
                and isinstance(sr["range"], list)
                and len(sr["range"]) == 2
            ), f"{fname}: range 必须是长度为 2 的列表"
            assert "recommendations" in sr and isinstance(
                sr["recommendations"], list
            ), f"{fname}: recommendations 必须是列表"
            for rec in sr["recommendations"]:
                rk = {"name", "frequency", "platforms"}
                assert rk <= set(rec.keys()), (
                    f"{fname}: rec 缺字段 {rk - set(rec.keys())}"
                )


def test_confidence_in_unit_interval():
    """confidence ∈ [0.0, 1.0]"""
    for fname in _list_json_files():
        d = json.load(open(os.path.join(DATA_DIR, fname), encoding="utf-8"))
        c = d.get("confidence")
        assert isinstance(c, (int, float)), f"{fname}: confidence 类型错误"
        assert 0.0 <= c <= 1.0, f"{fname}: confidence {c} 越界"


def test_loader_supported_count_27():
    """loader.PROVINCE_FILE_MAP 必须覆盖 27 省份"""
    loader = CrowdDBLoader()
    supported = loader.list_supported_provinces()
    assert len(supported) == 27, f"expected 27 supported, got {len(supported)}"


def test_loader_existing_count_27():
    """list_provinces 报告 27/27 存在"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    existing = [m for m in loader.list_provinces() if m.get("exists")]
    assert len(existing) == 27, f"expected 27 existing, got {len(existing)}"


def test_loader_metadata_hunan():
    """load_metadata('湖南') 返回 8 个字段且 record_count > 0"""
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
        assert k in meta, f"meta 缺 {k}"
    assert meta["record_count"] > 0, f"湖南 rec count = {meta['record_count']}"
    assert meta["confidence"] >= 0.8, (
        f"湖南 confidence 应 ≥ 0.8，实际 {meta['confidence']}"
    )


def test_loader_low_confidence_warning():
    """confidence<0.5 的省份加载时发出 UserWarning"""
    loader = CrowdDBLoader(warn_low_confidence=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        loader.load_province("贵州")  # 0.45
    user_warns = [w for w in caught if issubclass(w.category, UserWarning)]
    assert user_warns, "应至少发出 1 个 UserWarning"
    assert any("置信度" in str(w.message) for w in user_warns), (
        f"UserWarning 应提及 置信度, got: {[str(w.message) for w in user_warns]}"
    )


def test_loader_end_to_end_match():
    """端到端：用湖南数据 + 一条已知高校名，应当命中"""
    loader = CrowdDBLoader(warn_low_confidence=False)
    rec = loader.find_recommendation_by_school("湖南", "长沙理工大学")
    assert rec is not None, "长沙理工大学 应当在湖南 575 段命中"
    assert rec["frequency"] >= 1
    assert isinstance(rec["platforms"], list) and len(rec["platforms"]) >= 1
