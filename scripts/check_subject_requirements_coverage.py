#!/usr/bin/env python3
"""检查 7 个新高考 S 级省的选科匹配覆盖率。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/long/project/gaokao-volunteer-system")
S_PROVINCES = [
    "hunan",
    "guangdong",
    "jiangsu",
    "shandong",
    "hebei",
    "zhejiang",
    "fujian",
]


def main() -> int:
    print("=" * 80)
    print("选科匹配覆盖率检查")
    print("=" * 80)

    total_recs = 0
    total_with_sr = 0
    failed = []

    for prov in S_PROVINCES:
        path = ROOT / f"data/crowd_db/{prov}.json"
        d = json.loads(path.read_text(encoding="utf-8"))
        recs = 0
        with_sr = 0
        for sr in d.get("score_ranges", []):
            for rec in sr.get("recommendations", []):
                recs += 1
                if rec.get("subject_requirements") is not None:
                    with_sr += 1
        pct = with_sr / recs * 100 if recs > 0 else 0
        total_recs += recs
        total_with_sr += with_sr
        ok = pct == 100.0
        print(f"{prov:10}: {with_sr}/{recs} ({pct:.1f}%) {'✅' if ok else '❌'}")
        if not ok:
            failed.append(prov)

    print("\n总计:")
    total_pct = total_with_sr / total_recs * 100 if total_recs > 0 else 0
    print(f"  {total_with_sr}/{total_recs} ({total_pct:.1f}%)")

    if failed:
        print(f"\n❌ 未达 100% 覆盖的省份: {', '.join(failed)}")
        return 1

    print("\n✅ 7 个新高考 S 级省 100% 覆盖 subject_requirements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
