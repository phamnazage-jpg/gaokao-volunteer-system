#!/usr/bin/env python3
"""crowd_db 跨文档/数据一致性检查（防漂移）。

检查项：
1. 实测质量分布 vs CURRENT_STATE.md 顶部状态词一致
2. 实测 high 白名单 vs test_crowd_db_data_quality.py HIGH_TRUST_PROVINCES 一致
3. trusted_sources.kind != province_official_pending_review 当 quality_level in (high, usable)
4. 所有省份 confidence 在 [0, 1] 范围内
5. 所有 data_year 一致（当前应为 2025）

退出码：
- 0: 一致
- 非 0: 发现漂移（细节打印到 stdout）

用法：
    python scripts/check_crowd_db_consistency.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.crowd_db.loader import CrowdDBLoader  # noqa: E402
from data.crowd_db.quality_summary import build_quality_summary  # noqa: E402


def _extract_current_state_distribution() -> dict[str, int]:
    """从 CURRENT_STATE.md 顶部状态词解析质量分布。"""
    path = ROOT / "docs" / "CURRENT_STATE.md"
    text = path.read_text(encoding="utf-8")
    # 匹配 "7 high / 20 usable / 0 skeleton"
    match = re.search(
        r"(\d+)\s*high\s*/\s*(\d+)\s*usable\s*/\s*(\d+)\s*skeleton",
        text,
    )
    if not match:
        return {"high": -1, "usable": -1, "skeleton": -1}
    return {
        "high": int(match.group(1)),
        "usable": int(match.group(2)),
        "skeleton": int(match.group(3)),
    }


def _extract_test_whitelist() -> set[str]:
    """从 test_crowd_db_data_quality.py 解析 HIGH_TRUST_PROVINCES 白名单。"""
    path = ROOT / "data" / "crowd_db" / "tests" / "test_crowd_db_data_quality.py"
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"HIGH_TRUST_PROVINCES\s*=\s*frozenset\(\s*\{([^}]+)\}",
        text,
    )
    if not match:
        return set()
    raw = match.group(1)
    return set(re.findall(r'"([^"]+)"', raw))


def main() -> int:
    issues: list[str] = []

    # 实测
    loader = CrowdDBLoader(warn_low_confidence=False)
    summary = build_quality_summary(loader=loader)
    actual_dist = summary["by_quality_level"]
    actual_high = {
        p["province"] for p in summary["provinces"] if p["quality_level"] == "high"
    }

    # 检查 1: 状态词一致性
    doc_dist = _extract_current_state_distribution()
    for level in ("high", "usable", "skeleton"):
        if doc_dist[level] != actual_dist.get(level, 0):
            issues.append(
                f"[状态词漂移] CURRENT_STATE.md 声明 {level}={doc_dist[level]}, "
                f"实测 {level}={actual_dist.get(level, 0)}"
            )

    # 检查 2: 测试白名单一致性
    whitelist = _extract_test_whitelist()
    if whitelist != actual_high:
        missing = actual_high - whitelist
        extra = whitelist - actual_high
        if missing:
            issues.append(f"[白名单漂移] 实测 high 但测试白名单缺失: {sorted(missing)}")
        if extra:
            issues.append(f"[白名单漂移] 测试白名单有但实测非 high: {sorted(extra)}")

    # 检查 3: trusted_sources.kind 与 quality_level 一致性
    for province in loader.list_supported_provinces():
        full = loader.load_province(province)
        if not full:
            continue
        meta = loader.load_metadata(province) or {}
        normalized = _normalize_via_summary(summary, province)
        if normalized in ("high", "usable"):
            for ts in full.get("trusted_sources", []):
                if ts.get("kind") == "province_official_pending_review":
                    issues.append(
                        f"[kind 漂移] {province} quality_level={normalized} 但 "
                        f"{ts.get('name', '?')} kind=province_official_pending_review"
                    )

    # 检查 4: confidence 范围
    for province in loader.list_supported_provinces():
        meta = loader.load_metadata(province) or {}
        conf = meta.get("confidence")
        if conf is None or not (0.0 <= conf <= 1.0):
            issues.append(f"[confidence 越界] {province} confidence={conf}")

    # 检查 5: data_year 一致性（当前应为 2025）
    years = {
        (loader.load_metadata(p) or {}).get("data_year")
        for p in loader.list_supported_provinces()
    }
    if len(years) > 1:
        issues.append(f"[data_year 不一致] 多年份共存: {years}")
    elif years == {2026}:
        issues.append("[data_year 注意] 已切到 2026，确认 2026 录取数据已正式公布")

    # 输出
    if issues:
        print("❌ crowd_db 一致性检查发现漂移：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return 1

    print(
        f"✅ crowd_db 一致性检查通过："
        f"high={actual_dist.get('high', 0)} "
        f"usable={actual_dist.get('usable', 0)} "
        f"low={actual_dist.get('low', 0)} "
        f"skeleton={actual_dist.get('skeleton', 0)}"
    )
    return 0


def _normalize_via_summary(summary: dict, province: str) -> str:
    """从已构建的 summary 中取 quality_level。"""
    for p in summary["provinces"]:
        if p["province"] == province:
            return p["quality_level"]
    return "unknown"


if __name__ == "__main__":
    sys.exit(main())
