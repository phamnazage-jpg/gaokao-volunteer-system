"""健康检查路由 (T6.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.config import Settings, get_settings_dep


router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health(settings: Settings = Depends(get_settings_dep)) -> dict:
    """公开端点。只返回最小 readiness, 不暴露环境/路径/版本细节。"""
    return {"status": "ok"}
