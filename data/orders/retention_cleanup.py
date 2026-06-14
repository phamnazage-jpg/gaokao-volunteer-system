from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime

from data.orders.dao import OrdersDAO
from data.orders.deletion_service import OrderDeletionService


@dataclass
class RetentionCleanupResult:
    scanned: int = 0
    candidates: int = 0
    anonymized: int = 0


_TERMINAL_STATUSES = {"completed", "refunded"}


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts)


def _iter_candidates(db_path: str, cutoff_iso: str) -> tuple[int, list[str]]:
    cutoff = datetime.fromisoformat(cutoff_iso)
    scanned = 0
    candidates: list[str] = []
    offset = 0
    page_size = 1000
    while True:
        with OrdersDAO.connect(db_path) as dao:
            batch = dao.list(limit=page_size, offset=offset)
        if not batch:
            break
        scanned += len(batch)
        for order in batch:
            if order.status not in _TERMINAL_STATUSES:
                continue
            anchor = _parse_iso(
                order.completed_at or order.status_updated_at or order.created_at
            )
            if anchor is None:
                continue
            if anchor <= cutoff:
                candidates.append(order.id)
        if len(batch) < page_size:
            break
        offset += page_size
    return scanned, candidates


def run_cleanup(
    db_path: str, *, cutoff_iso: str, apply: bool
) -> RetentionCleanupResult:
    scanned, candidate_ids = _iter_candidates(db_path, cutoff_iso)
    result = RetentionCleanupResult(scanned=scanned, candidates=len(candidate_ids))
    if not apply:
        return result
    service = OrderDeletionService.for_db(db_path)
    try:
        for order_id in candidate_ids:
            service.anonymize_order(
                order_id, actor="retention_cleanup", reason="retention_expired"
            )
            result.anonymized += 1
    finally:
        service.close()
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run retention cleanup for old completed/refunded orders"
    )
    parser.add_argument(
        "--cutoff",
        required=True,
        help="ISO8601 cutoff; orders on or before this anchor are candidates",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None, *, db_path: str | None = None) -> int:
    if db_path is None:
        from admin.config import load_settings

        db_path = load_settings().orders_db_path
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_cleanup(db_path, cutoff_iso=args.cutoff, apply=not args.dry_run)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
