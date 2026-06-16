"""案例管理路由 (T6.5)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Path, Query, Response, status
from pydantic import BaseModel, Field

from admin.auth import get_current_user
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser, utc_now_iso
from admin.errors import DATA_NOT_FOUND
from admin.errors.exceptions import BusinessError
from data.cases.dao import CaseNotFound, CasesDAO
from data.cases.models import CaseRecord

router = APIRouter(prefix="/api/cases", tags=["cases"])
admin_router = APIRouter(prefix="/api/admin/cases", tags=["cases"])

CaseCategory = Literal["success", "typical", "warning"]
CaseReviewStatus = Literal["pending", "approved", "rejected"]


class CaseBasePayload(BaseModel):
    title: str = Field(min_length=1)
    category: CaseCategory
    summary: Optional[str] = None
    content: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class CaseReviewResponse(BaseModel):
    review_status: CaseReviewStatus
    review_note: Optional[str] = None
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None


class CaseDetailResponse(CaseBasePayload, CaseReviewResponse):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CaseListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CaseDetailResponse]


class ReviewCaseRequest(BaseModel):
    review_status: Literal["approved", "rejected"]
    review_note: Optional[str] = None


def _not_found(case_id: int) -> BusinessError:
    return BusinessError(DATA_NOT_FOUND, detail={"case_id": case_id})


def _to_payload(record: CaseRecord) -> dict[str, Any]:
    return asdict(record)


@router.get("", response_model=CaseListResponse, summary="案例列表（T6.5）")
@admin_router.get("", response_model=CaseListResponse, summary="案例列表（T6.5）")
def list_cases(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: Optional[CaseCategory] = Query(None),
    review_status: Optional[CaseReviewStatus] = Query(None),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> dict[str, Any]:
    with CasesDAO.connect(settings.db_path) as dao:
        items, total = dao.list(
            category=category,
            review_status=review_status,
            limit=limit,
            offset=offset,
        )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_to_payload(item) for item in items],
    }


@router.post(
    "",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建案例（T6.5）",
)
@admin_router.post(
    "",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建案例（T6.5）",
)
def create_case(
    payload: CaseBasePayload,
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> dict[str, Any]:
    record = CaseRecord(
        id=0,
        title=payload.title,
        category=payload.category,
        summary=payload.summary,
        content=payload.content,
        tags=payload.tags,
    )
    with CasesDAO.connect(settings.db_path) as dao:
        created = dao.create(record)
    return _to_payload(created)


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="案例详情（T6.5）",
)
@admin_router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="案例详情（T6.5）",
)
def get_case(
    case_id: int = Path(..., ge=1),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> dict[str, Any]:
    with CasesDAO.connect(settings.db_path) as dao:
        try:
            record = dao.get(case_id)
        except CaseNotFound as exc:
            raise _not_found(case_id) from exc
    return _to_payload(record)


@router.patch(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="更新案例（T6.5）",
)
@admin_router.patch(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="更新案例（T6.5）",
)
def update_case(
    payload: CaseBasePayload,
    case_id: int = Path(..., ge=1),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> dict[str, Any]:
    with CasesDAO.connect(settings.db_path) as dao:
        try:
            updated = dao.update(
                case_id,
                updates={
                    "title": payload.title,
                    "category": payload.category,
                    "summary": payload.summary,
                    "content": payload.content,
                    "tags": payload.tags,
                },
            )
        except CaseNotFound as exc:
            raise _not_found(case_id) from exc
    return _to_payload(updated)


@router.post(
    "/{case_id}/review",
    response_model=CaseDetailResponse,
    summary="审核案例（T6.5）",
)
@admin_router.post(
    "/{case_id}/review",
    response_model=CaseDetailResponse,
    summary="审核案例（T6.5）",
)
def review_case(
    payload: ReviewCaseRequest,
    case_id: int = Path(..., ge=1),
    settings: Settings = Depends(get_settings_dep),
    current_user: AdminUser = Depends(get_current_user),
) -> dict[str, Any]:
    with CasesDAO.connect(settings.db_path) as dao:
        try:
            reviewed = dao.update(
                case_id,
                updates={
                    "review_status": payload.review_status,
                    "review_note": payload.review_note,
                    "reviewer": current_user.username,
                    "reviewed_at": utc_now_iso(),
                },
            )
        except CaseNotFound as exc:
            raise _not_found(case_id) from exc
    return _to_payload(reviewed)


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除案例（T6.5）",
    response_class=Response,
)
@admin_router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除案例（T6.5）",
    response_class=Response,
)
def delete_case(
    case_id: int = Path(..., ge=1),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(get_current_user),
) -> Response:
    with CasesDAO.connect(settings.db_path) as dao:
        try:
            dao.delete(case_id)
        except CaseNotFound as exc:
            raise _not_found(case_id) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
