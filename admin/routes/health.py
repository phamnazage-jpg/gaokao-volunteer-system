"""健康检查路由 (T6.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.config import Settings, get_settings_dep


router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health(settings: Settings = Depends(get_settings_dep)) -> dict:
    """公开端点。返回服务状态 + DB 路径 + 环境。

    不依赖数据库查询,只验证服务进程可响应。
    """
    return {
        "status": "ok",
        "env": settings.env,
        "db_path": settings.db_path,
        "service": "gaokao-admin",
        "version": "0.1.0",
    }
