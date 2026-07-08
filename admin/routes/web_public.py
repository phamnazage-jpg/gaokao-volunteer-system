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

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse
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
from data.llm import LLMClient, LLMError, build_audit_prompt
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
_ALIPAY_NOTIFY_MAX_BODY_BYTES = 64 * 1024

_PUBLIC_ORDER_RATE_LIMIT = 5
_PUBLIC_ORDER_RATE_LIMIT_WINDOW_SECONDS = 60.0
_PUBLIC_ORDER_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = {}


def _public_order_rate_limit_key(
    request: Request, payload: PublicOrderCreate, settings: Settings
) -> str:
    client_host = request.client.host if request.client else "unknown"
    contact = (
        (payload.customer_phone or payload.customer_wechat or "unknown").strip().lower()
    )
    return f"{settings.orders_db_path}:{client_host}:{contact}"


def _assert_public_order_rate_limit(
    request: Request, payload: PublicOrderCreate, settings: Settings
) -> None:
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
            detail={
                "retry_after_seconds": int(_PUBLIC_ORDER_RATE_LIMIT_WINDOW_SECONDS)
            },
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



# Legacy backend-rendered page route removed: GET /

# Legacy backend-rendered page route removed: GET /pricing

# Legacy backend-rendered page route removed: GET /checkout/{service_version}

# Legacy backend-rendered page route removed: GET /portal/{token}/payment-success
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
                existing = dao.get_by_external_id(
                    "web", f"idempotency:{payload.idempotency_key}"
                )
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
            dao.delete(order.id, actor="public_web", reason="checkout_creation_failed")
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
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _ALIPAY_NOTIFY_MAX_BODY_BYTES:
                raise HTTPException(
                    status_code=413, detail="payment notify body too large"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="invalid content-length"
            ) from None
    raw_body = await request.body()
    if len(raw_body) > _ALIPAY_NOTIFY_MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="payment notify body too large")
    body = raw_body.decode("utf-8")
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



# Legacy backend-rendered page route removed: GET /pay/mock/{payment_id}
@router.post("/pay/mock/{payment_id}/complete", include_in_schema=False)
def complete_mock_payment(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _complete_simulated_payment(payment_id, settings, provider_slug="mock")



# Legacy backend-rendered page route removed: GET /pay/alipay-sim/{payment_id}
@router.post("/pay/alipay-sim/{payment_id}/complete", include_in_schema=False)
def complete_alipay_sim_payment(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _complete_simulated_payment(payment_id, settings, provider_slug="alipay-sim")



# Legacy backend-rendered page route removed: GET /portal/payment-return

# Legacy backend-rendered page route removed: GET /review/start

# Legacy backend-rendered page route removed: GET /portal/{token}/cwb

# Legacy backend-rendered page route removed: GET /portal/{token}/full-plan

# Legacy backend-rendered page route removed: GET /portal/{token}/info
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

    normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
    expected_content_types = {
        ".pdf": {"application/pdf"},
        ".txt": {"text/plain"},
        ".md": {"text/markdown", "text/plain"},
        ".json": {"application/json", "text/json"},
        ".png": {"image/png"},
        ".jpg": {"image/jpeg"},
        ".jpeg": {"image/jpeg"},
        ".webp": {"image/webp"},
    }
    if (
        normalized_content_type
        and normalized_content_type not in expected_content_types[suffix]
    ):
        raise HTTPException(
            status_code=415, detail="attachment content type does not match extension"
        )

    magic_prefixes = {
        ".pdf": (b"%PDF-",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".webp": (b"RIFF",),
    }
    if suffix in magic_prefixes and not any(
        payload.startswith(prefix) for prefix in magic_prefixes[suffix]
    ):
        raise HTTPException(
            status_code=415, detail="attachment content does not match extension"
        )
    if suffix == ".webp" and len(payload) >= 12 and payload[8:12] != b"WEBP":
        raise HTTPException(
            status_code=415, detail="attachment content does not match extension"
        )
    if suffix in {".txt", ".md", ".json"}:
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=415, detail="attachment text must be utf-8"
            ) from exc
        if suffix == ".json":
            try:
                json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=415, detail="attachment json is invalid"
                ) from exc


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



# Legacy backend-rendered page route removed: GET /portal/{token}/deletion-request
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



# Legacy backend-rendered page route removed: GET /portal/{token}/notifications
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



# Legacy backend-rendered page route removed: GET /portal/{token}/status

# Legacy backend-rendered page route removed: GET /portal/{token}/report

# Legacy backend-rendered page route removed: GET /portal/{token}/report.pdf
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
        jti = payload.get("jti")
        if isinstance(jti, str) and jti:
            revoked = dao.conn.execute(
                "SELECT 1 FROM portal_token_revocations WHERE jti=?", (jti,)
            ).fetchone()
            if revoked is not None:
                raise HTTPException(status_code=401, detail="portal token revoked")
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



# Legacy backend-rendered helper removed: _render_global_nav



# Legacy backend-rendered helper removed: _render_global_toast_script



# Legacy backend-rendered helper removed: _render_footer_links



# Legacy backend-rendered helper removed: _render_share_status_panel



# Legacy backend-rendered helper removed: _render_share_link_script



# Legacy backend-rendered helper removed: _render_basic_page



# Legacy backend-rendered helper removed: _render_placeholder_shell


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



# Legacy backend-rendered helper removed: _render_legal_doc_page



# Legacy backend-rendered page route removed: GET /privacy

# Legacy backend-rendered page route removed: GET /service-terms
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



# Legacy backend-rendered page route removed: GET /policy-center

# Legacy backend-rendered page route removed: GET /same-score-reference

# Legacy backend-rendered page route removed: GET /deletion-policy

# Legacy backend-rendered page route removed: GET /my-orders

# Legacy backend-rendered page route removed: GET /my-reports

# Legacy backend-rendered page route removed: GET /data-query

# Legacy backend-rendered page route removed: GET /score-line-query

# Legacy backend-rendered page route removed: GET /rank-estimator

# Legacy backend-rendered page route removed: GET /majors-query

# Legacy backend-rendered page route removed: GET /schools-query

# Legacy backend-rendered page route removed: GET /compare-reports

# Legacy backend-rendered helper removed: _render_landing_page



# Legacy backend-rendered helper removed: _render_pricing_page



# Legacy backend-rendered helper removed: _render_checkout_page



# Legacy backend-rendered helper removed: _render_payment_success_page



# Legacy backend-rendered helper removed: _render_mock_payment_page



# Legacy backend-rendered helper removed: _render_alipay_sim_payment_page



# Legacy backend-rendered helper removed: _render_simulated_payment_html


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



# Legacy backend-rendered helper removed: _render_simulated_payment_page


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



# Legacy backend-rendered helper removed: _render_info_page



# Legacy backend-rendered helper removed: _render_delivery_next_steps



# Legacy backend-rendered helper removed: _render_status_page



# Legacy backend-rendered helper removed: _render_notification_audit_page


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



# Legacy backend-rendered helper removed: _render_report_shell



# Legacy backend-rendered helper removed: _render_report_page


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



# Legacy backend-rendered helper removed: _render_review_start_page


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



# Legacy backend-rendered helper removed: _render_cwb_placeholder_page



# Legacy backend-rendered helper removed: _render_full_plan_placeholder_page



# Legacy backend-rendered helper removed: _render_deletion_request_page
