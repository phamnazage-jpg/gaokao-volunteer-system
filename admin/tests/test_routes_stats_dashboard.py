"""T6.2 仪表盘端点测试。

覆盖目标
--------

- ``GET /api/stats/dashboard`` 鉴权 (401 / 200)
- 鉴权通过后返回的 payload 形状稳定
- 空库时:
  - summary 全 0
  - by_status / by_source / by_service_version 完整 0 填充
  - trends.today = 1 点, 7d = 7 点, 30d = 30 点, 全部按日期升序
  - generated_at 是合法 ISO8601 UTC
- 真实写入订单后:
  - summary.total_orders / total_revenue_cents / orders_7d / 趋势 累加正确
  - 收入口径 = 排除 pending 与 refunded
  - 窗口边界 (今日 / 7d / 30d) 切分正确
  - 趋势 0 填充 : 范围内无订单的日也返回 0 点
- 业务隔离 : 订单 DB 与 admin DB 是分开的, admin_users 计数独立
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------


def _insert_order(
    db_path: str,
    *,
    order_id: str,
    status: str,
    source: str = "xianyu",
    service_version: str = "basic",
    amount_cents: int = 10000,
    created_at: str,
) -> None:
    """绕过 OrdersDAO 直接往 orders 表塞测试行 (含 status / amount / created_at)。

    orders 表要求必填字段 ; 测试只关心统计字段,其他可空。
    """
    from admin.db import get_connection

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO orders(
                id, source, external_id, service_version, amount_cents,
                status, status_updated_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                source,
                f"ext-{order_id}",
                service_version,
                int(amount_cents),
                status,
                created_at,
                created_at,
            ),
        )


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_at(d: datetime) -> str:
    return d.replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# 鉴权
# ---------------------------------------------------------------------------


def test_dashboard_requires_auth(client):
    resp = client.get("/api/stats/dashboard")
    assert resp.status_code == 401


def test_dashboard_with_token_returns_200(client, auth_headers):
    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 形状契约 (空库)
# ---------------------------------------------------------------------------


def test_dashboard_empty_db_shape(client, auth_headers):
    """空库时返回完整骨架 — 前端可直接渲染空状态。"""
    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()

    # summary 9 字段
    assert set(body["summary"].keys()) == {
        "total_orders",
        "total_revenue_cents",
        "total_users",
        "orders_today",
        "orders_7d",
        "orders_30d",
        "revenue_today_cents",
        "revenue_7d_cents",
        "revenue_30d_cents",
    }
    # 订单 / 收入 / 窗口切片都应为 0;total_users 由 bootstrap_admin 决定,
    # 这里只要求 >= 1 (conftest 启用了 bootstrap,默认管理员已建)
    for k, v in body["summary"].items():
        if k == "total_users":
            assert v >= 1, k
        else:
            assert isinstance(v, int)
            assert v == 0, k

    # 6 态 / 4 来源 / 4 版本 — 完整 0 填充
    assert body["by_status"] == {
        "pending": 0,
        "paid": 0,
        "serving": 0,
        "delivered": 0,
        "completed": 0,
        "refunded": 0,
    }
    assert body["by_source"] == {"xianyu": 0, "wechat": 0, "web": 0, "school": 0}
    assert body["by_service_version"] == {
        "audit": 0,
        "basic": 0,
        "standard": 0,
        "premium": 0,
    }

    # 趋势: today=1, 7d=7, 30d=30
    assert len(body["trends"]["today"]) == 1
    assert len(body["trends"]["7d"]) == 7
    assert len(body["trends"]["30d"]) == 30

    # generated_at 是 ISO8601 UTC
    ts = body["generated_at"]
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_dashboard_trends_strictly_ascending(client, auth_headers):
    """趋势序列按日期严格升序。"""
    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()

    for key, expected_len in (("today", 1), ("7d", 7), ("30d", 30)):
        points = body["trends"][key]
        assert len(points) == expected_len, key
        dates = [p["date"] for p in points]
        assert dates == sorted(dates), f"{key} not ascending: {dates}"
        # 间隔必须正好 1 天 (含 today=1 也只一个点)
        for prev, cur in zip(dates, dates[1:]):
            d_prev = datetime.fromisoformat(prev).date()
            d_cur = datetime.fromisoformat(cur).date()
            assert (d_cur - d_prev).days == 1, f"{key} gap: {d_prev} → {d_cur}"


def test_dashboard_trends_zero_filled_point_shape(client, auth_headers):
    """0 填充点也必须有完整三字段 (date/orders/revenue_cents)。"""
    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()
    for key in ("today", "7d", "30d"):
        for p in body["trends"][key]:
            assert set(p.keys()) == {"date", "orders", "revenue_cents"}, (key, p)
            assert p["orders"] == 0
            assert p["revenue_cents"] == 0


# ---------------------------------------------------------------------------
# 真实数据
# ---------------------------------------------------------------------------


def _seed_orders(db_path: str, now: datetime) -> List[Dict[str, Any]]:
    """构造一组覆盖各种状态的订单,日期分布在 today / 7d 内 / 30d 内 / 30d 外。

    Returns:
        写入的订单信息列表 (用于断言)
    """
    today_mid = now.replace(hour=12, minute=0, second=0)
    within_7d = now - timedelta(days=3)  # 4 天前
    within_30d = now - timedelta(days=15)  # 15 天前
    outside_30d = now - timedelta(days=45)  # 45 天前 — 应被 30d 窗口排除

    seeds: List[Dict[str, Any]] = [
        # today 一笔 paid
        dict(
            order_id="O-today-1",
            status="paid",
            amount_cents=20000,
            created_at=_iso_at(today_mid),
            source="xianyu",
        ),
        # 4 天前 serving
        dict(
            order_id="O-7d-1",
            status="serving",
            amount_cents=50000,
            created_at=_iso_at(within_7d),
            source="wechat",
        ),
        # 15 天前 completed
        dict(
            order_id="O-30d-1",
            status="completed",
            amount_cents=30000,
            created_at=_iso_at(within_30d),
            source="web",
        ),
        # 45 天前 (应被 30d 窗口排除) pending
        dict(
            order_id="O-out-1",
            status="pending",
            amount_cents=99999,
            created_at=_iso_at(outside_30d),
            source="xianyu",
        ),
        # today pending (应不计入收入)
        dict(
            order_id="O-pending-today",
            status="pending",
            amount_cents=88888,
            created_at=_iso_at(today_mid + timedelta(hours=1)),
            source="school",
        ),
        # today refunded (应不计入收入)
        dict(
            order_id="O-refunded-today",
            status="refunded",
            amount_cents=77777,
            created_at=_iso_at(today_mid + timedelta(hours=2)),
            source="xianyu",
        ),
    ]
    for s in seeds:
        _insert_order(
            db_path,
            order_id=s["order_id"],
            status=s["status"],
            amount_cents=s["amount_cents"],
            created_at=s["created_at"],
            source=s["source"],
        )
    return seeds


def test_dashboard_summary_excludes_30d_outside_orders(client, auth_headers, settings):
    """45 天前的订单不在 30d 窗口内,但应计入 total_orders / total_revenue_cents (paid+ 的话)。"""
    db = settings.orders_db_path
    _seed_orders(db, _now_utc())

    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()
    summary = body["summary"]

    # 总订单:全部 6 笔
    assert summary["total_orders"] == 6

    # 收入:仅 paid(2w) + serving(5w) + completed(3w) = 10w
    # (pending / refunded 不计入)
    assert summary["total_revenue_cents"] == 20000 + 50000 + 30000

    # today orders: O-today-1(paid) + O-pending-today(pending) + O-refunded-today(refunded) = 3
    assert summary["orders_today"] == 3
    # today revenue: 仅 O-today-1(20000),pending/refunded 排除
    assert summary["revenue_today_cents"] == 20000

    # 7d: today(3) + within_7d(1, serving) = 4
    assert summary["orders_7d"] == 4
    assert summary["revenue_7d_cents"] == 20000 + 50000

    # 30d: 7d(4) + within_30d(1, completed) = 5 (45 天前被排除)
    assert summary["orders_30d"] == 5
    assert summary["revenue_30d_cents"] == 20000 + 50000 + 30000

    # 至少 1 个管理员 (bootstrap admin) — 这里具体值不重要,但必须 >= 1
    assert summary["total_users"] >= 1


def test_dashboard_by_status_counts_seeded_orders(client, auth_headers, settings):
    db = settings.orders_db_path
    _seed_orders(db, _now_utc())

    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()

    # seeds: paid(1) + serving(1) + completed(1) + pending(2) + refunded(1) = 6
    assert body["by_status"]["paid"] == 1
    assert body["by_status"]["serving"] == 1
    assert body["by_status"]["completed"] == 1
    assert body["by_status"]["pending"] == 2  # today pending + 45d pending
    assert body["by_status"]["refunded"] == 1
    assert body["by_status"]["delivered"] == 0


def test_dashboard_by_source_and_service_version(client, auth_headers, settings):
    db = settings.orders_db_path
    _insert_order(
        db,
        order_id="A",
        status="paid",
        source="xianyu",
        service_version="basic",
        amount_cents=1000,
        created_at=_iso_at(_now_utc()),
    )
    _insert_order(
        db,
        order_id="B",
        status="paid",
        source="xianyu",
        service_version="standard",
        amount_cents=1000,
        created_at=_iso_at(_now_utc()),
    )
    _insert_order(
        db,
        order_id="C",
        status="paid",
        source="wechat",
        service_version="premium",
        amount_cents=1000,
        created_at=_iso_at(_now_utc()),
    )

    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()

    assert body["by_source"]["xianyu"] == 2
    assert body["by_source"]["wechat"] == 1
    assert body["by_source"]["web"] == 0
    assert body["by_source"]["school"] == 0

    assert body["by_service_version"]["basic"] == 1
    assert body["by_service_version"]["standard"] == 1
    assert body["by_service_version"]["premium"] == 1
    assert body["by_service_version"]["audit"] == 0


def test_dashboard_trends_today_only_contains_today(client, auth_headers, settings):
    """今日 trend 只包含今天一天的聚合,值与 summary.revenue_today_cents 一致。"""
    db = settings.orders_db_path
    now = _now_utc()
    today_iso = now.date().isoformat()
    # 2 笔 today paid
    _insert_order(
        db,
        order_id="T1",
        status="paid",
        amount_cents=1100,
        created_at=_iso_at(now.replace(hour=10)),
    )
    _insert_order(
        db,
        order_id="T2",
        status="paid",
        amount_cents=2200,
        created_at=_iso_at(now.replace(hour=20)),
    )
    # 1 笔 5 天前 paid (不在 today 内)
    five_ago = (now - timedelta(days=5)).replace(hour=10)
    _insert_order(
        db,
        order_id="T3",
        status="paid",
        amount_cents=99999,
        created_at=_iso_at(five_ago),
    )

    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()
    today_points = body["trends"]["today"]
    assert len(today_points) == 1
    assert today_points[0]["date"] == today_iso
    assert today_points[0]["orders"] == 2
    assert today_points[0]["revenue_cents"] == 3300  # 1100 + 2200 (T3 排除)

    # 7d 应包含 T3
    seven_total_orders = sum(p["orders"] for p in body["trends"]["7d"])
    seven_total_revenue = sum(p["revenue_cents"] for p in body["trends"]["7d"])
    assert seven_total_orders == 3
    assert seven_total_revenue == 1100 + 2200 + 99999


def test_dashboard_trends_zero_fills_gaps(client, auth_headers, settings):
    """窗口内无订单的日也要返回 0 点 (前端不会拿到空洞数组)。"""
    db = settings.orders_db_path
    now = _now_utc()
    five_ago = (now - timedelta(days=5)).replace(hour=10)
    _insert_order(
        db,
        order_id="Lone",
        status="paid",
        amount_cents=500,
        created_at=_iso_at(five_ago),
    )

    resp = client.get("/api/stats/dashboard", headers=auth_headers)
    body = resp.json()
    seven = body["trends"]["7d"]
    assert len(seven) == 7

    # 5 天前那一笔: 恰好 1 个点是 {orders: 1, revenue_cents: 500}
    lone_points = [p for p in seven if p["orders"] > 0]
    assert len(lone_points) == 1
    assert lone_points[0]["orders"] == 1
    assert lone_points[0]["revenue_cents"] == 500

    # 其余 6 个点全 0
    zero_points = [p for p in seven if p["orders"] == 0]
    assert len(zero_points) == 6
    for p in zero_points:
        assert p["revenue_cents"] == 0


# ---------------------------------------------------------------------------
# /api/stats/orders 兼容老契约
# ---------------------------------------------------------------------------


def test_stats_orders_real_shape_full_fields(client, auth_headers, settings):
    """``/api/stats/orders`` 老端点 5 字段契约,字段名不变,数据真实。"""
    db = settings.orders_db_path
    now = _now_utc()
    _insert_order(
        db,
        order_id="legacy-1",
        status="paid",
        amount_cents=12345,
        created_at=_iso_at(now),
        source="xianyu",
        service_version="basic",
    )

    resp = client.get("/api/stats/orders", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_orders"] == 1
    assert body["total_revenue_cents"] == 12345
    assert body["by_status"]["paid"] == 1
    assert body["by_source"]["xianyu"] == 1
    assert body["by_service_version"]["basic"] == 1
    # 旧契约: 不应有 dashboard 专属字段
    assert "summary" not in body
    assert "trends" not in body
    assert "total_users" not in body
    # _stub 标记已移除
    assert "_stub" not in body
