"""渠道兜底巡检 (T8.4).

目标：给 ops 一个可定时执行的健康检查入口，基于本地 SQLite 中已经存在的
webhook_audit / poller_state / poller_run 事实数据，判断渠道同步链路是否进入
降级态，并给出人工兜底建议。

不做：
- 不直接调用外部渠道 API（避免引入额外依赖 / 凭证）
- 不自动创建订单（人工兜底仍由 order-manager CLI 明确执行）
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("data/orders.db")
_STATUS_EXIT_CODE = {"ok": 0, "warn": 1, "critical": 2}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _minutes_ago(now: datetime, ts: str | None) -> float | None:
    dt = _parse_iso(ts)
    if dt is None:
        return None
    return round((now - dt).total_seconds() / 60.0, 2)


def _open_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _fetch_one(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]
) -> dict[str, Any] | None:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row is not None else None


def _manual_actions(db_path: str, source: str) -> list[str]:
    return [
        (
            "先执行巡检命令确认状态："
            f"python3 scripts/gaokao-channel-fallback --db {db_path} check --source {source} --human"
        ),
        (
            "若确认 webhook/poller 不可用，使用人工补录 CLI 新建订单："
            f"python3 scripts/gaokao-order-manager --db {db_path} create --source {source} "
            "--service-version basic --amount-cents 0 --customer-name <姓名> --customer-phone <手机号>"
        ),
        (
            "人工补录后按业务推进状态："
            f"python3 scripts/gaokao-order-manager --db {db_path} pay <ORDER_ID>"
            " / deliver <ORDER_ID>"
        ),
    ]


def summarize_channel_health(
    db_path: str,
    *,
    source: str = "xianyu",
    now: datetime | None = None,
    poller_stale_minutes: int = 15,
    webhook_stale_minutes: int = 30,
    recent_window_minutes: int = 60,
    reject_warn_threshold: int = 5,
    poller_error_warn_threshold: int = 3,
) -> dict[str, Any]:
    now = now or _utcnow()
    conn = _open_db(db_path)
    try:
        has_audit = _table_exists(conn, "webhook_audit")
        has_state = _table_exists(conn, "poller_state")
        has_run = _table_exists(conn, "poller_run")

        latest_accepted = None
        latest_recent = None
        recent_counts = {
            "accepted": 0,
            "duplicate": 0,
            "parse_error": 0,
            "rejected": 0,
        }
        if has_audit:
            latest_accepted = _fetch_one(
                conn,
                """
                SELECT received_at, decision, event_id, reject_reason
                FROM webhook_audit
                WHERE channel=? AND decision='accepted'
                ORDER BY id DESC LIMIT 1
                """,
                (source,),
            )
            latest_recent = _fetch_one(
                conn,
                """
                SELECT received_at, decision, event_id, reject_reason
                FROM webhook_audit
                WHERE channel=?
                ORDER BY id DESC LIMIT 1
                """,
                (source,),
            )
            since_iso = (now - timedelta(minutes=recent_window_minutes)).isoformat()
            for row in conn.execute(
                """
                SELECT decision, COUNT(*) AS n
                FROM webhook_audit
                WHERE channel=? AND received_at>=?
                GROUP BY decision
                """,
                (source, since_iso),
            ).fetchall():
                decision = str(row["decision"])
                if decision in recent_counts:
                    recent_counts[decision] = int(row["n"] or 0)

        state = None
        if has_state:
            state = _fetch_one(
                conn,
                """
                SELECT source, last_cursor, last_run_at, last_error, run_count, error_count
                FROM poller_state WHERE source=?
                """,
                (source,),
            )

        last_run = None
        if has_run:
            last_run = _fetch_one(
                conn,
                """
                SELECT started_at, finished_at, fetched, inserted, updated, unchanged,
                       rejected, error_message
                FROM poller_run
                WHERE source=?
                ORDER BY id DESC LIMIT 1
                """,
                (source,),
            )

        findings: list[str] = []
        actions: list[str] = []
        status = "ok"

        def raise_status(next_status: str) -> None:
            nonlocal status
            order = {"ok": 0, "warn": 1, "critical": 2}
            if order[next_status] > order[status]:
                status = next_status

        if not has_audit:
            raise_status("warn")
            findings.append("缺少 webhook_audit 表，无法判断 webhook 接收健康度")
        if not has_state:
            raise_status("warn")
            findings.append("缺少 poller_state 表，无法判断兜底轮询状态")
        if not has_run:
            raise_status("warn")
            findings.append("缺少 poller_run 表，无法回看最近轮询结果")

        accepted_age = _minutes_ago(
            now, latest_accepted["received_at"] if latest_accepted else None
        )
        recent_age = _minutes_ago(
            now, latest_recent["received_at"] if latest_recent else None
        )
        poller_age = _minutes_ago(now, state["last_run_at"] if state else None)

        if state and state.get("last_error"):
            error_count = int(state.get("error_count") or 0)
            if error_count >= poller_error_warn_threshold:
                raise_status("critical")
                findings.append(
                    f"poller 连续错误计数={error_count}，last_error={state['last_error']}"
                )
            else:
                raise_status("warn")
                findings.append(f"poller 最近一次报错：{state['last_error']}")

        if last_run and last_run.get("error_message"):
            raise_status("critical")
            findings.append(f"最近一次 poller_run 失败：{last_run['error_message']}")

        rejected_total = recent_counts["rejected"] + recent_counts["parse_error"]
        if rejected_total >= reject_warn_threshold:
            raise_status("warn")
            findings.append(
                f"最近 {recent_window_minutes} 分钟 webhook 拒绝/解析失败 {rejected_total} 次"
            )

        if poller_age is not None and poller_age > poller_stale_minutes:
            raise_status("warn")
            findings.append(
                f"poller 最近运行距今 {poller_age} 分钟，超过阈值 {poller_stale_minutes} 分钟"
            )

        if (
            accepted_age is not None
            and accepted_age > webhook_stale_minutes
            and recent_counts["rejected"] + recent_counts["parse_error"] > 0
        ):
            raise_status("warn")
            findings.append(
                f"最近成功 webhook 距今 {accepted_age} 分钟，且窗口内存在失败事件"
            )

        if latest_accepted is None and state is None and last_run is None:
            raise_status("warn")
            findings.append(
                "尚无 webhook accepted / poller_state / poller_run 证据，链路可能未启动"
            )

        if status != "ok":
            actions = _manual_actions(db_path, source)
        elif not findings:
            findings.append("最近 webhook/poller 未发现明显异常")

        payload = {
            "status": status,
            "checked_at": now.isoformat(),
            "source": source,
            "db_path": db_path,
            "tables": {
                "webhook_audit": has_audit,
                "poller_state": has_state,
                "poller_run": has_run,
            },
            "webhook": {
                "latest_accepted": latest_accepted,
                "latest_event": latest_recent,
                "latest_accepted_age_minutes": accepted_age,
                "latest_event_age_minutes": recent_age,
                "recent_counts": recent_counts,
            },
            "poller": {
                "state": state,
                "last_run": last_run,
                "last_run_age_minutes": poller_age,
            },
            "findings": findings,
            "recommended_actions": actions,
        }
        return payload
    finally:
        conn.close()


def _emit(payload: dict[str, Any], *, human: bool) -> None:
    if not human:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"status: {payload['status']}")
    print(f"source: {payload['source']}")
    print(f"checked_at: {payload['checked_at']}")
    print(f"db_path: {payload['db_path']}")
    print("findings:")
    for item in payload.get("findings", []):
        print(f"- {item}")
    actions = payload.get("recommended_actions", [])
    if actions:
        print("recommended_actions:")
        for item in actions:
            print(f"- {item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaokao-channel-fallback",
        description="渠道兜底巡检 CLI（T8.4）",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="订单 SQLite 路径（默认 data/orders.db）",
    )
    parser.add_argument(
        "--human",
        action="store_true",
        help="终端友好输出（默认 JSON）",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="检查 webhook/poller 健康度")
    check.add_argument("--source", default="xianyu", help="渠道 source，默认 xianyu")
    check.add_argument("--human", action="store_true", help=argparse.SUPPRESS)
    check.add_argument("--poller-stale-minutes", type=int, default=15)
    check.add_argument("--webhook-stale-minutes", type=int, default=30)
    check.add_argument("--recent-window-minutes", type=int, default=60)
    check.add_argument("--reject-warn-threshold", type=int, default=5)
    check.add_argument("--poller-error-warn-threshold", type=int, default=3)

    manual = subparsers.add_parser("manual-template", help="输出人工兜底建议命令")
    manual.add_argument("--source", default="xianyu", help="渠道 source，默认 xianyu")
    manual.add_argument("--human", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    human = bool(getattr(args, "human", False))

    if args.command == "manual-template":
        payload = {
            "status": "warn",
            "checked_at": _utcnow().isoformat(),
            "source": args.source,
            "db_path": args.db,
            "findings": ["人工兜底模板"],
            "recommended_actions": _manual_actions(args.db, args.source),
        }
        _emit(payload, human=human)
        return 0

    payload = summarize_channel_health(
        args.db,
        source=args.source,
        poller_stale_minutes=args.poller_stale_minutes,
        webhook_stale_minutes=args.webhook_stale_minutes,
        recent_window_minutes=args.recent_window_minutes,
        reject_warn_threshold=args.reject_warn_threshold,
        poller_error_warn_threshold=args.poller_error_warn_threshold,
    )
    _emit(payload, human=human)
    return _STATUS_EXIT_CODE[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
