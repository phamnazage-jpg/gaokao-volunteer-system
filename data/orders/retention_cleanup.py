from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from data.orders.dao import OrdersDAO
from data.orders.deletion_service import OrderDeletionService


@dataclass
class RetentionCleanupResult:
    cutoff_iso: str
    dry_run: bool
    scanned: int = 0
    candidates: int = 0
    anonymized: int = 0
    deletion_logs_pruned: int = 0
    share_events_pruned: int = 0


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


def _prune_deletion_request_log(log_path: str, candidate_ids: list[str]) -> int:
    path = Path(log_path)
    if not path.exists() or not candidate_ids:
        return 0
    keep: list[str] = []
    pruned = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            keep.append(line)
            continue
        if str(item.get("order_id") or "") in candidate_ids:
            pruned += 1
            continue
        keep.append(json.dumps(item, ensure_ascii=False))
    path.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
    return pruned


def _prune_share_access_events(share_db_path: str, candidate_ids: list[str]) -> int:
    if not candidate_ids:
        return 0
    from data.share.short_link import ShortLinkService

    service = ShortLinkService(db_path=share_db_path)
    with service._connect() as conn:
        rows = conn.execute(
            "SELECT code FROM share_links WHERE report_id IN ({})".format(
                ",".join("?" for _ in candidate_ids)
            ),
            tuple(candidate_ids),
        ).fetchall()
        codes = [str(row[0]) for row in rows]
        if not codes:
            return 0
        conn.execute(
            "DELETE FROM share_link_access_events WHERE code IN ({})".format(
                ",".join("?" for _ in codes)
            ),
            tuple(codes),
        )
        conn.commit()
        return int(conn.total_changes)


def resolve_cutoff_iso(
    *, cutoff_iso: str | None = None, retention_days: int | None = None
) -> str:
    if cutoff_iso is not None:
        datetime.fromisoformat(cutoff_iso)
        return cutoff_iso
    if retention_days is None or retention_days <= 0:
        raise ValueError("retention_days must be > 0 when cutoff is not provided")
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    return cutoff.replace(microsecond=0).isoformat()


def run_cleanup(
    db_path: str,
    *,
    cutoff_iso: str,
    apply: bool,
    deletion_request_log_path: str | None = None,
    share_db_path: str | None = None,
) -> RetentionCleanupResult:
    if deletion_request_log_path is None or share_db_path is None:
        try:
            from admin.config import load_settings

            settings = load_settings()
        except Exception:
            settings = None
        if deletion_request_log_path is None and settings is not None:
            deletion_request_log_path = settings.deletion_request_log_path
        if share_db_path is None and settings is not None:
            share_db_path = settings.share_db_path
    scanned, candidate_ids = _iter_candidates(db_path, cutoff_iso)
    result = RetentionCleanupResult(
        cutoff_iso=cutoff_iso,
        dry_run=not apply,
        scanned=scanned,
        candidates=len(candidate_ids),
    )
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
    if deletion_request_log_path:
        result.deletion_logs_pruned = _prune_deletion_request_log(
            deletion_request_log_path, candidate_ids
        )
    if share_db_path:
        result.share_events_pruned = _prune_share_access_events(
            share_db_path, candidate_ids
        )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run retention cleanup for old completed/refunded orders"
    )
    cutoff_group = parser.add_mutually_exclusive_group(required=True)
    cutoff_group.add_argument(
        "--cutoff",
        help="ISO8601 cutoff; orders on or before this anchor are candidates",
    )
    cutoff_group.add_argument(
        "--retention-days",
        type=int,
        help="Retention window in days; cutoff is computed as now - retention_days",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None, *, db_path: str | None = None) -> int:
    from admin.config import load_settings

    settings = load_settings()
    if db_path is None:
        db_path = settings.orders_db_path
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        cutoff_iso = resolve_cutoff_iso(
            cutoff_iso=args.cutoff,
            retention_days=args.retention_days,
        )
    except ValueError as exc:
        parser.error(str(exc))
    result = run_cleanup(
        db_path,
        cutoff_iso=cutoff_iso,
        apply=not args.dry_run,
        deletion_request_log_path=getattr(settings, "deletion_request_log_path", None),
        share_db_path=getattr(settings, "share_db_path", None),
    )
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
