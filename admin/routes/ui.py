"""轻量管理后台页面路由。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, cast

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, HTMLResponse

from admin.config import Settings, get_settings_dep
from admin.share_page import (
    load_report_from_directory,
    render_share_page,
    status_code_for_result,
)
from data.share.short_link import route_short_link_with_report


router = APIRouter(tags=["ui"])

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_DASHBOARD_HTML = _STATIC_DIR / "dashboard.html"


@router.get("/dashboard", include_in_schema=False)
@router.get("/admin/dashboard", include_in_schema=False)
def dashboard_page() -> FileResponse:
    """返回最小仪表盘页面壳。"""
    return FileResponse(_DASHBOARD_HTML)


@router.get("/s/{code}", include_in_schema=False)
def share_page(
    code: str,
    request: Request,
    pwd: Optional[str] = Query(default=None),
) -> HTMLResponse:
    """公开分享页（T7.5）。"""
    settings = get_settings_dep(request)
    report_loader = _resolve_report_loader(request, settings)
    result = route_short_link_with_report(
        code,
        password=pwd,
        base_url=str(request.base_url).rstrip("/"),
        db_path=Path(settings.share_db_path),
        report_loader=report_loader,
    )
    html = render_share_page(result, password=pwd)
    return HTMLResponse(html, status_code=status_code_for_result(result))


def _resolve_report_loader(
    request: Request, settings: Settings
) -> Optional[Callable[[str], Optional[dict[str, Any]]]]:
    custom_loader = getattr(request.app.state, "share_report_loader", None)
    if callable(custom_loader):
        return cast(Callable[[str], Optional[dict[str, Any]]], custom_loader)

    report_dir = settings.share_report_dir
    if not report_dir:
        return None

    def _loader(report_id: str) -> Optional[dict]:
        return load_report_from_directory(report_id, report_dir)

    return _loader
