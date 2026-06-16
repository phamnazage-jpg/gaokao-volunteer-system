"""统计路由 (T6.1 → T6.2 接入真实聚合).

T6.2 接入模块
-------------

- ``GET /api/stats/dashboard`` : 仪表盘一站式 payload
  (订单/用户/收入 汇总 + 6 态/来源/版本 分布 + 今日/7d/30d 趋势)
- ``GET /api/stats/orders``    : 订单维度统计 (沿用 T6.1 stub 字段名,
  移除 ``_stub`` 标记,接入真实 SQL 聚合)

所有路由均要求 JWT 鉴权;鉴权与权限边界与 T6.1 一致。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from admin.auth import get_current_user
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser
from admin.stats import (
    build_dashboard_payload,
    build_order_stats_payload,
)


router = APIRouter(prefix="/api/stats", tags=["stats"])
admin_router = APIRouter(prefix="/api/admin/stats", tags=["stats"])


class DashboardResponse(BaseModel):
    """``/api/stats/dashboard`` 响应契约。"""

    summary: dict
    by_status: dict
    by_source: dict
    by_service_version: dict
    trends: dict
    generated_at: str


class OrderStatsResponse(BaseModel):
    """``/api/stats/orders`` 响应契约 (沿用 T6.1 字段名,仅替换数据源)。"""

    total_orders: int
    total_revenue_cents: int
    by_status: dict
    by_source: dict
    by_service_version: dict


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="仪表盘统计（T6.2）",
    description=(
        "返回管理后台仪表盘完整 payload: "
        "summary(订单/用户/收入 + 今日/7d/30d 切片) + 6 态分布 + "
        "来源分布 + 服务版本分布 + 今日/7d/30d 趋势序列 (日粒度, 0 填充)。"
    ),
)
@admin_router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="仪表盘统计（T6.2）",
    description=(
        "返回管理后台仪表盘完整 payload: "
        "summary(订单/用户/收入 + 今日/7d/30d 切片) + 6 态分布 + "
        "来源分布 + 服务版本分布 + 今日/7d/30d 趋势序列 (日粒度, 0 填充)。"
    ),
)
def get_dashboard(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> dict:
    """仪表盘端点 — T6.2 真实聚合。

    实现位置在 :mod:`admin.stats` 纯函数层,与路由层解耦:
    - 业务测试可单独覆盖 SQL 聚合正确性
    - 路由层只负责鉴权 + 响应包装

    数据源:
    - ``orders`` 表 → 走 ``settings.orders_db_path`` (与 data.orders.* 共享)
    - ``admin_users`` 表 → 走 ``settings.db_path`` (管理后台)
    """
    return build_dashboard_payload(
        orders_db_path=settings.orders_db_path,
        admin_db_path=settings.db_path,
    )


@router.get(
    "/orders",
    response_model=OrderStatsResponse,
    summary="订单维度统计（T6.2 真实聚合）",
    description=(
        "订单维度统计:T6.1 阶段为占位,T6.2 接入真实 SQL 聚合。"
        "字段名保持 T6.1 stub 阶段不变,前端旧契约不破。"
    ),
)
@admin_router.get(
    "/orders",
    response_model=OrderStatsResponse,
    summary="订单维度统计（T6.2 真实聚合）",
    description=(
        "订单维度统计:T6.1 阶段为占位,T6.2 接入真实 SQL 聚合。"
        "字段名保持 T6.1 stub 阶段不变,前端旧契约不破。"
    ),
)
def get_order_stats(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> dict:
    """订单维度统计端点 — T6.2 真实聚合。"""
    return build_order_stats_payload(settings.orders_db_path)
