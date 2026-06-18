"""用户管理路由 (T6.3).

当前范围:
- GET /api/admin/users      用户列表（聚合 + 搜索 + 脱敏）
- GET /api/admin/users/{user_key} 用户详情（含订单明细,默认脱敏）
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel

from admin.auth import get_current_user, require_role
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser
from admin.errors import DATA_NOT_FOUND
from admin.errors.exceptions import BusinessError
from admin.users import build_user_detail_payload, build_user_list_payload


router = APIRouter(prefix="/api/admin/users", tags=["users"])


class UserSummaryResponse(BaseModel):
    user_key: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_wechat: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_province: Optional[str] = None
    order_count: int
    total_amount_cents: int
    latest_order_at: Optional[str] = None
    latest_status: Optional[str] = None


class UserListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    query: Optional[str] = None
    items: list[UserSummaryResponse]


class UserDetailResponse(UserSummaryResponse):
    orders: list[dict[str, Any]]


@router.get("", response_model=UserListResponse, summary="用户列表（T6.3）")
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(
        None, min_length=1, description="姓名/手机号/微信/订单号搜索"
    ),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    return build_user_list_payload(
        settings.orders_db_path,
        query=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_key}",
    response_model=UserDetailResponse,
    summary="用户详情（T6.3）",
)
def get_user_detail(
    user_key: str = Path(..., min_length=1),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    try:
        return build_user_detail_payload(settings.orders_db_path, user_key)
    except LookupError as exc:
        raise BusinessError(DATA_NOT_FOUND, detail={"user_key": user_key}) from exc
