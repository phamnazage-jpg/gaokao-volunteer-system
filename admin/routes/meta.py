"""元数据路由 (T6.1).

提供客户端需要的固定枚举值,避免前端硬编码。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.auth import get_current_user
from admin.db import AdminUser


router = APIRouter(prefix="/api/meta", tags=["meta"])


# MVP 阶段仅返回 27 省中已实现规范检查器的省份
SUPPORTED_PROVINCES = [
    "湖南",
    "广东",
    "湖北",
    "安徽",
    "江西",
    "甘肃",
    "黑龙江",
    "江苏",
    "福建",
    "广西",
    "北京",
    "上海",
    "天津",
    "海南",
    "浙江",
    "山东",
    "河北",
    "重庆",
    "辽宁",
    "贵州",
    "青海",
    "吉林",
    "河南",
    "四川",
    "新疆",
    "云南",
    "西藏",
]

ORDER_STATUSES = [
    "pending",
    "paid",
    "serving",
    "delivered",
    "completed",
    "refunded",
]

ORDER_SOURCES = ["xianyu", "wechat", "web", "school"]

SERVICE_VERSIONS = ["audit", "basic", "standard", "premium"]


@router.get("", summary="元数据枚举")
def meta(_: AdminUser = Depends(get_current_user)) -> dict:
    return {
        "supported_provinces": SUPPORTED_PROVINCES,
        "order_statuses": ORDER_STATUSES,
        "order_sources": ORDER_SOURCES,
        "service_versions": SERVICE_VERSIONS,
    }
