#!/usr/bin/env python3
"""Check that the contract quartet matrix covers required public/admin contracts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "CONTRACT_QUARTET_MATRIX_2026-07-07.md"
REQUIRED = [
    "POST /api/auth/login",
    "GET /api/admin/stats/dashboard",
    "POST /api/public/orders",
    "POST /api/public/payments/alipay/notify",
    "GET /portal/{token}/cwb",
    "GET /portal/{token}/full-plan",
    "GET /api/llm/config",
    "POST /api/llm/{provider}/enhance",
]


def main() -> int:
    text = MATRIX.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED if item not in text]
    if missing:
        print("missing contract rows:")
        for item in missing:
            print(f"- {item}")
        return 1
    print(f"contract quartet matrix ok: {len(REQUIRED)} contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
