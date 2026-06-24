from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

from .loader import CrowdDBLoader
from .risk_report import _normalize_provenance


def build_quality_summary(loader: CrowdDBLoader | None = None) -> dict[str, Any]:
    loader = loader or CrowdDBLoader(warn_low_confidence=False)
    provinces: list[dict[str, Any]] = []
    for province in loader.list_supported_provinces():
        # 加载完整数据（含 score_ranges）用于质量判定
        full_data = loader.load_province(province)
        metadata = loader.load_metadata(province) or {"province": province}
        normalized = _normalize_provenance(metadata, full_data=full_data)
        provinces.append({
            "province": province,
            "confidence": normalized["confidence"],
            "quality_level": normalized["quality_level"],
            "quality_label": normalized["quality_label"],
            "data_year": normalized["data_year"],
            "source_type": normalized["source_type"],
        })
    provinces.sort(key=lambda item: str(item["province"]))
    counts = Counter(item["quality_level"] for item in provinces)
    by_quality_level = {
        "high": counts.get("high", 0),
        "usable": counts.get("usable", 0),
        "low": counts.get("low", 0),
        "skeleton": counts.get("skeleton", 0),
        "unknown": counts.get("unknown", 0),
    }
    return {
        "total_provinces": len(provinces),
        "by_quality_level": by_quality_level,
        "provinces": provinces,
    }


def _emit_human(summary: dict[str, Any]) -> None:
    print(f"province_count: {summary['total_provinces']}")
    print("quality_counts:")
    for level, count in sorted(summary["by_quality_level"].items()):
        print(f"  - {level}: {count}")
    print("provinces:")
    for item in summary["provinces"]:
        print(
            f"  - {item['province']}: {item['quality_level']} ({item['quality_label']}), confidence={item['confidence']}, year={item['data_year']}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="crowd_db province quality summary")
    parser.add_argument("--human", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = build_quality_summary()
    if args.human:
        _emit_human(summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
