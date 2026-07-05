"""用户端 Web 自助 MVP 公共入口页面与 Portal 路由。"""

from __future__ import annotations

import json
import logging
import secrets
from html import escape
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta, timezone
import time
from typing import Any, Literal
from urllib.parse import parse_qsl

import markdown
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
)
from pydantic import BaseModel, Field

from admin.config import Settings, get_settings_dep
from admin.errors import BIZ_RATE_LIMITED, DATA_NOT_FOUND, DATA_VALIDATION_FAILED
from admin.errors.exceptions import BusinessError
from data.customer_portal.token import (
    PortalTokenError,
    issue_portal_token,
    verify_portal_token,
)
from data.crowd_db.loader import CrowdDBLoader
from data.llm import (
    LLMClient,
    LLMError,
    build_audit_prompt,
    build_full_plan_prompt,
)
from data.notifications.email_service import DeliveryNotificationService
from data.orders import crypto
from data.orders.dao import DuplicateOrder, OrderNotFound, OrdersDAO
from data.orders.deletion_service import RETENTION_GUARDED_STATUSES
from data.orders.intake_schema import IntakePayload
from data.orders.intake_store import IntakeStore
from data.orders.models import Order, utc_now_iso
from data.orders.public_flow import (
    PublicOrderCreate,
    create_public_order,
)
from data.orders.crypto import MissingEncryptionKey
from data.payments.service import PaymentError, PaymentService
from data.share.short_link import ShortLinkService, build_url


router = APIRouter(tags=["web-public"])
logger = logging.getLogger(__name__)

ServiceVersion = Literal["audit", "basic", "standard", "premium"]

_STAGE_META: dict[str, tuple[str, str]] = {
    "pending_payment": ("待支付", "请先完成支付，系统会自动推进到资料填写。"),
    "info_required": ("待填写资料", "支付已确认，请补充考生资料后进入处理队列。"),
    "info_submitted": ("资料已提交", "资料已进入系统，待后台接单处理。"),
    "processing": ("处理中", "后台已接单，正在生成审核/方案结果。"),
    "report_ready": ("报告已就绪", "已可站内查看报告并下载 PDF。"),
    "completed": ("已完成", "订单已完成，后续可继续查看历史交付内容。"),
    "refunded": ("已退款", "该订单已完成退款。"),
}
_SERVICE_PRICES = {
    "audit": 4900,
    "basic": 4900,
    "standard": 9900,
    "premium": 19900,
}
_SIMULATED_PAYMENT_ROUTE_NOT_FOUND = "not found"

_PUBLIC_ORDER_RATE_LIMIT = 5
_PUBLIC_ORDER_RATE_LIMIT_WINDOW_SECONDS = 60.0
_PUBLIC_ORDER_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = {}


def _public_order_rate_limit_key(request: Request, payload: PublicOrderCreate, settings: Settings) -> str:
    client_host = request.client.host if request.client else "unknown"
    contact = (payload.customer_phone or payload.customer_wechat or "unknown").strip().lower()
    return f"{settings.orders_db_path}:{client_host}:{contact}"


def _assert_public_order_rate_limit(request: Request, payload: PublicOrderCreate, settings: Settings) -> None:
    if payload.idempotency_key:
        return
    now = time.time()
    key = _public_order_rate_limit_key(request, payload, settings)
    bucket = _PUBLIC_ORDER_RATE_LIMIT_BUCKETS.setdefault(key, deque())
    cutoff = now - _PUBLIC_ORDER_RATE_LIMIT_WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= _PUBLIC_ORDER_RATE_LIMIT:
        raise BusinessError(
            BIZ_RATE_LIMITED,
            detail={"retry_after_seconds": int(_PUBLIC_ORDER_RATE_LIMIT_WINDOW_SECONDS)},
            http_status=429,
        )
    bucket.append(now)


def reset_public_order_rate_limit_for_tests() -> None:
    _PUBLIC_ORDER_RATE_LIMIT_BUCKETS.clear()


_DELETION_SCOPE_VALUES = ("order_only", "order_and_attachments", "full_account")
_DELETION_NEXT_STEP_OUTSIDE = (
    "已超过 180 天保留期，可申请删除；提交成功后将由人工核验后处理"
)
_DELETION_NEXT_STEP_WITHIN = "提交成功后将由人工核验后处理（订单仍在 180 天保留期内）"
_DELETION_NEXT_STEP_PENDING = "提交成功后将由人工核验后处理"


class PublicOrderCreated(BaseModel):
    order_id: str
    source: str
    status: str
    service_version: str
    amount_cents: int
    next_step: str
    checkout_url: str
    portal_status_url: str
    portal_info_url: str


class WebhookAck(BaseModel):
    payment_id: str
    processed: bool
    idempotent: bool
    order_status: str


class PortalIntakeResponse(BaseModel):
    intake_status: str
    stage: str
    order_id: str
    profile_minimum_complete: bool
    profile_missing_fields: list[str]


class PortalAttachmentUploaded(BaseModel):
    order_id: str
    intake_status: str
    stage: str
    attachments: list[dict[str, Any]]


class ReviewResultContract(BaseModel):
    review_result_id: str
    risk_level: Literal["high", "medium", "low"]
    top_findings: list[str]
    recommended_action: Literal["go_cwb", "go_step1", "go_full_plan"]
    available_actions: list[Literal["go_cwb", "go_step1", "go_full_plan"]]
    review_entry_source: Literal["home", "status", "report", "direct"]
    review_followup_action: Literal["cwb", "step1", "full_plan", "none"]
    review_input_summary: str = ""
    review_input_attachments: list[str] = Field(default_factory=list)
    review_constraints: dict[str, Any] = Field(default_factory=dict)
    llm_generated: bool = False
    llm_summary: str = ""
    llm_cwb_suggestions: dict[str, list[str]] = Field(default_factory=dict)


class ReviewActionRequest(BaseModel):
    token: str
    action: Literal["cwb", "step1", "full_plan"]


class ReviewActionResponse(BaseModel):
    review_result_id: str
    review_followup_action: Literal["cwb", "step1", "full_plan"]
    next_href: str


class DeletionRequestCreate(BaseModel):
    # 2026-06-19 T12-C: scope 锁定到白名单, confirm_guardian 强制要求
    requester_name: str = Field(..., min_length=1, max_length=64)
    requester_contact: str = Field(..., min_length=1, max_length=128)
    reason: str = Field(..., min_length=1, max_length=2000)
    scope: Literal["order_only", "order_and_attachments", "full_account"]
    confirm_guardian: bool = Field(...)


def _resolve_retention_status(order: Order, settings: Settings) -> str:
    """返回订单的保留期相对位置。

    - "pending": 订单状态不在保留期门禁子集内 (例如 pending)
    - "within": 订单在保留期门禁子集且未到保留期
    - "outside": 订单在保留期门禁子集且已超过保留期
    """
    if order.status not in RETENTION_GUARDED_STATUSES:
        return "pending"
    updated_raw = (
        order.status_updated_at or order.completed_at or order.created_at or ""
    ).strip()
    if not updated_raw:
        return "within"
    try:
        updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
    except ValueError:
        return "within"
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    elapsed = datetime.now(timezone.utc) - updated
    if elapsed >= timedelta(days=settings.retention_days):
        return "outside"
    return "within"


def _next_step_for_retention(status: str) -> str:
    if status == "outside":
        return _DELETION_NEXT_STEP_OUTSIDE
    if status == "within":
        return _DELETION_NEXT_STEP_WITHIN
    return _DELETION_NEXT_STEP_PENDING


class DeletionRequestCreated(BaseModel):
    order_id: str
    request_logged: bool
    next_step: str


def _log_deletion_request(
    order_id: str, payload: DeletionRequestCreate, settings: Settings
) -> None:
    from datetime import datetime

    path = Path(settings.deletion_request_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    item = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "order_id": order_id,
        "requester_name": payload.requester_name,
        "requester_contact": payload.requester_contact,
        "reason": payload.reason,
        "scope": payload.scope,
        "confirm_guardian": payload.confirm_guardian,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def _assert_simulated_payment_routes_allowed(settings: Settings) -> None:
    if settings.env == "prod":
        raise HTTPException(status_code=404, detail=_SIMULATED_PAYMENT_ROUTE_NOT_FOUND)


@router.get("/", include_in_schema=False)
def landing_page(
    request: Request, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    return HTMLResponse(_render_landing_page(request, settings))


@router.get("/pricing", include_in_schema=False)
def pricing_page(request: Request) -> HTMLResponse:
    return HTMLResponse(_render_pricing_page(request))


@router.get("/checkout/{service_version}", include_in_schema=False)
def checkout_page(service_version: ServiceVersion) -> HTMLResponse:
    return HTMLResponse(_render_checkout_page(service_version))


@router.get("/portal/{token}/payment-success", include_in_schema=False)
def payment_success_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    return HTMLResponse(_render_payment_success_page(token, context))


@router.post("/api/public/orders", response_model=PublicOrderCreated, status_code=201)
def create_public_order_endpoint(
    payload: PublicOrderCreate,
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> PublicOrderCreated:
    _assert_public_order_rate_limit(request, payload, settings)

    try:
        payment_service = _payment_service(settings)
    except PaymentError as exc:
        logger.warning(
            "public order create blocked by payment provider readiness: %s", exc
        )
        raise HTTPException(
            status_code=503,
            detail="当前暂时无法创建订单，请稍后重试或联系客服获取人工协助。",
        ) from exc

    try:
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            try:
                order = create_public_order(dao, payload)
            except DuplicateOrder:
                if not payload.idempotency_key:
                    raise
                existing = dao.get_by_external_id("web", f"idempotency:{payload.idempotency_key}")
                if existing is None:
                    raise
                order = existing
    except MissingEncryptionKey as exc:
        crypto.get_fernet.cache_clear()
        logger.warning("public order create blocked by missing encryption key: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="当前暂时无法创建订单，请稍后重试或联系客服获取人工协助。",
        ) from exc

    portal_token = issue_portal_token(order.id, settings.portal_token_secret)
    try:
        checkout = payment_service.create_checkout(order.id)
    except PaymentError as exc:
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            dao.delete(order.id)
        logger.warning("public order checkout creation failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="当前暂时无法创建订单，请稍后重试或联系客服获取人工协助。",
        ) from exc
    return PublicOrderCreated(
        order_id=order.id,
        source=order.source,
        status=order.status,
        service_version=order.service_version,
        amount_cents=order.amount_cents,
        next_step="payment",
        checkout_url=checkout.checkout_url,
        portal_status_url=f"/portal/{portal_token}/status",
        portal_info_url=f"/portal/{portal_token}/info",
    )


@router.post("/api/public/payments/mock/webhook", response_model=WebhookAck)
def mock_payment_webhook(
    payload: dict[str, Any],
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> WebhookAck:
    _assert_simulated_payment_routes_allowed(settings)
    signature = request.headers.get("X-Mock-Signature", "")
    service = _payment_service(settings)
    try:
        result = service.handle_webhook(payload, signature)
    except PaymentError as exc:
        message = str(exc)
        status_code = 409 if "amount mismatch" in message else 400
        raise HTTPException(status_code=status_code, detail=message) from exc
    return WebhookAck(**result.__dict__)


@router.post("/api/public/payments/alipay/notify", include_in_schema=False)
async def alipay_notify_webhook(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> PlainTextResponse:
    body = (await request.body()).decode("utf-8")
    payload = {key: value for key, value in parse_qsl(body, keep_blank_values=True)}
    signature = payload.pop("sign", "")
    payload.pop("sign_type", None)
    service = _payment_service(settings)
    try:
        service.handle_webhook(payload, signature)
    except PaymentError as exc:
        message = str(exc)
        status_code = 409 if "amount mismatch" in message else 400
        raise HTTPException(status_code=status_code, detail=message) from exc
    return PlainTextResponse("success")


@router.get("/pay/mock/{payment_id}", include_in_schema=False)
def mock_payment_page(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _render_simulated_payment_page(payment_id, settings, provider_slug="mock")


@router.post("/pay/mock/{payment_id}/complete", include_in_schema=False)
def complete_mock_payment(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _complete_simulated_payment(payment_id, settings, provider_slug="mock")


@router.get("/pay/alipay-sim/{payment_id}", include_in_schema=False)
def alipay_sim_payment_page(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _render_simulated_payment_page(
        payment_id, settings, provider_slug="alipay-sim"
    )


@router.post("/pay/alipay-sim/{payment_id}/complete", include_in_schema=False)
def complete_alipay_sim_payment(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _complete_simulated_payment(payment_id, settings, provider_slug="alipay-sim")


@router.get("/portal/payment-return", include_in_schema=False)
def payment_return_page(
    payment_id: str,
    return_nonce: str | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    service = _payment_service(settings)
    payment = service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    if payment.status != "paid":
        raise HTTPException(status_code=409, detail="payment not ready")
    if not payment.checkout_token or return_nonce != payment.checkout_token:
        raise HTTPException(status_code=403, detail="payment return nonce invalid")
    portal_token = issue_portal_token(payment.order_id, settings.portal_token_secret)
    return RedirectResponse(
        url=f"/portal/{portal_token}/payment-success", status_code=303
    )


@router.get("/review/start", include_in_schema=False)
def review_start_page(
    source: Literal["home", "status", "report", "direct"] = "direct",
    token: str | None = None,
    province: str | None = None,
    score: str | None = None,
    goal: str | None = None,
    consult: str | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    review_input_summary = (consult or goal or "").strip() or None
    review_constraints: dict[str, Any] = {}
    if province:
        review_constraints["candidate_province"] = province.strip()
    if score:
        parts = [part.strip() for part in score.replace("／", "/").split("/", 1)]
        if parts and parts[0]:
            review_constraints["candidate_score"] = parts[0]
        if len(parts) > 1 and parts[1]:
            review_constraints["candidate_rank"] = parts[1]
    contract = _start_review_result(
        source=source,
        token=token,
        settings=settings,
        review_input_summary=review_input_summary,
        review_constraints=review_constraints or None,
    )
    return HTMLResponse(_render_review_start_page(contract, token))


@router.get("/portal/{token}/cwb", include_in_schema=False)
def cwb_placeholder_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    contract = _load_latest_review_result(order.id, settings)
    context = _build_portal_context(order, settings)
    return HTMLResponse(_render_cwb_placeholder_page(token, order, contract, context))


@router.get("/portal/{token}/full-plan", include_in_schema=False)
def full_plan_placeholder_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    contract = _load_latest_review_result(order.id, settings)
    return HTMLResponse(
        _render_full_plan_placeholder_page(
            token, order, context, contract, settings=settings
        )
    )


@router.get("/portal/{token}/info", include_in_schema=False)
def order_info_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(order.id)
    finally:
        intake_store.close()
    context = _build_portal_context(order, settings)
    return HTMLResponse(
        _render_info_page(
            order,
            token,
            intake.payload if intake else {},
            context["stage"],
            settings,
        )
    )


def _assert_portal_info_mutable(stage: str) -> None:
    if stage == "pending_payment":
        raise HTTPException(status_code=409, detail="payment required before intake")
    if stage in {
        "processing",
        "report_ready",
        "completed",
        "refunded",
    }:
        raise HTTPException(
            status_code=409, detail="intake is read-only at current stage"
        )


def _sanitize_upload_filename(name: str) -> str:
    raw = Path(name or "upload.bin").name
    return raw.replace("/", "_").replace("\\", "_")


def _validate_upload(
    file_name: str, content_type: str | None, payload: bytes, settings: Settings
) -> None:
    suffix = Path(file_name).suffix.lower()
    allowed_suffixes = {
        ".pdf",
        ".txt",
        ".md",
        ".json",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }
    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=415,
            detail=f"unsupported attachment type: {suffix or 'unknown'}",
        )
    if len(payload) > settings.portal_upload_max_bytes:
        raise HTTPException(status_code=413, detail="attachment too large")
    if not payload:
        raise HTTPException(status_code=400, detail="empty attachment")


def _store_portal_attachment(
    *,
    order_id: str,
    upload_name: str,
    content_type: str | None,
    payload: bytes,
    settings: Settings,
) -> dict[str, Any]:
    safe_name = _sanitize_upload_filename(upload_name)
    _validate_upload(safe_name, content_type, payload, settings)
    upload_dir = Path(settings.portal_upload_dir) / order_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{secrets.token_hex(8)}-{safe_name}"
    target = upload_dir / stored_name
    target.write_bytes(payload)
    return {
        "original_name": safe_name,
        "stored_name": stored_name,
        "content_type": content_type or "application/octet-stream",
        "size_bytes": len(payload),
        "kind": "portal_attachment",
    }


@router.post("/portal/{token}/attachments", response_model=PortalAttachmentUploaded)
def upload_order_attachment(
    token: str,
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_settings_dep),
) -> PortalAttachmentUploaded:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    _assert_portal_info_mutable(context["stage"])

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    uploaded: list[dict[str, Any]] = []
    try:
        current = intake_store.get(order.id)
        payload = dict(current.payload) if current is not None else {}
        attachments = list(payload.get("attachments") or [])
        if len(attachments) + len(files) > settings.portal_upload_max_files:
            raise HTTPException(
                status_code=413,
                detail=f"too many attachments: max {settings.portal_upload_max_files}",
            )
        for file in files:
            raw = file.file.read()
            attachment = _store_portal_attachment(
                order_id=order.id,
                upload_name=file.filename or "upload.bin",
                content_type=file.content_type,
                payload=raw,
                settings=settings,
            )
            attachments.append(attachment)
            uploaded.append(attachment)
        payload["attachments"] = attachments
        record = intake_store.save(
            order_id=order.id,
            payload=payload,
            submit=(current.status == "submitted") if current is not None else False,
        )
    finally:
        intake_store.close()

    refreshed_order = _resolve_order_from_token(token, settings)
    refreshed_context = _build_portal_context(refreshed_order, settings)
    return PortalAttachmentUploaded(
        order_id=order.id,
        intake_status=record.status,
        stage=refreshed_context["stage"],
        attachments=uploaded,
    )


@router.post("/portal/{token}/info", response_model=PortalIntakeResponse)
def submit_order_info(
    token: str,
    payload: IntakePayload,
    settings: Settings = Depends(get_settings_dep),
) -> PortalIntakeResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    _assert_portal_info_mutable(context["stage"])
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        current = intake_store.get(order.id)
        base_payload = dict(current.payload) if current is not None else {}
        base_payload.update(payload.model_dump())
        saved_payload = _ensure_profile_version_metadata(base_payload)
        record = intake_store.save(
            order_id=order.id,
            payload=saved_payload,
            submit=payload.mode == "submit",
        )
    finally:
        intake_store.close()

    updates: dict[str, Any] = {}
    if payload.candidate_province is not None:
        updates["candidate_province"] = payload.candidate_province
    if payload.candidate_score is not None:
        updates["candidate_score"] = payload.candidate_score
    if payload.candidate_rank is not None:
        updates["candidate_rank"] = payload.candidate_rank
    if payload.candidate_subjects:
        updates["candidate_subjects"] = payload.candidate_subjects
    if payload.candidate_interests is not None:
        updates["candidate_interests"] = payload.candidate_interests
    if payload.guardian_notes is not None:
        updates["notes"] = payload.guardian_notes
    if updates or (payload.mode == "submit" and order.status == "paid"):
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            if updates:
                dao.update(
                    order.id, updates, actor="portal", reason=f"portal_{record.status}"
                )
            if payload.mode == "submit" and order.status == "paid":
                dao.transition_status(
                    order.id,
                    "serving",
                    actor="portal",
                    reason="portal_submit_auto_queue",
                )
    refreshed_order = _resolve_order_from_token(token, settings)
    refreshed_context = _build_portal_context(refreshed_order, settings)
    return PortalIntakeResponse(
        intake_status=record.status,
        stage=refreshed_context["stage"],
        order_id=order.id,
        profile_minimum_complete=_is_profile_minimum_complete(record.payload),
        profile_missing_fields=_profile_missing_fields(record.payload),
    )


@router.post("/review/action", include_in_schema=False)
def review_action_endpoint(
    token: str = Form(...),
    action: Literal["cwb", "step1", "full_plan"] = Form(...),
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    result = _apply_review_followup_action(token, action, settings)
    return RedirectResponse(url=result.next_href, status_code=303)


@router.get("/portal/{token}/deletion-request", include_in_schema=False)
def deletion_request_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    return HTMLResponse(_render_deletion_request_page(token, order, settings))


@router.post("/portal/{token}/deletion-request", response_model=DeletionRequestCreated)
def submit_deletion_request(
    token: str,
    payload: DeletionRequestCreate,
    settings: Settings = Depends(get_settings_dep),
) -> DeletionRequestCreated:
    order = _resolve_order_from_token(token, settings)
    _log_deletion_request(order.id, payload, settings)
    # 2026-06-19 T12-C: next_step 根据订单保留期分文案, 给用户明确预期
    retention_status = _resolve_retention_status(order, settings)
    return DeletionRequestCreated(
        order_id=order.id,
        request_logged=True,
        next_step=_next_step_for_retention(retention_status),
    )


@router.get("/portal/{token}/notifications", include_in_schema=False)
def notification_audit_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        events = notification_service.list_events(order.id)
    finally:
        notification_service.close()
    return HTMLResponse(_render_notification_audit_page(token, order, events))


def _portal_share_target(
    *,
    result_type: str,
    target_token: str,
    settings: Settings,
) -> tuple[Order, str]:
    order = _resolve_order_from_token(target_token, settings)
    if result_type == "review_result":
        contract = _load_latest_review_result(order.id, settings)
        if contract is None:
            raise BusinessError(
                DATA_NOT_FOUND,
                detail={"reason": "review_result not found"},
            )
        return order, contract.review_result_id
    if result_type == "report":
        if order.status not in {"delivered", "completed"} or not order.audit_report:
            raise BusinessError(
                DATA_NOT_FOUND,
                detail={"reason": "report not ready"},
            )
        return order, order.id
    raise BusinessError(
        DATA_VALIDATION_FAILED,
        detail={"reason": "result_type must be review_result or report"},
    )


def _latest_portal_share_link(
    *,
    svc: ShortLinkService,
    target_id: str,
    result_type: str,
    order_id: str,
) -> Any | None:
    prefix = f"{result_type}:{order_id}"
    links = svc.list_by_report(target_id)
    active = [
        link
        for link in links
        if str(link.note or "") == prefix and not link.revoked and not link.is_expired()
    ]
    if active:
        return active[0]
    for link in links:
        if str(link.note or "") == prefix:
            return link
    return None


def _portal_share_response(
    *,
    request: Request,
    link: Any,
    result_type: str,
    target_id: str,
    stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "code": link.code,
        "share_url": build_url(link.code, base=str(request.base_url).rstrip("/")),
        "permission": link.permission,
        "result_type": result_type,
        "target_id": target_id,
        "expires_at_iso": link.to_dict().get("expires_at_iso"),
        "revoked": bool(link.revoked),
        "access_count": link.access_count,
        "last_access_at_iso": link.to_dict().get("last_access_at_iso"),
    }
    if stats is not None:
        payload["stats"] = stats
    return payload


@router.get("/portal/share-link/latest")
def portal_latest_share_link(
    result_type: str,
    target_token: str,
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    order, target_id = _portal_share_target(
        result_type=result_type,
        target_token=target_token,
        settings=settings,
    )
    svc = ShortLinkService(db_path=settings.share_db_path)
    link = _latest_portal_share_link(
        svc=svc,
        target_id=target_id,
        result_type=result_type,
        order_id=order.id,
    )
    if link is None:
        raise BusinessError(
            DATA_NOT_FOUND,
            detail={"reason": "share_link not found", "target_id": target_id},
        )
    return _portal_share_response(
        request=request,
        link=link,
        result_type=result_type,
        target_id=target_id,
        stats=svc.get_stats(link.code),
    )


@router.post("/portal/share-link", status_code=201)
def portal_create_share_link(
    payload: dict[str, Any],
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    result_type = str(payload.get("result_type") or "").strip()
    target_token = str(payload.get("target_token") or "").strip()
    permission = str(payload.get("permission") or "read").strip()
    ttl_days_raw = payload.get("ttl_days")
    replace_existing = bool(payload.get("replace_existing"))
    if not target_token:
        raise BusinessError(
            DATA_VALIDATION_FAILED,
            detail={"reason": "target_token is required"},
        )
    ttl_days: int | None = None
    if ttl_days_raw is not None:
        try:
            ttl_days = int(ttl_days_raw)
        except (TypeError, ValueError) as exc:
            raise BusinessError(
                DATA_VALIDATION_FAILED,
                detail={"reason": "ttl_days must be integer"},
            ) from exc
        if ttl_days <= 0:
            raise BusinessError(
                DATA_VALIDATION_FAILED,
                detail={"reason": "ttl_days must be > 0"},
            )

    order, target_id = _portal_share_target(
        result_type=result_type,
        target_token=target_token,
        settings=settings,
    )
    svc = ShortLinkService(db_path=settings.share_db_path)
    existing = _latest_portal_share_link(
        svc=svc,
        target_id=target_id,
        result_type=result_type,
        order_id=order.id,
    )
    if replace_existing and existing is not None and not existing.revoked:
        svc.revoke(existing.code)

    link = svc.create(
        report_id=target_id,
        owner_id=f"portal:{order.id}",
        permission=permission,
        ttl_days=ttl_days,
        note=f"{result_type}:{order.id}",
    )
    return _portal_share_response(
        request=request,
        link=link,
        result_type=result_type,
        target_id=target_id,
    )


@router.post("/portal/share-link/{code}/revoke")
def portal_revoke_share_link(
    code: str,
    payload: dict[str, Any],
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    result_type = str(payload.get("result_type") or "").strip()
    target_token = str(payload.get("target_token") or "").strip()
    order, target_id = _portal_share_target(
        result_type=result_type,
        target_token=target_token,
        settings=settings,
    )
    svc = ShortLinkService(db_path=settings.share_db_path)
    link = _latest_portal_share_link(
        svc=svc,
        target_id=target_id,
        result_type=result_type,
        order_id=order.id,
    )
    if link is None or link.code != code:
        raise BusinessError(DATA_NOT_FOUND, detail={"code": code})
    changed = svc.revoke(code)
    current = svc.get(code)
    if current is None:
        raise BusinessError(DATA_NOT_FOUND, detail={"code": code})
    payload = _portal_share_response(
        request=request,
        link=current,
        result_type=result_type,
        target_id=target_id,
        stats=svc.get_stats(code),
    )
    payload["changed"] = changed
    return payload


@router.get("/portal/{token}/status", include_in_schema=False)
def order_status_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    return HTMLResponse(_render_status_page(token, context, settings))


@router.get("/portal/{token}/report", include_in_schema=False)
def report_view_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    if context["stage"] not in {"report_ready", "completed"}:
        raise HTTPException(status_code=409, detail="report not ready")
    return HTMLResponse(_render_report_page(order, settings))


@router.get("/portal/{token}/report.pdf", include_in_schema=False)
def report_pdf_download(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> FileResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    if context["stage"] not in {"report_ready", "completed"}:
        raise HTTPException(status_code=409, detail="report not ready")
    if (
        not order.pdf_path
        or not _is_trusted_report_path(order.pdf_path, settings)
        or not Path(order.pdf_path).is_file()
    ):
        raise HTTPException(status_code=404, detail="pdf not found")
    return FileResponse(
        order.pdf_path, media_type="application/pdf", filename=Path(order.pdf_path).name
    )


def _payment_service(settings: Settings) -> PaymentService:
    return PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
        provider_name=settings.payment_provider,
        notify_url=settings.payment_notify_url,
        return_url=settings.payment_return_url,
        app_id=settings.payment_app_id,
        merchant_id=settings.payment_merchant_id,
        private_key_path=settings.payment_private_key_path,
        alipay_public_key_path=settings.payment_alipay_public_key_path,
    )


def _resolve_order_from_token(token: str, settings: Settings) -> Order:
    try:
        payload = verify_portal_token(token, settings.portal_token_secret)
    except PortalTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            return dao.get(str(payload["order_id"]))
        except OrderNotFound as exc:
            raise HTTPException(status_code=404, detail="order not found") from exc


def _is_trusted_report_path(path: str | None, settings: Settings) -> bool:
    if not path:
        return False
    candidate = Path(path).resolve()
    trusted_roots = (
        Path(settings.share_report_dir).resolve(),
        (
            Path(settings.portal_upload_dir).resolve().parent / "order_artifacts"
        ).resolve(),
        Path("data/examples").resolve(),
    )
    return any(root == candidate or root in candidate.parents for root in trusted_roots)


def _build_portal_context(order: Order, settings: Settings) -> dict[str, Any]:
    payment_service = _payment_service(settings)
    payment = payment_service.get_payment_by_order(order.id)
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(order.id)
    finally:
        intake_store.close()
    notification_service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        sent_station_events = notification_service.list_events(
            order.id,
            status="validated",
            channel="station",
        )
        if not sent_station_events:
            sent_station_events = notification_service.list_events(
                order.id,
                status="delivered",
                channel="station",
            )
    finally:
        notification_service.close()

    stage = "pending_payment"
    report_html_ready = bool(
        order.audit_report
        and _is_trusted_report_path(order.audit_report, settings)
        and Path(order.audit_report).is_file()
    )
    report_pdf_ready = bool(
        order.pdf_path
        and _is_trusted_report_path(order.pdf_path, settings)
        and Path(order.pdf_path).is_file()
    )
    report_artifacts_ready = report_html_ready and report_pdf_ready
    if order.status == "refunded" or (
        payment is not None and payment.status == "refunded"
    ):
        stage = "refunded"
    elif payment is None or payment.status in {"pending", "failed"}:
        stage = "pending_payment"
    elif order.status == "completed":
        stage = "completed"
    elif order.status == "delivered" and report_artifacts_ready:
        stage = "report_ready"
    elif order.status in {"serving", "delivered"}:
        stage = "processing"
    elif intake is None or intake.status == "draft":
        stage = "info_required"
    elif intake.status == "submitted":
        stage = "info_submitted"

    title, subtitle = _STAGE_META[stage]
    latest_station_notice: dict[str, Any] | None = None
    intake_summary = None
    attachment_count = 0
    attachment_items: list[dict[str, Any]] = []
    profile_payload = (
        intake.payload
        if intake is not None
        else {
            "candidate_province": order.candidate_province,
            "candidate_score": order.candidate_score,
            "candidate_rank": order.candidate_rank,
            "candidate_subjects": order.candidate_subjects,
        }
    )
    if intake is not None:
        attachment_items = [
            item
            for item in list((intake.payload or {}).get("attachments") or [])
            if isinstance(item, dict)
        ]
        attachment_count = len(attachment_items)
        intake_summary = {
            "candidate_province": intake.payload.get("candidate_province")
            or order.candidate_province,
            "candidate_score": intake.payload.get("candidate_score"),
            "candidate_rank": intake.payload.get("candidate_rank"),
            "candidate_subjects": intake.payload.get("candidate_subjects") or [],
            "candidate_interests": intake.payload.get("candidate_interests"),
            "target_cities": intake.payload.get("target_cities") or [],
            "target_majors": intake.payload.get("target_majors") or [],
            "university_preferences": intake.payload.get("university_preferences"),
            "existing_plan_summary": intake.payload.get("existing_plan_summary"),
            "guardian_notes": intake.payload.get("guardian_notes"),
        }
    if sent_station_events:
        try:
            latest_payload = json.loads(sent_station_events[-1].payload_json)
        except json.JSONDecodeError:
            latest_payload = {}
        station_notice = latest_payload.get("station_notice")
        if isinstance(station_notice, dict):
            latest_station_notice = station_notice
    return {
        "stage": stage,
        "stage_title": title,
        "stage_subtitle": subtitle,
        "payment": payment,
        "payment_status": payment.status if payment is not None else "pending",
        "intake": intake,
        "intake_summary": intake_summary,
        "attachment_count": attachment_count,
        "attachments": attachment_items,
        "report_html_ready": report_html_ready,
        "report_pdf_ready": report_pdf_ready,
        "order": order,
        "station_notice": latest_station_notice,
        "profile_minimum_complete": _is_profile_minimum_complete(profile_payload),
        "profile_missing_fields": _profile_missing_fields(profile_payload),
    }


def _render_global_nav() -> str:
    """全局统一导航栏。所有页面必须注入。"""
    return '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="/data-query">数据查询</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'


def _render_global_toast_script() -> str:
    """全局 toast + loading 注入脚本。在 {_render_global_toast_script()}</body> 前注入。"""
    return """<div class="state-toast-stack" id="toast-stack" aria-live="polite" aria-atomic="true"></div>
<script>
window.showToast = function(msg, type) {
  var stack = document.getElementById('toast-stack');
  if (!stack) return;
  var toast = document.createElement('div');
  toast.className = 'state-toast state-toast--' + (type || 'info');
  toast.textContent = msg;
  stack.appendChild(toast);
  requestAnimationFrame(function() { toast.classList.add('state-toast--visible'); });
  setTimeout(function() {
    toast.classList.remove('state-toast--visible');
    setTimeout(function() { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
  }, 3000);
};
window.showLoading = function(container, msg) {
  if (!container) return null;
  var el = document.createElement('div');
  el.className = 'state-loading';
  el.innerHTML = '<div class="state-loading__spinner"></div><p class="state-loading__text">' + (msg || '加载中…') + '</p>';
  container.appendChild(el);
  return el;
};
window.hideLoading = function(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
};
</script>"""


def _render_footer_links(token: str | None = None) -> str:
    privacy_href = "/privacy"
    terms_href = "/service-terms"
    if token:
        privacy_href = "/privacy"
        terms_href = "/service-terms"
        deletion_href = f"/portal/{escape(token)}/deletion-request"
    else:
        deletion_href = "/deletion-policy"
    return (
        f'<footer style="margin-top:24px;color:#5b6b88;font-size:14px;">'
        f'<a href="{privacy_href}">隐私政策</a> · '
        f'<a href="{terms_href}">服务说明与免责声明</a> · '
        f'<a href="{deletion_href}">删除申请 / 数据删除说明</a>'
        f"</footer>"
    )


def _render_share_status_panel(
    *, result_type: str, token: str, settings: Settings | None = None
) -> str:
    """渲染"当前分享状态"面板。

    settings 可选；不传则现场加载。即使查询失败也会渲染骨架。
    """
    if not token or result_type not in {"review_result", "report"}:
        return ""

    latest_info: dict[str, Any] | None = None
    s = settings
    if s is None:
        try:
            from admin.config import load_settings as _load_settings

            s = _load_settings()
        except Exception:  # noqa: BLE001
            s = None
    if s is not None:
        try:
            order, target_id = _portal_share_target(
                result_type=result_type,
                target_token=token,
                settings=s,
            )
            svc = ShortLinkService(db_path=s.share_db_path)
            chosen = _latest_portal_share_link(
                svc=svc,
                target_id=target_id,
                result_type=result_type,
                order_id=order.id,
            )
            if chosen is not None:
                d = chosen.to_dict()
                stats = svc.get_stats(chosen.code) or {}
                latest_info = {
                    "permission": chosen.permission,
                    "expires_at_iso": d.get("expires_at_iso"),
                    "revoked": bool(chosen.revoked),
                    "expired": chosen.is_expired(),
                    "access_count": int(stats.get("access_count") or 0),
                    "last_access_at_iso": stats.get("last_access_at_iso"),
                }
        except Exception:  # noqa: BLE001
            latest_info = None

    if latest_info is None:
        status_line = '<p class="share-status-line">最近一次分享：无</p>'
    else:
        perm = str(latest_info.get("permission") or "read")
        suffix_parts: list[str] = []
        if latest_info.get("revoked"):
            suffix_parts.append("已撤销")
        elif latest_info.get("expired"):
            suffix_parts.append("已过期")
        elif latest_info.get("expires_at_iso"):
            suffix_parts.append("7天后过期")
        status_line = f'<p class="share-status-line">最近一次分享：{escape(perm)}'
        if suffix_parts:
            status_line += (
                "（" + "，".join(escape(part) for part in suffix_parts) + "）"
            )
        status_line += "</p>"
        access_count = int(latest_info.get("access_count") or 0)
        last_access = latest_info.get("last_access_at_iso")
        status_line += (
            f'<p class="share-status-line subtle">访问次数：{access_count}'
            + (f" · 最后访问：{escape(str(last_access))}" if last_access else "")
            + "</p>"
        )

    escaped_token = escape(token)
    escaped_result_type = escape(result_type)
    latest_query = f"/portal/share-link/latest?result_type={escaped_result_type}&target_token={escaped_token}"

    return f"""
<section class="panel share-status-panel" aria-label="当前分享状态">
  <h2>当前分享状态</h2>
  {status_line}
  <div class="share-actions" data-token="{escaped_token}" data-result-type="{escaped_result_type}" data-latest-url="{latest_query}">
    <button class="btn btn-secondary" id="share-copy-official" type="button">复制正式分享链接</button>
    <button class="btn btn-secondary" id="share-regenerate" type="button">重新生成分享链接</button>
    <button class="btn btn-secondary" id="share-revoke" type="button">撤销当前分享链接</button>
  </div>
  <p class="meta" id="share-status-panel-msg">正式链接用于向考生/家长稳定分享，不会随订单状态变更失效；你可以在这里复制、重生成或撤销当前链接。</p>
  <script>
  (function() {{
    var panelRoot = document.querySelector('.share-status-panel .share-actions');
    var msgEl = document.getElementById('share-status-panel-msg');
    function msg(text, ok) {{
      if (!msgEl) return;
      msgEl.textContent = text;
      msgEl.style.color = ok ? '#1f6feb' : '#b42318';
    }}
    async function adminFetch(url, opts) {{
      opts = opts || {{}};
      opts.credentials = 'include';
      var resp = await fetch(url, opts);
      var body = {{}};
      try {{ body = await resp.json(); }} catch (e) {{}}
      if (!resp.ok) {{
        throw new Error(body?.message || body?.detail?.reason || '请求失败 (' + resp.status + ')');
      }}
      return body;
    }}
    function bind(id, handler) {{
      var el = document.getElementById(id);
      if (el) el.addEventListener('click', handler);
    }}
    if (!panelRoot) return;
    var latestQuery = panelRoot.getAttribute('data-latest-url') || '{latest_query}';
    bind('share-copy-official', async function() {{
      try {{
        var data = await adminFetch(latestQuery);
        try {{
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            await navigator.clipboard.writeText(data.share_url);
          }}
          msg('已复制正式分享链接', true);
        }} catch (e) {{ msg('复制失败，请手动复制：' + data.share_url, false); }}
      }} catch (e) {{ msg(e.message || '复制失败', false); }}
    }});
    bind('share-regenerate', async function() {{
      try {{
        var token = panelRoot.getAttribute('data-token');
        var rt = panelRoot.getAttribute('data-result-type');
        await adminFetch('/portal/share-link', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ result_type: rt, target_token: token, permission: 'read', ttl_days: 7, replace_existing: true }})
        }});
        msg('已重新生成正式分享链接，点击"复制"按钮获取新链接', true);
      }} catch (e) {{ msg(e.message || '重新生成失败', false); }}
    }});
    bind('share-revoke', async function() {{
      try {{
        var data = await adminFetch(latestQuery);
        await adminFetch('/portal/share-link/' + encodeURIComponent(data.code) + '/revoke', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ result_type: panelRoot.getAttribute('data-result-type'), target_token: panelRoot.getAttribute('data-token') }})
        }});
        msg('已撤销当前分享链接', true);
      }} catch (e) {{ msg(e.message || '撤销失败', false); }}
    }});
  }})();
  </script>
</section>
"""


def _render_share_link_script(
    *,
    result_type: str,
    token: str,
    copy_id: str,
    share_id: str,
    status_id: str,
    title: str,
) -> str:
    escaped_title = escape(title)
    escaped_token = escape(token)
    escaped_result_type = escape(result_type)
    escaped_copy = escape(copy_id)
    escaped_share = escape(share_id)
    escaped_status = escape(status_id)
    return f"""<script>
(function() {{
  var statusEl = document.getElementById('{escaped_status}');
  var latestShareUrl = '';
  function setStatus(msg, ok) {{
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.style.color = ok ? '#1f6feb' : '#b42318';
  }}
  async function ensureShareUrl() {{
    if (latestShareUrl) return latestShareUrl;
    const resp = await fetch('/api/share-link', {{
      method: 'POST',
      credentials: 'include',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ result_type: '{escaped_result_type}', target_token: '{escaped_token}', permission: 'read', ttl_days: 7 }})
    }});
    const body = await resp.json();
    if (!resp.ok) {{
      throw new Error(body?.message || body?.detail?.reason || '正式分享链接生成失败');
    }}
    latestShareUrl = body.share_url || '';
    return latestShareUrl;
  }}
  async function copyUrl(url) {{
    try {{
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        await navigator.clipboard.writeText(url);
        setStatus('已生成正式分享链接并复制', true);
        return;
      }}
    }} catch (err) {{}}
    try {{
      var ta = document.createElement('textarea');
      ta.value = url;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      setStatus(ok ? '已生成正式分享链接并复制' : '生成成功，请手动复制链接', ok);
    }} catch (err) {{
      setStatus('生成成功，请手动复制链接', false);
    }}
  }}
  var copyBtn = document.getElementById('{escaped_copy}');
  if (copyBtn) copyBtn.addEventListener('click', async function() {{
    try {{
      const shareUrl = await ensureShareUrl();
      await copyUrl(shareUrl);
    }} catch (err) {{
      setStatus('正式分享链接生成失败', false);
    }}
  }});
  var shareBtn = document.getElementById('{escaped_share}');
  if (shareBtn) shareBtn.addEventListener('click', async function() {{
    try {{
      const shareUrl = await ensureShareUrl();
      if (navigator.share) {{
        navigator.share({{ title: '{escaped_title}', text: '{escaped_title}', url: shareUrl }}).then(
          function() {{ setStatus('已通过系统分享发送正式链接', true); }},
          function() {{ copyUrl(shareUrl); }}
        );
      }} else {{
        await copyUrl(shareUrl);
      }}
    }} catch (err) {{
      setStatus('正式分享链接生成失败', false);
    }}
  }});
}})();
</script>"""


def _render_basic_page(
    *,
    title: str,
    eyebrow: str,
    lead: str,
    sections_html: str,
    footer_token: str | None = None,
) -> str:
    nav = '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'
    back_link = '<div style="margin-bottom:8px;"><a href="/" style="color:#194fb6;font-size:13px;text-decoration:none;">← 返回首页</a></div>'
    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        f"<title>{escape(title)}</title>"
        "<link rel='stylesheet' href='/static/portal-ui.css' />"
        '<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:0;color:#172033;margin:0}.wrap{max-width:920px;margin:0 auto;display:grid;gap:18px;padding:32px 20px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.lead{color:#5b6b88;line-height:1.8}.checklist{margin:0;padding-left:18px;color:#5b6b88;line-height:1.8}.meta{color:#5b6b88;line-height:1.8}</style></head>'
        f"<body>{_render_global_nav()}{nav}<main class='wrap' role='main'>"
        f"{back_link}"
        f"<section class='panel'><span class='eyebrow'>{escape(eyebrow)}</span><h1>{escape(title)}</h1><p class='lead'>{lead}</p></section>"
        f"{sections_html}"
        f"{_render_footer_links(footer_token)}"
        "</main>{_render_global_toast_script()}</body></html>"
    )


def _render_placeholder_shell(
    *,
    title: str,
    max_width: int,
    body_html: str,
) -> str:
    top_toolbar = '<div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div>'
    return f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>{escape(title)}</title><link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f3f7fb;margin:0;padding:32px 20px;color:#142235}}.wrap{{max-width:{max_width}px;margin:0 auto;display:grid;gap:16px}}.panel{{background:#fff;border:1px solid #d7e3f1;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.meta{{color:#5b6b88;line-height:1.8}}.actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700}}.btn-primary{{background:#1f6feb;color:#fff}}.btn-secondary{{background:#edf3ff;color:#194fb6}}.empty-state{{padding:18px;border-radius:14px;background:#f8fbff;border:1px solid #d7e3f1;color:#5b6b88}}.error-state{{padding:18px;border-radius:14px;background:#fff5f5;border:1px solid #f5c2c7;color:#b42318}}</style></head><body><nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav><main class="wrap">{top_toolbar}{body_html}</main>{_render_global_toast_script()}</body></html>"""


def _find_legal_doc_path(doc_filename: str) -> Path | None:
    """定位 docs/<doc_filename> 法务文档；找不到返回 None。

    搜索顺序：项目根 docs/（开发态）→ 包内 admin/legal/（部署态）。
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "docs" / doc_filename,
        Path(__file__).resolve().parent / "legal" / doc_filename,
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def _render_legal_doc_page(
    *,
    doc_filename: str,
    title: str,
    eyebrow: str,
    lead: str,
    footer_token: str | None = None,
) -> str | None:
    """渲染完整法务文档为 HTML 页面。

    找不到文档时返回 None，调用方应 fallback 到简版概要页。
    """
    doc_path = _find_legal_doc_path(doc_filename)
    if doc_path is None:
        return None
    try:
        raw = doc_path.read_text(encoding="utf-8")
    except OSError:
        return None
    body_html = markdown.markdown(
        raw,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    nav = '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'
    back_link = '<div style="margin-bottom:8px;"><a href="/" style="color:#194fb6;font-size:13px;text-decoration:none;">← 返回首页</a></div>'
    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        f"<title>{escape(title)}</title>"
        "<link rel='stylesheet' href='/static/portal-ui.css' />"
        '<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:0;color:#172033;margin:0}'
        ".wrap{max-width:920px;margin:0 auto;display:grid;gap:18px;padding:32px 20px}"
        ".panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:32px;box-shadow:0 18px 42px rgba(20,34,53,.08)}"
        ".eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}"
        ".lead{color:#5b6b88;line-height:1.8;margin:8px 0 16px}"
        ".legal-doc h1{display:none}"
        ".legal-doc h2{color:#172033;font-size:18px;margin:24px 0 12px;border-bottom:2px solid #eef2fb;padding-bottom:6px}"
        ".legal-doc h3{color:#1f3a68;font-size:15px;margin:18px 0 8px}"
        ".legal-doc p{color:#34425b;line-height:1.85;margin:8px 0}"
        ".legal-doc ul,.legal-doc ol{color:#34425b;line-height:1.85;padding-left:22px;margin:8px 0}"
        ".legal-doc li{margin:4px 0}"
        ".legal-doc blockquote{border-left:3px solid #cfd9ee;color:#5b6b88;padding:8px 14px;margin:12px 0;background:#f8fbff;border-radius:0 8px 8px 0}"
        ".legal-doc table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px;background:#fff}"
        ".legal-doc th,.legal-doc td{border:1px solid #d7e3f1;padding:8px 10px;text-align:left;vertical-align:top}"
        ".legal-doc th{background:#eef4ff;color:#172033;font-weight:600}"
        ".legal-doc code{background:#f1f5fb;padding:1px 4px;border-radius:4px;font-size:12.5px;color:#1f3a68}"
        "</style></head>"
        f"<body>{_render_global_nav()}{nav}<main class='wrap' role='main'>"
        f"{back_link}"
        f"<section class='panel'><span class='eyebrow'>{escape(eyebrow)}</span><h1>{escape(title)}</h1><p class='lead'>{escape(lead)}</p></section>"
        f"<section class='panel legal-doc'>{body_html}</section>"
        f"{_render_footer_links(footer_token)}"
        "</main>{_render_global_toast_script()}</body></html>"
    )


@router.get("/privacy", include_in_schema=False)
def privacy_page(token: str | None = None) -> HTMLResponse:
    full_html = _render_legal_doc_page(
        doc_filename="PRIVACY_POLICY_DRAFT.md",
        title="隐私政策",
        eyebrow="隐私说明",
        lead="运营主体：龙某某（个人开发者）｜联系邮箱：lon22@qq.com｜版本：privacy-policy-v2026.06.25｜生效：2026-06-25。我们只收集下单、资料填写、支付与交付所需的最小信息，用于志愿服务流程，不用于营销出售或无关用途。",
        footer_token=token,
    )
    if full_html is not None:
        return HTMLResponse(full_html)
    sections_html = "<section class='panel'><h2>你可以预期什么</h2><ul class='checklist'><li>支付前只收必要下单信息</li><li>详细资料在支付后通过资料向导分步补充</li><li>隐私政策、服务说明与删除申请入口全程可见</li><li>如需撤回资料或申请删除，可通过删除申请入口提交请求</li></ul></section>"
    return HTMLResponse(
        _render_basic_page(
            title="隐私政策",
            eyebrow="隐私说明",
            lead="运营主体：龙某某（个人开发者）｜联系邮箱：lon22@qq.com｜版本：privacy-policy-v2026.06.25｜生效：2026-06-25。我们只收集下单、资料填写、支付与交付所需的最小信息，用于志愿服务流程，不用于营销出售或无关用途。",
            sections_html=sections_html,
            footer_token=token,
        )
    )


@router.get("/service-terms", include_in_schema=False)
def service_terms_page(token: str | None = None) -> HTMLResponse:
    full_html = _render_legal_doc_page(
        doc_filename="SERVICE_TERMS.md",
        title="服务说明与使用条款",
        eyebrow="服务边界",
        lead="运营主体：龙某某（个人开发者）｜联系邮箱：lon22@qq.com｜版本：service-terms-v2026.06.25｜生效：2026-06-25。本服务提供志愿填报辅助建议、方案审计与交付支持，不承诺录取结果；提交资料前请确认监护人与考生已知情。",
        footer_token=token,
    )
    if full_html is not None:
        return HTMLResponse(full_html)
    sections_html = "<section class='panel'><h2>下单前请了解</h2><ul class='checklist'><li>我们优先帮助你审计现有方案与风险点</li><li>支付后可继续补充详细资料与附件</li><li>交付状态、通知与报告入口会在站内持续更新</li><li>如需撤回资料或删除交付物，可通过删除申请入口提交请求</li></ul></section>"
    return HTMLResponse(
        _render_basic_page(
            title="服务说明与免责声明",
            eyebrow="服务边界",
            lead="运营主体：龙某某（个人开发者）｜联系邮箱：lon22@qq.com｜版本：service-terms-v2026.06.25｜生效：2026-06-25。本服务提供志愿填报辅助建议、方案审计与交付支持，不承诺录取结果；提交资料前请确认监护人与考生已知情。",
            sections_html=sections_html,
            footer_token=token,
        )
    )


def _normalized_profile_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    def _clean_list(value: Any) -> list[str]:
        return [str(item).strip() for item in list(value or []) if str(item).strip()]

    return {
        "candidate_province": str(payload.get("candidate_province") or "").strip(),
        "candidate_subjects": _clean_list(payload.get("candidate_subjects")),
        "candidate_score": payload.get("candidate_score"),
        "candidate_rank": payload.get("candidate_rank"),
        "target_cities": _clean_list(payload.get("target_cities")),
        "target_majors": _clean_list(payload.get("target_majors")),
        "target_schools": _clean_list(payload.get("target_schools")),
        "school_region_preferences": _clean_list(
            payload.get("school_region_preferences")
        ),
        "school_preference_types": _clean_list(payload.get("school_preference_types")),
        "disliked_majors": _clean_list(payload.get("disliked_majors")),
        "employment_region_preferences": _clean_list(
            payload.get("employment_region_preferences")
        ),
        "candidate_interests": str(payload.get("candidate_interests") or "").strip(),
        "university_preferences": str(
            payload.get("university_preferences") or ""
        ).strip(),
        "priority_strategy": str(payload.get("priority_strategy") or "").strip(),
        "graduation_plan": str(payload.get("graduation_plan") or "").strip(),
        "tuition_preference": str(payload.get("tuition_preference") or "").strip(),
        "family_background": str(payload.get("family_background") or "").strip(),
        "industry_resources": str(payload.get("industry_resources") or "").strip(),
        "extra_notes": str(payload.get("extra_notes") or "").strip(),
        "interest_assessment_type": str(
            payload.get("interest_assessment_type") or ""
        ).strip(),
        "interest_assessment_result": str(
            payload.get("interest_assessment_result") or ""
        ).strip(),
        "interest_assessment_notes": str(
            payload.get("interest_assessment_notes") or ""
        ).strip(),
        "existing_plan_summary": str(
            payload.get("existing_plan_summary") or ""
        ).strip(),
        "guardian_notes": str(payload.get("guardian_notes") or "").strip(),
    }


def _profile_stage_label(index: int) -> str:
    labels = ["初始档案方案", "查分后校准方案", "正式填报前调整方案"]
    if index < len(labels):
        return labels[index]
    return f"第 {index + 1} 次档案快照"


def _profile_version_id(index: int) -> str:
    return f"profile_v{index + 1}"


def _ensure_profile_version_metadata(
    payload: dict[str, Any], *, source: str = "portal"
) -> dict[str, Any]:
    updated = dict(payload)
    snapshot = _normalized_profile_snapshot(updated)
    versions = [
        item
        for item in list(updated.get("profile_versions") or [])
        if isinstance(item, dict)
    ]
    if versions and versions[-1].get("snapshot_payload") == snapshot:
        updated["profile_versions"] = versions
        updated["latest_profile_version_id"] = str(
            versions[-1].get("profile_version_id")
            or _profile_version_id(len(versions) - 1)
        )
        return updated
    version = {
        "profile_version_id": _profile_version_id(len(versions)),
        "stage_label": _profile_stage_label(len(versions)),
        "snapshot_payload": snapshot,
        "created_at": utc_now_iso(),
        "source": source,
    }
    versions.append(version)
    updated["profile_versions"] = versions
    updated["latest_profile_version_id"] = version["profile_version_id"]
    return updated


def _latest_profile_version(payload: dict[str, Any]) -> dict[str, Any] | None:
    versions = [
        item
        for item in list(payload.get("profile_versions") or [])
        if isinstance(item, dict)
    ]
    latest_id = str(payload.get("latest_profile_version_id") or "").strip()
    for item in versions:
        if str(item.get("profile_version_id") or "") == latest_id:
            return item
    return versions[-1] if versions else None


def _profile_version_label_from_payload(payload: dict[str, Any]) -> str:
    latest = _latest_profile_version(payload)
    if latest is not None:
        return str(latest.get("profile_version_id") or "profile-step1-incomplete")
    return _profile_version_label(
        {
            "intake_summary": payload,
            "profile_minimum_complete": _is_profile_minimum_complete(payload),
        }
    )


def _report_version_profile_reference(
    payload: dict[str, Any], *, report_version_id: str, fallback_profile_version_id: str
) -> str:
    for item in list(payload.get("report_versions") or []):
        if not isinstance(item, dict):
            continue
        if str(item.get("report_version_id") or "") != report_version_id:
            continue
        referenced = str(item.get("profile_version_id") or "").strip()
        if referenced:
            return referenced
    return fallback_profile_version_id


def _ensure_report_version_metadata(
    payload: dict[str, Any],
    *,
    report_version_id: str,
    profile_version_id: str,
    review_result_version_id: str | None,
    artifact_refs: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    versions = [
        item
        for item in list(updated.get("report_versions") or [])
        if isinstance(item, dict)
    ]
    for item in versions:
        if str(item.get("report_version_id") or "") == report_version_id:
            updated["latest_report_version_id"] = report_version_id
            return updated
    versions.append(
        {
            "report_version_id": report_version_id,
            "profile_version_id": profile_version_id,
            "review_result_version_id": review_result_version_id,
            "artifact_refs": artifact_refs,
            "created_at": utc_now_iso(),
        }
    )
    updated["report_versions"] = versions
    updated["latest_report_version_id"] = report_version_id
    return updated


def _current_intake_payload(context: dict[str, Any]) -> dict[str, Any]:
    intake = context.get("intake")
    if intake is not None and isinstance(getattr(intake, "payload", None), dict):
        return dict(intake.payload)
    summary = context.get("intake_summary")
    if isinstance(summary, dict):
        return dict(summary)
    return {}


def _render_trust_banner_html(
    *,
    province: str,
    official_source: str,
    last_updated: str,
    scope: str,
    confidence_label: str,
    boundary_note: str,
) -> str:
    return (
        '<div class="trust-banner">'
        f'<p class="meta">可信度说明：官方来源：{escape(official_source)} · 更新时间：{escape(last_updated or "未公布")}</p>'
        f'<p class="meta">适用范围：{escape(scope)} · 适用省份：{escape(province)} · 置信等级：{escape(confidence_label)}</p>'
        f'<p class="meta">{escape(boundary_note)}</p>'
        "</div>"
    )


def _helper_entry_hrefs(payload: dict[str, Any], order: Order) -> tuple[str, str]:
    province = (
        str(
            payload.get("candidate_province") or order.candidate_province or "湖南"
        ).strip()
        or "湖南"
    )
    score = payload.get("candidate_score") or order.candidate_score or 0
    return (
        f"/policy-center?province={escape(province)}",
        f"/same-score-reference?province={escape(province)}&score={escape(str(score))}",
    )


def _profile_version_state(payload: dict[str, Any], profile_version_id: str) -> str:
    latest_profile_version = str(
        payload.get("latest_profile_version_id") or profile_version_id
    )
    if profile_version_id == latest_profile_version:
        return "基于最新档案生成"
    return "基于历史档案版本生成，建议刷新"


def _render_auxiliary_factor_section(payload: dict[str, Any]) -> str:
    rows: list[str] = []
    if payload.get("interest_assessment_result"):
        rows.append(
            f"<li>测评结果：{escape(str(payload.get('interest_assessment_result') or ''))}</li>"
        )
    if payload.get("family_background"):
        rows.append(
            f"<li>家庭背景：{escape(str(payload.get('family_background') or ''))}</li>"
        )
    if payload.get("industry_resources"):
        rows.append(
            f"<li>行业资源：{escape(str(payload.get('industry_resources') or ''))}</li>"
        )
    if payload.get("extra_notes"):
        rows.append(
            f"<li>补充说明：{escape(str(payload.get('extra_notes') or ''))}</li>"
        )
    if not rows:
        return ""
    return (
        '<section class="panel"><h2>辅助判断因子</h2>'
        '<p class="meta">这些内容只用于辅助解释，不作为唯一判断。</p>'
        f"<ul>{''.join(rows)}</ul></section>"
    )


def _sync_report_version_metadata(
    order_id: str,
    settings: Settings,
    *,
    report_version_id: str,
    profile_version_id: str,
    review_result_version_id: str | None,
    artifact_refs: dict[str, Any],
) -> None:
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        current = intake_store.get(order_id)
        if current is None:
            return
        updated_payload = _ensure_report_version_metadata(
            current.payload,
            report_version_id=report_version_id,
            profile_version_id=profile_version_id,
            review_result_version_id=review_result_version_id,
            artifact_refs=artifact_refs,
        )
        if updated_payload != current.payload:
            intake_store.save(
                order_id=order_id,
                payload=updated_payload,
                submit=(current.status == "submitted"),
            )
    finally:
        intake_store.close()


def _public_supported_provinces() -> set[str]:
    return {
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "河南",
        "山东",
        "山西",
        "陕西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "甘肃",
        "青海",
        "新疆",
    }


@router.get("/policy-center", include_in_schema=False)
def policy_center_page(province: str = "湖南") -> HTMLResponse:
    safe_province = province or "湖南"
    supported = safe_province in _public_supported_provinces()
    trust_banner = _render_trust_banner_html(
        province=safe_province,
        official_source=f"{safe_province}省教育考试院",
        last_updated="2026-06-22",
        scope="政策摘要与填报提醒",
        confidence_label="参考" if supported else "暂不支持",
        boundary_note=(
            "未覆盖内容必须显式标注；页面仅提供摘要，不替代官方全文。"
            if supported
            else "当前省份尚未进入公开支持集，请不要把本页内容视为可用填报依据。"
        ),
    )
    support_notice = (
        ""
        if supported
        else "<section class='panel'><h2>当前省份暂不支持</h2><p class='meta'>公开政策摘要与同分段参考当前未覆盖该省份，请勿继续使用本页作为填报依据。</p></section>"
    )
    same_score_href = f"/same-score-reference?province={escape(safe_province)}&score=0"
    body = f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>政策中心</title><link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.eyebrow{{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}.meta{{color:#5b6b88;line-height:1.8}}.actions{{display:flex;gap:12px;flex-wrap:wrap}}a{{color:#1f6feb;text-decoration:none}}</style></head><body>{_render_global_nav()}<main class="wrap"><section class="panel"><span class="eyebrow">政策中心</span><h1>政策中心</h1><p class="meta">适用省份：{escape(safe_province)}</p>{trust_banner}<div class="actions"><a href=\"{same_score_href}\">查看同分段参考</a><a href=\"/\">返回首页</a></div></section>{support_notice}<section class="panel"><h2>时间节点</h2><ul><li>查分后先核对成绩、位次与选科要求。</li><li>正式填报前再次确认批次与专业组选科约束。</li></ul></section><section class="panel"><h2>批次规则</h2><p class="meta">当前只整理普通类主链的关键规则；特殊批次、艺体类等未覆盖内容需另行核对。</p></section><section class="panel"><h2>提前批与专项计划</h2><p class="meta">提前批和专项计划是可以降分进入好学校的特殊渠道，但各有报考条件限制。以下列出主要类型：</p><ul><li><strong>军校（本科提前批）</strong>：入学即入伍，毕业分配工作。需通过政审+军检，年龄不超过20周岁。比同层次普通院校低30-80分。</li><li><strong>公安院校（本科提前批）</strong>：毕业参加公安联考入警率90%+，需通过体检+体能测试+政审。注意只有公安专业才能参加联考。</li><li><strong>国家专项计划</strong>：面向脱贫县农村考生，需当地连续3年户籍+学籍。通常降10-30分。</li><li><strong>地方专项计划</strong>：面向农村户籍考生，各省自定实施区域。通常降15-40分。</li><li><strong>高校专项计划</strong>：教育部直属高校面向农村考生，需4-5月提前报名。通常降20-60分。</li><li><strong>公费师范生</strong>：免学费+住宿费+补贴，毕业包分配有编有岗，需回生源省任教6年。</li><li><strong>免费医学定向</strong>：免学费，毕业回基层卫生院事业编，需服务6年。</li></ul><p class="meta">具体资格要求、体检标准和降分幅度以当地教育考试院和各院校官方招生简章为准。</p></section><section class="panel"><h2>选科要求</h2><p class="meta">先核对目标专业组选科要求，再判断是否要调整冲稳保结构。</p></section><section class="panel"><h2>常见误区</h2><ul><li>不要把同分段参考当成最终结论。</li><li>不要用去年的批次规则替代当年正式发布口径。</li></ul><p class="meta">以{escape(safe_province)}省教育考试院官方信息为准。</p></section>{_render_footer_links()}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/same-score-reference", include_in_schema=False)
def same_score_reference_page(province: str = "湖南", score: int = 0) -> HTMLResponse:
    safe_province = province or "湖南"
    supported = safe_province in _public_supported_provinces()
    loader = CrowdDBLoader(warn_low_confidence=False)
    metadata = loader.load_metadata(safe_province) if supported else None
    metadata = metadata or {
        "province": safe_province,
        "last_updated": "",
        "source": "",
        "confidence": None,
    }
    recommendations = (
        loader.find_recommendations(safe_province, score)
        if (score and supported)
        else []
    )
    schools = [
        rec.get("name", "") for rec in recommendations[:5] if isinstance(rec, dict)
    ]
    majors = [
        rec.get("major", "") for rec in recommendations[:5] if isinstance(rec, dict)
    ]
    cities: list[str] = []
    for rec in recommendations[:5]:
        if not isinstance(rec, dict):
            continue
        for alt in rec.get("alternatives", []) or []:
            if isinstance(alt, dict) and alt.get("name"):
                cities.append(str(alt.get("name")))
    confidence = metadata.get("confidence")
    confidence_label = (
        "高"
        if supported and isinstance(confidence, (int, float)) and confidence >= 0.8
        else ("参考" if supported else "暂不支持")
    )
    trust_banner = _render_trust_banner_html(
        province=safe_province,
        official_source=str(
            metadata.get("source") or f"{safe_province}省公开同分段参考整理"
        ),
        last_updated=str(metadata.get("last_updated") or "未公布"),
        scope="同分段参考与扎堆风险提示",
        confidence_label=confidence_label,
        boundary_note=(
            "仅作参考，不替代正式填报判断；非高置信数据不得作为强推荐依据。当前高置信省份以数据质量白名单为准。"
            if supported
            else "当前省份暂不支持公开同分段参考，请不要把“暂无”理解为普通空数据。"
        ),
    )
    unsupported_notice = (
        ""
        if supported
        else "<section class='panel'><h2>当前省份暂不支持</h2><p class='meta'>公开同分段参考当前未覆盖该省份；请勿把当前页面的“暂无”视为普通空数据。</p></section>"
    )
    policy_href = f"/policy-center?province={escape(safe_province)}"
    body = f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>同分段参考</title><link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:1000px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.eyebrow{{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}.meta{{color:#5b6b88;line-height:1.8}}.actions{{display:flex;gap:12px;flex-wrap:wrap}}a{{color:#1f6feb;text-decoration:none}}</style></head><body>{_render_global_nav()}<main class="wrap"><section class="panel"><span class="eyebrow">同分段参考</span><h1>同分段参考</h1><p class="meta">适用省份：{escape(safe_province)} · 置信等级：{escape(confidence_label)} · 数据说明：仅作参考，不替代正式填报判断</p>{trust_banner}<div class="actions"><a href=\"{policy_href}\">查看政策中心</a><a href=\"/\">返回首页</a></div></section>{unsupported_notice}<section class="panel"><h2>同分段热门学校</h2><p>{escape("、".join([item for item in schools if item]) or "暂无")}</p></section><section class="panel"><h2>同分段热门专业</h2><p>{escape("、".join([item for item in majors if item]) or "暂无")}</p></section><section class="panel"><h2>同分段热门城市</h2><p>{escape("、".join([item for item in cities if item]) or "暂无")}</p></section><section class="panel"><h2>扎堆风险提示</h2><p class="meta">若热门学校/专业高度集中，建议回到审核页或冲稳保页重新看梯度风险。</p></section>{_render_footer_links()}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/deletion-policy", include_in_schema=False)
def deletion_policy_page() -> HTMLResponse:
    sections_html = "<section class='panel'><h2>你可以怎么做</h2><ul class='checklist'><li>在 Portal 中提交删除申请</li><li>填写申请人姓名、联系方式、删除范围与原因</li><li>确认监护人已知情并同意发起删除申请</li><li>处理结果会回到站内状态链路中查看</li></ul></section>"
    return HTMLResponse(
        _render_basic_page(
            title="删除申请 / 数据删除说明",
            eyebrow="数据删除",
            lead="如需申请删除订单资料、附件或交付物，可在支付后的 Portal 中提交删除申请；系统会保留必要的审计记录，并由人工核验后处理。",
            sections_html=sections_html,
        )
    )


@router.get("/my-orders", include_in_schema=False)
def my_orders_page(
    request: Request,
    token: str | None = None,
    phone: str
    | None = None,  # 已废弃：C 方案下不再支持手机号直查，保留参数仅为兼容旧链接不报错
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """C 方案：必须持有有效 portal token 才能查看订单。

    旧逻辑（手机号直查 → 现签 portal token）已废弃，因为它构成越权：
    任何知道家长手机号的人都能枚举他人订单和交付物入口。

    现逻辑：
    - 无 token → 显示说明页，引导用户通过下单时收到的 portal 链接进入
    - 有 token → 验证 token → 只展示该 token 对应的那一个订单（不查全量）
    - phone 参数保留仅为兼容旧链接，不再触发任何查询
    """
    from data.customer_portal.token import verify_portal_token, PortalTokenError

    nav = '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'

    # 无 token：显示引导说明（不再显示手机号查询表单）
    if not token:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的订单</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{_render_global_nav()}{nav}<main class="wrap" style="max-width:680px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的订单</h1><section class="state-empty" role="status"><h2 class="state-empty__title">请通过订单链接进入</h2><p class="state-empty__hint">为保护你的订单隐私，我们不再支持凭手机号查询订单。请使用下单时收到的订单进度链接（短信/页面跳转中已包含），直接进入你的订单状态页。如果链接已丢失，请联系客服核实身份后重新获取。</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body)

    # 有 token：验证并只展示该 token 对应的订单
    try:
        payload = verify_portal_token(token, settings.portal_token_secret)
        order_id = str(payload["order_id"])
    except PortalTokenError:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的订单</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{_render_global_nav()}{nav}<main class="wrap" style="max-width:680px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的订单</h1><section class="state-error" role="alert"><h2 class="state-error__title">链接无效或已过期</h2><p class="state-error__hint">你访问的订单链接无效。请使用下单时收到的最新链接，或联系客服。</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body, status_code=401)

    from data.orders.dao import OrdersDAO, OrderNotFound

    try:
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            order = dao.get(order_id)
    except OrderNotFound:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的订单</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{_render_global_nav()}{nav}<main class="wrap" style="max-width:680px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的订单</h1><section class="state-empty" role="status"><h2 class="state-empty__title">订单不存在</h2><p class="state-empty__hint">该订单可能已被删除。如有疑问请联系客服。</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body, status_code=404)

    # 只展示这一个订单，不查全量，不签发新 token（复用当前 token）
    status_url = f"/portal/{token}/status"
    orders_html = (
        f"<section class='panel'><h2>当前订单</h2>"
        f"<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
        f"<thead><tr style='text-align:left;border-bottom:2px solid #d7e3f1;'>"
        f"<th style='padding:8px;'>订单号</th>"
        f"<th style='padding:8px;'>套餐</th>"
        f"<th style='padding:8px;'>状态</th>"
        f"<th style='padding:8px;'>创建时间</th>"
        f"<th style='padding:8px;'>操作</th>"
        f"</tr></thead><tbody>"
        f"<tr><td style='padding:8px;'>{escape(order.id)}</td>"
        f"<td style='padding:8px;'>{escape(order.service_version)}</td>"
        f"<td style='padding:8px;'>{escape(order.status)}</td>"
        f"<td style='padding:8px;'>{escape(str(order.created_at or '')[:16])}</td>"
        f"<td style='padding:8px;'><a href=\"{status_url}\">查看详情</a></td></tr>"
        f"</tbody></table>"
        f"<p class='meta' style='margin-top:10px;font-size:12px;'>仅显示当前链接对应的订单。如需查看其他订单，请使用对应订单的进度链接。</p>"
        f"</section>"
    )

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的订单</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}.meta{{color:#5b6b88;line-height:1.8}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #eef2f7}}th{{font-weight:600;color:#172033}}a{{color:#1f6feb;text-decoration:none}}</style></head><body>{_render_global_nav()}{nav}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的订单</h1></section>{orders_html}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/my-reports", include_in_schema=False)
def my_reports_page(
    request: Request,
    token: str | None = None,
    phone: str | None = None,  # 已废弃：C 方案下不再支持手机号直查
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """C 方案：必须持有有效 portal token 才能查看报告。

    旧逻辑（手机号直查）已废弃，原因同 my_orders_page。
    - 无 token → 显示说明页
    - 有 token → 验证 → 只展示该 token 对应订单的报告（如有交付）
    """
    from data.customer_portal.token import verify_portal_token, PortalTokenError

    nav = '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'

    if not token:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的报告</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{_render_global_nav()}{nav}<main class="wrap" style="max-width:680px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的报告</h1><section class="state-empty" role="status"><h2 class="state-empty__title">请通过订单链接进入</h2><p class="state-empty__hint">为保护你的报告隐私，我们不再支持凭手机号查询报告。请使用下单时收到的订单进度链接进入，在订单状态页查看已交付的报告。如果链接已丢失，请联系客服核实身份后重新获取。</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body)

    try:
        payload = verify_portal_token(token, settings.portal_token_secret)
        order_id = str(payload["order_id"])
    except PortalTokenError:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的报告</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{_render_global_nav()}{nav}<main class="wrap" style="max-width:680px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的报告</h1><section class="state-error" role="alert"><h2 class="state-error__title">链接无效或已过期</h2><p class="state-error__hint">你访问的订单链接无效。请使用下单时收到的最新链接，或联系客服。</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body, status_code=401)

    from data.orders.dao import OrdersDAO, OrderNotFound

    try:
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            order = dao.get(order_id)
    except OrderNotFound:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的报告</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{_render_global_nav()}{nav}<main class="wrap" style="max-width:680px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的报告</h1><section class="state-empty" role="status"><h2 class="state-empty__title">订单不存在</h2><p class="state-empty__hint">该订单可能已被删除。如有疑问请联系客服。</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body, status_code=404)

    # 只展示该订单的报告（如果已交付）
    if order.status in ("delivered", "completed") and order.audit_report:
        report_url = f"/portal/{token}/report"
        reports_html = (
            f"<section class='panel'><h2>当前订单的报告</h2>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
            f"<thead><tr style='text-align:left;border-bottom:2px solid #d7e3f1;'>"
            f"<th style='padding:8px;'>订单号</th>"
            f"<th style='padding:8px;'>套餐</th>"
            f"<th style='padding:8px;'>状态</th>"
            f"<th style='padding:8px;'>创建时间</th>"
            f"<th style='padding:8px;'>操作</th>"
            f"</tr></thead><tbody>"
            f"<tr><td style='padding:8px;'>{escape(order.id)}</td>"
            f"<td style='padding:8px;'>{escape(order.service_version)}</td>"
            f"<td style='padding:8px;'>已交付</td>"
            f"<td style='padding:8px;'>{escape(str(order.created_at or '')[:16])}</td>"
            f"<td style='padding:8px;'><a href=\"{report_url}\">查看报告</a></td></tr>"
            f"</tbody></table></section>"
        )
    else:
        reports_html = (
            "<section class='state-empty' role='status'>"
            "<h2 class='state-empty__title'>当前订单暂无可查看的报告</h2>"
            "<p class='state-empty__hint'>报告在订单完成交付后才会显示。请关注订单状态页的进度更新。</p>"
            "</section>"
        )

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>我的报告</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #eef2f7}}th{{font-weight:600;color:#172033}}a{{color:#1f6feb;text-decoration:none}}</style></head><body>{_render_global_nav()}{nav}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>我的报告</h1></section>{reports_html}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/data-query", include_in_schema=False)
def data_query_page(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """数据查询入口页：分数线 / 位次 / 政策 / 同分段。"""
    body = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" />'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />'
        "<title>数据查询</title>"
        '<link rel="stylesheet" href="/static/portal-ui.css" />'
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}"
        ".wrap{max-width:980px;margin:0 auto;display:grid;gap:18px}"
        ".panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}"
        ".btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}"
        ".meta{color:#5b6b88;line-height:1.8}"
        ".query-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:16px}"
        ".query-card{padding:20px;border-radius:16px;background:#f8fbff;border:1px solid #d7e3f1}"
        ".query-card h3{margin:0 0 8px;font-size:18px}"
        ".query-card p{margin:0 0 12px;color:#5b6b88;font-size:14px;line-height:1.6}"
        "a{color:#1f6feb;text-decoration:none}"
        "@media(max-width:768px){.query-grid{grid-template-columns:1fr}}"
        "</style></head><body>"
        + '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="/data-query">数据查询</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'
        + '<main class="wrap" role="main"><section class="panel">'
        + '<div style="margin-bottom:8px;"><a class="btn" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div>'
        + '<h1>数据查询</h1><p class="meta">查询高考相关的基础数据，辅助你做志愿填报决策。</p>'
        + '<div class="query-grid">'
        + '<div class="query-card"><h3>分数线查询</h3><p>查询全国各省本科线、特殊类型控制线等官方录取分数线。</p><a class="btn" style="font-size:13px;min-height:36px;" href="/score-line-query">进入分数线查询</a></div>'
        + '<div class="query-card"><h3>位次估算</h3><p>输入分数，基于一分一段数据估算全省位次（支持省份取决于数据覆盖）。</p><a class="btn" style="font-size:13px;min-height:36px;" href="/rank-estimator">进入位次估算</a></div>'
        + '<div class="query-card"><h3>专业库</h3><p>搜索教育部公布的专业目录，查看专业代码、学科门类、学位类型。</p><a class="btn" style="font-size:13px;min-height:36px;" href="/majors-query">进入专业库查询</a></div>'
        + '<div class="query-card"><h3>院校库</h3><p>搜索院校，查看院校代码、招生专业和所属省份。</p><a class="btn" style="font-size:13px;min-height:36px;" href="/schools-query">进入院校库查询</a></div>'
        + '<div class="query-card"><h3>政策中心</h3><p>查看各省高考政策摘要、批次规则、选科要求和常见误区。</p><a class="btn" style="font-size:13px;min-height:36px;" href="/policy-center?province=广东">进入政策中心</a></div>'
        + '<div class="query-card"><h3>同分段参考</h3><p>查看某个分数段在各省份的热门学校、专业和城市分布。</p><a class="btn" style="font-size:13px;min-height:36px;" href="/same-score-reference?province=广东&score=578">进入同分段参考</a></div>'
        + "</div></section>"
        + _render_footer_links()
        + "</main>{_render_global_toast_script()}</body></html>"
    )
    return HTMLResponse(body)


@router.get("/score-line-query", include_in_schema=False)
def score_line_query_page(
    request: Request,
    province: str | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """分数线查询页：从 crowd_db 的 score_distribution 读各省本科线。"""
    from data.crowd_db.loader import CrowdDBLoader

    loader = CrowdDBLoader(warn_low_confidence=False)
    nav = '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="/data-query">数据查询</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'

    # 查询逻辑
    result_html = ""
    query_province = (province or "").strip()
    if query_province:
        try:
            data = loader.load_province(query_province)
            if data and data.get("score_distribution"):
                sd = data["score_distribution"]
                subjects = sd.get("subjects", {})
                rows = []
                for subject_name, subj_data in subjects.items():
                    bsl = subj_data.get("bachelor_score_line", 0)
                    rows.append(
                        f"<tr><td style='padding:8px;'>{escape(subject_name)}</td>"
                        f"<td style='padding:8px;'><strong>{bsl}</strong></td>"
                        f"<td style='padding:8px;'>{escape(str(sd.get('data_year', '')))}</td>"
                        f'<td style=\'padding:8px;\'><a href="{escape(str(sd.get("source_url", "")))}" target="_blank">查看来源</a></td></tr>'
                    )
                if rows:
                    result_html = (
                        f"<section class='panel'><h2>{escape(query_province)} 本科分数线</h2>"
                        f"<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
                        f"<thead><tr style='text-align:left;border-bottom:2px solid #d7e3f1;'>"
                        f"<th style='padding:8px;'>科类</th><th style='padding:8px;'>本科线</th>"
                        f"<th style='padding:8px;'>数据年份</th><th style='padding:8px;'>来源</th>"
                        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></section>"
                    )
                else:
                    result_html = "<section class='state-empty' role='status'><h2 class='state-empty__title'>该省份暂无分数线数据</h2><p class='state-empty__hint'>当前 crowd_db 尚未接入该省份的分数线数据。</p></section>"
            else:
                result_html = "<section class='state-empty' role='status'><h2 class='state-empty__title'>该省份暂无分数线数据</h2><p class='state-empty__hint'>当前 crowd_db 尚未接入该省份的分数线数据。</p></section>"
        except Exception:
            result_html = "<section class='state-error' role='alert'><h2 class='state-error__title'>查询失败</h2><p class='state-error__hint'>数据加载出错，请稍后重试。</p></section>"

    # 省份选项
    all_provinces = loader.list_supported_provinces()
    province_options = "".join(
        f'<option value="{p}" {"selected" if p == query_province else ""}>{p}</option>'
        for p in all_provinces
    )

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>分数线查询</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}.meta{{color:#5b6b88;line-height:1.8}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #eef2f7}}th{{font-weight:600}}a{{color:#1f6feb;text-decoration:none}}</style></head><body>{_render_global_nav()}{nav}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/data-query">返回数据查询</a></div><h1>分数线查询</h1><p class="meta">选择省份，查看官方公布的本科录取分数线。</p><form method="get" action="/score-line-query" style="margin-top:12px;"><select name="province" style="padding:10px;border-radius:10px;border:1px solid #d7e3f1;font-size:14px;"><option value="">请选择省份</option>{province_options}</select><button class="btn" type="submit" style="margin-left:8px;">查询</button></form></section>{result_html}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/rank-estimator", include_in_schema=False)
def rank_estimator_page(
    request: Request,
    province: str | None = None,
    score: int | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """位次估算页：基于 crowd_db 的 score_distribution.benchmarks 估算位次。"""
    from data.crowd_db.loader import CrowdDBLoader

    loader = CrowdDBLoader(warn_low_confidence=False)
    nav = '<nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="/data-query">数据查询</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>'

    result_html = ""
    query_province = (province or "").strip()
    query_score = score or 0

    if query_province and query_score:
        try:
            data = loader.load_province(query_province)
            if data and data.get("score_distribution"):
                sd = data["score_distribution"]
                subjects = sd.get("subjects", {})
                estimates = []
                for subject_name, subj_data in subjects.items():
                    benchmarks = subj_data.get("benchmarks", [])
                    # 线性插值估算位次
                    estimated_rank = None
                    if benchmarks:
                        sorted_bms = sorted(
                            benchmarks, key=lambda b: b.get("score", 0), reverse=True
                        )
                        for i, bm in enumerate(sorted_bms):
                            if query_score >= bm["score"]:
                                estimated_rank = bm["cumulative_count"]
                                break
                        if estimated_rank is None:
                            estimated_rank = sorted_bms[-1].get("cumulative_count", 0)
                    if estimated_rank is not None:
                        estimates.append(
                            f"<li>{escape(subject_name)}：估算累计位次约 <strong>{estimated_rank:,}</strong> 名（基于{escape(query_province)}一分一段数据插值）</li>"
                        )
                if estimates:
                    result_html = f"<section class='panel'><h2>{escape(query_province)} 分数 {query_score} 位次估算</h2><ul style='line-height:2;'>{''.join(estimates)}</ul><p class='meta' style='font-size:12px;margin-top:8px;'>⚠ 这是基于公开一分一段锚点的估算值，非精确位次。最终位次以官方一分一段表为准。</p></section>"
                else:
                    result_html = "<section class='state-empty' role='status'><h2 class='state-empty__title'>该省份暂无位次锚点数据</h2><p class='state-empty__hint'>当前 crowd_db 尚未接入该省份的一分一段表。</p></section>"
            else:
                result_html = "<section class='state-empty' role='status'><h2 class='state-empty__title'>该省份暂无位次数据</h2></section>"
        except Exception:
            result_html = "<section class='state-error' role='alert'><h2 class='state-error__title'>查询失败</h2></section>"

    all_provinces = loader.list_supported_provinces()
    province_options = "".join(
        f'<option value="{p}" {"selected" if p == query_province else ""}>{p}</option>'
        for p in all_provinces
    )

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>位次估算</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}.meta{{color:#5b6b88;line-height:1.8}}</style></head><body>{_render_global_nav()}{nav}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/data-query">返回数据查询</a></div><h1>位次估算</h1><p class="meta">选择省份并输入分数，基于公开一分一段数据估算你的全省位次。</p><form method="get" action="/rank-estimator" style="margin-top:12px;"><select name="province" style="padding:10px;border-radius:10px;border:1px solid #d7e3f1;font-size:14px;"><option value="">请选择省份</option>{province_options}</select><input name="score" type="number" value="{query_score}" placeholder="例如：578" style="padding:10px;border-radius:10px;border:1px solid #d7e3f1;font-size:14px;margin-left:8px;width:120px;" /><button class="btn" type="submit" style="margin-left:8px;">估算</button></form></section>{result_html}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/majors-query", include_in_schema=False)
def majors_query_page(
    request: Request,
    q: str | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """专业库查询页：从 majors_catalog 搜索专业。"""
    import json as _json
    from pathlib import Path as _Path

    nav_html = _render_global_nav()
    result_html = ""
    query = (q or "").strip()

    if query:
        try:
            data = _json.loads(
                _Path("data/majors_catalog/national/latest.json").read_text()
            )
            all_majors = data.get("majors", [])
            # 过滤匹配的
            matched = [
                m
                for m in (all_majors or [])
                if query.lower() in m.get("name", "").lower()
                or query.lower() in m.get("category", "").lower()
                or query.lower() in m.get("discipline", "").lower()
            ]
            if matched:
                rows = []
                for m in matched:
                    rows.append(
                        f"<tr>"
                        f"<td style='padding:8px;'>{m.get('code', '')}</td>"
                        f"<td style='padding:8px;'><strong>{m.get('name', '')}</strong></td>"
                        f"<td style='padding:8px;'>{m.get('discipline', '')}</td>"
                        f"<td style='padding:8px;'>{m.get('category', '')}</td>"
                        f"<td style='padding:8px;'>{m.get('degree', '')}</td>"
                        f"<td style='padding:8px;'>{m.get('status', '')}</td>"
                        f"</tr>"
                    )
                result_html = (
                    f"<section class='panel'><h2>搜索结果（{len(matched)} 个专业）</h2>"
                    f"<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
                    f"<thead><tr style='text-align:left;border-bottom:2px solid #d7e3f1;'>"
                    f"<th style='padding:8px;'>代码</th><th style='padding:8px;'>专业名称</th>"
                    f"<th style='padding:8px;'>学科门类</th><th style='padding:8px;'>专业类</th>"
                    f"<th style='padding:8px;'>学位</th><th style='padding:8px;'>状态</th>"
                    f"</tr></thead><tbody>{''.join(rows)}</tbody></table></section>"
                )
            else:
                result_html = f"<section class='state-empty' role='status'><h2 class='state-empty__title'>未找到匹配&quot;{escape(query)}&quot;的专业</h2><p class='state-empty__hint'>当前专业目录为 MVP 子集（13 个核心专业），完整目录待后续扩充。</p></section>"
        except Exception as e:
            result_html = f"<section class='state-error' role='alert'><h2 class='state-error__title'>查询失败</h2><p class='state-error__hint'>{escape(str(e))}</p></section>"

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>专业库查询</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}.meta{{color:#5b6b88;line-height:1.8}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #eef2f7}}th{{font-weight:600}}</style></head><body>{nav_html}{_render_global_nav()}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/data-query">返回数据查询</a></div><h1>专业库查询</h1><p class="meta">搜索教育部公布的专业目录，查看专业代码、学科门类、学位类型。</p><form method="get" action="/majors-query" style="margin-top:12px;"><input name="q" value="{escape(query)}" placeholder="例如：计算机、经济学、工学" style="padding:10px;border-radius:10px;border:1px solid #d7e3f1;font-size:14px;min-width:240px;" /><button class="btn" type="submit" style="margin-left:8px;">搜索</button></form></section>{result_html}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/schools-query", include_in_schema=False)
def schools_query_page(
    request: Request,
    q: str | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """院校库查询页：从 majors_catalog/schools/ 搜索院校。"""
    import json as _json
    from pathlib import Path as _Path

    nav_html = _render_global_nav()
    result_html = ""
    query = (q or "").strip()

    if query:
        try:
            schools_dir = _Path("data/majors_catalog/schools/2026")
            school_files = list(schools_dir.glob("*.json"))
            matched = []
            for f in school_files:
                data = _json.loads(f.read_text())
                if query.lower() in data.get(
                    "school_name", ""
                ).lower() or query in data.get("province", ""):
                    offerings = data.get("offerings", [])
                    offering_html = "".join(
                        f"<li>{escape(o.get('major_name', ''))} ({escape(o.get('major_code', ''))})</li>"
                        for o in offerings
                    )
                    matched.append(
                        f"<section class='panel'><h2>{escape(data.get('school_name', ''))}</h2>"
                        f"<p class='meta'>院校代码：{escape(data.get('school_code', ''))} · 省份：{escape(data.get('province', ''))} · 招生年份：{escape(str(data.get('admission_year', '')))}</p>"
                        f"<h3>开设专业（{len(offerings)} 个）</h3>"
                        f"<ul style='line-height:1.8;'>{offering_html}</ul></section>"
                    )
            if matched:
                result_html = "".join(matched)
            else:
                result_html = f"<section class='state-empty' role='status'><h2 class='state-empty__title'>未找到匹配&quot;{escape(query)}&quot;的院校</h2><p class='state-empty__hint'>当前院校目录仅含 MVP 子集，完整目录待后续扩充。</p></section>"
        except Exception as e:
            result_html = f"<section class='state-error' role='alert'><h2 class='state-error__title'>查询失败</h2><p class='state-error__hint'>{escape(str(e))}</p></section>"

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>院校库查询</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:980px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}.meta{{color:#5b6b88;line-height:1.8}}</style></head><body>{nav_html}{_render_global_nav()}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/data-query">返回数据查询</a></div><h1>院校库查询</h1><p class="meta">搜索院校，查看院校代码、招生专业和所属省份。</p><form method="get" action="/schools-query" style="margin-top:12px;"><input name="q" value="{escape(query)}" placeholder="例如：北京大学、湖南" style="padding:10px;border-radius:10px;border:1px solid #d7e3f1;font-size:14px;min-width:240px;" /><button class="btn" type="submit" style="margin-left:8px;">搜索</button></form></section>{result_html}</main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


@router.get("/compare-reports", include_in_schema=False)
def compare_reports_page(
    request: Request,
    token: str | None = None,
    tokens: str | None = None,
    phone: str | None = None,  # 已废弃：C 方案下不再支持手机号直查
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    """报告对比闭环：支持用户输入多个 portal token 进行真实对比。"""
    from data.customer_portal.token import verify_portal_token, PortalTokenError

    nav = _render_global_nav()

    # 解析 token 列表（query param tokens=token1,token2,...）
    token_list = []
    if tokens:
        token_list = [t.strip() for t in tokens.split(",") if t.strip()]
    elif token:
        token_list = [token]

    # 无 token：显示输入表单
    if not token_list:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>报告对比</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{nav}<main class="wrap" style="max-width:760px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>报告对比</h1><section class="state-empty" role="status"><h2 class="state-empty__title">请输入 2 份以上报告链接中的 token</h2><p class="state-empty__hint">为保护你的报告隐私，我们不再支持凭手机号查询报告。请把多个订单链接中的 token 复制到这里（逗号分隔），系统会并排对比这些报告的关键信息。</p></section><form method="get" action="/compare-reports" style="margin-top:16px;"><textarea name="tokens" placeholder="token1,token2,token3" style="width:100%;min-height:120px;padding:12px;border-radius:12px;border:1px solid #d7e3f1;font-size:14px;"></textarea><div style="margin-top:12px;"><button class="btn" type="submit">开始对比</button></div></form></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body)

    # 验证每个 token 并收集数据
    compare_rows = []
    invalid_tokens = []
    from data.orders.dao import OrdersDAO, OrderNotFound

    for tk in token_list:
        try:
            payload = verify_portal_token(tk, settings.portal_token_secret)
            order_id = str(payload["order_id"])
            with OrdersDAO.connect(settings.orders_db_path) as dao:
                order = dao.get(order_id)
            context = _build_portal_context(order, settings)
            intake = context.get("intake_summary") or {}
            latest_review = _load_latest_review_result(order.id, settings)
            compare_rows.append(
                {
                    "token": tk,
                    "order_id": order.id,
                    "service_version": order.service_version,
                    "status": order.status,
                    "score": intake.get("candidate_score")
                    or order.candidate_score
                    or "-",
                    "rank": intake.get("candidate_rank") or order.candidate_rank or "-",
                    "subjects": ", ".join(
                        intake.get("candidate_subjects")
                        or order.candidate_subjects
                        or []
                    )
                    or "-",
                    "target_cities": ", ".join(intake.get("target_cities") or [])
                    or "-",
                    "target_majors": ", ".join(intake.get("target_majors") or [])
                    or "-",
                    "latest_review": latest_review.review_result_id
                    if latest_review
                    else "-",
                    "has_pdf": "是" if context.get("report_pdf_ready") else "否",
                    "report_url": f"/portal/{tk}/report",
                    "status_url": f"/portal/{tk}/status",
                }
            )
        except (PortalTokenError, OrderNotFound):
            invalid_tokens.append(tk)

    # 对比结果
    if len(compare_rows) < 2:
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>报告对比</title><link rel="stylesheet" href="/static/portal-ui.css" /></head><body>{nav}<main class="wrap" style="max-width:760px;margin:0 auto;padding:32px 20px;display:grid;gap:16px;" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>报告对比</h1><section class="state-empty" role="status"><h2 class="state-empty__title">有效报告不足 2 份，无法对比</h2><p class="state-empty__hint">请提供至少 2 个有效的 portal token。无效 token：{escape(", ".join(invalid_tokens) or "无")}</p></section></section></main>{_render_global_toast_script()}</body></html>"""
        return HTMLResponse(body)

    # 构建对比表（以列为报告）
    headers = [f"报告 {i + 1}" for i in range(len(compare_rows))]
    fields = [
        ("订单号", "order_id"),
        ("套餐", "service_version"),
        ("状态", "status"),
        ("分数", "score"),
        ("位次", "rank"),
        ("选科", "subjects"),
        ("目标城市", "target_cities"),
        ("目标专业", "target_majors"),
        ("最近复核版本", "latest_review"),
        ("是否有 PDF", "has_pdf"),
    ]
    rows_html = []
    for label, key in fields:
        cells = "".join(
            f"<td style='padding:10px;border-bottom:1px solid #eef2f7;'>{escape(str(row[key]))}</td>"
            for row in compare_rows
        )
        rows_html.append(
            f"<tr><th style='padding:10px;text-align:left;background:#f8fbff;border-bottom:1px solid #d7e3f1;'>{label}</th>{cells}</tr>"
        )

    quick_links = "".join(
        f"<li><a href='{escape(str(row['report_url']))}'>查看 {escape(str(row['order_id']))} 报告</a> · <a href='{escape(str(row['status_url']))}'>查看状态</a></li>"
        for row in compare_rows
    )

    body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>报告对比</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:1100px;margin:0 auto;display:grid;gap:18px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #eef2f7;vertical-align:top}}th{{font-weight:600}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff;border:none;cursor:pointer}}.meta{{color:#5b6b88;line-height:1.8}}</style></head><body>{nav}<main class="wrap" role="main"><section class="panel"><div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;background:#edf3ff;color:#194fb6;" href="/">返回首页</a></div><h1>报告对比</h1><p class="meta">已对比 {len(compare_rows)} 份有效报告。无效 token：{escape(", ".join(invalid_tokens) or "无")}</p><table><thead><tr><th style='padding:10px;background:#f8fbff;border-bottom:2px solid #d7e3f1;'>字段</th>{"".join(f"<th style='padding:10px;background:#f8fbff;border-bottom:2px solid #d7e3f1;'>{escape(h)}</th>" for h in headers)}</tr></thead><tbody>{"".join(rows_html)}</tbody></table></section><section class='panel'><h2>快速跳转</h2><ul style='line-height:1.8;'>{quick_links}</ul></section></main>{_render_global_toast_script()}</body></html>"""
    return HTMLResponse(body)


def _render_landing_page(request: Request, settings: Settings) -> str:
    query = dict(request.query_params)
    escape(str(query.get("consult") or ""))
    consult_province = escape(str(query.get("province") or ""))
    consult_score = escape(str(query.get("score") or ""))
    consult_goal = escape(str(query.get("goal") or ""))
    consult_subjects = escape(str(query.get("subjects") or query.get("subject") or ""))
    portal_token = str(query.get("token") or "").strip()
    latest_review_href = (
        f"/review/start?source=home&amp;token={escape(portal_token)}"
        if portal_token
        else ""
    )
    latest_review_version_html = ""
    latest_contract: ReviewResultContract | None = None
    workspace_context: dict[str, Any] | None = None
    if portal_token:
        try:
            order = _resolve_order_from_token(portal_token, settings)
            latest_contract = _load_latest_review_result(order.id, settings)
            workspace_context = _build_portal_context(order, settings)
            if latest_contract is not None:
                latest_review_version_html = f'<p class="hero-note" style="margin-top:10px;">最新版本：{escape(latest_contract.review_result_id)}</p>'
        except HTTPException:
            latest_contract = None
            workspace_context = None
            latest_review_version_html = ""
    latest_review_html = (
        f'<div class="consult-card" style="margin-top:14px;"><h2>最近一次复核结果</h2><p class="hero-note" style="margin-top:0;">如果你刚完成过复核，可以从这里继续回到复核入口，决定是去冲稳保、补 Step 1，还是进入完整规划。</p>{latest_review_version_html}<div class="consult-actions"><a class="btn btn-secondary" href="{latest_review_href}">查看最近一次复核结果</a></div></div>'
        if latest_contract is not None
        else ""
    )

    workspace_primary_label = "先做方案复核"
    workspace_primary_href = "/review/start?source=home"
    if portal_token:
        workspace_primary_label = "继续补充 Step 1"
        workspace_primary_href = f"/portal/{escape(portal_token)}/info"
        if latest_contract is not None:
            workspace_primary_label = "继续查看最近一次复核"
            workspace_primary_href = latest_review_href
        elif workspace_context is not None and workspace_context.get(
            "profile_minimum_complete"
        ):
            workspace_primary_label = "开始方案复核"
            workspace_primary_href = latest_review_href
    workspace_card_html = (
        f'<div class="consult-card" style="margin-top:14px;"><h2>工作台主动作</h2><p class="hero-note" style="margin-top:0;">根据当前资料完整度与最近一次复核结果，给出默认下一步。</p><div class="consult-actions"><a class="btn btn-secondary" href="{workspace_primary_href}">{workspace_primary_label}</a></div></div>'
        if portal_token
        else ""
    )

    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>高考志愿填报智能规划服务</title>
    <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" />
    <style>
      :root {{
        color-scheme: light;
        --bg: #f3f7fb;
        --surface: #ffffff;
        --surface-soft: #eef5ff;
        --border: #d7e3f1;
        --text: #142235;
        --muted: #5b6b88;
        --primary: #1f6feb;
        --primary-dark: #194fb6;
        --accent: #0f766e;
        --accent-soft: #dff7f1;
        --shadow: 0 18px 42px rgba(20, 34, 53, 0.08);
        --radius-xl: 28px;
        --radius-lg: 20px;
        --radius-md: 14px;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background: linear-gradient(180deg,#0e1a2b 0,#13243d 38%,var(--bg) 38%,var(--bg) 100%); color: var(--text); }}
      .global-nav {{ position: sticky; top: 0; z-index: 100; background: rgba(14,26,43,.92); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,.08); padding: 12px 20px; }}
      .global-nav-inner {{ max-width: 1180px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 16px; }}
      .global-nav-brand {{ font-size: 18px; font-weight: 700; color: #fff; text-decoration: none; }}
      .global-nav-links {{ display: flex; gap: 20px; align-items: center; }}
      .global-nav-link {{ color: #b8c8e4; text-decoration: none; font-size: 14px; font-weight: 500; transition: color .18s; }}
      .global-nav-link:hover {{ color: #fff; }}
      @media (max-width: 768px) {{ .global-nav {{ padding: 10px 14px; }} .global-nav-brand {{ font-size: 16px; }} .global-nav-links {{ gap: 12px; }} .global-nav-link {{ font-size: 13px; }} }}
      .wrap {{ max-width: 1180px; margin: 0 auto; padding: 40px 20px 72px; }}
      .hero {{ display: grid; grid-template-columns: minmax(0, 1.22fr) minmax(340px, .78fr); gap: 32px; align-items: stretch; }}
      .hero-copy {{ color: #ecf4ff; padding: 40px 8px 18px 0; }}
      .eyebrow {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(223,247,241,.12); border: 1px solid rgba(223,247,241,.24); color: #c9fff3; font-size: 13px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
      h1 {{ margin: 18px 0 14px; max-width: 760px; font-size: clamp(36px, 6vw, 56px); line-height: 1.04; letter-spacing: -0.04em; }}
      .sub {{ margin: 0; max-width: 700px; color: #d4ddea; line-height: 1.82; font-size: 17px; }}
      .hero-actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; align-items: center; }}
      .consult-card {{ margin-top: 18px; padding: 18px; border-radius: 18px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); }}
      .consult-card h2 {{ margin: 0 0 8px; font-size: 18px; color: #fff; }}
      .consult-grid {{ display:grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap:10px; }}
      .consult-field {{ display:flex; flex-direction:column; gap:6px; }}
      .consult-field label {{ color:#475569; font-size:13px; font-weight:600; }}
      .consult-field input, .consult-field textarea, .consult-field select {{ width:100%; padding:11px 12px; border-radius:12px; border:1px solid rgba(255,255,255,.18); background: #ffffff; color:#142235; font-size:14px; }} .consult-field select {{ -webkit-appearance:none; -moz-appearance:none; appearance:none; background-color:#fff !important; min-height:44px; line-height:1.5; background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="%23142235" d="M6 8L2 4h8z"/></svg>'); background-repeat:no-repeat; background-position:right 12px center; padding-right:32px; }}
      .consult-field textarea {{ min-height:74px; resize:vertical; }} .consult-field select option {{ background:#fff; color:#142235; }}
      .consult-actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }}
      .consult-privacy {{ margin: 10px 0 0; padding: 10px 12px; border-radius: 12px; background: #f0f7ff; border: 1px solid #c7d7ef; color: #0f172a; font-size: 13px; line-height: 1.65; }}
      .consult-privacy strong {{ color: #1e40af; font-weight: 700; }}
      .consult-privacy-tail {{ margin: 10px 0 0; color: #475569; font-size: 13px; line-height: 1.6; }}
      .btn {{ display: inline-flex; align-items: center; justify-content: center; min-height: 46px; padding: 0 18px; border-radius: 14px; text-decoration: none; font-weight: 700; transition: .18s ease; }}
      .btn-primary {{ min-height: 54px; padding: 0 28px; font-size: 17px; background: linear-gradient(135deg,#2d7cff,#0f4fd6); color: #fff; box-shadow: 0 22px 40px rgba(31,111,235,.42), inset 0 1px 0 rgba(255,255,255,.18); letter-spacing: .01em; }}
      .btn-primary:hover {{ background: linear-gradient(135deg,#276fe7,#0d45bf); transform: translateY(-1px); }}
      .btn-secondary {{ background: rgba(255,255,255,.12); color: #e2e8f0; border: 1px solid rgba(255,255,255,.25); min-height: 44px; padding: 0 14px; font-size: 14px; }}
      .btn-secondary:hover {{ background: rgba(255,255,255,.14); }}
      .btn-text {{ color:#cfe0ff; padding: 0 6px; min-height: 44px; font-size: 14px; text-decoration: underline; text-underline-offset: 4px; }}
      .hero-note {{ margin-top: 12px; color:#e8edf7; font-size:13px; line-height:1.6; }}
      .hero-risk-band {{ display:grid; gap:6px; margin-bottom:16px; padding:12px 14px; border-radius:14px; background: rgba(255,255,255,.7); border:1px solid #f3d49f; }}
      .hero-risk-band strong {{ font-size:14px; color:#4a3700; }}
      .hero-risk-band span {{ color:#5c3d00; font-size:13px; line-height:1.55; }}
      .hero-trust {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:18px; }}
      .hero-trust-item {{ padding:12px 14px; border-radius:14px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); color:#d9e7ff; font-size:13px; line-height:1.5; }}
      .hero-trust-item strong {{ display:block; color:#fff; margin-bottom:4px; font-size:14px; }}
      .hero-points {{ display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12px; margin-top: 24px; }}
      .point {{ padding: 14px; border-radius: 16px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); }}
      .point.lead {{ background: rgba(31,111,235,.18); border-color: rgba(125,180,255,.42); }}
      .point strong {{ display: block; color: #fff; margin-bottom: 6px; font-size: 15px; }}
      .point span {{ color: #b8c8e4; font-size: 13px; line-height: 1.6; }}
      .hero-divider {{ margin: 28px 0 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.18), transparent); }}
      .hero-panel {{ background: rgba(255,255,255,.98); border: 1px solid rgba(215,227,241,.88); border-radius: var(--radius-xl); box-shadow: var(--shadow); padding: 24px; align-self: end; }}
      .hero-panel h2 {{ margin: 0 0 10px; font-size: 22px; }}
      .hero-panel p {{ margin: 0 0 16px; color: var(--muted); line-height: 1.7; }}
      .metric-list {{ display: grid; gap: 12px; }}
      .metric {{ padding: 14px 16px; border-radius: 16px; background: var(--surface-soft); border: 1px solid var(--border); }}
      .metric strong {{ display: block; font-size: 15px; margin-bottom: 6px; }}
      .metric span {{ color: var(--muted); font-size: 13px; line-height: 1.6; }}
      .section {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-xl); box-shadow: var(--shadow); padding: 30px; margin-top: 26px; }}
      .section h2 {{ margin: 0 0 10px; font-size: 28px; letter-spacing: -0.02em; }}
      .section-intro {{ margin: 0 0 22px; color: var(--muted); line-height: 1.75; }}
      .grid-3 {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
      .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 22px; }}
      .card .tag {{ display: inline-flex; margin-bottom: 12px; padding: 6px 10px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-size: 12px; font-weight: 700; }}
      .card h3 {{ margin: 0 0 8px; font-size: 20px; }}
      .card p, .card li {{ color: var(--muted); line-height: 1.7; }}
      .flow {{ position:relative; display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:18px; margin-top:6px; }}
      .flow::before {{ content:''; position:absolute; left:6%; right:6%; top:42px; height:2px; background:linear-gradient(90deg,#c7d7ef,#dfe9f8); z-index:0; }}
      .flow-step {{ position:relative; z-index:1; padding: 22px 18px 18px; border-radius: 20px; background: linear-gradient(180deg,#f9fbff,#eef5ff); border: 1px solid var(--border); }}
      .flow-step strong {{ display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; margin-bottom: 12px; border-radius:999px; background:#1f6feb; color:#fff; font-size:13px; letter-spacing: .02em; text-transform: none; }}
      .flow-step h3 {{ margin: 0 0 8px; font-size: 18px; }}
      .flow-step p {{ margin: 0; color: var(--muted); line-height: 1.7; }}
      .trust {{ display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 16px; }}
      .trust-item {{ padding: 18px 20px; border-radius: 18px; background:#f8fbff; border:1px solid var(--border); }}
      .trust-item strong {{ display:block; margin-bottom:8px; }}
      .cta-band {{ display:flex; justify-content:space-between; gap:18px; align-items:center; flex-wrap:wrap; background: linear-gradient(135deg,#16355e,#1f6feb); color:#fff; }}
      .cta-band p {{ margin: 0; color: rgba(255,255,255,.82); }}
      .cta-band .btn-secondary {{ background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.22); }}
      @media (max-width: 960px) {{
        .hero, .grid-3, .flow, .trust {{ grid-template-columns: 1fr; }}
        .hero-points {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <nav class="global-nav" aria-label="全局导航" role="navigation">
      <div class="global-nav-inner">
        <a class="global-nav-brand" href="/">高考志愿填报</a>
        <div class="global-nav-links">
          <a class="global-nav-link" href="/">首页</a>
          <a class="global-nav-link" href="/pricing">套餐</a>
          <a class="global-nav-link" href="mailto:lon22@qq.com">客服</a>
        </div>
      </div>
    </nav>
    <main class="wrap">
      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow">新高考志愿填报 · 志愿决策支持</div>
          <h1>高考志愿填报智能规划服务</h1>
          <p class="sub">先免费复核一次你的现有方案，再决定要不要继续付费。</p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="/review/start?source=home">先做方案复核</a>
            <a class="btn btn-primary" href="/pricing">查看套餐</a>
          </div>
          <p class="hero-note">提交省份、分数、目标后，我们先判断你的方案是否需要复核。复核现有方案本身免费；新方案生成与深度辅导在支付后启动。</p>
          {workspace_card_html}{latest_review_html}
        </div>
        <aside class="hero-panel">
          <div class="hero-risk-band"><strong>最常见的不是“不会选”，而是先选错方向</strong><span>我们优先帮你筛出踩线、扎堆、梯度失衡这三类最容易带来后悔成本的风险。</span></div>
          <h2>先看你的方案值不值得继续</h2>
          <p>如果你已经拿到老师、机构或其他平台给出的方案，后续可以直接上传文档继续核查。</p>
        </aside>
      </section>

      <section class="section" id="consult-box">
        <h2>先做一次免费复核</h2>
        <p class="section-intro">先提交最小必要信息，我们会判断你当前方案值不值得继续；如果你已经拿到老师、机构或其他平台给出的方案，后续资料页也可以上传文档继续复核。</p>
        <div class="consult-card" style="margin-top:0; background:#f8fbff; border:1px solid var(--border); padding:24px;">
          <p class="consult-privacy" aria-label="隐私说明">🔒 这些输入只用于判断要不要复核你的方案，<strong>不会留底、不会用于生成方案、不会发邮件推销</strong>。如果你决定不进入付费方案，提交的资料不会保存到我们的数据库。</p>
          <form action="/review/start" method="get" aria-label="免费复核表单">
            <input type="hidden" name="source" value="home" />
            {f'<input type="hidden" name="token" value="{escape(portal_token)}" />' if portal_token else ""}
            <div class="consult-grid">
              <div class="consult-field"><label for="consult-province">考试省份</label><select id="consult-province" name="province">{_province_options_html(consult_province)}</select></div>
              <div class="consult-field"><label for="consult-score">分数 / 位次</label><input id="consult-score" name="score" value="{consult_score}" placeholder="例如：578 / 12034" /></div>
            </div>
            <div class="consult-grid" style="margin-top:10px;">
              <div class="consult-field"><label for="consult-subjects">选科组合</label><input id="consult-subjects" name="subjects" value="{consult_subjects}" placeholder="例如：物理、化学、生物" /></div>
              <div class="consult-field"><label for="consult-goal">目标学校或方向</label><input id="consult-goal" name="goal" value="{consult_goal}" placeholder="例如：广东工业大学 / 先复核现有方案" /></div>
            </div>
            <p style="margin-top:10px;color:#475569;font-size:13px;line-height:1.6;">后续资料页可以<strong style="color:#1f6feb;">上传已有方案文档</strong>，我们会先做免费复核，再决定是否进入付费完整规划。</p>
            <div class="consult-actions">
              <button class="btn btn-primary" type="submit">获取复核与推荐</button>
              <a class="btn btn-secondary" style="min-height:48px;padding:0 22px;font-size:15px;background:#fff;color:#1f6feb;border:2px solid #1f6feb;" href="/pricing">直接做完整规划</a>
            </div>
          </form>
          <script>
          (function(){{
            var form = document.querySelector('#consult-box form[action="/review/start"]');
            if (!form) return;
            var province = form.querySelector('select[name="province"]');
            var score = form.querySelector('input[name="score"]');
            var subjects = form.querySelector('input[name="subjects"]');
            var goal = form.querySelector('input[name="goal"]');

            function validateField(field, rules) {{
              var errs = [];
              for (var i = 0; i < rules.length; i++) {{
                var msg = rules[i](field);
                if (msg) errs.push(msg);
              }}
              return errs;
            }}

            function showFieldError(field, errs) {{
              if (!field) return;
              var hintId = field.getAttribute('data-error-id') || (field.name + '-error');
              field.setAttribute('data-error-id', hintId);
              var hint = document.getElementById(hintId);
              if (!hint) {{
                hint = document.createElement('div');
                hint.id = hintId;
                hint.className = 'field-error-hint';
                hint.setAttribute('role', 'alert');
                hint.setAttribute('aria-live', 'polite');
                if (field.parentNode) field.parentNode.appendChild(hint);
              }}
              if (errs.length) {{
                hint.textContent = errs.join('；');
                hint.style.display = 'block';
                field.style.borderColor = '#b42318';
                field.setAttribute('aria-invalid', 'true');
              }} else {{
                hint.style.display = 'none';
                field.style.borderColor = '';
                field.removeAttribute('aria-invalid');
              }}
            }}

            function validateProvince() {{
              return validateField(province, [
                function(f) {{ return (!f || !f.value || f.value.indexOf('请选择') === 0) ? '请选择考试省份' : null; }}
              ]);
            }}
            function validateScore() {{
              return validateField(score, [
                function(f) {{
                  if (!f || !f.value.trim()) return null; // 分数可选
                  var parts = f.value.split('/').map(function(s) {{ return s.trim(); }});
                  var sc = parseInt(parts[0]);
                  if (isNaN(sc) || sc < 0 || sc > 800) return '分数应在 0-800 之间';
                  if (parts.length === 2) {{
                    var rank = parseInt(parts[1]);
                    if (isNaN(rank) || rank < 1) return '位次应为正整数';
                  }}
                  return null;
                }}
              ]);
            }}
            function validateSubjects() {{
              return validateField(subjects, [
                function(f) {{
                  if (!f || !f.value.trim()) return null;
                  var count = f.value.split(/[,，、\s]+/).filter(function(s) {{ return s.trim(); }}).length;
                  if (count > 6) return '选科组合最多 6 科';
                  return null;
                }}
              ]);
            }}
            function validateGoal() {{
              return validateField(goal, [
                function(f) {{
                  if (!f || !f.value.trim()) return null;
                  if (f.value.length > 200) return '目标说明不超过 200 字';
                  return null;
                }}
              ]);
            }}

            function validateAll() {{
              var allErrs = [].concat(validateProvince(), validateScore(), validateSubjects(), validateGoal());
              showFieldError(province, validateProvince());
              showFieldError(score, validateScore());
              showFieldError(subjects, validateSubjects());
              showFieldError(goal, validateGoal());
              // 全局提示
              var globalHint = document.getElementById('consult-error-hint');
              if (!globalHint) {{
                globalHint = document.createElement('div');
                globalHint.id = 'consult-error-hint';
                globalHint.className = 'field-error-hint';
                globalHint.setAttribute('role', 'alert');
                form.appendChild(globalHint);
              }}
              if (allErrs.length) {{
                globalHint.innerHTML = allErrs.join('；');
                globalHint.style.display = 'block';
              }} else {{
                globalHint.style.display = 'none';
              }}
              return allErrs.length === 0;
            }}

            form.addEventListener('submit', function(e) {{
              if (!validateAll()) e.preventDefault();
            }});
            // 即时校验：每个字段 blur/change 时即时反馈
            if (province) province.addEventListener('change', function() {{ showFieldError(province, validateProvince()); }});
            if (score) score.addEventListener('blur', function() {{ showFieldError(score, validateScore()); }});
            if (subjects) subjects.addEventListener('blur', function() {{ showFieldError(subjects, validateSubjects()); }});
            if (goal) goal.addEventListener('blur', function() {{ showFieldError(goal, validateGoal()); }});
            // 输入时清除错误（用户开始修正时立即移除红色提示）
            if (score) score.addEventListener('input', function() {{ if (score.getAttribute('aria-invalid')) showFieldError(score, validateScore()); }});
            if (subjects) subjects.addEventListener('input', function() {{ if (subjects.getAttribute('aria-invalid')) showFieldError(subjects, validateSubjects()); }});
            if (goal) goal.addEventListener('input', function() {{ if (goal.getAttribute('aria-invalid')) showFieldError(goal, validateGoal()); }});
          }})();
          </script>
          <style>
          .field-error-hint {{
            margin-top: 4px;
            padding: 6px 10px;
            border-radius: 8px;
            background: #fff5f5;
            border: 1px solid #f5c2c7;
            color: #b42318;
            font-size: 12px;
            line-height: 1.5;
            display: none;
          }}
          </style>
          <div class="upload-hint" style="margin-top:16px; padding:20px; border-radius:14px; background:rgba(31,111,235,.06); border:2px dashed rgba(31,111,235,.35); text-align:center;">
            <div style="font-size:36px; margin-bottom:8px;">📄</div>
            <p style="margin:0 0 4px; color:#1f6feb; font-size:15px; font-weight:600; line-height:1.5;">已有方案文档？拖拽或点击上传</p>
            <p style="margin:0 0 12px; color:#5b6b88; font-size:13px; line-height:1.5;">支持 Word / PDF / 截图格式，最大 10MB。上传后先做免费复核，再决定是否进入付费完整规划。</p>
            <a class="btn btn-secondary" style="font-size:14px;min-height:40px;padding:8px 20px;background:#fff;color:#1f6feb;border:2px solid #1f6feb;" href="/pricing">上传方案文档并进入完整规划 →</a>
          </div>
          <p class="consult-privacy-tail">不会收到营销短信，提交后你也可以随时要求删除已填资料。</p>
        </div>
      </section>

      <section class="section">
        <h2>为什么选择我们</h2>
        <p class="section-intro">高考志愿填报不是只看一个分数，而是要在时间、信息、风险和沟通成本之间做平衡。我们的特点不是只“生成方案”，而是先帮你审计现有方案、识别扎堆和踩线风险，再决定是否进入更完整的规划与交付。</p>
        <div class=\"grid-3\">
          <article class="card">
          <span class="tag">方案审计</span>
          <h3>先判断现有方案值不值得继续</h3>
          <p>如果你已经拿到老师、机构或 AI 给出的方案，我们会先审计是否踩线、是否扎堆、是否存在明显结构风险，再决定下一步。</p>
          </article>
          <article class="card">
            <span class="tag">风险沟通</span>
            <h3>把风险解释清楚</h3>
            <p>不只输出结果，还会说明冲稳保梯度、可能踩线的位置，以及需要重点确认的选择风险。</p>
          </article>
          <article class="card">
            <span class="tag">交付透明</span>
            <h3>过程可追踪</h3>
            <p>从下单、资料填写、通知到报告查看，都能在站内看到当前进度，减少反复追问。</p>
          </article>
        </div>
      </section>

      <section id="service-flow" class="section">
        <h2>服务流程</h2>
        <p class="section-intro">你先拿到判断，再决定是否付费进入完整规划。流程越清楚，越不容易在关键节点反复来回确认。</p>
        <div class="flow">
          <article class="flow-step"><strong>1</strong><h3>先判断入口</h3><p>判断你需要的是方案复核（免费）还是完整方案 / 深度辅导（付费）。</p></article>
          <article class="flow-step"><strong>2</strong><h3>确认下单</h3><p>选完整方案或深度辅导时，先填写考生姓名、手机号等最小信息后再支付。</p></article>
          <article class="flow-step"><strong>3</strong><h3>补充资料</h3><p>支付成功后进入资料向导，分步提交分数、位次、偏好与已有方案附件。</p></article>
          <article class="flow-step"><strong>4</strong><h3>查看交付</h3><p>在站内追踪状态、查看通知，并在交付就绪后在线阅读或下载 PDF。</p></article>
        </div>
      </section>

      <section class="section cta-band">
        <div>
          <h2 style="margin:0 0 8px;font-size:28px;">已有方案？先免费复核；明确要做？看付费套餐</h2>
          <p>如果已经拿到一版方案，可先做一次免费复核；明确要完整方案或深度辅导，可直接进入套餐页查看内容和下单说明。</p>
        </div>
        <div class="hero-actions" style="margin-top:0;">
          <a class="btn btn-primary" href="/pricing">进入套餐页</a>
          <a class="btn btn-secondary" href="/service-terms">查看服务说明</a>
        </div>
      </section>
      {_render_footer_links()}
    </main>
  {_render_global_toast_script()}</body>
</html>
"""


def _render_pricing_page(request: Request) -> str:
    query = dict(request.query_params)
    consult_text = str(query.get("consult") or "").strip()
    province = str(query.get("province") or "").strip()
    score = str(query.get("score") or "").strip()
    goal = str(query.get("goal") or "").strip()
    recommendation_title = "你可以先从 99 元完整志愿方案开始"
    recommendation_body = (
        "如果你没有现成方案，直接进入完整规划最省时间；如果已有方案，再先审计。"
    )
    if consult_text or "审计" in goal or "审核" in goal:
        recommendation_title = "更适合先做 49 元方案审核"
        recommendation_body = "你提到已有方案或需要先判断风险，先做审核更符合当前目标。"
    elif "深度" in goal or "沟通" in goal:
        recommendation_title = "更适合 199 元深度辅导版"
        recommendation_body = "如果你需要多轮解释或目标冲突较大，深度辅导更合适。"
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>服务套餐 - 高考志愿填报智能规划服务</title>
    <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" />
    <style>
      :root {{
        --bg: #f3f7fb;
        --surface: #ffffff;
        --surface-soft: #eef5ff;
        --border: #d7e3f1;
        --text: #142235;
        --muted: #5b6b88;
        --primary: #1f6feb;
        --primary-dark: #194fb6;
        --accent: #0f766e;
        --accent-soft: #dff7f1;
        --warning-soft: #fff7e6;
        --warning-text: #8a5a00;
        --shadow: 0 18px 42px rgba(20,34,53,.08);
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background: var(--bg); color: var(--text); }}
      .wrap {{ max-width: 1180px; margin: 0 auto; padding: 40px 20px 72px; }}
      .hero {{ display:grid; grid-template-columns: minmax(0,1.1fr) 320px; gap: 20px; align-items:start; }}
      .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 26px; box-shadow: var(--shadow); padding: 28px; }}
      h1 {{ margin: 0 0 12px; font-size: clamp(32px, 5vw, 44px); letter-spacing: -0.03em; }}
      .lead {{ margin: 0; color: var(--muted); line-height: 1.8; font-size: 16px; }}
      .summary {{ background: linear-gradient(180deg,#f7fbff,#eef5ff); }}
      .summary h2 {{ margin: 0 0 12px; font-size: 22px; }}
      .summary ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.75; }}
      .pricing-grid {{ display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 18px; margin-top: 24px; }}
      .card {{ position: relative; display:flex; flex-direction:column; gap: 14px; background: var(--surface); border: 1px solid var(--border); border-radius: 24px; padding: 24px; box-shadow: var(--shadow); }}
      .card.recommended {{ border: 2px solid var(--primary); transform: translateY(-8px); background: linear-gradient(180deg,#f8fbff,#eef5ff); box-shadow: 0 24px 52px rgba(31,111,235,.16); }}
      .card.recommended::before {{ content:''; position:absolute; left:0; right:0; top:0; height:6px; border-radius:24px 24px 0 0; background:linear-gradient(90deg,#1f6feb,#38bdf8); }}
      .badge {{ position:absolute; top:14px; left:50%; transform:translateX(-50%); display:inline-flex; padding:7px 12px; border-radius:999px; background: var(--primary); color: #fff; font-size:12px; font-weight:700; box-shadow:0 10px 20px rgba(31,111,235,.22); }}
      .eyebrow {{ font-size: 13px; font-weight: 700; color: var(--primary); letter-spacing: .04em; text-transform: uppercase; }}
      .price {{ font-size: 40px; font-weight: 800; letter-spacing: -0.04em; }}
      .price small {{ font-size: 15px; font-weight: 600; color: var(--muted); margin-left: 4px; }}
      .desc {{ color: var(--muted); line-height: 1.75; min-height: 72px; }}
      .feature-list {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.75; display:grid; gap:6px; }}
      .button {{ display:inline-flex; align-items:center; justify-content:center; min-height:46px; border-radius:14px; background: var(--primary); color:#fff; text-decoration:none; font-weight:700; box-shadow:0 14px 28px rgba(31,111,235,.2); }}
      .button:hover {{ background: var(--primary-dark); }}
      .button.secondary {{ background:transparent; color:var(--primary-dark); border:1px solid #c7d7ef; box-shadow:none; }}
      .button.secondary:hover {{ background:#eef5ff; }}
      .button.recommended-cta {{ background:#0f4fd6; box-shadow:0 18px 34px rgba(15,79,214,.28); }}
      .button.recommended-cta:hover {{ background:#0b43ba; }}
      .trust-band {{ display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; margin-top: 24px; }}
      .trust-item {{ padding: 18px 20px; border-radius: 18px; background: #fff; border:1px solid var(--border); }}
      .trust-item strong {{ display:block; margin-bottom:8px; }}
      .trust-proof {{ display:grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 12px; margin-top: 22px; }}
      .trust-proof-item {{ padding:14px 16px; border-radius:16px; background:linear-gradient(180deg,#f8fbff,#eef5ff); border:1px solid var(--border); }}
      .trust-proof-item strong {{ display:block; margin-bottom:4px; font-size:15px; }}
      .trust-proof-item span {{ color:var(--muted); font-size:13px; line-height:1.6; }}
      .faq {{ margin-top: 24px; display:grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; }}
      .faq-item {{ padding: 20px; border-radius: 20px; background: #fff; border:1px solid var(--border); }}
      .faq-item h3 {{ margin:0 0 8px; font-size:18px; }}
      .faq-item p {{ margin:0; color:var(--muted); line-height:1.7; }}
      .notice {{ margin-top:26px; padding:16px 18px; border-radius:16px; background:var(--warning-soft); color:var(--warning-text); border:1px solid #f4d39b; line-height:1.7; }}
      .consult-summary {{ margin-top:18px; padding:18px 20px; border-radius:18px; background:linear-gradient(180deg,#f8fbff,#eef5ff); border:1px solid var(--border); }}
      .consult-summary h2 {{ margin:0 0 8px; font-size:20px; }}
      .consult-summary p {{ margin:0; color:var(--muted); line-height:1.75; }}
      .consult-reassure {{ margin-top: 10px !important; padding: 10px 12px; border-radius: 12px; background: var(--success-soft); color: var(--accent); border: 1px solid #b9e7dd; font-size: 14px; }}
      .consult-reassure a {{ color: var(--accent); font-weight: 700; }}
      .summary-reassure {{ margin-top: 14px; padding: 10px 12px; border-radius: 12px; background: var(--success-soft); color: var(--accent); border: 1px solid #b9e7dd; font-size: 13px; line-height: 1.6; }}
      .summary-reassure a {{ color: var(--accent); font-weight: 700; }}
      @media (max-width: 980px) {{
        .hero, .pricing-grid, .trust-band, .faq, .trust-proof {{ grid-template-columns: 1fr; }}
        .card.recommended {{ transform: none; }}
      }}
    </style>
  </head>
  <body>
    <nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>
    <main class="wrap">
      <section class="hero">
        <div class="panel">
          <div style="margin-bottom:8px;"><a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;" href="/">返回首页</a></div>
          <h1>服务套餐</h1>
          <p class="lead">先按服务深度选择适合自己的方案：<strong>复核现有方案本身免费</strong>；如果你已经拿到其他方案，先做复核判断风险；如果希望一次拿到完整建议，优先看 99 元完整志愿方案；如果需要更多人工沟通和多轮修订，再选择 199 元深度辅导版。</p>
          <div class="consult-summary">
            <h2>{escape(recommendation_title)}</h2>
            <p>{escape(recommendation_body)}{" 当前输入：" if (province or score or goal) else ""}{escape(" ".join(filter(None, [province, score, goal])))}</p>
            <p class="consult-reassure">💡 如果你还没决定，<a href="/#consult-box">先做一次免费复核</a>，再决定要不要进入付费方案。</p>
          </div>
          <div class="trust-proof">
            <article class="trust-proof-item"><strong>复核免费 / 方案付费</strong><span>免费帮你审现有方案的风险；新方案生成和深度辅导在支付后启动。</span></article>
            <article class="trust-proof-item"><strong>主推档更清晰</strong><span>99 元方案覆盖大多数用户最关心的完整线上交付路径。</span></article>
            <article class="trust-proof-item"><strong>进度站内可查</strong><span>资料、通知与报告状态都能在站内持续追踪。</span></article>
            <article class="trust-proof-item"><strong>隐私与删除入口可见</strong><span>隐私政策、服务说明和删除申请入口始终保留。</span></article>
          </div>
        </div>
        <aside class="panel summary">
          <h2>下单前你会看到什么</h2>
          <ul>
            <li>套餐说明与适用场景</li>
            <li>下单后需要补充的资料范围</li>
            <li>交付形式：站内查看 + PDF 下载</li>
            <li>隐私政策、服务说明与删除申请入口</li>
          </ul>
          <p class="summary-reassure">🔒 还没下单前，<a href="/#consult-box">提交的基本情况</a>仅用于判断是否需要复核，不会留底。</p>
        </aside>
      </section>

      <section class="pricing-grid">
        <article class="card" data-package="audit">
          <div class="eyebrow">复核 / 风险</div>
          <h2>49元 AI方案审核</h2>
          <div class="price">¥49<small>/ 份</small></div>
          <p class="desc">适合已经拿到其他 AI 志愿方案，想先判断方案是否踩线、是否扎堆、是否存在明显风险的家庭。审核只针对你提供的现有方案，不会重新生成志愿表。</p>
          <ul class="feature-list">
            <li>针对你提供的现有方案做风险复核</li>
            <li>聚焦风险点、冲稳保结构与明显异常</li>
            <li>给出是否值得继续深做的判断</li>
            <li>不重新生成志愿表（生成需选 99 元）</li>
          </ul>
          <a class="button secondary" href="/checkout/audit">选择付费审核</a>
        </article>

        <article class="card recommended" data-package="standard">
          <span class="badge">推荐方案</span>
          <div class="eyebrow">生成 / 完整</div>
          <h2>99元 完整志愿方案</h2>
          <div class="price">¥99<small>/ 份</small></div>
          <p class="desc">适合大多数希望一次拿到完整志愿建议的家庭：先完成线上下单，再在资料向导里补充分数、位次、偏好与已有方案信息。方案生成与详细报告在支付后启动。</p>
          <ul class="feature-list">
            <li>适合首次系统化做志愿规划的用户</li>
            <li>支付后启动方案生成与报告交付</li>
            <li>站内追踪资料、通知与交付状态</li>
            <li>支持在线查看报告与 PDF 下载</li>
          </ul>
          <a class="button recommended-cta" href="/checkout/standard">支付并启动方案生成</a>
        </article>

        <article class="card" data-package="premium">
          <div class="eyebrow">生成 / 深度</div>
          <h2>199元 深度辅导版</h2>
          <div class="price">¥199<small>/ 份</small></div>
          <p class="desc">适合志愿范围复杂、目标城市/专业冲突较大，或需要更多人工沟通、反复修订和深度解释的家庭。在 99 元完整方案基础上提供多轮修订和深度解释。</p>
          <ul class="feature-list">
            <li>适合目标复杂或分歧较大的家庭</li>
            <li>包含 99 元完整方案的所有交付</li>
            <li>留出多轮沟通与补充说明空间</li>
            <li>更强调过程解释与决策支持</li>
          </ul>
          <a class="button secondary" href="/checkout/premium">选择深度辅导</a>
        </article>
      </section>

      <section class="trust-band">
        <article class="trust-item"><strong>站内可追踪</strong><span>下单后可以查看资料提交、通知记录和交付状态，不需要反复追问进度。</span></article>
        <article class="trust-item"><strong>资料入口清晰</strong><span>支付前只收必要下单信息，详细资料在支付后通过资料向导分步补充。</span></article>
        <article class="trust-item"><strong>复核免费 / 方案付费</strong><span>还没决定？回到首页 <a href="/#consult-box">先做一次免费复核</a>，再决定要不要进入付费方案。</span></article>
      </section>

      <section class="section" style="text-align:center;">
        <h2 style="margin:0 0 8px;font-size:24px;">家长和学生的选择</h2>
        <div style="display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin-top:18px;">
          <div style="flex:1;min-width:200px;max-width:280px;padding:20px;border-radius:18px;background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow);">
            <div style="font-size:28px;font-weight:800;color:var(--primary);letter-spacing:-.03em;">31 省</div>
            <div style="color:var(--muted);font-size:13px;margin-top:4px;">覆盖省级录取数据</div>
          </div>
          <div style="flex:1;min-width:200px;max-width:280px;padding:20px;border-radius:18px;background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow);">
            <div style="font-size:28px;font-weight:800;color:var(--primary);letter-spacing:-.03em;">3 个版本</div>
            <div style="color:var(--muted);font-size:13px;margin-top:4px;">从免费复核到深度辅导</div>
          </div>
          <div style="flex:1;min-width:200px;max-width:280px;padding:20px;border-radius:18px;background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow);">
            <div style="font-size:28px;font-weight:800;color:var(--primary);letter-spacing:-.03em;">站内全流程</div>
            <div style="color:var(--muted);font-size:13px;margin-top:4px;">下单→支付→资料→交付→追踪</div>
          </div>
        </div>
        <p style="margin:18px 0 0;color:var(--muted);font-size:14px;line-height:1.7;">已有方案？先 <a href="/#consult-box" style="color:var(--primary);font-weight:600;">免费复核</a>，再决定是否进入付费方案。</p>
      </section>

      <section class="faq">
        <article class="faq-item"><h3>复核是免费的吗？包含什么？</h3><p>提交基本情况后我们免费帮你判断你的现有方案是否需要复核，并说明后续可走的步骤。复核本身免费；如需正式 AI 方案审核报告（49 元）或重新生成完整方案（99 元起）才需要支付。</p></article>
        <article class="faq-item"><h3>为什么推荐 99 元完整志愿方案？</h3><p>它覆盖大多数用户最关心的完整资料收集、站内进度追踪与报告交付，是当前最适合线上自助下单的标准路径。99 元是 <em>生成</em> 一份完整方案的价格，不是 <em>查看</em> 价格。</p></article>
        <article class="faq-item"><h3>支付后还要补哪些信息？</h3><p>主要是分数、位次、选科、目标城市/专业、已有方案说明与附件。支付前不让用户一次填太长的表单。</p></article>
        <article class="faq-item"><h3>我已经有一版志愿方案怎么办？</h3><p>先 <a href="/#consult-box">免费复核</a> 看是否值得继续；如需正式审核报告再选 49 元版本；如已决定要重做或生成完整方案，再进入 99 元完整方案。</p></article>
      </section>

      <div class="notice">还没决定？<a href="/#consult-box">先做一次免费复核</a>，再决定要不要进入付费方案。如果你已经拿到一版方案，49 元审核版会给出明确风险判断；如果已经决定要做完整方案，优先选择 99 元完整志愿方案。</div>
      {_render_footer_links()}
    </main>
  {_render_global_toast_script()}</body>
</html>
"""


def _render_checkout_page(service_version: str) -> str:
    amount = _SERVICE_PRICES[service_version]
    service_label = {
        "audit": "49元 AI方案审核",
        "basic": "49元 基础版",
        "standard": "99元 完整志愿方案",
        "premium": "199元 深度辅导版",
    }[service_version]
    service_desc = {
        "audit": "适合已经拿到其他方案、希望先快速校验风险的家庭。",
        "basic": "适合需求较轻、希望先收敛选校范围的家庭。",
        "standard": "适合大多数希望一次拿到完整建议与站内交付追踪的家庭。",
        "premium": "适合需要更多沟通、补充说明与深度修订支持的家庭。",
    }[service_version]
    province_options = [
        "",
        "北京",
        "上海",
        "天津",
        "重庆",
        "河北",
        "河南",
        "山东",
        "山西",
        "陕西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "湖北",
        "湖南",
        "广东",
        "广西",
        "海南",
        "四川",
        "贵州",
        "云南",
        "甘肃",
        "青海",
        "宁夏",
        "新疆",
        "内蒙古",
        "西藏",
    ]
    province_html = "".join(
        f'<option value="{escape(p)}">{escape(p) or "请选择考试省份（可稍后补充）"}</option>'
        for p in province_options
    )
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>下单 - {escape(service_label)}</title>
    <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" />
    <style>
      :root {{
        --bg: #f3f7fb;
        --surface: #ffffff;
        --surface-soft: #f8fbff;
        --border: #d7e3f1;
        --text: #142235;
        --muted: #5b6b88;
        --primary: #1f6feb;
        --primary-dark: #194fb6;
        --success: #0f766e;
        --success-soft: #dff7f1;
        --danger: #b42318;
        --shadow: 0 18px 42px rgba(20,34,53,.08);
      }}
      * {{ box-sizing: border-box; }}
      body {{ font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background: var(--bg); color: var(--text); margin:0; }}
      .wrap {{ max-width: 1160px; margin:0 auto; padding:32px 20px 72px; }}
      .header {{ margin-bottom: 18px; }}
      .eyebrow {{ display:inline-flex; padding:6px 10px; border-radius:999px; background: var(--success-soft); color: var(--success); font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }}
      h1 {{ margin: 14px 0 10px; font-size: clamp(30px, 5vw, 42px); letter-spacing:-0.03em; }}
      .lead {{ margin:0; max-width:760px; color: var(--muted); line-height: 1.8; }}
      .layout {{ display:grid; grid-template-columns: minmax(0,1.1fr) 360px; gap: 20px; align-items:start; }}
      .panel {{ background:#fff; border:1px solid var(--border); border-radius:24px; padding:24px; box-shadow: var(--shadow); }}
      .summary {{ position: sticky; top: 20px; background: linear-gradient(180deg,#f9fbff,#eef5ff); }}
      .summary h2, .form-panel h2 {{ margin: 0 0 10px; font-size: 22px; }}
      .summary p, .summary li {{ color: var(--muted); line-height: 1.7; }}
      .summary-list {{ display:grid; gap:12px; margin:18px 0; }}
      .summary-item {{ padding:14px 16px; border-radius:16px; background:#fff; border:1px solid var(--border); }}
      .summary-item strong {{ display:block; margin-bottom:6px; font-size:15px; }}
      .price-box {{ display:flex; align-items:end; justify-content:space-between; gap:12px; margin-top:18px; padding:16px 18px; border-radius:18px; background:#fff; border:1px solid var(--border); }}
      .price-box .label {{ color: var(--muted); font-size: 13px; }}
      .price-box .amount {{ font-size: 36px; font-weight: 800; letter-spacing: -0.04em; }}
      .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
      .field {{ display:flex; flex-direction:column; gap:6px; margin-bottom:16px; }}
      .field label {{ font-size:14px; color:#334155; font-weight:600; }}
      .required {{ color:#dc2626; margin-left:4px; }}
      input, textarea, select {{ width:100%; padding:12px; border-radius:12px; border:1px solid #cfd7e6; font-size:14px; background:#fff; color:var(--text); }}
      textarea {{ min-height: 112px; resize: vertical; }}
      input:focus, textarea:focus, select:focus {{ outline:none; border-color: var(--primary); box-shadow: 0 0 0 4px rgba(31,111,235,.12); }}
      .hint {{ color: var(--muted); font-size: 12px; line-height: 1.6; }}
      .error {{ color: var(--danger); font-size:12px; min-height:18px; }}
      .helper {{ margin: 0 0 18px; color: var(--muted); line-height: 1.7; }}
      .trust-strip {{ display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12px; margin: 8px 0 20px; }}
      .trust-card {{ padding: 14px 16px; border-radius: 16px; background: var(--surface-soft); border:1px solid var(--border); }}
      .trust-card strong {{ display:block; margin-bottom:6px; font-size:14px; }}
      .actions {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-top: 8px; }}
      button {{ border:none; border-radius:14px; background: var(--primary); color:#fff; font-weight:700; padding:13px 18px; cursor:pointer; min-height:48px; }}
      button:hover {{ background: var(--primary-dark); }}
      button[disabled] {{ opacity:.6; cursor:not-allowed; }}
      #result {{ margin-top:14px; min-height:24px; color:var(--muted); line-height:1.7; }}
      .service-note {{ margin-top: 18px; padding: 16px 18px; border-radius: 16px; background:#fff7e6; border:1px solid #f4d39b; color:#8a5a00; line-height:1.7; }}
      .form-proof {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin: 0 0 18px; }}
      .form-proof-item {{ padding:14px 16px; border-radius:16px; background:linear-gradient(180deg,#f8fbff,#eef5ff); border:1px solid var(--border); }}
      .form-proof-item strong {{ display:block; margin-bottom:4px; font-size:14px; }}
      .form-proof-item span {{ color:var(--muted); font-size:13px; line-height:1.6; }}
      .summary-badges {{ display:grid; gap:10px; margin-bottom:16px; }}
      .summary-badge {{ padding:12px 14px; border-radius:14px; background:#fff; border:1px solid var(--border); color:var(--muted); line-height:1.6; }}
      .summary-badge strong {{ display:block; margin-bottom:4px; color:var(--text); }}
      @media (max-width: 980px) {{
        .layout, .grid, .trust-strip, .form-proof {{ grid-template-columns: 1fr; }}
        .summary {{ position: static; }}
      }}
    </style>
  </head>
  <body>
    <nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav>
    <main class="wrap">
      <header class="header">
        <div style="margin-bottom:12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;" href="/">← 返回首页</a>
          <div class="stepper" style="display:flex;align-items:center;gap:0;margin-left:auto;">
            <div class="step active" style="display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:8px 0 0 8px;background:#1f6feb;color:#fff;font-size:13px;font-weight:600;">
              <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,.25);font-size:11px;">1</span>
              填写信息
            </div>
            <div class="step" style="display:flex;align-items:center;gap:6px;padding:6px 12px;background:#e2e8f0;color:#64748b;font-size:13px;border-left:1px solid #cbd5e1;">
              <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#cbd5e1;color:#94a3b8;font-size:11px;">2</span>
              支付
            </div>
            <div class="step" style="display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:0 8px 8px 0;background:#e2e8f0;color:#64748b;font-size:13px;border-left:1px solid #cbd5e1;">
              <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#cbd5e1;color:#94a3b8;font-size:11px;">3</span>
              补充资料
            </div>
          </div>
        </div>
        <span class="eyebrow">在线下单</span>
        <h1>{escape(service_label)}</h1>
        <p class="lead">{escape(service_desc)} 现在先确认联系人与考生基础信息；支付成功后，再进入资料向导补充分数、位次、偏好和已有方案附件。</p>
      </header>

      <section class="layout">
        <section class=\"panel form-panel\">
          <h2>填写下单信息</h2>
          <p class="helper">当前这一步只收会影响下单与后续联系的必要信息，不要求你一次性填完整个长表单。</p>
          <div class="form-proof">
            <article class="form-proof-item"><strong>先下单再补资料</strong><span>先把关键联系信息确认下来，再进入资料向导补充分数、位次和偏好。</span></article>
            <article class="form-proof-item"><strong>隐私入口始终可见</strong><span>隐私政策、服务说明与删除申请入口在这条链路上持续可访问。</span></article>
          </div>
          <form id=\"checkout-form\">
            <div class="grid">
              <div class="field">
                <label>考生姓名<span class="required">*</span></label>
                <input name=\"candidate_name\" required maxlength=\"32\" placeholder=\"请输入考生姓名\" />
                <div class="error" data-error=\"candidate_name\"></div>
              </div>
              <div class="field">
                <label>手机号<span class="required">*</span></label>
                <input name=\"customer_phone\" required inputmode=\"tel\" maxlength=\"20\" placeholder=\"请输入便于联系的手机号\" />
                <div class="error" data-error=\"customer_phone\"></div>
              </div>
            </div>
            <div class="grid">
              <div class="field">
                <label>称呼</label>
                <input name=\"customer_name\" maxlength=\"32\" placeholder=\"可选，例如：张同学 / 张家长\" />
              </div>
              <div class="field">
                <label>邮箱（接收通知）</label>
                <input name=\"customer_email\" type=\"email\" maxlength=\"120\" placeholder=\"可选，用于接收交付提醒\" />
              </div>
            </div>
            <div class="grid">
              <div class="field">
                <label>考试省份<span class="required">*</span></label>
                <select name=\"candidate_province\">{province_html}</select>
                <div class="hint">如果你暂时还没决定，也可以支付后在资料向导中补充。</div>
              </div>
              <div class="field">
                <label>备注</label>
                <textarea name=\"notes\" maxlength=\"500\" placeholder=\"可选，例如希望重点关注的城市、专业或顾虑\"></textarea>
              </div>
            </div>
            <div class="actions">
              <button type=\"submit\" id=\"submit-btn\">立即支付 ¥{amount / 100:.0f}</button>
              <span class="hint">提交后会进入支付与资料完善流程。</span>
            </div>
          </form>
          <p id=\"result\"></p>
          <div class="service-note">
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
              <div style="flex:1;min-width:200px;">
                <strong style="display:block;margin-bottom:4px;">💳 支付方式</strong>
                <span style="font-size:13px;">支持支付宝在线支付</span>
              </div>
              <div style="flex:1;min-width:200px;">
                <strong style="display:block;margin-bottom:4px;">↩️ 退款政策</strong>
                <span style="font-size:13px;">报告交付前可全额退款；交付后如有不满意，联系客服协商处理。</span>
              </div>
              <div style="flex:1;min-width:200px;">
                <strong style="display:block;margin-bottom:4px;">🔒 支付安全</strong>
                <span style="font-size:13px;">通过官方支付渠道处理，不存储银行卡信息。</span>
              </div>
            </div>
            <p style="margin:12px 0 0;font-size:13px;">支付后可进入资料向导继续补充详细信息；提交资料后，后续状态、通知与交付入口都将在站内持续更新。</p>
          </div>
          {_render_footer_links()}
        </section>

        <aside class=\"panel summary\">
          <h2>订单摘要</h2>
          <p>你当前选择的是 <strong>{escape(service_label)}</strong>。这一步先确认下单人与考生基础信息，支付成功后再继续补完整资料。</p>
          <div class="summary-badges">
            <div class="summary-badge"><strong>当前建议</strong><span>如果你已经有现成方案，49 元审核版适合先判断风险；99 元适合直接进入完整线上规划。</span></div>
            <div class="summary-badge"><strong>交付方式</strong><span>站内资料向导、通知状态、在线报告与 PDF 下载入口。</span></div>
          </div>
          <div class="summary-list">
            <div class="summary-item"><strong>适合谁</strong><span>{escape(service_desc)}</span></div>
            <div class="summary-item"><strong>你会得到什么</strong><span>站内资料向导、通知状态、报告在线查看和 PDF 下载入口。</span></div>
            <div class="summary-item"><strong>下单后下一步</strong><span>支付成功 → 进入资料向导 → 查看状态与交付。</span></div>
          </div>
          <div class="price-box">
            <div>
              <div class="label">当前应付</div>
              <div class="amount">¥{amount / 100:.0f}</div>
            </div>
            <div class="label">完成支付后即可继续补完整资料</div>
          </div>
        </aside>
      </section>
    </main>
    <script>
      function validateCheckout(form) {{
        const errors = {{ candidate_name: '', customer_phone: '' }};
        const name = String(form.get('candidate_name') || '').trim();
        const phone = String(form.get('customer_phone') || '').trim();
        if (!name) errors.candidate_name = '请填写考生姓名';
        if (!phone) errors.customer_phone = '请填写手机号';
        if (phone && !/^1[3-9]\\d{{9}}$/.test(phone)) errors.customer_phone = '手机号格式不正确';
        for (const [key, msg] of Object.entries(errors)) {{
          const node = document.querySelector(`[data-error="${{key}}"]`);
          if (node) node.textContent = msg;
        }}
        return !errors.candidate_name && !errors.customer_phone;
      }}

      function setSubmitState(loading) {{
        const button = document.getElementById('submit-btn');
        button.disabled = loading;
        button.textContent = loading ? '正在创建订单…' : '立即支付 ¥{amount / 100:.0f}';
      }}

      document.getElementById('checkout-form').addEventListener('input', function (event) {{
        const form = new FormData(event.currentTarget);
        validateCheckout(form);
      }});

      document.getElementById('checkout-form').addEventListener('submit', async function (event) {{
        event.preventDefault();
        const form = new FormData(event.target);
        if (!validateCheckout(form)) return;
        const payload = {{
          service_version: '{service_version}',
          amount_cents: {amount},
          customer_name: form.get('customer_name') || null,
          customer_phone: form.get('customer_phone'),
          customer_email: form.get('customer_email') || null,
          candidate_name: form.get('candidate_name'),
          candidate_province: form.get('candidate_province') || null,
          notes: form.get('notes') || null,
        }};
        const resultNode = document.getElementById('result');
        resultNode.textContent = '正在创建订单，请稍候…';
        setSubmitState(true);
        try {{
          const resp = await fetch('/api/public/orders', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload),
          }});
          const body = await resp.json();
          if (!resp.ok) {{
            resultNode.textContent = body.detail || body.message || '当前暂时无法创建订单，请稍后重试或联系客服。';
            return;
          }}
          resultNode.textContent = '订单创建成功，正在进入支付流程…';
          window.location.href = body.checkout_url;
        }} catch (error) {{
          resultNode.textContent = '网络异常，请稍后重试或联系客服获取人工协助。';
        }} finally {{
          setSubmitState(false);
        }}
      }});
    </script>
  {_render_global_toast_script()}</body>
</html>
"""


def _render_payment_success_page(token: str, context: dict[str, Any]) -> str:
    stage = str(context.get("stage") or "")
    next_action = "立即补充资料"
    next_href = f"/portal/{escape(token)}/info"
    if stage in {"processing", "report_ready", "completed"}:
        next_action = "查看订单状态"
        next_href = f"/portal/{escape(token)}/status"
    payment_status = escape(str(context.get("payment_status") or "pending"))
    next_hint = "当前最重要的是补充分数、位次、选科和目标信息，提交后系统会继续推进。"
    if stage in {"processing", "report_ready", "completed"}:
        next_hint = "订单已进入后续处理阶段，可以直接查看进度和交付结果。"
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>支付成功</title>
    <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" />
    <style>
      body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f3f7fb; color:#142235; }}
      .wrap {{ max-width:980px; margin:0 auto; padding:32px 20px 72px; display:grid; gap:16px; }}
      .panel {{ background:#fff; border:1px solid #d7e3f1; border-radius:24px; box-shadow:0 18px 42px rgba(20,34,53,.08); padding:24px; }}
      .eyebrow {{ display:inline-flex; padding:6px 10px; border-radius:999px; background:#dff7f1; color:#0f766e; font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }}
      h1 {{ margin:14px 0 10px; font-size:clamp(30px,5vw,42px); letter-spacing:-0.03em; }}
      .lead {{ margin:0; color:#5b6b88; line-height:1.8; }}
      .hero-actions {{ display:flex; gap:12px; flex-wrap:wrap; margin-top:20px; }}
      .btn {{ display:inline-flex; align-items:center; justify-content:center; min-height:48px; padding:0 18px; border-radius:14px; text-decoration:none; font-weight:700; }}
      .btn-primary {{ background:#1f6feb; color:#fff; }}
      .btn-secondary {{ background:#edf3ff; color:#194fb6; }}
      .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
      .item {{ padding:14px 16px; border-radius:16px; background:#f8fbff; border:1px solid #d7e3f1; }}
      .item strong {{ display:block; margin-bottom:6px; font-size:14px; }}
      .meta {{ color:#5b6b88; line-height:1.7; font-size:14px; }}
      @media (max-width: 860px) {{ .grid {{ grid-template-columns:1fr; }} }}
    </style>
  </head>
  <body>{_render_global_nav()}
    <main class="wrap">
      <section class="panel">
        <span class="eyebrow">支付成功</span>
        <h1>订单已创建，下一步继续补资料</h1>
        <p class="lead">支付状态：{payment_status}。{escape(next_hint)}</p>
        <div class="hero-actions">
          <a class=\"btn btn-primary\" href=\"{next_href}\">{escape(next_action)}</a>
          <a class=\"btn btn-secondary\" href=\"/portal/{escape(token)}/status\">查看订单进度</a>
        </div>
      </section>
      <section class="panel">
        <h2 style=\"margin:0 0 10px;\">你现在要做什么</h2>
        <div class="grid">
          <div class="item"><strong>补充基础信息</strong><span class="meta">先填分数、位次、选科。</span></div>
          <div class="item"><strong>填写偏好目标</strong><span class="meta">补充城市、专业或院校偏好。</span></div>
          <div class="item"><strong>持续查看进度</strong><span class="meta">资料提交后可继续查看状态、通知和报告。</span></div>
        </div>
      </section>
    </main>
  {_render_global_toast_script()}</body>
</html>"""


def _render_mock_payment_page(payment_id: str, amount_cents: int) -> str:
    return _render_simulated_payment_html(
        title="支付确认页",
        provider_slug="mock",
        payment_id=payment_id,
        amount_cents=amount_cents,
        submit_label="确认支付并返回订单页",
    )


def _render_alipay_sim_payment_page(payment_id: str, amount_cents: int) -> str:
    return _render_simulated_payment_html(
        title="支付宝模拟收银台",
        provider_slug="alipay-sim",
        payment_id=payment_id,
        amount_cents=amount_cents,
        submit_label="模拟支付宝支付成功并返回订单页",
    )


def _render_simulated_payment_html(
    *,
    title: str,
    provider_slug: str,
    payment_id: str,
    amount_cents: int,
    submit_label: str,
) -> str:
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>{escape(title)}</title><link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /></head>
  <body style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fb;padding:24px;margin:0;\">
    {_render_global_nav()}
    <main style=\"max-width:640px;margin:24px auto;background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;\">
      <div style="margin-bottom:8px;"><a href="/" style="color:#194fb6;font-size:13px;text-decoration:none;">← 返回首页</a></div>
      <h1>{escape(title)}</h1>
      <p>订单支付单号：{escape(payment_id)}</p>
      <p>支付金额：¥{amount_cents / 100:.2f}</p>
      <form method=\"post\" action=\"/pay/{escape(provider_slug)}/{escape(payment_id)}/complete\">
        <button type=\"submit\" style=\"border:none;border-radius:12px;background:#1f6feb;color:#fff;font-weight:700;padding:12px 18px;cursor:pointer;\">{escape(submit_label)}</button>
      </form>
    </main>
  {_render_global_toast_script()}</body>
</html>
"""


def _is_profile_minimum_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("candidate_province")
        and payload.get("candidate_subjects")
        and payload.get("candidate_score") is not None
        and payload.get("candidate_rank") is not None
    )


def _profile_missing_fields(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not payload.get("candidate_province"):
        missing.append("candidate_province")
    if payload.get("candidate_score") is None:
        missing.append("candidate_score")
    if payload.get("candidate_rank") is None:
        missing.append("candidate_rank")
    if not payload.get("candidate_subjects"):
        missing.append("candidate_subjects")
    return missing


def _province_options_html(selected: str) -> str:
    province_options = [
        "",
        "北京",
        "上海",
        "天津",
        "重庆",
        "河北",
        "河南",
        "山东",
        "山西",
        "陕西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "甘肃",
        "青海",
        "新疆",
    ]

    return "".join(
        f'<option value="{escape(p)}"'
        + (" selected" if p == selected else "")
        + f">{escape(p) or '请选择考试省份（可稍后补充）'}</option>"
        for p in province_options
    )


def _render_simulated_payment_page(
    payment_id: str,
    settings: Settings,
    *,
    provider_slug: str,
) -> HTMLResponse:
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
        provider_name=settings.payment_provider,
    )
    payment = service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    if provider_slug == "mock":
        body = _render_mock_payment_page(payment_id, payment.amount_cents)
    elif provider_slug == "alipay-sim":
        body = _render_alipay_sim_payment_page(payment_id, payment.amount_cents)
    else:
        raise HTTPException(
            status_code=404, detail="unsupported simulated payment page"
        )
    return HTMLResponse(body)


def _complete_simulated_payment(
    payment_id: str,
    settings: Settings,
    *,
    provider_slug: str,
) -> RedirectResponse:
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
        provider_name=settings.payment_provider,
    )
    payment = service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    payload, headers = service.provider.build_webhook_request(
        payment_id=payment.id,
        amount_cents=payment.amount_cents,
        provider_trade_no=f"SIM-{payment.id}",
    )
    if provider_slug == "mock":
        signature = headers["X-Mock-Signature"]
    elif provider_slug == "alipay-sim":
        signature = headers["X-Alipay-Sim-Signature"]
    else:
        raise HTTPException(
            status_code=404, detail="unsupported simulated payment completion"
        )
    service.handle_webhook(payload, signature)
    portal_token = issue_portal_token(payment.order_id, settings.portal_token_secret)
    return RedirectResponse(
        url=f"/portal/{portal_token}/payment-success", status_code=303
    )


def _render_info_page(
    order: Order,
    token: str,
    payload: dict[str, Any],
    stage: str,
    settings: Settings,
) -> str:
    consent_version = str(payload.get("consent_version") or settings.consent_version)
    consent_scope = str(payload.get("consent_scope") or settings.consent_scope_portal)
    privacy_checked = "checked" if payload.get("privacy_accepted") else ""
    service_terms_checked = "checked" if payload.get("service_terms_accepted") else ""
    guardian_checked = "checked" if payload.get("guardian_confirmed") else ""
    attachments = payload.get("attachments") or []
    missing_items: list[str] = []
    if not payload.get("candidate_province"):
        missing_items.append("省份")
    if not payload.get("candidate_score"):
        missing_items.append("分数")
    if not payload.get("candidate_rank"):
        missing_items.append("位次")
    if not payload.get("candidate_subjects"):
        missing_items.append("选科")
    attachment_items = []
    for item in attachments:
        if not isinstance(item, dict):
            continue
        attachment_items.append(
            f"<li>{escape(str(item.get('original_name') or item.get('stored_name') or '未命名附件'))}"
            f"<span>{escape(str(item.get('size_bytes') or '0'))} bytes</span></li>"
        )
    attachments_html = "".join(attachment_items) or "<li class='empty'>暂无附件</li>"
    stage_title, stage_subtitle = _STAGE_META[stage]
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>考生资料填写</title>
    <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" />
    <style>
      :root {{
        --bg: #f3f7fb;
        --surface: #ffffff;
        --surface-soft: #f7fbff;
        --border: #d7e3f1;
        --text: #142235;
        --muted: #5b6b88;
        --primary: #1f6feb;
        --primary-soft: rgba(31,111,235,.12);
        --success: #0f766e;
        --success-soft: #dff7f1;
        --warning: #8a5a00;
        --warning-soft: #fff7e6;
        --shadow: 0 18px 42px rgba(20,34,53,.08);
      }}
      * {{ box-sizing: border-box; }}
      body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);margin:0;color:var(--text); }}
      .wrap {{ max-width: 1160px; margin:0 auto; padding:32px 20px 72px; }}
      .hero {{ display:grid; grid-template-columns:minmax(0,1.12fr) 340px; gap:20px; align-items:start; }}
      .panel {{ background:var(--surface); border:1px solid var(--border); border-radius:24px; box-shadow:var(--shadow); padding:24px; }}
      .eyebrow {{ display:inline-flex; padding:6px 10px; border-radius:999px; background:var(--success-soft); color:var(--success); font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }}
      h1 {{ margin:14px 0 10px; font-size:clamp(30px,5vw,42px); letter-spacing:-0.03em; }}
      .lead {{ margin:0; color:var(--muted); line-height:1.8; }}
      .status-card {{ background:linear-gradient(180deg,#f9fbff,#eef5ff); }}
      .status-card h2, .main-panel h2 {{ margin:0 0 10px; font-size:22px; }}
      .status-card p {{ margin:0 0 12px; color:var(--muted); line-height:1.7; }}
      .status-pill {{ display:inline-flex; padding:8px 12px; border-radius:999px; background:var(--primary); color:#fff; font-weight:700; font-size:13px; }}
      .status-list {{ display:grid; gap:12px; margin-top:16px; }}
      .status-item {{ padding:14px 16px; border-radius:16px; background:#fff; border:1px solid var(--border); }}
      .status-item strong {{ display:block; margin-bottom:6px; font-size:14px; }}
      .compliance-note {{ margin-top:16px; padding:16px 18px; border-radius:16px; background:var(--warning-soft); border:1px solid #f4d39b; color:var(--warning); line-height:1.7; }}
      .wizard-head {{ margin-top:20px; padding:18px 20px; border-radius:18px; background:var(--surface-soft); border:1px solid var(--border); }}
      .wizard-head h2 {{ margin:0 0 8px; font-size:22px; }}
      .wizard-head p {{ margin:0; color:var(--muted); line-height:1.7; }}
      .wizard-steps {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; list-style:none; padding:0; margin:18px 0 0; }}
      .wizard-steps li {{ padding:10px 12px; border-radius:999px; background:#e8eef8; color:#334155; text-align:center; font-size:13px; font-weight:700; }}
      .step-panel {{ margin-top:18px; padding:20px; border-radius:20px; background:#fff; border:1px solid var(--border); }}
      .step-panel h3 {{ margin:0 0 8px; font-size:20px; }}
      .step-panel > p {{ margin:0 0 16px; color:var(--muted); line-height:1.7; }}
      .field-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
      .field {{ display:flex; flex-direction:column; gap:6px; margin-bottom:16px; }}
      .field label {{ font-size:14px; font-weight:600; color:#334155; }}
      input, textarea, select {{ width:100%; padding:12px; border-radius:12px; border:1px solid #cfd7e6; font-size:14px; background:#fff; color:var(--text); }}
      textarea {{ min-height:110px; resize:vertical; }}
      input:focus, textarea:focus, select:focus {{ outline:none; border-color:var(--primary); box-shadow:0 0 0 4px var(--primary-soft); }}
      .helper {{ color:var(--muted); font-size:12px; line-height:1.6; }}
      .upload-box {{ margin-top:16px; padding:16px 18px; border:1px solid var(--border); border-radius:16px; background:var(--surface-soft); }}
      .attachment-list {{ list-style:none; padding:0; margin:12px 0 0; display:grid; gap:8px; }}
      .attachment-list li {{ display:flex; justify-content:space-between; gap:12px; padding:12px 14px; border-radius:14px; background:#fff; border:1px solid var(--border); color:var(--muted); }}
      .attachment-list li.empty {{ justify-content:flex-start; }}
      .check-list {{ display:grid; gap:10px; margin-top:12px; }}
      .check-list label {{ display:flex; gap:10px; align-items:flex-start; color:var(--text); font-weight:500; }}
      .check-list input {{ width:auto; margin-top:2px; }}
      .actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; }}
      button {{ border:none; border-radius:14px; background:var(--primary); color:#fff; font-weight:700; padding:13px 18px; cursor:pointer; min-height:46px; }}
      .wizard-actions {{ position: sticky; bottom: 0; z-index: 5; margin-top: 20px; padding: 12px 0 calc(12px + env(safe-area-inset-bottom, 0px)); background: var(--bg); }}
      .wizard-actions::before {{ content: ""; position: absolute; left: 0; right: 0; top: -16px; height: 16px; background: linear-gradient(180deg, rgba(243,247,251,0), var(--bg)); pointer-events: none; }}
      .wizard-actions .actions {{ background:#fff; border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:12px; margin-top:0; }}
      .wizard-actions button {{ flex:1 1 180px; }}
      button:hover {{ background:#194fb6; }}
      button[disabled] {{ opacity:.55; cursor:not-allowed; }}
      #prev-step, .ghost {{ background:#edf3ff; color:#194fb6; }}
      #result {{ margin-top:16px; min-height:24px; color:var(--muted); line-height:1.7; white-space:pre-wrap; }}
      .summary-box {{ background:#f8fafc; border:1px solid var(--border); border-radius:16px; padding:14px 16px; white-space:pre-wrap; font-size:13px; line-height:1.7; color:var(--muted); }}
      .progress-box {{ margin-top:14px; padding:14px 16px; border-radius:16px; background:#fff7e6; border:1px solid #f4d39b; color:#8a5a00; line-height:1.7; }}
      .footer-link {{ margin-top:18px; }}
      .main-panel {{ position: relative; }}
      /* 移动端关键操作按钮固定在视口底部, 滚动时持续可达 */
      @media (max-width: 980px) {{
        .hero, .field-grid, .wizard-steps {{ grid-template-columns:1fr; }}
        .wizard-actions {{ position: fixed; left: 0; right: 0; bottom: 0; padding: 12px 14px calc(12px + env(safe-area-inset-bottom, 0px)); margin-top: 0; background: rgba(243,247,251,.92); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); box-shadow: 0 -8px 24px rgba(20,34,53,.08); }}
        .wizard-actions .actions {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:10px; }}
        .wizard-actions button {{ width:100%; min-height:52px; }}
        #submit-step {{ grid-column: 1 / -1; }}
        /* 主面板底部留出空间, 防止按钮遮挡最后内容 */
        .main-panel {{ padding-bottom: 168px; }}
      }}
      @media (max-width: 640px) {{
        .wrap {{ padding:20px 14px 88px; }}
        .panel {{ padding:18px; border-radius:20px; }}
        .wizard-actions .actions {{ grid-template-columns:1fr; }}
      }}
    </style>
  </head>
  <body>{_render_global_nav()}
    <main class="wrap">
      <section class="hero">
        <section class=\"panel main-panel\">
          <span class="eyebrow">资料填写向导</span>
          <h1>考生资料填写</h1>
          <p class="helper" style=\"margin:8px 0 0;\">资料填写向导</p>
          <p class="lead">支付完成后，请按向导逐步补充分数、位次、偏好与已有方案信息。我们会把这份资料作为后续方案分析与交付的基础。</p>
          <section class="progress-box"><strong>当前还需要补充：</strong><span>{escape("、".join(missing_items) or "资料已基本完整，可以继续提交")}</span></section>

          <section class="wizard-head">
            <h2>五步资料向导</h2>
            <p>你不需要一次性完成所有内容。可以先保存草稿，再回来继续补充；第 4 步完成偏好与协议确认，第 5 步补已有方案与附件。</p>
            <ol class="wizard-steps">
              <li data-step-badge="1">基础信息</li>
              <li data-step-badge="2">院校偏好</li>
              <li data-step-badge="3">专业偏好</li>
              <li data-step-badge="4">其他偏好与确认</li>
              <li data-step-badge="5">已有方案与附件</li>
            </ol>
          </section>

          <form id="intake-form">
            <section class="step-panel" data-step="1">
              <h3>基础信息</h3>
              <p>先确认最影响志愿方案判断的基本数据：省份、分数、位次、选科。</p>
              <div class="field-grid">
                <div class="field"><label>考试省份</label><select name="candidate_province">{_province_options_html(str(payload.get("candidate_province") or order.candidate_province or ""))}</select><span class="helper">这是 Step 1 的第一项，先选省份再继续。</span></div>
                <div class="field"><label>高考分数</label><input name="candidate_score" value="{escape(str(payload.get("candidate_score") or ""))}" /><span class="helper">如暂未最终确认，也可先保存草稿。</span></div>
                <div class="field"><label>位次</label><input name="candidate_rank" value="{escape(str(payload.get("candidate_rank") or ""))}" /><span class="helper">建议填写与成绩单一致的最新位次。</span></div>
              </div>
              <div class="field"><label>选科（逗号分隔）</label><input name="candidate_subjects" value="{escape(",".join(payload.get("candidate_subjects") or []))}" /><span class="helper">例如：物理,化学,生物</span></div>
            </section>

            <section class="step-panel" data-step="2" style="display:none;">
              <h3>院校偏好</h3>
              <p>用于判断你更偏向哪些地区、哪些学校层次，以及是否已经有明确目标院校。</p>
              <div class="field-grid">
                <div class="field"><label>院校地域偏好（逗号分隔）</label><input name="school_region_preferences" value="{escape(",".join(payload.get("school_region_preferences") or []))}" /></div>
                <div class="field"><label>院校类型偏好（逗号分隔）</label><input name="school_preference_types" value="{escape(",".join(payload.get("school_preference_types") or []))}" /></div>
              </div>
              <div class="field-grid">
                <div class="field"><label>目标院校（逗号分隔）</label><input name="target_schools" value="{escape(",".join(payload.get("target_schools") or []))}" /></div>
                <div class="field"><label>目标城市（逗号分隔）</label><input name="target_cities" value="{escape(",".join(payload.get("target_cities") or []))}" /></div>
              </div>
              <div class="field"><label>院校偏好说明</label><textarea name="university_preferences">{escape(str(payload.get("university_preferences") or ""))}</textarea></div>
            </section>

            <section class="step-panel" data-step="3" style="display:none;">
              <h3>专业偏好</h3>
              <p>用于判断你的专业方向、明确排斥项，以及优先策略更偏学校还是专业。</p>
              <div class="field"><label>兴趣方向</label><input name="candidate_interests" value="{escape(str(payload.get("candidate_interests") or ""))}" /></div>
              <div class="field-grid">
                <div class="field"><label>目标专业（逗号分隔）</label><input name="target_majors" value="{escape(",".join(payload.get("target_majors") or []))}" /></div>
                <div class="field"><label>不接受专业（逗号分隔）</label><input name="disliked_majors" value="{escape(",".join(payload.get("disliked_majors") or []))}" /></div>
              </div>
              <div class="field"><label>优先策略</label><input name="priority_strategy" value="{escape(str(payload.get("priority_strategy") or ""))}" placeholder="例如：major_first" /></div>
            </section>

            <section class="step-panel" data-step="4" style="display:none;">
              <h3>其他偏好与确认</h3>
              <p>用于补充毕业规划、预算、就业区域和家庭背景，不强制提交，也不会阻塞审核入口。</p>
              <div class="field-grid">
                <div class="field"><label>毕业规划</label><input name="graduation_plan" value="{escape(str(payload.get("graduation_plan") or ""))}" /></div>
                <div class="field"><label>学费倾向</label><input name="tuition_preference" value="{escape(str(payload.get("tuition_preference") or ""))}" /></div>
              </div>
              <div class="field"><label>就业地域偏好（逗号分隔）</label><input name="employment_region_preferences" value="{escape(",".join(payload.get("employment_region_preferences") or []))}" /></div>
              <div class="field"><label>家庭背景</label><textarea name="family_background">{escape(str(payload.get("family_background") or ""))}</textarea></div>
              <div class="field"><label>行业资源</label><textarea name="industry_resources">{escape(str(payload.get("industry_resources") or ""))}</textarea></div>
              <div class="field"><label>深层补充说明</label><textarea name="extra_notes">{escape(str(payload.get("extra_notes") or ""))}</textarea></div>
              <div class="field-grid">
                <div class="field"><label>测评类型</label><input name="interest_assessment_type" value="{escape(str(payload.get("interest_assessment_type") or ""))}" placeholder="例如：holland / mbti" /></div>
                <div class="field"><label>测评结果</label><input name="interest_assessment_result" value="{escape(str(payload.get("interest_assessment_result") or ""))}" placeholder="例如：R型+I型" /></div>
              </div>
              <div class="field"><label>测评补充说明</label><textarea name="interest_assessment_notes">{escape(str(payload.get("interest_assessment_notes") or ""))}</textarea></div>
              <div class="compliance-note">测评结果只作为辅助因子，不作为唯一判断依据。</div>
              <div class="field"><label>补充说明</label><textarea name="guardian_notes">{escape(str(payload.get("guardian_notes") or ""))}</textarea></div>
              <input type="hidden" name="consent_version" value="{escape(consent_version)}" />
              <input type="hidden" name="consent_scope" value="{escape(consent_scope)}" />
              <div class="check-list">
                <label><input type="checkbox" name="privacy_accepted" {privacy_checked} /> <span>我已阅读并同意隐私政策草案</span></label>
                <label><input type="checkbox" name="service_terms_accepted" {service_terms_checked} /> <span>我已阅读并同意服务说明与免责声明</span></label>
                <label><input type="checkbox" name="guardian_confirmed" {guardian_checked} /> <span>我确认监护人已知情并同意提交资料</span></label>
              </div>
              <div class="compliance-note">当前资料状态会随提交结果同步更新；未勾选必要同意项时，系统不会进入正式处理阶段。</div>
              <div id="confirm-summary" class="summary-box"></div>
            </section>

            <section class="step-panel" data-step="5" style="display:none;">
              <h3>已有方案与附件</h3>
              <p>如果你已经拿到其他平台、老师或 AI 生成的方案，可以在这里上传并说明担心点。</p>
              <div class="field"><label>已有方案说明</label><textarea name="existing_plan_summary">{escape(str(payload.get("existing_plan_summary") or ""))}</textarea></div>
              <section class="upload-box">
                <h4 style="margin:0 0 10px; font-size:18px;">已上传附件</h4>
                <p class="helper" style="margin:0 0 12px;">支持继续补充方案附件、成绩截图或其他参考资料。</p>
                <div id="attachment-panel">
                  <input type="file" name="files" multiple />
                  <div class="actions" style="margin-top:12px;">
                    <button type="button" onclick="uploadAttachment()">上传方案与资料附件</button>
                  </div>
                </div>
                <ul class="attachment-list">{attachments_html}</ul>
              </section>
            </section>
          </form>
          <div class="wizard-actions">
            <div class="actions">
              <button type="button" id="prev-step" onclick="moveStep(-1)" disabled>上一步</button>
              <button type="button" id="next-step" onclick="moveStep(1)">下一步</button>
              <button type="button" class="ghost" onclick="submitIntake('draft')">保存草稿</button>
              <button type="button" id="submit-step" style="display:none;" onclick="submitIntake('submit')">确认并提交资料</button>
            </div>
          </div>
          <div class="footer-link"><a href="/portal/{escape(token)}/status">返回订单状态页</a></div>
          {_render_footer_links(token)}
          <div id=\"result\"></div>
        </section>

        <aside class=\"panel status-card\">
          <h2>当前资料状态</h2>
          <span class="status-pill">{escape(stage_title)}</span>
          <p style=\"margin-top:12px;\">{escape(stage_subtitle)}</p>
          <div class="status-list">
            <div class="status-item"><strong>订单号</strong><span>{escape(order.id)}</span></div>
            <div class="status-item"><strong>当前服务版本</strong><span>{escape(order.service_version)}</span></div>
            <div class="status-item"><strong>你可以怎么做</strong><span>保存草稿、继续补资料，或在最后一步统一提交进入后续处理。</span></div>
          </div>
          <div class="compliance-note">提交资料即表示：监护人已知情并同意将考生资料用于志愿填报服务；当前版本号：{escape(consent_version)}</div>
        </aside>
      </section>
    </main>
    <script>
      let currentStep = 1;
      const totalSteps = 5;

      function collectPayload(mode) {{
        const form = new FormData(document.getElementById('intake-form'));
        const subjects = String(form.get('candidate_subjects') || '').split(',').map(s => s.trim()).filter(Boolean);
        const targetCities = String(form.get('target_cities') || '').split(',').map(s => s.trim()).filter(Boolean);
        const targetMajors = String(form.get('target_majors') || '').split(',').map(s => s.trim()).filter(Boolean);
        const schoolRegions = String(form.get('school_region_preferences') || '').split(',').map(s => s.trim()).filter(Boolean);
        const schoolTypes = String(form.get('school_preference_types') || '').split(',').map(s => s.trim()).filter(Boolean);
        const targetSchools = String(form.get('target_schools') || '').split(',').map(s => s.trim()).filter(Boolean);
        const dislikedMajors = String(form.get('disliked_majors') || '').split(',').map(s => s.trim()).filter(Boolean);
        const employmentRegions = String(form.get('employment_region_preferences') || '').split(',').map(s => s.trim()).filter(Boolean);
        return {{
          mode,
          candidate_province: form.get('candidate_province') || null,
          candidate_score: form.get('candidate_score') ? Number(form.get('candidate_score')) : null,
          candidate_rank: form.get('candidate_rank') ? Number(form.get('candidate_rank')) : null,
          candidate_subjects: subjects,
          candidate_interests: form.get('candidate_interests') || null,
          target_cities: targetCities,
          target_majors: targetMajors,
          university_preferences: form.get('university_preferences') || null,
          school_region_preferences: schoolRegions,
          school_preference_types: schoolTypes,
          target_schools: targetSchools,
          disliked_majors: dislikedMajors,
          priority_strategy: form.get('priority_strategy') || null,
          graduation_plan: form.get('graduation_plan') || null,
          tuition_preference: form.get('tuition_preference') || null,
          employment_region_preferences: employmentRegions,
          family_background: form.get('family_background') || null,
          industry_resources: form.get('industry_resources') || null,
          extra_notes: form.get('extra_notes') || null,
          interest_assessment_type: form.get('interest_assessment_type') || null,
          interest_assessment_result: form.get('interest_assessment_result') || null,
          interest_assessment_notes: form.get('interest_assessment_notes') || null,
          existing_plan_summary: form.get('existing_plan_summary') || null,
          guardian_notes: form.get('guardian_notes') || null,
          consent_version: form.get('consent_version') || null,
          consent_scope: form.get('consent_scope') || null,
          privacy_accepted: !!document.querySelector('input[name="privacy_accepted"]')?.checked,
          service_terms_accepted: !!document.querySelector('input[name="service_terms_accepted"]')?.checked,
          guardian_confirmed: !!document.querySelector('input[name="guardian_confirmed"]')?.checked,
        }};
      }}

      function renderConfirmSummary() {{
        const payload = collectPayload('draft');
        const list = [
          ['考试省份', payload.candidate_province || '待补充'],
          ['高考分数', payload.candidate_score ?? '待补充'],
          ['位次', payload.candidate_rank ?? '待补充'],
          ['选科', (payload.candidate_subjects || []).join('、') || '待补充'],
          ['兴趣方向', payload.candidate_interests || '待补充'],
          ['目标城市', (payload.target_cities || []).join('、') || '待补充'],
          ['目标专业', (payload.target_majors || []).join('、') || '待补充'],
          ['院校偏好', payload.university_preferences || '待补充'],
          ['已有方案说明', payload.existing_plan_summary || '待补充'],
        ];
        document.getElementById('confirm-summary').replaceChildren(...list.map(([label, value]) => {{
          const row = document.createElement('div');
          row.style.cssText = 'padding:8px 0;border-bottom:1px solid #e5edf7;';
          const strong = document.createElement('strong');
          strong.textContent = `${{label}}：`;
          const span = document.createElement('span');
          span.textContent = String(value);
          row.append(strong, span);
          return row;
        }}));
      }}

      function updateWizard() {{
        document.querySelectorAll('[data-step]').forEach((node) => {{
          node.style.display = Number(node.getAttribute('data-step')) === currentStep ? '' : 'none';
        }});
        document.querySelectorAll('[data-step-badge]').forEach((node) => {{
          const step = Number(node.getAttribute('data-step-badge'));
          if (step === currentStep) {{
            node.style.background = '#1f6feb';
            node.style.color = '#fff';
          }} else {{
            node.style.background = '#e8eef8';
            node.style.color = '#334155';
          }}
        }});
        document.getElementById('prev-step').disabled = currentStep === 1;
        document.getElementById('next-step').style.display = currentStep === totalSteps ? 'none' : '';
        document.getElementById('submit-step').style.display = currentStep === totalSteps ? '' : 'none';
        if (currentStep === totalSteps) renderConfirmSummary();
      }}

      function moveStep(delta) {{
        currentStep = Math.min(totalSteps, Math.max(1, currentStep + delta));
        updateWizard();
      }}

      function validateStep1Fields() {{
        var errs = [];
        var province = document.querySelector('select[name="candidate_province"]');
        var score = document.querySelector('input[name="candidate_score"]');
        var rank = document.querySelector('input[name="candidate_rank"]');
        var subjects = document.querySelector('input[name="candidate_subjects"]');
        // 只在 submit 模式下强制必填；draft 模式放行
        // 但即时校验仍然给格式反馈
        function showFieldError(input, msg) {{
          if (!input) return;
          var hintId = input.name + '-inline-error';
          var hint = document.getElementById(hintId);
          if (!hint) {{
            hint = document.createElement('div');
            hint.id = hintId;
            hint.className = 'field-error-hint';
            hint.setAttribute('role', 'alert');
            input.parentNode.appendChild(hint);
          }}
          if (msg) {{
            hint.textContent = msg;
            hint.style.display = 'block';
            input.style.borderColor = '#b42318';
            input.setAttribute('aria-invalid', 'true');
          }} else {{
            hint.style.display = 'none';
            input.style.borderColor = '';
            input.removeAttribute('aria-invalid');
          }}
        }}
        // 格式校验（即时反馈）
        if (score && score.value.trim()) {{
          var sc = Number(score.value.trim());
          if (isNaN(sc) || sc < 0 || sc > 800) {{
            errs.push('分数格式错误');
            showFieldError(score, '分数应在 0-800 之间');
          }} else {{
            showFieldError(score, '');
          }}
        }}
        if (rank && rank.value.trim()) {{
          var rk = Number(rank.value.trim());
          if (isNaN(rk) || rk < 1 || rk > 5000000) {{
            errs.push('位次格式错误');
            showFieldError(rank, '位次应为 1-5000000 之间的正整数');
          }} else {{
            showFieldError(rank, '');
          }}
        }}
        if (subjects && subjects.value.trim()) {{
          var subjCount = subjects.value.split(/[,，、\\s]+/).filter(function(s){{return s.trim();}}).length;
          if (subjCount > 6) {{
            errs.push('选科超过6科');
            showFieldError(subjects, '选科组合最多 6 科');
          }} else {{
            showFieldError(subjects, '');
          }}
        }}
        return errs.length === 0;
      }}

      // 即时校验绑定
      (function() {{
        var score = document.querySelector('input[name="candidate_score"]');
        var rank = document.querySelector('input[name="candidate_rank"]');
        var subjects = document.querySelector('input[name="candidate_subjects"]');
        if (score) score.addEventListener('blur', validateStep1Fields);
        if (rank) rank.addEventListener('blur', validateStep1Fields);
        if (subjects) subjects.addEventListener('blur', validateStep1Fields);
        if (score) score.addEventListener('input', function() {{ if (score.getAttribute('aria-invalid')) validateStep1Fields(); }});
        if (rank) rank.addEventListener('input', function() {{ if (rank.getAttribute('aria-invalid')) validateStep1Fields(); }});
        if (subjects) subjects.addEventListener('input', function() {{ if (subjects.getAttribute('aria-invalid')) validateStep1Fields(); }});
      }})();

      async function submitIntake(mode) {{
        // 提交前校验（draft 也校验格式，但不强制必填）
        if (!validateStep1Fields()) {{
          document.getElementById('result').textContent = '资料格式有误，请修正红色提示后再提交。';
          return;
        }}
        const payload = collectPayload(mode);
        const resultNode = document.getElementById('result');
        resultNode.textContent = '';
        var loadingEl = window.showLoading ? window.showLoading(document.querySelector('.main-panel'), mode === 'draft' ? '正在保存草稿…' : '正在提交资料…') : null;
        resultNode.textContent = mode === 'draft' ? '正在保存草稿…' : '正在提交资料…';
        const resp = await fetch('/portal/{escape(token)}/info', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
        }});
        const body = await resp.json();
        if (!resp.ok) {{
          if (loadingEl) window.hideLoading(loadingEl);
          resultNode.textContent = body.detail || body.message || '提交失败，请检查资料后重试。';
          if (window.showToast) window.showToast('提交失败', 'error');
          return;
        }}
        if (loadingEl) window.hideLoading(loadingEl);
        resultNode.textContent = mode === 'draft' ? '草稿已保存，可稍后继续补充。' : '资料提交成功，正在进入订单状态页…';
        if (window.showToast) window.showToast(mode === 'draft' ? '草稿已保存' : '提交成功', 'success');
        if (resp.ok && mode === 'submit') window.location.href = '/portal/{escape(token)}/status';
      }}

      async function uploadAttachment() {{
        const input = document.querySelector('#attachment-panel input[name="files"]');
        if (!input || !input.files || input.files.length === 0) {{
          document.getElementById('result').textContent = '请先选择至少一个附件';
          return;
        }}
        const data = new FormData();
        Array.from(input.files).forEach((file) => data.append('files', file));
        const resp = await fetch('/portal/{escape(token)}/attachments', {{
          method: 'POST',
          body: data,
        }});
        const body = await resp.json();
        document.getElementById('result').textContent = resp.ok ? '附件上传成功，页面将刷新显示最新结果。' : (body.detail || body.message || '附件上传失败');
        if (resp.ok) window.location.reload();
      }}
      updateWizard();
    </script>
  {_render_global_toast_script()}</body>
</html>
"""


def _render_delivery_next_steps(token: str, stage: str) -> str:
    """当报告已交付时，给出明确的下一步行动引导。"""
    if stage not in ("report_ready", "completed"):
        return ""
    return f"""
        <div style="margin-top:16px;padding:16px;border-radius:14px;background:#f0f7ff;border:1px solid #1f6feb;">
          <p style="margin:0 0 10px;font-size:14px;font-weight:700;color:#1f6feb;">报告已就绪，你可以：</p>
          <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <a class="btn btn-primary" style="font-size:14px;min-height:40px;padding:8px 16px;" href="/portal/{escape(token)}/report.pdf">下载 PDF</a>
            <a class="btn btn-secondary" style="font-size:14px;min-height:40px;padding:8px 16px;" href="/portal/{escape(token)}/report">在线查看</a>
            <a class="btn btn-secondary" style="font-size:14px;min-height:40px;padding:8px 16px;" href="/pricing">继续规划其他方案</a>
          </div>
          <p style="margin:10px 0 6px;font-size:12px;color:#5a7cb8;">如需与家人商量，可生成正式分享链接并发送给家人。</p>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="btn btn-secondary" id="report-copy-link" style="font-size:12px;min-height:32px;padding:6px 10px;">复制正式分享链接</button>
            <button class="btn btn-secondary" id="report-share-btn" style="font-size:12px;min-height:32px;padding:6px 10px;">系统分享正式链接</button>
          </div>
          <p id="report-share-status" style="margin:6px 0 0;font-size:12px;color:#5a7cb8;" role="status" aria-live="polite"></p>
          {_render_share_status_panel(result_type="report", token=token)}
          {_render_share_link_script(result_type="report", token=token, copy_id="report-copy-link", share_id="report-share-btn", status_id="report-share-status", title="志愿报告分享")}
        </div>"""


def _render_status_page(token: str, context: dict[str, Any], settings: Settings) -> str:
    order = context["order"]
    stage = str(context["stage"])
    report_links = ""
    can_access_delivery = stage in {"report_ready", "completed"}
    if can_access_delivery and context["report_html_ready"]:
        report_links += (
            f'<li><a href="/portal/{escape(token)}/report">查看在线报告</a></li>'
        )
    if can_access_delivery and context["report_pdf_ready"]:
        report_links += (
            f'<li><a href="/portal/{escape(token)}/report.pdf">下载 PDF</a></li>'
        )
    if not report_links:
        report_links = "<li>报告生成中，交付物就绪后这里会显示查看/下载入口。</li>"
    station_notice_html = ""
    station_notice = context.get("station_notice")
    if isinstance(station_notice, dict):
        title = escape(str(station_notice.get("title") or "站内通知"))
        body = escape(str(station_notice.get("body") or ""))
        sent_at = escape(
            str(
                station_notice.get("sent_at")
                or station_notice.get("delivered_at")
                or ""
            )
        )
        station_notice_html = f"""
      <section class=\"panel notice-panel\">
        <h2>通知已发送</h2>
        <p><strong>{title}</strong></p>
        <p>{body}</p>
        <p class="meta">发送时间：{sent_at}</p>
      </section>"""
    summary_html = ""
    intake_summary = context.get("intake_summary") or {}
    attachment_count = int(context.get("attachment_count") or 0)
    attachments = context.get("attachments") or []
    if intake_summary or attachments:
        summary_items = [
            f"<li>分数：{escape(str(intake_summary.get('candidate_score') or '-'))}</li>",
            f"<li>位次：{escape(str(intake_summary.get('candidate_rank') or '-'))}</li>",
            f"<li>选科：{escape(','.join(intake_summary.get('candidate_subjects') or [])) or '-'}</li>",
            f"<li>兴趣方向：{escape(str(intake_summary.get('candidate_interests') or '-'))}</li>",
            f"<li>目标城市：{escape(','.join(intake_summary.get('target_cities') or [])) or '-'}</li>",
            f"<li>目标专业：{escape(','.join(intake_summary.get('target_majors') or [])) or '-'}</li>",
            f"<li>院校偏好：{escape(str(intake_summary.get('university_preferences') or '-'))}</li>",
            f"<li>已有方案说明：{escape(str(intake_summary.get('existing_plan_summary') or '-'))}</li>",
            f"<li>附件数量：{attachment_count}</li>",
        ]
        attachment_lines = []
        for item in attachments:
            if not isinstance(item, dict):
                continue
            attachment_lines.append(
                f"<li>{escape(str(item.get('original_name') or item.get('stored_name') or '未命名附件'))}"
                f"<span>{escape(str(item.get('content_type') or '-'))} · {escape(str(item.get('size_bytes') or '0'))} bytes</span></li>"
            )
        attachment_html = "".join(attachment_lines) or "<li class='empty'>暂无附件</li>"
        summary_html = f"""
      <section class="panel">
        <h2>当前资料摘要</h2>
        <ul class="summary-list">{"".join(summary_items)}</ul>
        <h3>已上传附件</h3>
        <ul class="attachment-list">{attachment_html}</ul>
      </section>"""
    payment_status = escape(str(context.get("payment_status") or "pending"))
    delivery_html = f"""
      <section class="panel">
        <h2>支付与交付状态</h2>
        <div class="status-grid">
          <div class="status-item"><strong>支付状态</strong><span>{payment_status}</span></div>
          <div class="status-item"><strong>资料状态</strong><span>{escape(context["stage_title"])}</span></div>
          <div class="status-item"><strong>HTML 报告</strong><span>{"已就绪" if context["report_html_ready"] else "未就绪"}</span></div>
          <div class="status-item"><strong>PDF 报告</strong><span>{"已就绪" if context["report_pdf_ready"] else "未就绪"}</span></div>
          <div class="status-item"><strong>交付阶段</strong><span>{escape(context["stage"])}</span></div>
        </div>
      </section>"""
    share_status_panel = _render_share_status_panel(
        result_type="report",
        token=token,
        settings=settings,
    )
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>订单进度总览</title>
    <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" />
    <style>
      :root {{
        --bg: #f3f7fb;
        --surface: #ffffff;
        --surface-soft: #f7fbff;
        --border: #d7e3f1;
        --text: #142235;
        --muted: #5b6b88;
        --primary: #1f6feb;
        --success: #0f766e;
        --success-soft: #dff7f1;
        --notice-soft: #eef6ff;
        --notice-border: #b9d7ff;
        --shadow: 0 18px 42px rgba(20,34,53,.08);
      }}
      * {{ box-sizing: border-box; }}
      body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);margin:0;color:var(--text); }}
      .wrap {{ max-width: 1100px; margin:0 auto; padding:32px 20px 72px; }}
      .hero {{ display:grid; grid-template-columns:minmax(0,1.08fr) 340px; gap:20px; align-items:start; }}
      .panel {{ background:#fff; border:1px solid var(--border); border-radius:24px; box-shadow:var(--shadow); padding:24px; }}
      .eyebrow {{ display:inline-flex; padding:6px 10px; border-radius:999px; background:var(--success-soft); color:var(--success); font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }}
      h1 {{ margin:14px 0 10px; font-size:clamp(30px,5vw,42px); letter-spacing:-0.03em; }}
      .lead {{ margin:0; color:var(--muted); line-height:1.8; }}
      .stage-pill {{ display:inline-flex; margin-top:16px; padding:10px 14px; border-radius:999px; background:var(--primary); color:#fff; font-weight:700; }}
      .progress-bar {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:18px; }}
      .progress-step {{ padding:12px 14px; border-radius:14px; background:var(--surface-soft); border:1px solid var(--border); color:var(--muted); text-align:center; }}
      .progress-step.active {{ background:var(--primary); color:#fff; border-color:var(--primary); }}
      .progress-step.done {{ background:var(--success-soft); color:var(--success); border-color:var(--success); }}
      .hero-actions {{ display:flex; gap:12px; flex-wrap:wrap; margin-top:18px; }}
      .hero-btn {{ display:inline-flex; align-items:center; justify-content:center; min-height:48px; padding:0 18px; border-radius:14px; text-decoration:none; font-weight:700; }}
      .hero-btn-primary {{ background:var(--primary); color:#fff; }}
      .hero-btn-secondary {{ background:#edf3ff; color:#194fb6; }}
      .hero-meta {{ display:grid; gap:12px; margin-top:18px; }}
      .hero-meta-item {{ padding:14px 16px; border-radius:16px; background:var(--surface-soft); border:1px solid var(--border); }}
      .hero-meta-item strong {{ display:block; margin-bottom:6px; font-size:14px; }}
      .summary-list, .action-list {{ margin:0; padding-left:18px; color:var(--muted); line-height:1.8; }}
      .attachment-list {{ list-style:none; padding:0; margin:12px 0 0; display:grid; gap:8px; }}
      .attachment-list li {{ display:flex; justify-content:space-between; gap:12px; padding:12px 14px; border-radius:14px; background:var(--surface-soft); border:1px solid var(--border); color:var(--muted); }}
      .attachment-list li.empty {{ justify-content:flex-start; }}
      .status-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
      .status-item {{ padding:14px 16px; border-radius:16px; background:var(--surface-soft); border:1px solid var(--border); }}
      .status-item strong {{ display:block; margin-bottom:6px; font-size:14px; }}
      .notice-panel {{ background:var(--notice-soft); border-color:var(--notice-border); }}
      .meta {{ color:#4f6480; font-size:14px; }}
      .sections {{ display:grid; gap:16px; margin-top:20px; }}
      @media (max-width: 980px) {{
        .hero, .status-grid {{ grid-template-columns:1fr; }}
      }}
    </style>
  </head>
  <body>{_render_global_nav()}
    <main class="wrap">
      <section class="hero">
        <section class="panel">
          <span class="eyebrow">订单进度总览</span>
          <h1>{escape(context["stage_title"])}</h1>
          <div class="progress-bar"><div class="progress-step {"done" if stage not in ("pending_payment",) else "active"}">1. 支付成功</div><div class="progress-step {"done" if stage in ("processing", "report_ready", "completed") else ("active" if stage in ("paid", "serving", "info_submitted") else "")}">2. 资料处理中</div><div class="progress-step {"done" if stage in ("completed",) else ("active" if stage in ("report_ready",) else "")}">3. 报告交付</div></div>
          <p class="lead">{escape(context["stage_subtitle"])}</p>
          <span class="stage-pill">当前阶段：{escape(context["stage"])}</span>
          <div class="hero-actions">
            <a class="hero-btn hero-btn-primary" href="/review/start?source=status&amp;token={escape(token)}">查看当前进度 / 先复核当前方案</a>
            <a class="hero-btn hero-btn-secondary" href="/portal/{escape(token)}/info">继续补充资料</a>
            <a class="hero-btn hero-btn-secondary" href="/">返回首页</a>
          </div>
          <div class="hero-meta">
            <div class="hero-meta-item"><strong>订单号</strong><span>{escape(order.id)}</span></div>
            <div class="hero-meta-item"><strong>服务版本</strong><span>{escape(order.service_version)}</span></div>
            <div class="hero-meta-item"><strong>当前订单状态</strong><span>{escape(order.status)}</span></div>
            <div class="hero-meta-item"><strong>Step 1 最小建档</strong><span>{"已完成" if context["profile_minimum_complete"] else "未完成"}</span></div>
          </div>
        </section>
        <aside class="panel">
          <h2>下一步建议</h2>
          <ul class="action-list">
            <li>如资料还未完善，可返回资料页继续补充。</li>
            <li>如报告尚未就绪，请以后续通知与状态页更新为准。</li>
            <li>如交付已完成，可优先查看报告与 PDF 下载入口。</li>
          </ul>
        </aside>
      </section>

      <section class="sections">
        {summary_html}
        <div id=\"delivery-status\">{delivery_html}</div>
        {share_status_panel}
        {station_notice_html}
        <section class="panel">
          <h2>Step 1 最小建档状态</h2>
          <ul class="action-list">
            <li>Step 1 最小建档：{"已完成" if context["profile_minimum_complete"] else "未完成"}</li>
            <li>缺失字段：{escape("、".join(context["profile_missing_fields"]) or "无")}</li>
          </ul>
        </section>
        <section class="panel">
          <h2>下一步操作</h2>
          <ul class="action-list">
            <li><a href=\"/portal/{escape(token)}/info\">填写 / 更新资料</a></li>
            <li><a href=\"/review/start?source=status&amp;token={escape(token)}\">从状态页进入方案复核</a></li>
            <li><a href=\"/portal/{escape(token)}/notifications\">查看通知记录</a></li>
            {report_links}
          </ul>
          {_render_delivery_next_steps(token, stage)}
        </section>
      </section>
    </main>
  {_render_global_toast_script()}</body>
</html>
"""


def _render_notification_audit_page(token: str, order: Order, events: list[Any]) -> str:
    rows = []
    for event in events:
        failure_reason = escape(str(event.failure_reason or "-"))
        rows.append(
            "<tr>"
            f"<td>{escape(str(event.channel))}</td>"
            f"<td>{escape(str(event.event_type))}</td>"
            f"<td>{escape(str(event.status))}</td>"
            f"<td>{escape(str(event.attempt_count))}</td>"
            f"<td>{escape(str(event.last_attempt_at or '-'))}</td>"
            f"<td>{failure_reason}</td>"
            "</tr>"
        )
    rows_html = "".join(rows) or "<tr><td colspan='6'>暂无通知事件</td></tr>"
    return f"""<!doctype html>
<html lang=\"zh-CN\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>通知审计</title><link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;margin:0;padding:32px 20px;color:#172033}}.wrap{{max-width:1100px;margin:0 auto;display:grid;gap:16px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.meta{{color:#5b6b88;line-height:1.7}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px 10px;border-bottom:1px solid #e5edf7;text-align:left;font-size:14px}}th{{color:#475569;font-size:13px;text-transform:uppercase;letter-spacing:.03em}}.toolbar{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}}</style></head>
  <body>{_render_global_nav()}
    <main class="wrap">
      <section class="panel">
        <div class="toolbar"><div><h1>通知审计</h1><p class="meta">订单号：{escape(order.id)} · 服务版本：{escape(order.service_version)}</p></div><div><a href=\"/portal/{escape(token)}/status\">返回订单状态页</a></div></div>
        <p class="meta">这里只展示通知摘要，方便你确认系统是否已经发出站内提醒或邮件通知；原始 payload 与附件路径不会在前台显示。</p>
      </section>
      <section class="panel" style=\"overflow:auto\">
        <table>
          <thead>
            <tr>
              <th>渠道</th><th>事件</th><th>状态</th><th>尝试次数</th><th>最后尝试时间</th><th>失败原因</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </section>
    </main>
  {_render_global_toast_script()}</body>
</html>
"""


def _report_version_label(order: Order) -> str:
    timestamp = (
        order.delivered_at or order.completed_at or order.paid_at or order.created_at
    )
    return f"report-{timestamp}" if timestamp else f"report-{order.id}"


def _profile_version_label(context: dict[str, Any]) -> str:
    intake_summary = context.get("intake_summary") or {}
    if context.get("profile_minimum_complete"):
        province = intake_summary.get("candidate_province") or "unknown"
        score = intake_summary.get("candidate_score") or "x"
        rank = intake_summary.get("candidate_rank") or "x"
        return f"profile-step1-{province}-{score}-{rank}"
    return "profile-step1-incomplete"


def _review_version_label(contract: ReviewResultContract | None) -> str:
    if contract is None:
        return "review-none"
    return contract.review_result_id


def _review_history_summary(order_id: str, settings: Settings) -> str:
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        current = intake_store.get(order_id)
    finally:
        intake_store.close()
    if current is None:
        return "暂无版本历史"
    review_map = dict(current.payload.get("review_results") or {})
    if not review_map:
        return "暂无版本历史"
    return f"版本历史：{len(review_map)} 个版本，最新 {escape(str(current.payload.get('latest_review_result_id') or 'unknown'))}"


def _render_report_shell(
    token: str,
    order: Order,
    context: dict[str, Any],
    report_body_html: str,
    settings: Settings,
) -> str:
    contract = _load_latest_review_result(order.id, settings)
    payload = _current_intake_payload(context)
    report_version = _report_version_label(order)
    latest_profile_version = (
        _profile_version_label_from_payload(payload)
        if payload
        else _profile_version_label(context)
    )
    profile_version = _report_version_profile_reference(
        payload,
        report_version_id=report_version,
        fallback_profile_version_id=latest_profile_version,
    )
    review_version = _review_version_label(contract)
    history_summary = _review_history_summary(order.id, settings)
    _sync_report_version_metadata(
        order.id,
        settings,
        report_version_id=report_version,
        profile_version_id=profile_version,
        review_result_version_id=(review_version if contract is not None else None),
        artifact_refs={
            "audit_report": order.audit_report,
            "pdf_path": order.pdf_path,
            "plan_file": order.plan_file,
        },
    )
    next_href_map = {
        "cwb": f"/portal/{escape(token)}/cwb",
        "step1": f"/portal/{escape(token)}/info",
        "full_plan": f"/portal/{escape(token)}/full-plan",
        "none": f"/portal/{escape(token)}/full-plan",
    }
    next_href = next_href_map.get(
        (contract.review_followup_action if contract is not None else "none"),
        f"/portal/{escape(token)}/full-plan",
    )
    review_summary = (
        f"<pre>{escape(json.dumps(contract.model_dump(), ensure_ascii=False, indent=2))}</pre>"
        if contract is not None
        else "<p class='meta'>当前暂无复核结果，可先从状态页或首页进入方案复核。</p>"
    )
    policy_href, same_score_href = _helper_entry_hrefs(payload, order)
    auxiliary_html = _render_auxiliary_factor_section(payload)
    version_state = _profile_version_state(payload, profile_version)
    return f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>志愿报告资产页</title><link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f3f7fb;margin:0;padding:32px 20px;color:#142235}}.wrap{{max-width:1100px;margin:0 auto;display:grid;gap:16px}}.panel{{background:#fff;border:1px solid #d7e3f1;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.meta{{color:#5b6b88;line-height:1.8}}.actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:14px;text-decoration:none;font-weight:700;background:#1f6feb;color:#fff}}.btn.secondary{{background:#eef6ff;color:#1f4fb6}}ul{{padding-left:20px;line-height:1.8}}pre{{white-space:pre-wrap;background:#f8fbff;border:1px solid #d7e3f1;border-radius:16px;padding:16px;overflow:auto}}</style></head><body>{_render_global_nav()}<main class="wrap"><section class="panel"><h1>志愿报告资产页</h1><p class="meta">报告版本：{escape(report_version)} · 基于哪个档案版本：{escape(profile_version)} · 当前复核版本：{escape(review_version)}</p><p class="meta">{escape(version_state)} · {history_summary}</p><div class="actions"><a class="btn" href="{next_href}">继续下一步</a><a class="btn secondary" href="/portal/{escape(token)}/info">回到资料页继续补充</a><a class="btn secondary" href="{policy_href}">查看政策中心</a><a class="btn secondary" href="{same_score_href}">查看同分段参考</a></div></section>{_render_share_status_panel(result_type="report", token=token, settings=settings)}<section class="panel"><h2>当前复核摘要</h2>{review_summary}</section>{auxiliary_html}<section class="panel"><h2>原始报告内容</h2>{report_body_html}</section><section class="panel"><h2>下一步建议</h2><ul><li><a href="/portal/{escape(token)}/info">回到资料页继续补充</a></li><li><a href="{next_href}">继续当前主路径</a></li><li><a href="/review/start?source=report&amp;token={escape(token)}">重新发起方案复核</a></li></ul></section>{_render_footer_links(token)}</main>{_render_global_toast_script()}</body></html>"""


def _render_report_page(order: Order, settings: Settings) -> str:
    token = issue_portal_token(order.id, settings.portal_token_secret)
    context = _build_portal_context(order, settings)
    if (
        order.audit_report
        and _is_trusted_report_path(order.audit_report, settings)
        and Path(order.audit_report).is_file()
    ):
        path = Path(order.audit_report)
        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".html":
            return _render_report_shell(token, order, context, content, settings)
        if path.suffix.lower() == ".json":
            pretty = json.dumps(json.loads(content), ensure_ascii=False, indent=2)
            return _render_report_shell(
                token, order, context, f"<pre>{escape(pretty)}</pre>", settings
            )
        return _render_report_shell(
            token, order, context, f"<pre>{escape(content)}</pre>", settings
        )
    if (
        order.plan_file
        and _is_trusted_report_path(order.plan_file, settings)
        and Path(order.plan_file).is_file()
    ):
        content = Path(order.plan_file).read_text(encoding="utf-8")
        return _render_report_shell(
            token, order, context, f"<pre>{escape(content)}</pre>", settings
        )
    raise HTTPException(status_code=409, detail="report not ready")


def _review_payload_key() -> str:
    return "review_result_contract"


def _review_constraints_subjects_text(value: Any) -> str:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return " / ".join(parts) or "待补充"
    text = str(value or "").strip()
    return text or "待补充"


def _review_constraints_display(value: Any) -> str:
    text = str(value or "").strip()
    return text or "待补充"


def _get_crowd_db_recs_for_review(constraints: dict[str, Any]) -> list[dict[str, Any]]:
    """根据当前约束从 crowd_db 取同分段参考。"""
    province = str(constraints.get("candidate_province") or "").strip()
    score = constraints.get("candidate_score")
    if not province or score in (None, ""):
        return []
    try:
        score_int = int(str(score))
    except (TypeError, ValueError):
        return []
    try:
        loader = CrowdDBLoader(warn_low_confidence=False)
        return loader.find_recommendations(province, score_int)
    except Exception:
        return []


def _llm_review_contract(
    *,
    settings: Settings,
    review_result_id: str,
    source: Literal["home", "status", "report", "direct"],
    resolved_summary: str,
    resolved_constraints: dict[str, Any],
    resolved_attachments: list[str],
) -> ReviewResultContract | None:
    """尝试用 LLM 生成审核结果；未配置或失败时返回 None。"""
    client = LLMClient(settings)
    if not client.is_configured:
        return None

    province = (
        str(resolved_constraints.get("candidate_province") or "").strip() or "湖南"
    )
    score = resolved_constraints.get("candidate_score")
    rank = resolved_constraints.get("candidate_rank")
    subjects = list(resolved_constraints.get("candidate_subjects") or [])
    crowd_recs = _get_crowd_db_recs_for_review(resolved_constraints)
    system, user = build_audit_prompt(
        province=province,
        score=int(str(score)) if score not in (None, "") else None,
        rank=int(str(rank)) if rank not in (None, "") else None,
        subjects=[str(s) for s in subjects],
        existing_plan=resolved_summary,
        crowd_db_recs=crowd_recs,
    )
    try:
        resp = client.chat_with_system(system, user, temperature=0.3)
        data = json.loads(resp.content)
    except (LLMError, json.JSONDecodeError, TypeError, ValueError):
        return None

    risk_level = str(data.get("risk_level") or "medium").lower()
    if risk_level not in {"low", "medium", "high"}:
        risk_level = "medium"
    findings = [
        str(x).strip() for x in list(data.get("key_findings") or []) if str(x).strip()
    ][:5]
    if not findings:
        findings = [str(data.get("risk_summary") or "当前方案可继续复核")]
    cwb = data.get("cwb_suggestions") or {}
    cwb_suggestions = {
        "rush": [
            f"{item.get('school', '?')} - {item.get('major', '?')}"
            for item in list(cwb.get("rush") or [])
            if isinstance(item, dict)
        ],
        "stable": [
            f"{item.get('school', '?')} - {item.get('major', '?')}"
            for item in list(cwb.get("stable") or [])
            if isinstance(item, dict)
        ],
        "safety": [
            f"{item.get('school', '?')} - {item.get('major', '?')}"
            for item in list(cwb.get("safety") or [])
            if isinstance(item, dict)
        ],
    }

    profile_ready = _is_profile_minimum_complete(resolved_constraints)
    recommended_action: Literal["go_cwb", "go_step1", "go_full_plan"] = (
        "go_cwb" if profile_ready else "go_step1"
    )

    return ReviewResultContract(
        review_result_id=review_result_id,
        risk_level=risk_level,  # type: ignore[arg-type]
        top_findings=findings,
        recommended_action=recommended_action,
        available_actions=["go_cwb", "go_step1", "go_full_plan"],
        review_entry_source=source,
        review_followup_action="none",
        review_input_summary=resolved_summary or "未提供现有方案说明",
        review_input_attachments=resolved_attachments,
        review_constraints=resolved_constraints,
        llm_generated=True,
        llm_summary=str(data.get("risk_summary") or ""),
        llm_cwb_suggestions=cwb_suggestions,
    )


def _start_review_result(
    *,
    source: Literal["home", "status", "report", "direct"],
    token: str | None,
    settings: Settings,
    review_input_summary: str | None = None,
    review_constraints: dict[str, Any] | None = None,
) -> ReviewResultContract:
    resolved_summary = (review_input_summary or "").strip()
    resolved_constraints = dict(review_constraints or {})
    resolved_attachments: list[str] = []
    order = None
    if token:
        order = _resolve_order_from_token(token, settings)
        context = _build_portal_context(order, settings)
        intake_summary = context.get("intake_summary") or {}
        if not resolved_summary:
            resolved_summary = str(
                intake_summary.get("existing_plan_summary") or ""
            ).strip()
        if not resolved_constraints:
            resolved_constraints = {
                "candidate_province": intake_summary.get("candidate_province")
                or order.candidate_province
                or "",
                "candidate_subjects": intake_summary.get("candidate_subjects")
                or order.candidate_subjects
                or [],
                "candidate_score": intake_summary.get("candidate_score")
                or order.candidate_score,
                "candidate_rank": intake_summary.get("candidate_rank")
                or order.candidate_rank,
            }
        resolved_attachments = [
            str(item.get("original_name") or item.get("stored_name") or "").strip()
            for item in list(context.get("attachments") or [])
            if isinstance(item, dict)
            and (item.get("original_name") or item.get("stored_name"))
        ]
        existing = _load_latest_review_result(order.id, settings)
        if existing is not None:
            existing_summary = (existing.review_input_summary or "").strip()
            if existing_summary == "未提供现有方案说明":
                existing_summary = ""
            existing_constraints = dict(existing.review_constraints or {})
            existing_attachments = [
                str(item).strip()
                for item in existing.review_input_attachments
                if str(item).strip()
            ]
            if (
                existing_summary == resolved_summary
                and existing_constraints == resolved_constraints
                and existing_attachments == resolved_attachments
            ):
                return existing

    review_result_id = f"rvw_{secrets.token_hex(4)}"
    profile_ready = _is_profile_minimum_complete(resolved_constraints)
    recommended_action: Literal["go_cwb", "go_step1", "go_full_plan"] = (
        "go_cwb" if profile_ready else "go_step1"
    )

    contract = _llm_review_contract(
        settings=settings,
        review_result_id=review_result_id,
        source=source,
        resolved_summary=resolved_summary,
        resolved_constraints=resolved_constraints,
        resolved_attachments=resolved_attachments,
    )
    if contract is None:
        top_finding = (
            "Step 1 已齐全，可直接进入冲稳保微调，再决定是否进入完整规划。"
            if profile_ready
            else "当前方案建议先补充 Step 1 后再继续判断梯度风险。"
        )
        contract = ReviewResultContract(
            review_result_id=review_result_id,
            risk_level="medium",
            top_findings=[top_finding],
            recommended_action=recommended_action,
            available_actions=["go_cwb", "go_step1", "go_full_plan"],
            review_entry_source=source,
            review_followup_action="none",
            review_input_summary=resolved_summary,
            review_input_attachments=resolved_attachments,
            review_constraints=resolved_constraints,
        )
    if order is not None:
        intake_store = IntakeStore.for_db(settings.orders_db_path)
        try:
            current = intake_store.get(order.id)
            payload = dict(current.payload) if current is not None else {}
            payload["latest_review_result_id"] = contract.review_result_id
            review_map = dict(payload.get("review_results") or {})
            review_map[contract.review_result_id] = contract.model_dump()
            payload["review_results"] = review_map
            intake_store.save(
                order_id=order.id,
                payload=payload,
                submit=(current.status == "submitted")
                if current is not None
                else False,
            )
        finally:
            intake_store.close()
    return contract


def _render_review_start_page(contract: ReviewResultContract, token: str | None) -> str:
    token_input = (
        f'<input type="hidden" name="token" value="{escape(token)}" />' if token else ""
    )
    findings_html = (
        "".join(f"<li>{escape(str(item))}</li>" for item in contract.top_findings)
        or "<li>暂无核心问题</li>"
    )
    attachment_html = (
        "、".join(
            escape(str(item))
            for item in contract.review_input_attachments
            if str(item).strip()
        )
        or "无附件"
    )
    llm_summary_html = (
        f'<section class="panel"><h2>AI 风险总结</h2><p class="meta">{escape(contract.llm_summary)}</p></section>'
        if contract.llm_generated and contract.llm_summary
        else ""
    )
    constraints = contract.review_constraints or {}
    profile_ready = bool(
        constraints.get("candidate_province") and constraints.get("candidate_score")
    )
    recommended_label = {
        "go_cwb": "先去看冲稳保建议",
        "go_step1": "先补齐基础信息",
        "go_full_plan": "进入完整规划",
    }[contract.recommended_action]
    # 根据是否有token决定按钮行为：无token时跳首页表单，有token时走portal流程
    if token is None:
        # 免费复核无订单场景：引导用户先去首页完善信息或下单
        primary_action = (
            "完善信息后重新复核",
            "home",
            "当前是免费复核，建议先完善分数、位次、选科等信息，或选择付费服务获得完整分析。",
        )
    else:
        # 有订单场景：跳转到portal相应页面
        primary_action = {
            "go_cwb": (
                "去看冲稳保建议",
                "cwb",
                "如果你的基础信息已经完整，下一步先看冲稳保梯度更合适。",
            ),
            "go_step1": (
                "先补齐基础信息",
                "step1",
                "当前更适合先补齐省份、分数、位次、选科等基础信息，再继续判断梯度风险。",
            ),
            "go_full_plan": (
                "进入完整规划",
                "full_plan",
                "如果你已经明确要进入完整服务，可以直接继续到完整规划页。",
            ),
        }[contract.recommended_action]
    summary = escape(contract.review_input_summary or "未提供现有方案说明")
    # 风险等级视觉映射
    risk_level_map = {
        "low": ("偏低（风险可控）", "#1f6feb", "#eef6ff", "#d7e3f1"),
        "medium": ("中等（需要关注）", "#f59e0b", "#fffbeb", "#fcd34d"),
        "high": ("偏高（尽快调整）", "#dc2626", "#fef2f2", "#fecaca"),
    }
    risk_label, risk_color, risk_bg, risk_border = risk_level_map.get(
        contract.risk_level.lower(), risk_level_map["medium"]
    )

    # 建议标签
    recommended_label = {
        "go_cwb": "先去看冲稳保建议",
        "go_step1": "先补齐基础信息",
        "go_full_plan": "进入完整规划",
    }[contract.recommended_action]

    province = escape(
        _review_constraints_display(constraints.get("candidate_province"))
    )
    subjects = escape(
        _review_constraints_subjects_text(constraints.get("candidate_subjects"))
    )
    score = escape(_review_constraints_display(constraints.get("candidate_score")))
    # 信息完整性提示
    info_complete_html = (
        (
            '<div style="margin-top:16px;padding:14px;border-radius:12px;background:#fffbeb;border:1px solid #fcd34d;">'
            '<p style="margin:0;font-size:14px;color:#92400e;"><strong>⚠ 信息不完整</strong>：选科组合或位次为"待补充"，无法给出具体录取差距分析。</p>'
            "</div>"
        )
        if not profile_ready
        else (
            '<div style="margin-top:16px;padding:14px;border-radius:12px;background:#ecfdf5;border:1px solid #a7f3d0;">'
            '<p style="margin:0;font-size:14px;color:#065f46;"><strong>✓ 信息完整</strong>：已具备生成冲稳保建议的条件。</p>'
            "</div>"
        )
    )
    rank = escape(_review_constraints_display(constraints.get("candidate_rank")))
    share_hint = "此页可生成正式分享链接"
    body_html = f"""
<section class="panel">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <span class="eyebrow">免费复核结果</span>
    <a class="btn btn-secondary" style="font-size:13px;min-height:32px;padding:6px 12px;" href="/">返回首页</a>
  </div>
  <h1>复核结果</h1>
  <p class="meta">基于你当前提交的信息，下面先告诉你当前的风险判断和最适合的下一步。</p>
  <div style="margin-top:12px;padding:12px 14px;border-radius:12px;background:#f0f7ff;border:1px solid #1f6feb;">
    <p style="margin:0 0 6px;font-size:13px;color:#1f6feb;"><strong>分享给家人商量</strong></p>
    <p style="margin:0 0 8px;font-size:12px;color:#5a7cb8;">{share_hint}。生成的将是独立分享链接，而不是当前页面地址。</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <button class="btn btn-secondary" id="copy-link-btn" style="font-size:12px;min-height:32px;padding:6px 10px;">复制正式分享链接</button>
      <button class="btn btn-secondary" id="share-btn" style="font-size:12px;min-height:32px;padding:6px 10px;">系统分享正式链接</button>
      <button class="btn btn-secondary" id="save-draft-btn" style="font-size:12px;min-height:32px;padding:6px 10px;">保存到本地草稿</button>
    </div>
    <p id="share-status" style="margin:8px 0 0;font-size:12px;color:#5a7cb8;" role="status" aria-live="polite"></p>
  </div>
</section>
{_render_share_status_panel(result_type="review_result", token=token or "", settings=None)}
{llm_summary_html}
<section class="panel">
  <h2>你当前提交的信息</h2>
  <ul>
    <li>已有方案说明：{summary}</li>
    <li>考试省份：{province}</li>
    <li>选科组合：{subjects}</li>
    <li>高考分数：{score}</li>
    <li>位次：{rank}</li>
    <li>附件：{attachment_html}</li>
  </ul>
  {info_complete_html}
</section>

<section class="panel">
  <h2>初步评估结果</h2>
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 16px;">
    <span style="display:inline-flex;padding:8px 14px;border-radius:999px;background:{risk_bg};border:1px solid {risk_border};color:{risk_color};font-weight:700;font-size:13px;">风险等级：{risk_label}</span>
    <span style="display:inline-flex;padding:8px 14px;border-radius:999px;background:#f1f5f9;border:1px solid #cbd5e1;color:#475569;font-weight:600;font-size:13px;">建议：{recommended_label}</span>
  </div>
  <h3>核心问题</h3>
  <ul>{findings_html}</ul>
  <p class="meta" style="margin-top:8px;">风险等级说明：低 = 当前方案结构基本合理，微调即可；中 = 存在踩线或扎堆风险，需要进一步判断；高 = 存在明显梯度失衡或结构风险，建议尽快调整。</p>
</section>

<section class="panel">
  <h2>下一步建议</h2>
  <p class="meta">{escape(primary_action[2])}</p>
  <div class="actions">
    <form action="/review/action" method="post">{token_input}<input type="hidden" name="action" value="{escape(primary_action[1])}" /><button class="btn btn-primary" type="submit">{escape(primary_action[0])}</button></form>
    <form action="/review/action" method="post">{token_input}<input type="hidden" name="action" value="cwb" /><button class="btn btn-secondary" type="submit">查看冲稳保建议</button></form>
    <a class="btn btn-secondary" href="/pricing">进入完整规划（付费）</a>
  </div>
  <p class="meta" style="margin-top:10px;">免费复核帮你判断风险方向；完整规划和深度辅导在支付后启动，会给你逐志愿解析、冲稳保梯度表和交付报告。</p>
</section>
{_render_share_link_script(result_type="review_result", token=token or "", copy_id="copy-link-btn", share_id="share-btn", status_id="share-status", title="高考志愿复核结果")}
<script>
(function() {{
  document.getElementById('save-draft-btn').addEventListener('click', function() {{
    try {{
      localStorage.setItem('gaokao-review-draft', JSON.stringify({{
        url: window.location.href,
        savedAt: new Date().toISOString(),
        summary: '{escape(contract.review_input_summary or "")}',
        riskLevel: '{escape(contract.risk_level)}'
      }}));
      const statusEl = document.getElementById('share-status');
      if (statusEl) {{
        statusEl.textContent = '已保存到本地草稿，可稍后回来看';
        statusEl.style.color = '#1f6feb';
      }}
    }} catch (e) {{
      const statusEl = document.getElementById('share-status');
      if (statusEl) {{
        statusEl.textContent = '本地草稿保存失败';
        statusEl.style.color = '#b42318';
      }}
    }}
  }});
}})();
</script>

"""
    return _render_placeholder_shell(
        title="复核结果", max_width=960, body_html=body_html
    )


def _apply_review_followup_action(
    token: str, action: Literal["cwb", "step1", "full_plan"], settings: Settings
) -> ReviewActionResponse:
    order = _resolve_order_from_token(token, settings)
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        current = intake_store.get(order.id)
        if current is None:
            raise HTTPException(status_code=404, detail="review result not found")
        payload = dict(current.payload)
        review_id = payload.get("latest_review_result_id")
        review_map = dict(payload.get("review_results") or {})
        contract_raw = review_map.get(review_id) if review_id else None
        if not isinstance(contract_raw, dict):
            raise HTTPException(status_code=404, detail="review result not found")
        contract = ReviewResultContract.model_validate(contract_raw)
        updated = contract.model_copy(update={"review_followup_action": action})
        review_map[updated.review_result_id] = updated.model_dump()
        payload["review_results"] = review_map
        intake_store.save(
            order_id=order.id,
            payload=payload,
            submit=(current.status == "submitted"),
        )
    finally:
        intake_store.close()
    next_href = {
        "cwb": f"/portal/{token}/cwb",
        "step1": f"/portal/{token}/info",
        "full_plan": f"/portal/{token}/full-plan",
    }[action]
    return ReviewActionResponse(
        review_result_id=updated.review_result_id,
        review_followup_action=action,
        next_href=next_href,
    )


def _load_latest_review_result(
    order_id: str, settings: Settings
) -> ReviewResultContract | None:
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        current = intake_store.get(order_id)
    finally:
        intake_store.close()
    if current is None:
        return None
    review_id = current.payload.get("latest_review_result_id")
    review_map = dict(current.payload.get("review_results") or {})
    contract_raw = review_map.get(review_id) if review_id else None
    if not isinstance(contract_raw, dict):
        return None
    return ReviewResultContract.model_validate(contract_raw)


def _render_cwb_placeholder_page(
    token: str,
    order: Order,
    contract: ReviewResultContract | None,
    context: dict[str, Any],
) -> str:
    payload = (
        contract.model_dump()
        if contract is not None
        else {"review_followup_action": "cwb"}
    )
    intake_payload = _current_intake_payload(context)
    policy_href, same_score_href = _helper_entry_hrefs(intake_payload, order)
    auxiliary_html = _render_auxiliary_factor_section(intake_payload)
    findings = contract.top_findings if contract is not None else []
    findings_html = (
        "".join(f"<li>{escape(str(item))}</li>" for item in findings)
        or "<li>当前暂无复核摘要，请先回到复核入口。</li>"
    )
    recommendation = {
        "go_cwb": "优先微调冲稳保梯度，先补齐冲刺 / 稳妥 / 保底三档，再决定是否进入完整规划。",
        "go_step1": "先补齐 Step 1 的省份 / 分数 / 位次 / 选科，再回到冲稳保判断。",
        "go_full_plan": "当前资料已可进入完整规划，建议继续补学校、专业与家庭约束。",
    }.get(
        (contract.recommended_action if contract is not None else "go_step1"),
        "先补齐关键信息再继续。",
    )

    # 基于考生分数和 crowd_db 生成三档真实建议
    candidate_score_raw = intake_payload.get("candidate_score") or order.candidate_score
    candidate_province = (
        intake_payload.get("candidate_province") or order.candidate_province or "湖南"
    )
    candidate_score = None
    try:
        candidate_score = int(candidate_score_raw) if candidate_score_raw else None
    except (ValueError, TypeError):
        pass

    def _cwb_tier(title: str, offset: int, color: str) -> str:
        """根据分数偏移生成一档建议，优先使用 LLM 建议，fallback 到 crowd_db。"""
        # 1. 优先使用 LLM 生成的三档建议
        tier_key = {"冲刺建议": "rush", "稳妥建议": "stable", "保底建议": "safety"}.get(
            title
        )
        if contract is not None and contract.llm_cwb_suggestions and tier_key:
            llm_suggestions = contract.llm_cwb_suggestions.get(tier_key) or []
            if llm_suggestions:
                schools_html = "".join(
                    f"<li>{escape(s)}</li>" for s in llm_suggestions[:3]
                )
                return (
                    f'<article style="padding:16px;border-radius:14px;background:{color};border:1px solid #d7e3f1;">'
                    f"<h2>{title}</h2>"
                    f'<ul style="margin:8px 0;padding-left:18px;line-height:1.8;">{schools_html}</ul>'
                    f'<p class="meta" style="margin-top:6px;color:#1f6feb;">🤖 LLM 结合你的分数、位次和同分段数据生成</p>'
                    f"</article>"
                )

        # 2. fallback 到 crowd_db
        if candidate_score is None:
            return (
                f'<article style="padding:16px;border-radius:14px;background:{color};border:1px solid #d7e3f1;">'
                f"<h2>{title}</h2>"
                f'<p class="meta">补齐当前分数后，这里会基于同分段数据给出具体的院校方向建议。</p>'
                f"</article>"
            )

        target_score = candidate_score + offset
        try:
            from data.crowd_db.loader import CrowdDBLoader

            loader = CrowdDBLoader(warn_low_confidence=False)
            recs = loader.find_recommendations(candidate_province, target_score)
            schools = [
                f"{r.get('name', '?')} - {r.get('major', '?')}"
                for r in recs[:3]
                if isinstance(r, dict)
            ]
            if not schools:
                schools = ["该分段暂无 crowd_db 推荐，请参考同分段参考页"]
        except Exception:
            schools = ["数据加载中，请稍后查看"]

        risk_note = ""
        if offset > 0:
            risk_note = f'<p class="meta" style="color:#b42318;margin-top:6px;">⚠ 这档分数要求更高（目标分 ≈ {target_score}），存在不被录取的风险，只作为冲刺方向参考。</p>'
        elif offset < 0:
            risk_note = f'<p class="meta" style="color:#1f7a4d;margin-top:6px;">✓ 这档分数要求更低（目标分 ≈ {target_score}），录取概率更高，作为保底。</p>'
        else:
            risk_note = f'<p class="meta" style="color:#1f6feb;margin-top:6px;">→ 围绕当前分数（{candidate_score}）匹配，作为主力选择。</p>'

        schools_html = "".join(f"<li>{escape(s)}</li>" for s in schools)
        return (
            f'<article style="padding:16px;border-radius:14px;background:{color};border:1px solid #d7e3f1;">'
            f"<h2>{title}</h2>"
            f'<ul style="margin:8px 0;padding-left:18px;line-height:1.8;">{schools_html}</ul>'
            f"{risk_note}"
            f"</article>"
        )

    cwb_tier_html = (
        f'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;">'
        f"{_cwb_tier('冲刺建议', 20, '#fff5f5')}"
        f"{_cwb_tier('稳妥建议', 0, '#f0f7ff')}"
        f"{_cwb_tier('保底建议', -20, '#f0fff4')}"
        f"</div>"
    )
    score_context = (
        f'<p class="meta">当前分数：{escape(str(candidate_score or "待补充"))} · 省份：{escape(candidate_province)} · 冲刺+20分 / 稳妥0分 / 保底-20分</p>'
        if candidate_score
        else ""
    )

    body_html = f"""<section class="panel"><h1>冲稳保建议页</h1><p class="meta">订单号：{escape(order.id)}。基于你当前分数和同分段数据，这里给出三档策略建议。</p>{score_context}<div class="actions"><a href="{policy_href}">查看政策中心</a><a href="{same_score_href}">查看同分段参考</a></div></section><section class="panel"><h2>当前建议</h2><p class="meta">{escape(recommendation)}</p><ul>{findings_html}</ul></section><section class="panel">{cwb_tier_html}</section><section class="panel"><h2>当前复核摘要</h2><pre>{escape(json.dumps(payload, ensure_ascii=False, indent=2))}</pre></section>{auxiliary_html}<section class="panel"><h2>下一步建议</h2><ul><li><a href="/portal/{escape(token)}/full-plan">进入完整规划</a></li><li><a href="/portal/{escape(token)}/status">返回订单状态页</a></li></ul></section>"""
    return _render_placeholder_shell(
        title="冲稳保建议页", max_width=1080, body_html=body_html
    )


def _render_full_plan_placeholder_page(
    token: str,
    order: Order,
    context: dict[str, Any],
    contract: ReviewResultContract | None,
    settings: Settings | None = None,
) -> str:
    payload = (
        contract.model_dump()
        if contract is not None
        else {"review_followup_action": "full_plan"}
    )
    missing = "、".join(context.get("profile_missing_fields") or []) or "无"
    intake_payload = _current_intake_payload(context)
    versions = [
        item
        for item in list(intake_payload.get("profile_versions") or [])
        if isinstance(item, dict)
    ]
    version_lines = (
        "".join(
            f"<li>{escape(str(item.get('stage_label') or item.get('profile_version_id') or '未知版本'))}</li>"
            for item in versions
        )
        or "<li>暂无版本历史</li>"
    )
    auxiliary_html = _render_auxiliary_factor_section(intake_payload)

    # LLM 生成完整规划方案（如果配置了 LLM）
    llm_plan_html = ""
    llm_client = LLMClient(settings) if settings else None
    if llm_client and llm_client.is_configured:
        try:
            intake_summary = context.get("intake_summary") or {}
            crowd_recs = _get_crowd_db_recs_for_review(intake_summary)
            system, user = build_full_plan_prompt(
                province=str(
                    intake_summary.get("candidate_province")
                    or order.candidate_province
                    or "湖南"
                ),
                score=int(
                    intake_summary.get("candidate_score") or order.candidate_score or 0
                )
                if intake_summary.get("candidate_score") or order.candidate_score
                else 0,
                rank=int(
                    intake_summary.get("candidate_rank") or order.candidate_rank or 0
                )
                if intake_summary.get("candidate_rank") or order.candidate_rank
                else None,
                subjects=list(intake_summary.get("candidate_subjects") or []),
                target_cities=list(intake_summary.get("target_cities") or []),
                target_majors=list(intake_summary.get("target_majors") or []),
                family_background=str(intake_summary.get("family_background") or ""),
                interest_assessment=str(
                    intake_summary.get("interest_assessment_result") or ""
                ),
                existing_plan=str(intake_summary.get("existing_plan_summary") or ""),
                crowd_db_recs=crowd_recs,
            )
            resp = llm_client.chat_with_system(system, user, temperature=0.5)
            plan_data = json.loads(resp.content)
            volunteers = plan_data.get("volunteers") or []
            vol_rows = []
            for v in volunteers:
                tier_badge = {"冲": "🔴", "稳": "🟢", "保": "🔵"}.get(
                    v.get("tier", ""), "•"
                )
                vol_rows.append(
                    f'<tr><td style="padding:8px;">{tier_badge} {escape(v.get("tier", ""))}</td>'
                    f'<td style="padding:8px;"><strong>{escape(v.get("school", ""))}</strong></td>'
                    f'<td style="padding:8px;">{escape(v.get("major", ""))}</td>'
                    f'<td style="padding:8px;color:#5b6b88;font-size:12px;">{escape(v.get("reason", ""))}</td>'
                    f"</tr>"
                )
            llm_plan_html = (
                f'<section class="panel"><h2>🤖 AI 生成的完整志愿方案</h2>'
                f'<p class="meta">{escape(plan_data.get("overall_assessment", ""))}</p>'
                f'<p class="meta" style="margin-top:6px;"><strong>核心策略：</strong>{escape(plan_data.get("strategy", ""))}</p>'
                f'<table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:12px;">'
                f'<thead><tr style="text-align:left;border-bottom:2px solid #d7e3f1;">'
                f'<th style="padding:8px;">档位</th><th style="padding:8px;">院校</th>'
                f'<th style="padding:8px;">专业</th><th style="padding:8px;">推荐理由</th>'
                f"</tr></thead><tbody>{''.join(vol_rows)}</tbody></table>"
                f"</section>"
            )
            warnings = plan_data.get("warnings") or []
            if warnings:
                warn_html = "".join(f"<li>{escape(str(w))}</li>" for w in warnings[:5])
                llm_plan_html += f'<section class="panel"><h2>⚠️ 注意事项</h2><ul>{warn_html}</ul></section>'
        except (LLMError, json.JSONDecodeError, TypeError, ValueError):
            llm_plan_html = '<section class="panel"><h2>AI 方案生成</h2><p class="meta">AI 方案生成暂时不可用，请稍后重试或联系客服。</p></section>'

    planning_summary = (
        "当前资料已进入完整规划阶段，可继续围绕学校、专业、预算与家庭约束做结构化取舍。"
    )
    body_html = f"""<section class="panel"><h1>完整规划建议页</h1><p class="meta">订单号：{escape(order.id)}。这里承接复核后的完整规划建议，不再只是入口说明。</p><p class="meta">{escape(planning_summary)}</p><ul><li>Step 1 最小建档：{"已完成" if context.get("profile_minimum_complete") else "未完成"}</li><li>缺失字段：{escape(missing)}</li></ul></section>{llm_plan_html}<section class="panel"><h2>方案优先级</h2><ul><li>先按省份 / 分数 / 位次确认基本梯度</li><li>再按院校偏好、专业偏好与家庭约束收敛方案</li><li>最后结合已有方案与附件做增量修订</li></ul></section><section class="panel"><h2>版本历史</h2><ul>{version_lines}</ul></section>{auxiliary_html}<section class="panel"><h2>当前复核摘要</h2><pre>{escape(json.dumps(payload, ensure_ascii=False, indent=2))}</pre></section><section class="panel"><a href=\"/portal/{escape(token)}/info\">继续补充资料</a></section>"""
    return _render_placeholder_shell(
        title="完整规划建议页", max_width=960, body_html=body_html
    )


def _render_deletion_request_page(token: str, order: Order, settings: Settings) -> str:
    # 2026-06-19 T12-C: 让用户先看见"我的订单处于哪个保留期阶段", 决定是否现在就申请
    retention_status = _resolve_retention_status(order, settings)
    if retention_status == "outside":
        retention_card = (
            "<section class='panel'>"
            "<span class='eyebrow'>保留期状态</span>"
            "<p class='lead'><strong>已超过 180 天保留期</strong>，可申请删除订单资料、附件与交付物。"
            "提交后我们会同步做人工核验，并在订单状态链路中继续反馈处理进度。</p>"
            "</section>"
        )
    elif retention_status == "within":
        retention_card = (
            "<section class='panel'>"
            "<span class='eyebrow'>保留期状态</span>"
            "<p class='lead'>当前订单仍在 <strong>180 天保留期</strong>内。提交删除申请后，我们仍会先做人工核验，"
            "并按既定保留期规则处理订单、资料与附件。</p>"
            "</section>"
        )
    else:
        retention_card = (
            "<section class='panel'>"
            "<span class='eyebrow'>保留期状态</span>"
            "<p class='lead'>本订单当前不需要走保留期清理流程（尚未进入服务完成阶段）。"
            "如需撤回资料或申请删除，提交申请后我们会先做人工核验。</p>"
            "</section>"
        )
    return f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>删除申请</title><link rel='stylesheet' href='/static/portal-ui.css' /><style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:920px;margin:0 auto;display:grid;gap:16px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.eyebrow{{display:inline-flex;padding:6px 10px;border-radius:999px;background:#fff7e6;color:#8a5a00;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}.lead{{color:#5b6b88;line-height:1.8}}.field{{display:flex;flex-direction:column;gap:6px;margin-bottom:14px}}input,textarea{{width:100%;padding:12px;border-radius:12px;border:1px solid #cfd7e6}}textarea{{min-height:120px;resize:vertical}}.check{{display:flex;gap:10px;align-items:flex-start;margin:12px 0}}button{{border:none;border-radius:14px;background:#1f6feb;color:#fff;font-weight:700;padding:13px 18px;cursor:pointer}}#result{{margin-top:14px;min-height:24px;color:#5b6b88;white-space:pre-wrap}}</style></head>
<body>{_render_global_nav()}<main class='wrap' role='main'>
<section class='panel'><span class='eyebrow'>删除申请</span><h1>提交删除申请</h1><p class='lead'>可用于申请删除资料、附件或交付物。提交后，系统会保留必要审计记录，并由人工核验订单与监护人信息后处理。</p></section>
{retention_card}
<section class='panel'>
  <p><strong>订单号：</strong>{escape(order.id)}</p>
  <form id='deletion-request-form'>
    <div class='field'><label>申请人姓名</label><input name='requester_name' required /></div>
    <div class='field'><label>联系方式</label><input name='requester_contact' required /></div>
    <div class='field'><label>删除范围</label><input name='scope' value='order_and_attachments' required /></div>
    <div class='field'><label>申请原因</label><textarea name='reason' required></textarea></div>
    <label class='check'><input type='checkbox' name='confirm_guardian' /> <span>我确认监护人已知情并同意发起删除申请</span></label>
    <button type='button' onclick='submitDeletionRequest()'>提交删除申请</button>
  </form>
  {_render_footer_links(token)}
  <div id='result'></div>
</section>
<script>
async function submitDeletionRequest() {{
  const form = new FormData(document.getElementById('deletion-request-form'));
  const payload = {{
    requester_name: form.get('requester_name') || '',
    requester_contact: form.get('requester_contact') || '',
    scope: form.get('scope') || '',
    reason: form.get('reason') || '',
    confirm_guardian: form.get('confirm_guardian') === 'on',
  }};
  const resultNode = document.getElementById('result');
  resultNode.textContent = '正在提交删除申请…';
  const resp = await fetch('/portal/{escape(token)}/deletion-request', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify(payload),
  }});
  const body = await resp.json();
  resultNode.textContent = resp.ok ? '删除申请已提交，后续可在订单状态链路中继续跟踪。' : JSON.stringify(body, null, 2);
}}
</script>
</main>{_render_global_toast_script()}</body></html>"""
