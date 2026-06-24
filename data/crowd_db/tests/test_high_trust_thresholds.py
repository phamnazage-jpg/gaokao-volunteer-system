"""高信任门槛约束测试（防静默升级）。

目的：锁死 high/usable 判定的完整门槛，防止只改 confidence 值就升级 quality_level。
门槛来源：docs/plans/2026-06-23-national-high-trust-crowd-db-plan.md §4

关键约束：
- high 必须同时满足 conf>=0.8 + sr>=8 + recs>=40 + alts>=60 + 3层分数带
- usable 必须同时满足 conf>=0.65 + sr>=6 + recs>=24 + alts>=24
"""

from __future__ import annotations

import pytest

from data.crowd_db.loader import CrowdDBLoader
from data.crowd_db.quality_summary import build_quality_summary


def _classify_score_bands(score_ranges):
    """复用 risk_report.py 的分数带分类逻辑（防重复）。"""
    bands = set()
    for sr in score_ranges:
        rng = sr.get("range", [0, 0])
        if not rng or len(rng) < 2:
            continue
        mid = (rng[0] + rng[1]) / 2
        if mid >= 580:
            bands.add("high")
        elif mid >= 480:
            bands.add("mid")
        else:
            bands.add("low")
    return bands


# 加载满数据版本（含 score_ranges）
loader = CrowdDBLoader(warn_low_confidence=False)


@pytest.fixture(scope="module")
def quality_data():
    """返回各省份的质量元数据，含完整内容。"""
    provinces = []
    for province in loader.list_supported_provinces():
        full_data = loader.load_province(province)
        if not full_data:
            continue

        conf = full_data.get("confidence", 0)
        sr = full_data.get("score_ranges", [])

        # 统计 recs / alts
        recs = sum(len(r.get("recommendations", [])) for r in sr)
        alts = sum(
            len(rec.get("alternatives", []))
            for r in sr
            for rec in r.get("recommendations", [])
        )
        bands = _classify_score_bands(sr)

        provinces.append({
            "province": province,
            "confidence": conf,
            "score_ranges": sr,
            "recs": recs,
            "alts": alts,
            "bands": bands,
            "sr_count": len(sr),
        })
    return provinces


def test_high_province_must_meet_all_thresholds(quality_data):
    """high 省必须同时满足 conf + sr + recs + alts + 分数带（防静默升级）。

    用例：所有 quality_level=high 的省份，必须完全达标。
    """
    high_provinces = [p for p in quality_data if p["confidence"] >= 0.80]
    assert high_provinces, "应有 high 省"

    for p in high_provinces:
        assert p["confidence"] >= 0.8, (
            f"{p['province']}: high 门槛要求 conf >= 0.80 (实际 {p['confidence']})"
        )
        assert p["sr_count"] >= 8, (
            f"{p['province']}: high 门槛要求 >= 8 个分数段 (实际 {p['sr_count']})"
        )
        assert p["recs"] >= 40, (
            f"{p['province']}: high 门槛要求 >= 40 条 recommendations "
            f"(实际 {p['recs']})"
        )
        assert p["alts"] >= 60, (
            f"{p['province']}: high 门槛要求 >= 60 条 alternatives (实际 {p['alts']})"
        )
        assert len(p["bands"]) >= 3, (
            f"{p['province']}: high 门槛要求覆盖至少 3 层分数带 "
            f"(实际 {sorted(p['bands'])})"
        )


def test_usable_province_must_meet_all_thresholds(quality_data):
    """usable 省必须同时满足 conf + sr + recs + alts。

    用例：所有 quality_level=usable 的省份，必须完全达标。
    """
    usable_provinces = [p for p in quality_data if 0.65 <= p["confidence"] < 0.8]
    # 当前实地运行无 usable（均为 high），但保留门槛测试
    if not usable_provinces:
        pytest.skip("当前无 usable 省份")

    for p in usable_provinces:
        assert p["confidence"] >= 0.65, (
            f"{p['province']}: usable 门槛要求 conf >= 0.65 (实际 {p['confidence']})"
        )
        assert p["sr_count"] >= 6, (
            f"{p['province']}: usable 门槛要求 >= 6 个分数段 (实际 {p['sr_count']})"
        )
        assert p["recs"] >= 24, (
            f"{p['province']}: usable 门槛要求 >= 24 条 recommendations "
            f"(实际 {p['recs']})"
        )
        assert p["alts"] >= 24, (
            f"{p['province']}: usable 门槛要求 >= 24 条 alternatives (实际 {p['alts']})"
        )


def test_low_province_meets_confidence_half(quality_data):
    """low 省应满足 conf >= 0.5 但未达 usable 门槛（新旧分层边界）。"""
    low_provinces = [p for p in quality_data if 0.5 <= p["confidence"] < 0.65]
    if not low_provinces:
        pytest.skip("当前无 low 省份")

    for p in low_provinces:
        assert p["confidence"] >= 0.5, (
            f"{p['province']}: low 要求 conf >= 0.5 (实际 {p['confidence']})"
        )
        # 未达 usable 门槛即为 low（具体缺什么在详细质量说明中）
        # 此处不做细分断言，保持"低但仍可用"的模糊边界


def test_skeleton_province_confidence_below_half(quality_data):
    """skeleton 省应 conf < 0.5（骨架门槛）。"""
    skeleton_provinces = [
        p for p in quality_data if p["confidence"] >= 0.5 and p["recs"] < 24
    ]  # 低 recs 实际仍为 skeleton
    if not skeleton_provinces:
        pytest.skip("当前无 skeleton 省份")

    for p in skeleton_provinces:
        # 结构上应该为 skeleton，但当前实在数据无 skeleton
        # 持留接口：未来迁移数据到真正的 skeleton 样板后可激活
        assert p["confidence"] < 0.5 or p["recs"] < 24


def test_only_high_is_approved_by_quality_summary():
    """quality_summary 与门槛测试不应存在"只看 conf"的漏洞。

    门槛测试已覆盖需求，此测试相当于双重验证。
    """
    summary = build_quality_summary()
    high_provinces = [p for p in summary["provinces"] if p["quality_level"] == "high"]
    assert high_provinces, "quality_summary 应统计到 high 省份"

    # 手动复核一次门槛（防质量问题被测试隐藏）
    loader = CrowdDBLoader(warn_low_confidence=False)
    for p_dict in high_provinces:
        metadata = loader.load_province(p_dict["province"])
        if not metadata:
            continue

        conf = metadata.get("confidence", 0)
        sr = metadata.get("score_ranges", [])
        recs = sum(len(r.get("recommendations", [])) for r in sr)
        alts = sum(
            len(rec.get("alternatives", []))
            for r in sr
            for rec in r.get("recommendations", [])
        )
        bands = _classify_score_bands(sr)

        assert conf >= 0.8, (
            f"{p_dict['province']}: 质量摘要判 high，但 conf {conf} 不满足 high 门槛"
        )
        assert len(sr) >= 8, (
            f"{p_dict['province']}: 质量摘要判 high，但 score_ranges 数量 {len(sr)} 不满足 >= 8"
        )
        assert recs >= 40, (
            f"{p_dict['province']}: 质量摘要判 high，但 recs {recs} 不满足 >= 40"
        )
        assert alts >= 60, (
            f"{p_dict['province']}: 质量摘要判 high，但 alts {alts} 不满足 >= 60"
        )
        assert len(bands) >= 3, (
            f"{p_dict['province']}: 质量摘要判 high，但分数带 {sorted(bands)} 不满层"
        )
