"""订单管理路由 (T6.4).

范围:
- GET /api/orders            订单列表（真实 DAO + 脱敏）
- GET /api/orders/export     CSV 导出（默认脱敏）
- GET /api/orders/{id}       订单详情 + 状态历史
- POST /api/orders           手工录单
- PATCH /api/orders/{id}     业务字段更新 / 状态流转 / 退款
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from io import StringIO
from typing import Any, Literal, Optional, cast

from fastapi import APIRouter, Depends, Path as ApiPath, Query, Response, status
from pydantic import BaseModel, Field

from admin.auth import require_role
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser
from admin.errors import (
    BIZ_ORDER_INVALID_STATUS,
    BIZ_ORDER_NOT_FOUND,
    DATA_PERSIST_FAILED,
    DATA_VALIDATION_FAILED,
)
from admin.errors.exceptions import BusinessError
from data.orders.dao import DuplicateOrder, OrderNotFound, OrdersDAO
from data.orders.deletion_service import OrderDeletionService
from data.orders.intake_store import IntakeStore
from data.orders.models import Order, generate_order_id
from data.orders.state_machine import InvalidStateTransition, next_states


router = APIRouter(prefix="/api/orders", tags=["orders"])
admin_router = APIRouter(prefix="/api/admin/orders", tags=["orders"])

OrderSource = Literal["xianyu", "wechat", "web", "school"]
ServiceVersion = Literal["audit", "basic", "standard", "premium"]
OrderStatus = Literal[
    "pending", "paid", "serving", "delivered", "completed", "refunded"
]
DevSeedScenario = Literal["overdue_pending_once", "cleanup_demo_seed"]

_DEMO_SEED_TAG = "__demo_seed__"
_DEMO_SEED_SOURCE = "dashboard_hidden_tools"

_SUMMARY_FIELDS = (
    "id",
    "source",
    "external_id",
    "service_version",
    "status",
    "amount_cents",
    "customer_name",
    "customer_phone",
    "customer_wechat",
    "candidate_name",
    "candidate_province",
    "assigned_consultant",
    "created_at",
    "status_updated_at",
    "tags",
)
_EXPORT_FIELDS = (
    "id",
    "source",
    "external_id",
    "service_version",
    "status",
    "amount_cents",
    "customer_name",
    "customer_phone",
    "customer_wechat",
    "candidate_name",
    "candidate_id_card",
    "candidate_province",
    "candidate_score",
    "assigned_consultant",
    "created_at",
    "status_updated_at",
    "notes",
)
_ALLOWED_UPDATE_FIELDS = {
    "external_id",
    "service_version",
    "amount_cents",
    "customer_name",
    "customer_wechat",
    "candidate_name",
    "candidate_province",
    "candidate_score",
    "candidate_rank",
    "candidate_subjects",
    "candidate_interests",
    "candidate_strong_subjects",
    "candidate_weak_subjects",
    "candidate_family",
    "assigned_consultant",
    "plan_file",
    "audit_report",
    "pdf_path",
    "notes",
    "tags",
}
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


class OrderSummaryResponse(BaseModel):
    id: str
    source: str
    external_id: Optional[str] = None
    service_version: str
    status: str
    amount_cents: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_wechat: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_province: Optional[str] = None
    assigned_consultant: Optional[str] = None
    intake_status: Optional[str] = None
    intake_submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    status_updated_at: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class OrderHistoryItem(BaseModel):
    id: int
    order_id: str
    from_status: Optional[str] = None
    to_status: str
    actor: Optional[str] = None
    reason: Optional[str] = None
    changed_at: str


class OrderDetailPayload(BaseModel):
    order: dict[str, Any]
    history: list[OrderHistoryItem]
    available_next_statuses: list[str]


class OrderMutationResponse(OrderDetailPayload):
    action: str


class OrderDeletionResponse(BaseModel):
    action: str
    order_id: str
    files_deleted: int = 0


class CreateOrderRequest(BaseModel):
    source: OrderSource
    external_id: Optional[str] = None
    service_version: ServiceVersion
    amount_cents: int = Field(ge=0)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_wechat: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_id_card: Optional[str] = None
    candidate_province: Optional[str] = None
    candidate_score: Optional[int] = None
    candidate_rank: Optional[int] = None
    candidate_subjects: list[str] = Field(default_factory=list)
    candidate_interests: Optional[str] = None
    candidate_strong_subjects: Optional[str] = None
    candidate_weak_subjects: Optional[str] = None
    candidate_family: Optional[str] = None
    assigned_consultant: Optional[str] = None
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class UpdateOrderRequest(BaseModel):
    updates: Optional[dict[str, Any]] = None
    to_status: Optional[OrderStatus] = None
    reason: Optional[str] = None


class DevSeedRequest(BaseModel):
    scenario: DevSeedScenario


class DevSeedResponse(BaseModel):
    action: str
    created_ids: list[str] = Field(default_factory=list)
    deleted_ids: list[str] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)


def _mask_order(order: Order) -> dict[str, Any]:
    masked = order.to_dict(decrypt_sensitive="mask")
    masked.pop("customer_phone_hash", None)
    return masked


def _summary(order: Order) -> dict[str, Any]:
    masked = _mask_order(order)
    return {field: masked.get(field) for field in _SUMMARY_FIELDS}


def _attach_intake_fields(order_payload: dict[str, Any], intake: Any) -> dict[str, Any]:
    enriched = dict(order_payload)
    enriched["intake_status"] = getattr(intake, "status", None)
    enriched["intake_submitted_at"] = getattr(intake, "submitted_at", None)
    return enriched


def _csv_safe_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def _export_row(order: Order) -> dict[str, Any]:
    masked = _mask_order(order)
    return {field: _csv_safe_value(masked.get(field)) for field in _EXPORT_FIELDS}


def _history_payload(dao: OrdersDAO, order_id: str) -> list[dict[str, Any]]:
    return [asdict(item) for item in dao.get_status_history(order_id)]


def _detail_payload(
    dao: OrdersDAO, order: Order, *, intake: Any = None
) -> dict[str, Any]:
    return {
        "order": _attach_intake_fields(_mask_order(order), intake),
        "history": _history_payload(dao, order.id),
        "available_next_statuses": sorted(next_states(order.status)),
    }


def _normalize_updates(updates: Optional[dict[str, Any]], settings: Settings) -> dict[str, Any]:
    if not updates:
        return {}
    bad = sorted(set(updates) - _ALLOWED_UPDATE_FIELDS)
    if bad:
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"invalid_update_fields": bad},
        )
    normalized = dict(updates)
    if "audit_report" in normalized:
        normalized["audit_report"] = _validate_report_artifact_path(
            normalized["audit_report"], settings
        )
    if "pdf_path" in normalized:
        normalized["pdf_path"] = _validate_report_artifact_path(
            normalized["pdf_path"], settings
        )
    if "plan_file" in normalized:
        normalized["plan_file"] = _validate_report_artifact_path(
            normalized["plan_file"], settings
        )
    return normalized


def _business_error_for_lookup(order_id: str) -> BusinessError:
    return BusinessError(BIZ_ORDER_NOT_FOUND, detail={"order_id": order_id})


_REPORT_ARTIFACT_SUFFIXES = {".html", ".json", ".md", ".pdf"}


def _trusted_report_roots(settings: Settings) -> tuple[Path, ...]:
    return (
        Path(settings.share_report_dir).resolve(),
        (Path(settings.portal_upload_dir).resolve().parent / "order_artifacts").resolve(),
        Path("data/examples").resolve(),
    )


def _validate_report_artifact_path(raw_path: Any, settings: Settings) -> str | None:
    if raw_path is None or raw_path == "":
        return None
    if not isinstance(raw_path, str):
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"reason": "artifact path must be a string"},
        )
    path = Path(raw_path).expanduser().resolve()
    if path.suffix.lower() not in _REPORT_ARTIFACT_SUFFIXES:
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"reason": f"untrusted artifact suffix: {raw_path}"},
        )
    trusted_roots = _trusted_report_roots(settings)
    if not any(root == path or root in path.parents for root in trusted_roots):
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"reason": f"untrusted artifact path: {raw_path}"},
        )
    return str(path)


def _ensure_non_prod_seed_env(settings: Settings) -> None:
    if settings.env == "prod":
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"reason": "生产环境禁用隐藏测试造数入口"},
        )


def _list_demo_seed_order_ids(dao: OrdersDAO) -> list[str]:
    rows = dao.conn.execute(
        "SELECT id, tags FROM orders ORDER BY created_at DESC LIMIT 500"
    ).fetchall()
    ids: list[str] = []
    for row in rows:
        raw_tags = row["tags"] if hasattr(row, "keys") else row[1]
        try:
            tags = json.loads(raw_tags) if raw_tags else []
        except (TypeError, json.JSONDecodeError):
            tags = []
        if _DEMO_SEED_TAG in tags:
            ids.append(row["id"] if hasattr(row, "keys") else row[0])
    return ids


def _create_overdue_pending_seed(
    settings: Settings, current_user: AdminUser
) -> tuple[list[str], dict[str, Any]]:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc).replace(microsecond=0)
    created_at = (now - timedelta(days=2)).isoformat()
    order = Order(
        id=generate_order_id(),
        source="web",
        external_id=f"demo-seed-{generate_order_id()}",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        status_updated_at=created_at,
        customer_name="演示造数-超时待办",
        candidate_name="演示考生",
        candidate_province="湖南",
        notes="隐藏入口补造：超时待办演示单",
        tags=[_DEMO_SEED_TAG, _DEMO_SEED_SOURCE, "overdue_pending_once"],
        created_at=created_at,
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        created = dao.create(order, actor=current_user.username, reason="admin_hidden_seed")
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake_store.save(
            order_id=created.id,
            payload={
                "mode": "draft",
                "existing_plan_summary": "隐藏入口补造的超时待办演示单",
            },
            submit=False,
        )
    finally:
        intake_store.close()
    return [created.id], {"scenario": "overdue_pending_once", "created_at": created_at}


def _cleanup_demo_seed_orders(settings: Settings) -> tuple[list[str], dict[str, Any]]:
    deleted_ids: list[str] = []
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        for order_id in _list_demo_seed_order_ids(dao):
            if dao.delete(order_id):
                deleted_ids.append(order_id)
    return deleted_ids, {"scenario": "cleanup_demo_seed", "deleted_count": len(deleted_ids)}


def _transition_error(order_id: str, to_status: str, exc: Exception) -> BusinessError:
    return BusinessError(
        BIZ_ORDER_INVALID_STATUS,
        detail={"order_id": order_id, "to_status": to_status, "reason": str(exc)},
    )


@router.get(
    "",
    response_model=list[OrderSummaryResponse],
    summary="订单列表（T6.4）",
)
@admin_router.get(
    "",
    response_model=list[OrderSummaryResponse],
    summary="订单列表（T6.4）",
)
def list_orders(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    source: Optional[OrderSource] = Query(None),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(require_role("admin")),
) -> list[dict[str, Any]]:
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        orders = dao.list(
            status=status_filter, source=source, limit=limit, offset=offset
        )
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        return [
            _attach_intake_fields(_summary(order), intake_store.get(order.id))
            for order in orders
        ]
    finally:
        intake_store.close()


@router.get(
    "/export",
    summary="订单导出（CSV，默认脱敏）",
)
@admin_router.get(
    "/export",
    summary="订单导出（CSV，默认脱敏）",
)
def export_orders_csv(
    limit: int = Query(1000, ge=1, le=1000),
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    source: Optional[OrderSource] = Query(None),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(require_role("admin")),
) -> Response:
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        orders = dao.list(status=status_filter, source=source, limit=limit, offset=0)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(_EXPORT_FIELDS))
    writer.writeheader()
    for order in orders:
        writer.writerow(cast(Any, _export_row(order)))

    filename = "orders_export.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{order_id}",
    response_model=OrderDetailPayload,
    summary="订单详情（T6.4）",
)
@admin_router.get(
    "/{order_id}",
    response_model=OrderDetailPayload,
    summary="订单详情（T6.4）",
)
def get_order(
    order_id: str = ApiPath(..., min_length=1),
    settings: Settings = Depends(get_settings_dep),
    _: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            order = dao.get(order_id)
        except OrderNotFound as exc:
            raise _business_error_for_lookup(order_id) from exc
        intake_store = IntakeStore.for_db(settings.orders_db_path)
        try:
            intake = intake_store.get(order_id)
        finally:
            intake_store.close()
        return _detail_payload(dao, order, intake=intake)


@router.post(
    "",
    response_model=OrderMutationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="手工录入订单（T6.4）",
)
@admin_router.post(
    "",
    response_model=OrderMutationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="手工录入订单（T6.4）",
)
def create_order(
    payload: CreateOrderRequest,
    settings: Settings = Depends(get_settings_dep),
    current_user: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    order = Order(
        id=generate_order_id(),
        source=payload.source,
        external_id=payload.external_id,
        service_version=payload.service_version,
        amount_cents=payload.amount_cents,
        status="pending",
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_wechat=payload.customer_wechat,
        candidate_name=payload.candidate_name,
        candidate_id_card=payload.candidate_id_card,
        candidate_province=payload.candidate_province,
        candidate_score=payload.candidate_score,
        candidate_rank=payload.candidate_rank,
        candidate_subjects=payload.candidate_subjects,
        candidate_interests=payload.candidate_interests,
        candidate_strong_subjects=payload.candidate_strong_subjects,
        candidate_weak_subjects=payload.candidate_weak_subjects,
        candidate_family=payload.candidate_family,
        assigned_consultant=payload.assigned_consultant,
        notes=payload.notes,
        tags=payload.tags,
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            created = dao.create(
                order, actor=current_user.username, reason="admin_create"
            )
        except DuplicateOrder as exc:
            raise BusinessError(
                DATA_VALIDATION_FAILED,
                detail={"reason": str(exc)},
            ) from exc
        except Exception as exc:  # pragma: no cover - 持久层兜底
            raise BusinessError(DATA_PERSIST_FAILED) from exc
        return {"action": "created", **_detail_payload(dao, created)}


@router.post(
    "/dev-seed",
    response_model=DevSeedResponse,
    include_in_schema=False,
)
@admin_router.post(
    "/dev-seed",
    response_model=DevSeedResponse,
    include_in_schema=False,
)
def create_dev_seed_order(
    payload: DevSeedRequest,
    settings: Settings = Depends(get_settings_dep),
    current_user: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    _ensure_non_prod_seed_env(settings)
    if payload.scenario == "overdue_pending_once":
        created_ids, detail = _create_overdue_pending_seed(settings, current_user)
        return {
            "action": "created",
            "created_ids": created_ids,
            "deleted_ids": [],
            "detail": detail,
        }
    deleted_ids, detail = _cleanup_demo_seed_orders(settings)
    return {
        "action": "cleaned",
        "created_ids": [],
        "deleted_ids": deleted_ids,
        "detail": detail,
    }


@router.patch(
    "/{order_id}",
    response_model=OrderMutationResponse,
    summary="订单更新 / 状态流转 / 退款（T6.4）",
)
@admin_router.patch(
    "/{order_id}",
    response_model=OrderMutationResponse,
    summary="订单更新 / 状态流转 / 退款（T6.4）",
)
def patch_order(
    payload: UpdateOrderRequest,
    order_id: str = ApiPath(..., min_length=1),
    settings: Settings = Depends(get_settings_dep),
    current_user: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    updates = _normalize_updates(payload.updates, settings)
    if not updates and payload.to_status is None:
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"reason": "至少提供 updates 或 to_status 之一"},
        )

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            current = dao.get(order_id)
        except OrderNotFound as exc:
            raise _business_error_for_lookup(order_id) from exc

        order = current
        if updates:
            try:
                order = dao.update(
                    order_id,
                    updates,
                    actor=current_user.username,
                    reason=payload.reason or "admin_update",
                )
            except OrderNotFound as exc:
                raise _business_error_for_lookup(order_id) from exc
            except DuplicateOrder as exc:
                raise BusinessError(
                    DATA_VALIDATION_FAILED,
                    detail={"reason": str(exc)},
                ) from exc
            except ValueError as exc:
                raise BusinessError(
                    DATA_VALIDATION_FAILED,
                    detail={"reason": str(exc)},
                ) from exc

        if payload.to_status is not None:
            try:
                if payload.to_status == "serving":
                    intake_store = IntakeStore.for_db(settings.orders_db_path)
                    try:
                        intake = intake_store.get(order_id)
                    finally:
                        intake_store.close()
                    if intake is None or intake.status != "submitted":
                        raise BusinessError(
                            DATA_VALIDATION_FAILED,
                            detail={
                                "reason": "资料未提交，不能开始接单处理",
                                "required_intake_status": "submitted",
                            },
                        )
                order = dao.transition_status(
                    order_id,
                    payload.to_status,
                    actor=current_user.username,
                    reason=payload.reason or f"admin_transition:{payload.to_status}",
                )
            except OrderNotFound as exc:
                raise _business_error_for_lookup(order_id) from exc
            except InvalidStateTransition as exc:
                raise _transition_error(order_id, payload.to_status, exc) from exc

        action = "updated"
        if payload.to_status is not None and not updates:
            action = f"transitioned:{payload.to_status}"
        elif payload.to_status is not None:
            action = f"updated:{payload.to_status}"
        intake_store = IntakeStore.for_db(settings.orders_db_path)
        try:
            intake = intake_store.get(order_id)
        finally:
            intake_store.close()
        return {"action": action, **_detail_payload(dao, order, intake=intake)}


@router.delete(
    "/{order_id}",
    response_model=OrderDeletionResponse,
    summary="订单删除 / 匿名化（T12/A-4）",
)
@admin_router.delete(
    "/{order_id}",
    response_model=OrderDeletionResponse,
    summary="订单删除 / 匿名化（T12/A-4）",
)
def delete_or_anonymize_order(
    order_id: str = ApiPath(..., min_length=1),
    mode: Literal["delete", "anonymize"] = Query("delete"),
    reason: str = Query(..., min_length=1),
    settings: Settings = Depends(get_settings_dep),
    current_user: AdminUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    service = OrderDeletionService.for_db(settings.orders_db_path)
    try:
        try:
            if mode == "delete":
                result = service.delete_order(
                    order_id,
                    actor=current_user.username,
                    reason=reason,
                )
            else:
                result = service.anonymize_order(
                    order_id,
                    actor=current_user.username,
                    reason=reason,
                )
        except OrderNotFound as exc:
            raise _business_error_for_lookup(order_id) from exc
    finally:
        service.close()
    return result.__dict__
