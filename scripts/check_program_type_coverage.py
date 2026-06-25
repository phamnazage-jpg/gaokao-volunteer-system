#!/usr/bin/env python3
"""program_type 覆盖率检查（Phase 1）。"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path("/home/long/project/gaokao-volunteer-system")


def main() -> int:
    total = 0
    tagged = 0
    counter: Counter[str] = Counter()

    for path in sorted((ROOT / "data/crowd_db").glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        for sr in d.get("score_ranges", []):
            for rec in sr.get("recommendations", []):
                total += 1
                ptype = rec.get("program_type")
                if ptype is not None:
                    tagged += 1
                    counter[ptype] += 1

    coverage = tagged / total if total else 0
    print("=" * 80)
    print("program_type 覆盖率检查")
    print("=" * 80)
    print(f"总 recs: {total}")
    print(f"已标注: {tagged}")
    print(f"覆盖率: {coverage:.1%}")
    print("\n类型分布:")
    for k, v in counter.most_common():
        print(f"  - {k}: {v}")

    if coverage < 0.30:
        print(f"\n❌ 未达标：应 >= 30%，当前 {coverage:.1%}")
        return 1

    print("\n✅ 达标：覆盖率 >= 30%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
