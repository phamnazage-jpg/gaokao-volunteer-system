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
from datetime import datetime, timezone
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
    BIZ_ORDER_RETENTION_NOT_EXPIRED,
    DATA_PERSIST_FAILED,
    DATA_VALIDATION_FAILED,
)
from admin.errors.exceptions import BusinessError
from data.orders.dao import DuplicateOrder, OrderNotFound, OrdersDAO
from data.orders.deletion_service import (
    RETENTION_GUARDED_STATUSES,
    OrderDeletionService,
)
from data.orders.intake_store import IntakeStore
from data.orders.models import Order, generate_order_id, utc_now_iso
from data.orders.state_machine import InvalidStateTransition, next_states


def _parse_iso_utc(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _assert_retention_expired(
    order: Order,
    *,
    retention_days: int,
    now: Optional[datetime] = None,
) -> None:
    """保留期门禁 — paid/serving/... 状态的订单必须过 retention_days 才允许 delete/anonymize。

    口径来源: docs/DATA_RETENTION_AND_DELETION.md §2 — 服务完成后 180 天。
    落在 admin 层而不是 data.orders 层,避免反向依赖。
    """
    if order.status not in RETENTION_GUARDED_STATUSES:
        return
    anchor = _parse_iso_utc(order.status_updated_at) or _parse_iso_utc(order.created_at)
    if anchor is None:
        return
    from datetime import timedelta

    current = now or datetime.now(timezone.utc)
    elapsed = current - anchor
    if elapsed < timedelta(days=retention_days):
        remaining = timedelta(days=retention_days) - elapsed
        raise BusinessError(
            BIZ_ORDER_RETENTION_NOT_EXPIRED,
            detail={
                "order_id": order.id,
                "status": order.status,
                "status_updated_at": order.status_updated_at,
                "retention_days": retention_days,
                "remaining_seconds": int(remaining.total_seconds()),
            },
        )


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

    # A-2 (2026-06-20): 后台/外部渠道补录同意审计统一化
    # LEGAL_PRIVACY_BASELINE §6 要求任何订单创建路径必须记录同意审计字段。
    # portal 路径已自动落 consent_channel=portal / consent_operator=guardian
    # (见 web_public.py + intake_store.save), admin/外部渠道补录必须显式带
    # consent 块, 否则 422。空 consent_note 也允许, 表示"已确认但无备注"。
    consent: "ConsentInfo"


# A-2: 同意审计子模型
# consent_method 白名单:
# - verbal_chat: 家长/考生口头同意 (微信/电话/线下沟通)
# - phone_recording: 通话录音存档
# - screenshot: 微信/聊天截图存档
# - written_form: 书面/电子签字确认单
# - self_declared: 平台代填声明 (极少使用, 仅限已签长期合作协议的渠道)
ConsentMethod = Literal[
    "verbal_chat",
    "phone_recording",
    "screenshot",
    "written_form",
    "self_declared",
]


class ConsentInfo(BaseModel):
    consent_method: ConsentMethod
    consent_note: Optional[str] = None


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
    enriched["intake"] = (
        dict(getattr(intake, "payload", {}) or {}) if intake is not None else None
    )
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


def _normalize_updates(
    updates: Optional[dict[str, Any]], settings: Settings
) -> dict[str, Any]:
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
        (
            Path(settings.portal_upload_dir).resolve().parent / "order_artifacts"
        ).resolve(),
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
        created = dao.create(
            order, actor=current_user.username, reason="admin_hidden_seed"
        )
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
            if dao.delete(order_id, actor="admin_hidden_seed", reason="cleanup_demo_seed"):
                deleted_ids.append(order_id)
    return deleted_ids, {
        "scenario": "cleanup_demo_seed",
        "deleted_count": len(deleted_ids),
    }


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
    # A-2 (2026-06-20): 后台代录/外部渠道补录的同意审计时间戳统一为"创建时间"
    # portal 路径用 intake_store.save(submit=True) 内部 utc_now_iso() 自动落库
    # (web_public.py + intake_store.save), admin 路径这里手动计算保持口径一致
    consent_given_at = utc_now_iso()
    # consent_operator:
    # 严格按 LEGAL_PRIVACY_BASELINE §4 白名单: self / guardian / admin_import
    # - web 渠道: "guardian" (用户本人或监护人自助 portal, 与 web_public.py 一致)
    # - 其他渠道 (xianyu/wechat/school): "admin_import" (后台代录, 同意来源是渠道商)
    consent_operator = "guardian" if payload.source == "web" else "admin_import"

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
        consent_method=payload.consent.consent_method,
        consent_given_at=consent_given_at,
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
        order_id = created.id
        # 在 dao 仍持有 conn 的 with-block 内先抓 detail_payload 快照,
        # 避免退出 with-block 后再调 dao.get_status_history 等接口
        detail = _detail_payload(dao, created)

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake_payload: dict[str, Any] = {
            "candidate_name": payload.candidate_name,
            "candidate_province": payload.candidate_province,
            "candidate_score": payload.candidate_score,
            "candidate_subjects": payload.candidate_subjects,
            "customer_name": payload.customer_name,
            "customer_phone": payload.customer_phone,
            "customer_wechat": payload.customer_wechat,
            "consent_version": settings.consent_version,
            "consent_scope": f"{payload.source}-{settings.consent_scope_channel_prefix}",
            "consent_channel": payload.source,
            "consent_operator": consent_operator,
            "consent_method": payload.consent.consent_method,
            "consent_given_at": consent_given_at,
        }
        if payload.consent.consent_note:
            intake_payload["consent_note"] = payload.consent.consent_note
        if payload.customer_phone:
            intake_payload["privacy_accepted"] = False
        intake_record = intake_store.save(
            order_id=order_id, payload=intake_payload, submit=False
        )
    finally:
        intake_store.close()

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        refreshed = dao.get(order_id)
        detail = _detail_payload(dao, refreshed, intake=intake_record)

    return {"action": "created", **detail}


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
    # 保留期门禁: 必须先查到订单, 校验 retention_days 内不允许 delete / anonymize
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            order = dao.get(order_id)
        except OrderNotFound as exc:
            raise _business_error_for_lookup(order_id) from exc
        _assert_retention_expired(order, retention_days=settings.retention_days)

    service = OrderDeletionService.for_db(
        settings.orders_db_path,
        portal_upload_root=Path(settings.portal_upload_dir),
        artifact_roots=_trusted_report_roots(settings),
    )
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
