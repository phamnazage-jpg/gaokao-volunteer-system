"""T6.3 用户管理端点测试。

覆盖:
- 鉴权: /api/admin/users 与 /api/admin/users/{user_key} 401
- 列表: 按用户聚合、分页骨架、遮罩展示
- 搜索: 支持手机号 / 姓名关键字
- 详情: 返回该用户的订单明细,且敏感字段保持遮罩
- 未命中: 404
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from data.orders.dao import OrdersDAO
from data.orders.models import Order, generate_order_id


os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-admin-users")


def _iso_at(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _seed_users(db_path: str) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0, hour=12, minute=0, second=0)
    with OrdersDAO.connect(db_path) as dao:
        dao.create(
            Order(
                id=generate_order_id(),
                source="web",
                service_version="basic",
                amount_cents=9900,
                status="pending",
                customer_name="李明",
                customer_phone="13800001234",
                customer_wechat="wx-li",
                candidate_name="李小明",
                candidate_id_card="430102200501011234",
                candidate_province="湖南",
                created_at=_iso_at(now - timedelta(days=1)),
            )
        )
        dao.create(
            Order(
                id=generate_order_id(),
                source="wechat",
                service_version="standard",
                amount_cents=12900,
                status="paid",
                customer_name="李明",
                customer_phone="13800001234",
                customer_wechat="wx-li",
                candidate_name="李小明",
                candidate_id_card="430102200501011234",
                candidate_province="湖南",
                created_at=_iso_at(now),
            )
        )
        dao.create(
            Order(
                id=generate_order_id(),
                source="xianyu",
                service_version="premium",
                amount_cents=15900,
                status="serving",
                customer_name="王芳",
                customer_phone="13911112222",
                customer_wechat="wx-wang",
                candidate_name="王小芳",
                candidate_id_card="430102200601019876",
                candidate_province="浙江",
                created_at=_iso_at(now - timedelta(days=2)),
            )
        )


def test_users_requires_auth(client):
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401


def test_users_list_groups_and_masks_pii(client, auth_headers, settings):
    _seed_users(settings.orders_db_path)

    resp = client.get("/api/admin/users", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["total"] == 2
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["query"] is None
    assert len(body["items"]) == 2

    li = next(item for item in body["items"] if item["customer_phone"] == "138****1234")
    assert li["customer_name"] == "李*"
    assert li["customer_wechat"] == "wx*li"
    assert li["candidate_name"] == "李*明"
    assert li["order_count"] == 2
    assert li["latest_status"] == "paid"
    assert li["total_amount_cents"] == 22800
    assert li["latest_order_at"]


def test_users_search_by_phone_and_name(client, auth_headers, settings):
    _seed_users(settings.orders_db_path)

    by_phone = client.get(
        "/api/admin/users",
        params={"q": "13800001234"},
        headers=auth_headers,
    )
    assert by_phone.status_code == 200
    body = by_phone.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["customer_phone"] == "138****1234"

    by_name = client.get(
        "/api/admin/users",
        params={"q": "王芳"},
        headers=auth_headers,
    )
    assert by_name.status_code == 200
    body = by_name.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_name"] == "王*"


def test_user_detail_returns_masked_orders(client, auth_headers, settings):
    _seed_users(settings.orders_db_path)

    listed = client.get("/api/admin/users", headers=auth_headers)
    user_key = next(
        item["user_key"] for item in listed.json()["items"] if item["order_count"] == 2
    )

    resp = client.get(f"/api/admin/users/{user_key}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["user_key"] == user_key
    assert body["order_count"] == 2
    assert len(body["orders"]) == 2
    assert all(order["customer_phone"] == "138****1234" for order in body["orders"])
    assert all(order["customer_wechat"] == "wx*li" for order in body["orders"])
    assert all(
        order["candidate_id_card"] == "430102********1234" for order in body["orders"]
    )


def test_user_detail_404_for_unknown(client, auth_headers):
    resp = client.get("/api/admin/users/unknown-key", headers=auth_headers)
    assert resp.status_code == 404
