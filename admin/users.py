"""管理后台用户管理聚合 (T6.3).

用户管理的口径基于 orders 表中的下单人/考生信息做聚合:
- 有手机号时按 customer_phone_hash 聚合
- 无手机号时退回 customer_wechat 指纹
- 再退回订单号,避免丢失孤立记录

公开 API:
- build_user_list_payload : 用户列表 + 搜索 + 分页
- build_user_detail_payload : 用户详情 + 订单明细
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Optional

from admin.db import get_connection
from data.orders.crypto import hash_for_index
from data.orders.models import Order


_USER_LIST_DEFAULT_LIMIT = 50
_USER_LIST_MAX_LIMIT = 200


@dataclass(frozen=True)
class UserOrderRecord:
    order: Order

    def to_dict(self) -> dict[str, Any]:
        return self.order.to_dict(decrypt_sensitive="mask")


@dataclass(frozen=True)
class UserSummary:
    user_key: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_wechat: Optional[str]
    candidate_name: Optional[str]
    candidate_province: Optional[str]
    order_count: int
    total_amount_cents: int
    latest_order_at: Optional[str]
    latest_status: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_key": self.user_key,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_wechat": self.customer_wechat,
            "candidate_name": self.candidate_name,
            "candidate_province": self.candidate_province,
            "order_count": int(self.order_count),
            "total_amount_cents": int(self.total_amount_cents),
            "latest_order_at": self.latest_order_at,
            "latest_status": self.latest_status,
        }


@dataclass(frozen=True)
class UserDetail(UserSummary):
    orders: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["orders"] = list(self.orders)
        return data


_PHONE_SPLIT_RE = re.compile(r"[\s\-+()]")
_NON_DIGIT_RE = re.compile(r"\D+")


def _normalize_phone(value: Optional[str]) -> str:
    if value is None:
        return ""
    s = _PHONE_SPLIT_RE.sub("", value.strip())
    s = _NON_DIGIT_RE.sub("", s)
    if len(s) > 11 and s.startswith("86"):
        s = s[2:]
    return s


def _wechat_fingerprint(value: Optional[str]) -> str:
    if value is None:
        return ""
    s = value.strip().lower()
    if not s:
        return ""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _user_key(order: Order) -> str:
    phone = _normalize_phone(order.customer_phone)
    if phone:
        return f"phone:{order.customer_phone_hash or phone}"
    wechat = _wechat_fingerprint(order.customer_wechat)
    if wechat:
        return f"wechat:{wechat}"
    return f"order:{order.id}"


def _load_orders(orders_db_path: str) -> list[Order]:
    with get_connection(orders_db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [Order.from_db_row(dict(row)) for row in rows]


def _matches_query(order: Order, query: str) -> bool:
    needle = query.strip().lower()
    if not needle:
        return True
    phone = _normalize_phone(query)
    if phone:
        if _normalize_phone(order.customer_phone) == phone:
            return True
        if (
            order.customer_phone_hash
            and order.customer_phone_hash
            == hash_for_index(phone)
        ):
            return True
    haystack = [
        order.id,
        order.external_id,
        order.source,
        order.service_version,
        order.status,
        order.customer_name,
        order.customer_phone,
        order.customer_wechat,
        order.candidate_name,
        order.candidate_province,
        order.candidate_interests,
        order.candidate_strong_subjects,
        order.candidate_weak_subjects,
        order.candidate_family,
        order.assigned_consultant,
        order.notes,
    ]
    return any(needle in (value or "").lower() for value in haystack)


def _group_orders(
    orders: list[Order], query: Optional[str] = None
) -> list[tuple[str, list[Order]]]:
    groups: dict[str, list[Order]] = {}
    order_keys: list[str] = []
    for order in orders:
        if query and not _matches_query(order, query):
            continue
        key = _user_key(order)
        if key not in groups:
            groups[key] = []
            order_keys.append(key)
        groups[key].append(order)
    return [(key, groups[key]) for key in order_keys]


def _build_summary(user_key: str, orders: list[Order]) -> UserSummary:
    latest = orders[0]
    total_amount_cents = sum(int(o.amount_cents or 0) for o in orders)
    masked = latest.to_dict(decrypt_sensitive="mask")
    return UserSummary(
        user_key=user_key,
        customer_name=masked.get("customer_name"),
        customer_phone=masked.get("customer_phone"),
        customer_wechat=masked.get("customer_wechat"),
        candidate_name=masked.get("candidate_name"),
        candidate_province=masked.get("candidate_province"),
        order_count=len(orders),
        total_amount_cents=total_amount_cents,
        latest_order_at=latest.created_at,
        latest_status=latest.status,
    )


def _build_detail(user_key: str, orders: list[Order]) -> UserDetail:
    summary = _build_summary(user_key, orders)
    return UserDetail(
        **summary.__dict__,
        orders=[UserOrderRecord(order=o).to_dict() for o in orders],
    )


def _paginate_groups(
    groups: list[tuple[str, list[Order]]],
    *,
    limit: int,
    offset: int,
) -> list[tuple[str, list[Order]]]:
    return groups[offset : offset + limit]


def build_user_list_payload(
    orders_db_path: str,
    *,
    query: Optional[str] = None,
    limit: int = _USER_LIST_DEFAULT_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    """返回用户列表 payload。"""
    if not (1 <= limit <= _USER_LIST_MAX_LIMIT):
        raise ValueError(f"limit 越界 (1..{_USER_LIST_MAX_LIMIT}): {limit}")
    if offset < 0:
        raise ValueError(f"offset 不能为负: {offset}")

    orders = _load_orders(orders_db_path)
    groups = _group_orders(orders, query=query)
    total = len(groups)
    page = _paginate_groups(groups, limit=limit, offset=offset)
    items = [_build_summary(key, grouped).to_dict() for key, grouped in page]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": query,
        "items": items,
    }


def build_user_detail_payload(orders_db_path: str, user_key: str) -> dict[str, Any]:
    """返回单个用户详情 payload。"""
    orders = _load_orders(orders_db_path)
    for key, grouped in _group_orders(orders):
        if key == user_key:
            return _build_detail(key, grouped).to_dict()
    raise LookupError(user_key)
