#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path


ARTIFACT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("audit_report", "audit_report"),
    ("pdf_path", "pdf_path"),
)


def _safe_target_path(source: Path) -> Path:
    if source.is_absolute():
        return Path(*source.parts[1:])
    return source


def collect_order_artifacts(orders_db: Path, output_dir: Path) -> dict[str, object]:
    if not orders_db.is_file():
        return {
            "copied": 0,
            "missing": 0,
            "skipped": [{"reason": "orders_db_missing", "path": str(orders_db)}],
        }

    conn = sqlite3.connect(orders_db)
    conn.row_factory = sqlite3.Row
    copied = 0
    missing = 0
    skipped: list[dict[str, str]] = []
    try:
        try:
            rows = conn.execute(
                "SELECT id, audit_report, pdf_path FROM orders ORDER BY created_at, id"
            )
        except sqlite3.OperationalError as exc:
            return {
                "copied": 0,
                "missing": 0,
                "skipped": [
                    {
                        "reason": "orders_table_unavailable",
                        "path": str(orders_db),
                        "error": str(exc),
                    }
                ],
            }

        for row in rows:
            order_id = str(row["id"])
            for column_name, artifact_kind in ARTIFACT_COLUMNS:
                raw_path = row[column_name]
                if not raw_path:
                    continue
                source = Path(str(raw_path))
                if not source.is_file():
                    missing += 1
                    skipped.append(
                        {
                            "order_id": order_id,
                            "artifact": artifact_kind,
                            "path": str(source),
                            "reason": "missing_source",
                        }
                    )
                    continue

                relative_target = (
                    Path(order_id) / artifact_kind / _safe_target_path(source)
                )
                target = output_dir / relative_target
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied += 1
    finally:
        conn.close()

    return {
        "copied": copied,
        "missing": missing,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect order-linked delivery artifacts into a backup staging dir"
    )
    parser.add_argument("--orders-db", required=True, help="Path to orders.db")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where copied artifacts should be stored",
    )
    args = parser.parse_args(argv)

    result = collect_order_artifacts(
        orders_db=Path(args.orders_db).resolve(),
        output_dir=Path(args.output_dir).resolve(),
    )
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
