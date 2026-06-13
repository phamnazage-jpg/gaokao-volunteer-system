"""闲鱼兜底轮询器 (T8.1 §3.2)

当 Webhook 不可用（平台维护、网络抖动）时，由 ``poller`` 从外部 API
拉取未确认订单并写入数据库。Webhook 与 poller 共享 ``upsert_by_external_id``
幂等机制，因此两端都收到同一条订单不会重复入库。

本模块只暴露可注入的 :class:`XianyuOpenAPIClient` 协议与 :func:`poll_once`
函数；CLI/定时器启动由 ``scripts/`` 下的入口负责（见 T8.4 兜底 SOP）。

数据契约:
- 输入: ``XianyuOpenAPIClient.list_orders(since: int) -> Iterable[dict]``
- 输出: 每条订单都经过 :func:`data.channel_sync.xianyu_adapter.to_order` →
  :func:`data.channel_sync.dao_extension.upsert_by_external_id`
- cursor: ``max(updated_at)`` 写入 ``poller_state`` 表（新建）
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Iterable, Optional, Protocol

from data.orders.models import utc_now_iso

from .dao_extension import UpsertResult, upsert_by_external_id
from .xianyu_adapter import XianyuEventError, parse_event, to_order


POLLER_STATE_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS poller_state (
    source          TEXT PRIMARY KEY,
    last_cursor     TEXT,
    last_run_at     TEXT,
    last_error      TEXT,
    run_count       INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0
);
"""

POLLER_RUN_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS poller_run (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    fetched         INTEGER NOT NULL DEFAULT 0,
    inserted        INTEGER NOT NULL DEFAULT 0,
    updated         INTEGER NOT NULL DEFAULT 0,
    unchanged       INTEGER NOT NULL DEFAULT 0,
    rejected        INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT
);
"""


class XianyuOpenAPIClient(Protocol):
    """外部 API 客户端协议，便于注入假实现做单测。"""

    def list_orders(self, since: Optional[str]) -> list[dict]: ...


class _DefaultClient:
    """默认空实现；真实接入留给 T8.2 之后的真接入阶段。"""

    def list_orders(self, since: Optional[str]) -> list[dict]:
        return []


def apply_poller_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(POLLER_STATE_SCHEMA + POLLER_RUN_SCHEMA)
    conn.commit()


@dataclass
class PollReport:
    source: str
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    rejected: int = 0
    error: Optional[str] = None
    last_cursor: Optional[str] = None
    upsert_results: list[UpsertResult] = field(default_factory=list)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    apply_poller_schema(conn)


def get_cursor(conn: sqlite3.Connection, source: str) -> Optional[str]:
    row = conn.execute(
        "SELECT last_cursor FROM poller_state WHERE source=?", (source,)
    ).fetchone()
    return row[0] if row else None


def _set_cursor(
    conn: sqlite3.Connection,
    source: str,
    cursor: Optional[str],
    error: Optional[str] = None,
    run_count_delta: int = 1,
    error_count_delta: int = 0,
    last_run_at: Optional[str] = None,
) -> None:
    if last_run_at is None:
        last_run_at = utc_now_iso()
    conn.execute(
        """
        INSERT INTO poller_state(
            source, last_cursor, last_run_at, last_error,
            run_count, error_count
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source) DO UPDATE SET
            last_cursor   = excluded.last_cursor,
            last_run_at   = excluded.last_run_at,
            last_error    = excluded.last_error,
            run_count     = run_count + excluded.run_count,
            error_count   = error_count + excluded.error_count
        """,
        (source, cursor, last_run_at, error, run_count_delta, error_count_delta),
    )


def _record_run(
    conn: sqlite3.Connection,
    *,
    source: str,
    started_at: str,
    finished_at: str,
    fetched: int,
    inserted: int,
    updated: int,
    unchanged: int,
    rejected: int,
    error_message: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO poller_run(
            source, started_at, finished_at, fetched, inserted,
            updated, unchanged, rejected, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source,
            started_at,
            finished_at,
            fetched,
            inserted,
            updated,
            unchanged,
            rejected,
            error_message,
        ),
    )
    return int(cur.lastrowid or 0)


def _parse_event_dicts(raw_orders: Iterable[dict]) -> list[dict]:
    """把 list_orders() 返回的 dict 列表规整化：必须含 raw_body (JSON str)。

    兜底模式：poller 拿到的 order 字典与 Webhook body 同构；这里不重新解析，
    留给 :func:`_process_one` 走完整 parse_event 路径以复用校验。
    """
    out: list[dict] = []
    for raw in raw_orders:
        if "raw_body" not in raw:
            # 上游直接给了字段时，按 Webhook body 形式重新组装
            import json as _json

            raw = dict(raw)
            raw.setdefault("raw_body", _json.dumps(raw, ensure_ascii=False))
        out.append(raw)
    return out


def _process_one(
    conn: sqlite3.Connection,
    raw: dict,
    *,
    actor: str = "xianyu_poller",
) -> UpsertResult:
    """单条订单: parse_event → to_order → upsert_by_external_id。"""
    event = parse_event(raw["raw_body"])
    order = to_order(event)
    return upsert_by_external_id(
        conn,
        order,
        actor=actor,
        reason=f"poller_event_{event.event_id}",
    )


def poll_once(
    conn: sqlite3.Connection,
    *,
    source: str = "xianyu",
    client: XianyuOpenAPIClient | None = None,
    actor: str = "xianyu_poller",
) -> PollReport:
    """执行一次轮询；返回 :class:`PollReport`。

    - 读取上次 cursor
    - 调 ``client.list_orders(since=cursor)``
    - 对每条订单走 parse + upsert
    - 写 ``poller_run`` / 更新 ``poller_state.cursor``

    失败不会抛出，返回 ``report.error`` 携带异常信息。
    """
    _ensure_schema(conn)
    if client is None:
        client = _DefaultClient()

    started_at = utc_now_iso()
    report = PollReport(source=source)

    try:
        cursor = get_cursor(conn, source)
        raw_orders = client.list_orders(cursor)
        normalized = _parse_event_dicts(raw_orders)
        report.fetched = len(normalized)
        for raw in normalized:
            try:
                res = _process_one(conn, raw, actor=actor)
            except XianyuEventError as e:
                report.rejected += 1
                report.upsert_results.append(
                    UpsertResult(
                        order_id="",
                        action="rejected",
                        error=str(e),
                    )
                )
                continue
            except Exception as e:  # 解析 / 落库异常 → 单条失败不阻塞整体
                report.rejected += 1
                report.upsert_results.append(
                    UpsertResult(
                        order_id="",
                        action="rejected",
                        error=f"unexpected: {e!r}",
                    )
                )
                continue
            report.upsert_results.append(res)
            if res.action == "inserted":
                report.inserted += 1
            elif res.action == "updated":
                report.updated += 1
            elif res.action == "unchanged":
                report.unchanged += 1
            elif res.action == "illegal_transition":
                report.rejected += 1
        # cursor 推进：取最大外部 updated_at；空列表时不更新;
        # fetched>0 但缺时间戳时回退到 started_at(详见 _compute_new_cursor)
        report.last_cursor = _compute_new_cursor(
            conn, source, raw_orders, now_iso=started_at
        )
        _set_cursor(
            conn,
            source,
            cursor=report.last_cursor,
            error=None,
            run_count_delta=1,
            error_count_delta=0,
        )
        _record_run(
            conn,
            source=source,
            started_at=started_at,
            finished_at=utc_now_iso(),
            fetched=report.fetched,
            inserted=report.inserted,
            updated=report.updated,
            unchanged=report.unchanged,
            rejected=report.rejected,
        )
        conn.commit()
    except Exception as e:
        report.error = f"{type(e).__name__}: {e}"
        _set_cursor(
            conn,
            source,
            cursor=get_cursor(conn, source),
            error=report.error,
            run_count_delta=1,
            error_count_delta=1,
        )
        _record_run(
            conn,
            source=source,
            started_at=started_at,
            finished_at=utc_now_iso(),
            fetched=report.fetched,
            inserted=report.inserted,
            updated=report.updated,
            unchanged=report.unchanged,
            rejected=report.rejected,
            error_message=report.error,
        )
        conn.commit()
    return report


def _compute_new_cursor(
    conn: sqlite3.Connection,
    source: str,
    raw_orders: list[dict],
    *,
    now_iso: Optional[str] = None,
) -> Optional[str]:
    """根据本批订单的最大 updated_at 推进 cursor。

    异常兜底: 当 fetched>0 但本批订单全部缺 updated_at/paid_at/created_at
    时,不允许 cursor 保持 None 而让 poller 永久卡在同一窗口。
    推进策略: 回退到 ``utc_now_iso()``,用 "本次拉取的时间" 作为新的
    cursor 下界。已知限制: 若上游 API 长期返回无时间戳的订单,可能会
    跳过部分窗口;但这是 fail-forward 策略,优于无限循环。
    """
    candidates: list[str] = []
    for raw in raw_orders:
        ts = raw.get("updated_at") or raw.get("paid_at") or raw.get("created_at")
        if ts:
            candidates.append(str(ts))
    if candidates:
        # ISO8601 字符串可直接字典序比较
        return max(candidates)
    if raw_orders:
        # fetched>0 但本批无任何时间戳,使用当前时间作为推进值
        return now_iso if now_iso is not None else utc_now_iso()
    # 真正空批:沿用旧 cursor(由调用方决定是否更新)
    return get_cursor(conn, source)
