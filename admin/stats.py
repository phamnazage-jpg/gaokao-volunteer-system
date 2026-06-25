"""管理后台仪表盘统计 (T6.2).

提供一组纯函数,接受 db_path 返回仪表盘 payload。SQL 聚合在
:mod:`data.orders.dao.OrdersDAO` 之外的轻量连接里直接执行 (避免
DAO 解密 PII 字段带来的开销) — 统计只涉及 ``status`` /
``source`` / ``service_version`` / ``amount_cents`` / ``created_at`` 等
非敏感列。

公开 API
--------

- :func:`build_dashboard_payload` : 一次返回 dashboard 全部数据
- :func:`compute_summary`         : 汇总卡片 (订单/用户/收入 + 今日/7d/30d)
- :func:`compute_by_status`       : 6 态分布
- :func:`compute_by_source`       : 来源分布
- :func:`compute_by_service_version` : 服务版本分布
- :func:`compute_trends`          : 今日 / 7d / 30d 趋势 (日粒度)
- :func:`generate_day_series`     : 趋势补零辅助 (0 填充生成完整序列)

口径约定
--------

- **收入 (revenue)** = 所有 **非 pending 且非 refunded** 订单的
  ``amount_cents`` 累计值。pending 表示未付款,refunded 表示已退款,
  两者均不计入有效收入。
- **趋势桶粒度** = 日 (UTC 日期, ``YYYY-MM-DD``)。ISO8601 字符串的
  前 10 位切片 (``substr(created_at, 1, 10)``) 与 UTC 日期等价。
- **"今日"** = 服务器当前 UTC 日;**7d/30d** = 含今日回溯 7/30 个
  完整日。窗口外的点会被丢弃,缺失日以 0 填充。
- **不读 PII** : 统计路径只触碰 ``amount_cents``/``status``/``source``
  /``service_version``/``created_at``,避免进入加密层。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from admin.db import get_connection


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 收入口径:进入这些状态的订单算有效收入 (paid 之后才付款, refunded 排除)
_REVENUE_STATUSES: tuple[str, ...] = (
    "paid",
    "serving",
    "delivered",
    "completed",
)

# 完整 6 态 (分布统计时强制输出 0 计数)
_ALL_STATUSES: tuple[str, ...] = (
    "pending",
    "paid",
    "serving",
    "delivered",
    "completed",
    "refunded",
)

# 完整来源 (与 meta.py 对齐)
_ALL_SOURCES: tuple[str, ...] = ("xianyu", "wechat", "web", "school")

# 完整服务版本
_ALL_SERVICE_VERSIONS: tuple[str, ...] = ("audit", "basic", "standard", "premium")


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrendPoint:
    """单日趋势点。"""

    date: str  # YYYY-MM-DD
    orders: int
    revenue_cents: int

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "orders": int(self.orders),
            "revenue_cents": int(self.revenue_cents),
        }


# ---------------------------------------------------------------------------
# 时间窗口辅助
# ---------------------------------------------------------------------------


def _utc_today() -> datetime:
    """返回当前 UTC 的午夜 (00:00:00)。"""
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _date_range(end: datetime, days: int) -> List[str]:
    """返回 end 当天及之前 ``days`` 个 UTC 日期字符串 (含端点)。"""
    return [
        (end - timedelta(days=i)).date().isoformat() for i in range(days - 1, -1, -1)
    ]


def _format_utc_now_iso() -> str:
    """当前 UTC 时间的 ISO8601 字符串 (秒精度)。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# 单查询辅助
# ---------------------------------------------------------------------------


def _open_conn(db_path: str) -> sqlite3.Connection:
    """打开 SQLite 连接 (统一走 admin.db.get_connection 避免 PRAGMA 分裂)。"""
    return get_connection(db_path)


def _fetchall_dict(
    conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()
) -> List[dict]:
    """执行查询并以 dict 形式返回全部行。"""
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    out: List[dict] = []
    for row in rows:
        # sqlite3.Row 走 keys() + 索引; tuple 走索引
        if hasattr(row, "keys"):
            out.append({k: row[k] for k in row.keys()})
        else:
            out.append(dict(row))
    return out


# ---------------------------------------------------------------------------
# 聚合函数
# ---------------------------------------------------------------------------


def compute_summary(
    orders_db_path: str,
    admin_db_path: Optional[str] = None,
    *,
    today: Optional[datetime] = None,
) -> dict:
    """汇总卡片:订单/用户/收入/待处理多口径,以及今日/7d/30d 三个窗口的切片。

    待处理订单 (pending_orders) 提供三个互不互斥的视角,用于运营快速分流:
      - pending_orders             : 所有 status='pending' 的订单数
      - pending_overdue_24h        : 24h 内仍未付款的待处理订单(超时未付,需主动催付)
      - pending_missing_intake     : 未提交完整报名资料的待处理订单(资料待补,需主动跟进)

    Args:
        orders_db_path: orders / order_status_history / order_intakes 所在 DB (data.orders.*)
        admin_db_path: admin_users 所在 DB;传 None 时跳过用户统计,返回 0
        today: 测试可注入的"当前 UTC 日" (默认 = 真实 now)

    Returns:
        dict 形如::

            {
                "total_orders":         int,
                "total_revenue_cents":  int,
                "total_users":          int,
                "pending_orders":       int,
                "pending_overdue_24h":  int,
                "pending_missing_intake": int,
                "orders_today":         int,
                "orders_7d":            int,
                "orders_30d":           int,
                "revenue_today_cents":  int,
                "revenue_7d_cents":     int,
                "revenue_30d_cents":    int,
            }
    """
    if today is None:
        today = _utc_today()
    today_iso = today.date().isoformat()
    seven_ago = (today - timedelta(days=6)).date().isoformat()  # 7 天窗口含今天
    thirty_ago = (today - timedelta(days=29)).date().isoformat()  # 30 天窗口含今天
    # 24h 超时切割点: 当前 UTC 时刻往前 24h, ISO8601 字符串
    overdue_cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(microsecond=0).isoformat()

    revenue_status_placeholder = ",".join("?" for _ in _REVENUE_STATUSES)

    with _open_conn(orders_db_path) as conn:
        # 总订单数 / 总收入 / 待处理多口径 (一次性走单条聚合 SQL)
        # pending_missing_intake 走 LEFT JOIN order_intakes 判定:
        #   - 没记录 OR 记录 status='draft'  → 资料未提交完整
        #   - 记录 status='submitted'        → 资料已完整, 不算缺失
        row = conn.execute(
                f"""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(
                    CASE WHEN orders.status IN ({revenue_status_placeholder})
                         THEN amount_cents ELSE 0 END
                ), 0) AS total_revenue_cents,
                COALESCE(SUM(
                    CASE WHEN orders.status = 'pending' THEN 1 ELSE 0 END
                ), 0) AS pending_orders,
                COALESCE(SUM(
                    CASE WHEN orders.status = 'pending' AND orders.created_at < ?
                         THEN 1 ELSE 0 END
                ), 0) AS pending_overdue_24h,
                COALESCE(SUM(
                    CASE WHEN orders.status = 'pending' AND (
                        i.status IS NULL OR i.status = 'draft'
                    ) THEN 1 ELSE 0 END
                ), 0) AS pending_missing_intake
            FROM orders
            LEFT JOIN order_intakes AS i ON i.order_id = orders.id
            """,
            (*_REVENUE_STATUSES, overdue_cutoff),
        ).fetchone()

        # 今日 / 7d / 30d 切片 (用 substr 切日期)
        slice_row = conn.execute(
            f"""
            SELECT
                COALESCE(SUM(
                    CASE WHEN substr(created_at, 1, 10) = ? THEN 1 ELSE 0 END
                ), 0) AS orders_today,
                COALESCE(SUM(
                    CASE WHEN substr(created_at, 1, 10) >= ? THEN 1 ELSE 0 END
                ), 0) AS orders_7d,
                COALESCE(SUM(
                    CASE WHEN substr(created_at, 1, 10) >= ? THEN 1 ELSE 0 END
                ), 0) AS orders_30d,
                COALESCE(SUM(
                    CASE WHEN substr(created_at, 1, 10) = ?
                          AND status IN ({revenue_status_placeholder})
                         THEN amount_cents ELSE 0 END
                ), 0) AS revenue_today_cents,
                COALESCE(SUM(
                    CASE WHEN substr(created_at, 1, 10) >= ?
                          AND status IN ({revenue_status_placeholder})
                         THEN amount_cents ELSE 0 END
                ), 0) AS revenue_7d_cents,
                COALESCE(SUM(
                    CASE WHEN substr(created_at, 1, 10) >= ?
                          AND status IN ({revenue_status_placeholder})
                         THEN amount_cents ELSE 0 END
                ), 0) AS revenue_30d_cents
            FROM orders
            """,
            (
                today_iso,
                seven_ago,
                thirty_ago,
                today_iso,
                *_REVENUE_STATUSES,
                seven_ago,
                *_REVENUE_STATUSES,
                thirty_ago,
                *_REVENUE_STATUSES,
            ),
        ).fetchone()


    # 用户数 (单独连接 admin DB,避免在 orders DB 上去找可能不存在的表)
    total_users = 0
    if admin_db_path is not None:
        with _open_conn(admin_db_path) as conn:
            user_row = conn.execute("SELECT COUNT(*) AS n FROM admin_users").fetchone()
            total_users = int(user_row["n"] or 0)

    return {
        "total_orders": int(row["total_orders"] or 0),
        "total_revenue_cents": int(row["total_revenue_cents"] or 0),
        "total_users": total_users,
        "pending_orders": int(row["pending_orders"] or 0),
        "pending_overdue_24h": int(row["pending_overdue_24h"] or 0),
        "pending_missing_intake": int(row["pending_missing_intake"] or 0),
        "orders_today": int(slice_row["orders_today"] or 0),
        "orders_7d": int(slice_row["orders_7d"] or 0),
        "orders_30d": int(slice_row["orders_30d"] or 0),
        "revenue_today_cents": int(slice_row["revenue_today_cents"] or 0),
        "revenue_7d_cents": int(slice_row["revenue_7d_cents"] or 0),
        "revenue_30d_cents": int(slice_row["revenue_30d_cents"] or 0),
    }


def compute_by_status(db_path: str) -> Dict[str, int]:
    """按 status 分组统计订单数,缺失的 6 态以 0 填充。"""
    with _open_conn(db_path) as conn:
        rows = _fetchall_dict(
            conn,
            "SELECT status, COUNT(*) AS n FROM orders GROUP BY status",
        )
    result: Dict[str, int] = {s: 0 for s in _ALL_STATUSES}
    for r in rows:
        s = str(r.get("status", ""))
        if s in result:
            result[s] = int(r.get("n", 0) or 0)
    return result


def compute_by_source(db_path: str) -> Dict[str, int]:
    """按 source 分组统计订单数,缺失的来源以 0 填充。"""
    with _open_conn(db_path) as conn:
        rows = _fetchall_dict(
            conn,
            "SELECT source, COUNT(*) AS n FROM orders GROUP BY source",
        )
    result: Dict[str, int] = {s: 0 for s in _ALL_SOURCES}
    for r in rows:
        s = str(r.get("source", ""))
        if s in result:
            result[s] = int(r.get("n", 0) or 0)
    return result


def compute_by_service_version(db_path: str) -> Dict[str, int]:
    """按 service_version 分组统计订单数,缺失版本以 0 填充。"""
    with _open_conn(db_path) as conn:
        rows = _fetchall_dict(
            conn,
            "SELECT service_version, COUNT(*) AS n FROM orders GROUP BY service_version",
        )
    result: Dict[str, int] = {s: 0 for s in _ALL_SERVICE_VERSIONS}
    for r in rows:
        s = str(r.get("service_version", ""))
        if s in result:
            result[s] = int(r.get("n", 0) or 0)
    return result


def generate_day_series(
    db_path: str, *, days: int, today: Optional[datetime] = None
) -> List[TrendPoint]:
    """按日粒度聚合订单数 + 收入(收入走 :data:`_REVENUE_STATUSES` 口径),并 0 填充空日。

    Args:
        db_path: SQLite 路径
        days: 窗口大小 (7 / 30);含今天,共生成 ``days`` 个点
        today: 测试可注入的"当前 UTC 日"

    Returns:
        按日期升序排列的 :class:`TrendPoint` 列表,长度 = ``days``。
    """
    if days <= 0:
        raise ValueError(f"days 必须 >= 1, 得到 {days}")
    if today is None:
        today = _utc_today()
    end = today
    start = end - timedelta(days=days - 1)
    start_iso = start.date().isoformat()
    end_iso = end.date().isoformat()
    date_keys = _date_range(end, days)

    revenue_status_placeholder = ",".join("?" for _ in _REVENUE_STATUSES)

    sql = f"""
        SELECT
            substr(created_at, 1, 10) AS day,
            COUNT(*) AS orders,
            COALESCE(SUM(
                CASE WHEN status IN ({revenue_status_placeholder})
                     THEN amount_cents ELSE 0 END
            ), 0) AS revenue_cents
        FROM orders
        WHERE substr(created_at, 1, 10) >= ?
          AND substr(created_at, 1, 10) <= ?
        GROUP BY substr(created_at, 1, 10)
    """
    params: List[Any] = [*_REVENUE_STATUSES, start_iso, end_iso]

    with _open_conn(db_path) as conn:
        rows = _fetchall_dict(conn, sql, params)

    by_day: Dict[str, TrendPoint] = {}
    for r in rows:
        day = str(r.get("day") or "")
        if not day:
            continue
        by_day[day] = TrendPoint(
            date=day,
            orders=int(r.get("orders", 0) or 0),
            revenue_cents=int(r.get("revenue_cents", 0) or 0),
        )

    return [
        by_day.get(d, TrendPoint(date=d, orders=0, revenue_cents=0)) for d in date_keys
    ]


def compute_trends(
    db_path: str, *, today: Optional[datetime] = None
) -> Dict[str, List[dict]]:
    """返回今日 / 7d / 30d 三个窗口的趋势点 (每个点 to_dict)。

    "今日" 返回 1 个点 (当前 UTC 日); 7d / 30d 分别返回 7 / 30 个点。
    """
    return {
        "today": [
            p.to_dict() for p in generate_day_series(db_path, days=1, today=today)
        ],
        "7d": [p.to_dict() for p in generate_day_series(db_path, days=7, today=today)],
        "30d": [
            p.to_dict() for p in generate_day_series(db_path, days=30, today=today)
        ],
    }


# ---------------------------------------------------------------------------
# 顶层 payload
# ---------------------------------------------------------------------------


def build_dashboard_payload(
    orders_db_path: str,
    admin_db_path: Optional[str] = None,
    *,
    today: Optional[datetime] = None,
) -> dict:
    """组装仪表盘一站式 payload,供 ``GET /api/stats/dashboard`` 渲染。

    Args:
        orders_db_path: orders / order_status_history 所在 DB
        admin_db_path: admin_users 所在 DB (传 None 时 ``total_users`` 为 0)
        today: 测试可注入的"当前 UTC 日"

    Returns:
        dict,字段详见模块 docstring。空库也返回完整骨架 (全 0 计数 + 完整
        趋势序列),前端可直接渲染。
    """
    return {
        "summary": compute_summary(
            orders_db_path, admin_db_path=admin_db_path, today=today
        ),
        "by_status": compute_by_status(orders_db_path),
        "by_source": compute_by_source(orders_db_path),
        "by_service_version": compute_by_service_version(orders_db_path),
        "trends": compute_trends(orders_db_path, today=today),
        "generated_at": _format_utc_now_iso(),
    }


# ---------------------------------------------------------------------------
# 兼容层 — /api/stats/orders 老端点
# ---------------------------------------------------------------------------
#
# T6.1 时挂在 ``/api/stats/orders`` 上的占位端点 (返回 ``_stub=True``)
# 在 T6.2 被赋以"订单维度统计"的实际意义,前端若还在用旧契约 (只读
# by_status / by_source / by_service_version / total_orders /
# total_revenue_cents) 不会破。前端新接 dashboard 端点可获完整聚合。
# ---------------------------------------------------------------------------


def build_order_stats_payload(
    orders_db_path: str,
    admin_db_path: Optional[str] = None,
    *,
    today: Optional[datetime] = None,
) -> dict:
    """``/api/stats/orders`` 真实数据。

    字段集 = :func:`build_dashboard_payload` 的"订单子集",保持 T6.1
    stub 阶段的字段名不变,避免前端破契约。

    Args:
        orders_db_path: orders / order_status_history 所在 DB
        admin_db_path: 当前未使用 (T6.2 端点不含 user 字段),保留便于未来扩展
        today: 测试可注入的"当前 UTC 日"
    """
    del admin_db_path  # 当前未消费,显式忽略
    summary = compute_summary(orders_db_path, today=today)
    return {
        "total_orders": summary["total_orders"],
        "total_revenue_cents": summary["total_revenue_cents"],
        "by_status": compute_by_status(orders_db_path),
        "by_source": compute_by_source(orders_db_path),
        "by_service_version": compute_by_service_version(orders_db_path),
    }


__all__ = [
    "TrendPoint",
    "build_dashboard_payload",
    "build_order_stats_payload",
    "compute_summary",
    "compute_by_status",
    "compute_by_source",
    "compute_by_service_version",
    "compute_trends",
    "generate_day_series",
]
