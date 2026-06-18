"""用户端 Web 自助 MVP 公共入口页面与 Portal 路由。"""

from __future__ import annotations

import json
import logging
import secrets
from html import escape
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
)
from pydantic import BaseModel

from admin.config import Settings, get_settings_dep
from data.customer_portal.token import (
    PortalTokenError,
    issue_portal_token,
    verify_portal_token,
)
from data.notifications.email_service import DeliveryNotificationService
from data.orders import crypto
from data.orders.dao import OrderNotFound, OrdersDAO
from data.orders.intake_schema import IntakePayload
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.orders.public_flow import (
    PublicOrderCreate,
    create_public_order,
)
from data.orders.crypto import MissingEncryptionKey
from data.payments.service import PaymentError, PaymentService


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
    "payment_failed": ("支付失败", "支付未成功，请重新发起支付。"),
}
_SERVICE_PRICES = {
    "audit": 4900,
    "basic": 4900,
    "standard": 9900,
    "premium": 19900,
}
_SIMULATED_PAYMENT_ROUTE_NOT_FOUND = "not found"


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


class PortalAttachmentUploaded(BaseModel):
    order_id: str
    intake_status: str
    stage: str
    attachments: list[dict[str, Any]]


class DeletionRequestCreate(BaseModel):
    requester_name: str
    requester_contact: str
    reason: str
    scope: str
    confirm_guardian: bool


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
def landing_page(request: Request) -> HTMLResponse:
    return HTMLResponse(_render_landing_page(request))


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
    settings: Settings = Depends(get_settings_dep),
) -> PublicOrderCreated:
    try:
        payment_service = _payment_service(settings)
    except PaymentError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"payment provider unavailable: {exc}",
        ) from exc

    try:
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            order = create_public_order(dao, payload)
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
        raise HTTPException(
            status_code=503,
            detail=f"payment checkout unavailable: {exc}",
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
    return _render_simulated_payment_page(payment_id, settings, provider_slug="alipay-sim")


@router.post("/pay/alipay-sim/{payment_id}/complete", include_in_schema=False)
def complete_alipay_sim_payment(
    payment_id: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    _assert_simulated_payment_routes_allowed(settings)
    return _complete_simulated_payment(payment_id, settings, provider_slug="alipay-sim")


@router.get("/portal/payment-return", include_in_schema=False)
def payment_return_page(
    payment_id: str, settings: Settings = Depends(get_settings_dep)
) -> RedirectResponse:
    service = _payment_service(settings)
    payment = service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    portal_token = issue_portal_token(payment.order_id, settings.portal_token_secret)
    return RedirectResponse(
        url=f"/portal/{portal_token}/payment-success", status_code=303
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
            order, token, intake.payload if intake else {}, context["stage"]
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
        "storage_path": str(target),
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
        record = intake_store.save(
            order_id=order.id,
            payload=payload.model_dump(),
            submit=payload.mode == "submit",
        )
    finally:
        intake_store.close()

    updates: dict[str, Any] = {}
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
    )


@router.get("/portal/{token}/deletion-request", include_in_schema=False)
def deletion_request_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    return HTMLResponse(_render_deletion_request_page(token, order))


@router.post("/portal/{token}/deletion-request", response_model=DeletionRequestCreated)
def submit_deletion_request(
    token: str,
    payload: DeletionRequestCreate,
    settings: Settings = Depends(get_settings_dep),
) -> DeletionRequestCreated:
    order = _resolve_order_from_token(token, settings)
    _log_deletion_request(order.id, payload, settings)
    return DeletionRequestCreated(
        order_id=order.id,
        request_logged=True,
        next_step="客服将在核验后处理删除申请",
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


@router.get("/portal/{token}/status", include_in_schema=False)
def order_status_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> HTMLResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    return HTMLResponse(_render_status_page(token, context))


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
        (Path(settings.portal_upload_dir).resolve().parent / "order_artifacts").resolve(),
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
    elif payment is not None and payment.status == "failed":
        stage = "payment_failed"
    elif payment is None or payment.status == "pending":
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
    if intake is not None:
        attachment_items = [
            item
            for item in list((intake.payload or {}).get("attachments") or [])
            if isinstance(item, dict)
        ]
        attachment_count = len(attachment_items)
        intake_summary = {
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
    }


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


@router.get("/privacy", include_in_schema=False)
def privacy_page(token: str | None = None) -> HTMLResponse:
    body = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        "<title>隐私政策</title>"
        "<link rel='stylesheet' href='/static/portal-ui.css' />"
        '<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}.wrap{max-width:920px;margin:0 auto;display:grid;gap:18px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#dff7f1;color:#0f766e;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.lead{color:#5b6b88;line-height:1.8}.checklist{margin:0;padding-left:18px;color:#5b6b88;line-height:1.8}</style></head>'
        "<body><main class='wrap'>"
        "<section class='panel'><span class='eyebrow'>隐私说明</span><h1>隐私政策</h1>"
        "<p class='lead'>我们只收集下单、资料填写、支付与交付所需的最小信息，用于志愿服务流程，不用于营销出售或无关用途。</p></section>"
        "<section class='panel'><h2>你可以预期什么</h2><ul class='checklist'><li>支付前只收必要下单信息</li><li>详细资料在支付后通过资料向导分步补充</li><li>隐私政策、服务说明与删除申请入口全程可见</li><li>如需撤回资料或申请删除，可通过删除申请入口提交请求</li></ul>"
        + _render_footer_links(token)
        + "</section></main></body></html>"
    )
    return HTMLResponse(body)


@router.get("/service-terms", include_in_schema=False)
def service_terms_page(token: str | None = None) -> HTMLResponse:
    body = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        "<title>服务说明与免责声明</title>"
        "<link rel='stylesheet' href='/static/portal-ui.css' />"
        '<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}.wrap{max-width:920px;margin:0 auto;display:grid;gap:18px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef5ff;color:#1f6feb;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.lead{color:#5b6b88;line-height:1.8}.checklist{margin:0;padding-left:18px;color:#5b6b88;line-height:1.8}</style></head>'
        "<body><main class='wrap'>"
        "<section class='panel'><span class='eyebrow'>服务边界</span><h1>服务说明与免责声明</h1>"
        "<p class='lead'>本服务提供志愿填报辅助建议、方案审计与交付支持，不承诺录取结果；提交资料前请确认监护人与考生已知情。</p></section>"
        "<section class='panel'><h2>下单前请了解</h2><ul class='checklist'><li>我们优先帮助你审计现有方案与风险点</li><li>支付后可继续补充详细资料与附件</li><li>交付状态、通知与报告入口会在站内持续更新</li><li>如需撤回资料或删除交付物，可通过删除申请入口提交请求</li></ul>"
        + _render_footer_links(token)
        + "</section></main></body></html>"
    )
    return HTMLResponse(body)


@router.get("/deletion-policy", include_in_schema=False)
def deletion_policy_page() -> HTMLResponse:
    body = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        "<title>删除申请 / 数据删除说明</title>"
        "<link rel='stylesheet' href='/static/portal-ui.css' />"
        '<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}.wrap{max-width:920px;margin:0 auto;display:grid;gap:18px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#fff7e6;color:#8a5a00;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.lead{color:#5b6b88;line-height:1.8}.checklist{margin:0;padding-left:18px;color:#5b6b88;line-height:1.8}</style></head>'
        "<body><main class='wrap'>"
        "<section class='panel'><span class='eyebrow'>数据删除</span><h1>删除申请 / 数据删除说明</h1>"
        "<p class='lead'>如需申请删除订单资料、附件或交付物，可在支付后的 Portal 中提交删除申请；系统会保留必要的审计记录，并由人工核验后处理。</p></section>"
        "<section class='panel'><h2>你可以怎么做</h2><ul class='checklist'><li>在 Portal 中提交删除申请</li><li>填写申请人姓名、联系方式、删除范围与原因</li><li>确认监护人已知情并同意发起删除申请</li><li>处理结果会回到站内状态链路中查看</li></ul>"
        + _render_footer_links()
        + "</section></main></body></html>"
    )
    return HTMLResponse(body)


def _render_landing_page(request: Request) -> str:
    query = dict(request.query_params)
    consult_text = escape(str(query.get("consult") or ""))
    consult_province = escape(str(query.get("province") or ""))
    consult_score = escape(str(query.get("score") or ""))
    consult_goal = escape(str(query.get("goal") or ""))
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
      .wrap {{ max-width: 1180px; margin: 0 auto; padding: 40px 20px 72px; }}
      .hero {{ display: grid; grid-template-columns: minmax(0, 1.22fr) minmax(340px, .78fr); gap: 32px; align-items: stretch; }}
      .hero-copy {{ color: #ecf4ff; padding: 40px 8px 18px 0; }}
      .eyebrow {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(223,247,241,.12); border: 1px solid rgba(223,247,241,.24); color: #c9fff3; font-size: 13px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
      h1 {{ margin: 18px 0 14px; max-width: 760px; font-size: clamp(36px, 6vw, 56px); line-height: 1.04; letter-spacing: -0.04em; }}
      .sub {{ margin: 0; max-width: 700px; color: #b8c8e4; line-height: 1.82; font-size: 17px; }}
      .hero-actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; align-items: center; }}
      .consult-card {{ margin-top: 18px; padding: 18px; border-radius: 18px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); }}
      .consult-card h2 {{ margin: 0 0 8px; font-size: 18px; color: #fff; }}
      .consult-grid {{ display:grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap:10px; }}
      .consult-field {{ display:flex; flex-direction:column; gap:6px; }}
      .consult-field label {{ color:#d9e7ff; font-size:12px; font-weight:600; }}
      .consult-field input, .consult-field textarea {{ width:100%; padding:11px 12px; border-radius:12px; border:1px solid rgba(255,255,255,.18); background: rgba(255,255,255,.96); color:#142235; font-size:14px; }}
      .consult-field textarea {{ min-height:74px; resize:vertical; }}
      .consult-actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }}
      .consult-privacy {{ margin: 10px 0 0; padding: 10px 12px; border-radius: 12px; background: rgba(223,247,241,.10); border: 1px solid rgba(223,247,241,.30); color: #d9e7ff; font-size: 12.5px; line-height: 1.65; }}
      .consult-privacy strong {{ color: #c9fff3; font-weight: 700; }}
      .consult-privacy-tail {{ margin: 10px 0 0; color: #8fb0df; font-size: 12px; line-height: 1.6; }}
      .btn {{ display: inline-flex; align-items: center; justify-content: center; min-height: 46px; padding: 0 18px; border-radius: 14px; text-decoration: none; font-weight: 700; transition: .18s ease; }}
      .btn-primary {{ min-height: 54px; padding: 0 28px; font-size: 17px; background: linear-gradient(135deg,#2d7cff,#0f4fd6); color: #fff; box-shadow: 0 22px 40px rgba(31,111,235,.42), inset 0 1px 0 rgba(255,255,255,.18); letter-spacing: .01em; }}
      .btn-primary:hover {{ background: linear-gradient(135deg,#276fe7,#0d45bf); transform: translateY(-1px); }}
      .btn-secondary {{ background: rgba(255,255,255,.08); color: #fff; border: 1px solid rgba(255,255,255,.18); min-height: 44px; padding: 0 14px; font-size: 14px; }}
      .btn-secondary:hover {{ background: rgba(255,255,255,.14); }}
      .btn-text {{ color:#cfe0ff; padding: 0 6px; min-height: 44px; font-size: 14px; text-decoration: underline; text-underline-offset: 4px; }}
      .hero-note {{ margin-top: 12px; color:#8fb0df; font-size:13px; line-height:1.6; }}
      .hero-risk-band {{ display:grid; gap:6px; margin-bottom:16px; padding:12px 14px; border-radius:14px; background: rgba(255,255,255,.7); border:1px solid #f3d49f; }}
      .hero-risk-band strong {{ font-size:14px; color:#7a5a00; }}
      .hero-risk-band span {{ color:#7a5c24; font-size:13px; line-height:1.55; }}
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
    <main class=\"wrap\">
      <section class=\"hero\">
        <div class=\"hero-copy\">
          <div class=\"eyebrow\">新高考志愿填报 · 志愿决策支持</div>
          <h1>高考志愿填报智能规划服务</h1>
          <p class=\"sub\">先审计现有志愿方案，再判断是否踩线、扎堆或梯度失衡，再决定要不要进入完整规划。先完成线上下单，再进入资料向导补充详细信息，后续可在站内查看报告与交付进度。</p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="#consult-box">立即咨询</a>
            <a class="btn btn-primary" href="/pricing">查看套餐</a>
            <a class="btn btn-text" href="#service-flow">了解服务流程 →</a>
          </div>
          <p class="hero-note">提交省份、分数、目标后，我们先判断你的方案是否需要复核。复核现有方案本身免费；新方案生成与深度辅导在支付后启动。</p>
          <div class="consult-card" id="consult-box">
            <h2>告诉我们你的基本情况</h2>
            <p class="hero-note" style="margin-top:0;">我们先判断你的现有方案是否需要复核，并说明后续可走的步骤。复核本身免费；新方案生成与深度辅导在支付后启动。</p>
            <p class="consult-privacy" aria-label="隐私说明">🔒 这些输入只用于判断要不要复核你的方案，<strong>不会留底、不会用于生成方案、不会发邮件推销</strong>。如果你决定不进入付费方案，提交的资料不会保存到我们的数据库。</p>
            <form action="/pricing" method="get">
              <div class="consult-grid">
                <div class="consult-field"><label>考试省份</label><input name="province" value="{consult_province}" placeholder="例如：湖南" /></div>
                <div class="consult-field"><label>分数 / 位次</label><input name="score" value="{consult_score}" placeholder="例如：578 / 12034" /></div>
              </div>
              <div class="consult-field" style="margin-top:10px;"><label>当前目标</label><input name="goal" value="{consult_goal}" placeholder="例如：先复核现有方案" /></div>
              <div class="consult-field" style="margin-top:10px;"><label>补充说明</label><textarea name="consult" placeholder="例如：已有一版方案，想先看有没有明显风险">{consult_text}</textarea></div>
              <div class="consult-actions">
                <button class="btn btn-primary" type="submit">获取复核与推荐</button>
                <a class="btn btn-secondary" href="/pricing">直接看付费套餐</a>
              </div>
            </form>
            <p class="consult-privacy-tail">不会收到营销短信，提交后你也可以随时要求删除已填资料。</p>
          </div>
          <div class="hero-trust">
            <article class="hero-trust-item"><strong>复核免费 / 方案付费</strong><span>免费帮你审现有方案的风险；新方案生成和深度辅导在支付后启动。</span></article>
            <article class="hero-trust-item"><strong>风险重点可解释</strong><span>重点识别踩线、扎堆、梯度失衡和结构异常，不只给结果。</span></article>
            <article class="hero-trust-item"><strong>进度站内可查</strong><span>资料、通知、报告、下载入口都能在站内持续追踪。</span></article>
            <article class="hero-trust-item"><strong>隐私与删除入口可见</strong><span>隐私政策、服务说明与删除申请入口全程可访问。</span></article>
          </div>
          <div class="hero-divider"></div>
          <div class="hero-points">
            <article class="point lead"><strong>先把方案看清，再决定要不要重做</strong><span>如果你已经拿到一版方案，先做免费复核看是否踩线、扎堆、梯度失衡，再决定是否进入付费的完整规划。</span></article>
            <article class="point"><strong>重点可解释</strong><span>不只给一份结论，更说明为什么这样选、需要确认什么。</span></article>
            <article class="point"><strong>资料、通知、报告都在站内</strong><span>支付后只需按提示补充资料，状态、通知、报告、下载入口全部站内可查。</span></article>
          </div>
        </div>
        <aside class="hero-panel">
          <div class="hero-risk-band"><strong>最常见的不是“不会选”，而是先选错方向</strong><span>我们优先帮你筛出踩线、扎堆、梯度失衡这三类最容易带来后悔成本的风险。</span></div>
          <h2>我们先把现有方案看明白</h2>
          <p>不让你在海量院校、专业、城市与预算之间盲目来回切换，先审计现有方案的风险与结构，再决定是否进入更完整的志愿规划。</p>
          <div class="metric-list">
            <div class="metric"><strong>资料采集更克制</strong><span>首屏只收真正影响下单的最小信息，详细资料支付后分步完成。</span></div>
            <div class="metric"><strong>方案表达更可读</strong><span>优先解释为什么这样选，而不是堆给用户一页难消化的数据。</span></div>
            <div class="metric"><strong>交付链路更透明</strong><span>资料、通知、报告、下载入口都放在同一条可追踪用户路径里。</span></div>
          </div>
        </aside>
      </section>

      <section class=\"section\">
        <h2>为什么选择我们</h2>
        <p class=\"section-intro\">高考志愿填报不是只看一个分数，而是要在时间、信息、风险和沟通成本之间做平衡。我们的特点不是只“生成方案”，而是先帮你审计现有方案、识别扎堆和踩线风险，再决定是否进入更完整的规划与交付。</p>
        <div class=\"grid-3\">
          <article class=\"card\">
          <span class=\"tag\">方案审计</span>
          <h3>先判断现有方案值不值得继续</h3>
          <p>如果你已经拿到老师、机构或 AI 给出的方案，我们会先审计是否踩线、是否扎堆、是否存在明显结构风险，再决定下一步。</p>
          </article>
          <article class=\"card\">
            <span class=\"tag\">风险沟通</span>
            <h3>把风险解释清楚</h3>
            <p>不只输出结果，还会说明冲稳保梯度、可能踩线的位置，以及需要重点确认的选择风险。</p>
          </article>
          <article class=\"card\">
            <span class=\"tag\">交付透明</span>
            <h3>过程可追踪</h3>
            <p>从下单、资料填写、通知到报告查看，都能在站内看到当前进度，减少反复追问。</p>
          </article>
        </div>
      </section>

      <section id="service-flow" class="section">
        <h2>服务流程</h2>
        <p class="section-intro">让用户知道每一步会发生什么，比空泛地说“智能系统已接入”更重要。复核免费，方案生成和深度辅导需付费。</p>
        <div class="flow">
          <article class="flow-step"><strong>01</strong><h3>先判断入口</h3><p>判断你需要的是方案复核（免费）还是完整方案 / 深度辅导（付费）。</p></article>
          <article class="flow-step"><strong>02</strong><h3>确认下单</h3><p>选完整方案或深度辅导时，先填写考生姓名、手机号等最小信息后再支付。</p></article>
          <article class="flow-step"><strong>03</strong><h3>补充资料</h3><p>支付成功后进入资料向导，分步提交分数、位次、偏好与已有方案附件。</p></article>
          <article class="flow-step"><strong>04</strong><h3>查看交付</h3><p>在站内追踪状态、查看通知，并在交付就绪后在线阅读或下载 PDF。</p></article>
        </div>
      </section>

      <section class=\"section\">
        <h2>基础信任说明</h2>
        <div class=\"trust\">
          <article class=\"trust-item\"><strong>资料最小化采集</strong><span>支付前只收必要信息，详细资料在支付后按步骤补充。</span></article>
          <article class=\"trust-item\"><strong>隐私与删除入口可见</strong><span>隐私政策、服务说明和删除申请入口在全站统一可访问。</span></article>
          <article class=\"trust-item\"><strong>交付状态有记录</strong><span>资料提交、通知、报告状态都会在用户可见页面持续更新。</span></article>
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
  </body>
</html>
"""


def _render_pricing_page(request: Request) -> str:
    query = dict(request.query_params)
    consult_text = str(query.get("consult") or "").strip()
    province = str(query.get("province") or "").strip()
    score = str(query.get("score") or "").strip()
    goal = str(query.get("goal") or "").strip()
    recommendation_title = "你可以先从 99 元完整志愿方案开始"
    recommendation_body = "如果你没有现成方案，直接进入完整规划最省时间；如果已有方案，再先审计。"
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
    <main class=\"wrap\">
      <section class="hero">
        <div class="panel">
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
          <div class="price">¥49<small>/ 次</small></div>
          <p class="desc">适合已经拿到其他 AI 志愿方案，想先判断方案是否踩线、是否扎堆、是否存在明显风险的家庭。审核只针对你提供的现有方案，不会重新生成志愿表。</p>
          <ul class="feature-list">
            <li>针对你提供的现有方案做风险复核</li>
            <li>聚焦风险点、冲稳保结构与明显异常</li>
            <li>给出是否值得继续深做的判断</li>
            <li>不重新生成志愿表（生成需选 99 元）</li>
          </ul>
          <a class="button secondary" href="/checkout/audit">先做付费审核</a>
        </article>

        <article class="card recommended" data-package="standard">
          <span class="badge">推荐方案</span>
          <div class="eyebrow">生成 / 完整</div>
          <h2>99元 完整志愿方案</h2>
          <div class="price">¥99<small>/ 单</small></div>
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
          <div class="price">¥199<small>/ 单</small></div>
          <p class="desc">适合志愿范围复杂、目标城市/专业冲突较大，或需要更多人工沟通、反复修订和深度解释的家庭。在 99 元完整方案基础上提供多轮修订和深度解释。</p>
          <ul class="feature-list">
            <li>适合目标复杂或分歧较大的家庭</li>
            <li>包含 99 元完整方案的所有交付</li>
            <li>留出多轮沟通与补充说明空间</li>
            <li>更强调过程解释与决策支持</li>
          </ul>
          <a class="button secondary" href="/checkout/premium">了解深度辅导</a>
        </article>
      </section>

      <section class="trust-band">
        <article class="trust-item"><strong>站内可追踪</strong><span>下单后可以查看资料提交、通知记录和交付状态，不需要反复追问进度。</span></article>
        <article class="trust-item"><strong>资料入口清晰</strong><span>支付前只收必要下单信息，详细资料在支付后通过资料向导分步补充。</span></article>
        <article class="trust-item"><strong>复核免费 / 方案付费</strong><span>还没决定？回到首页 <a href="/#consult-box">先做一次免费复核</a>，再决定要不要进入付费方案。</span></article>
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
  </body>
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
    <main class=\"wrap\">
      <header class=\"header\">
        <span class=\"eyebrow\">在线下单</span>
        <h1>{escape(service_label)}</h1>
        <p class=\"lead\">{escape(service_desc)} 现在先确认联系人与考生基础信息；支付成功后，再进入资料向导补充分数、位次、偏好和已有方案附件。</p>
      </header>

      <section class=\"layout\">
        <section class=\"panel form-panel\">
          <h2>填写下单信息</h2>
          <p class=\"helper\">当前这一步只收会影响下单与后续联系的必要信息，不要求你一次性填完整个长表单。</p>
          <div class=\"form-proof\">
            <article class=\"form-proof-item\"><strong>先下单再补资料</strong><span>先把关键联系信息确认下来，再进入资料向导补充分数、位次和偏好。</span></article>
            <article class=\"form-proof-item\"><strong>状态站内可追踪</strong><span>支付、通知、交付状态都能在站内持续查看，不必反复追问进度。</span></article>
            <article class=\"form-proof-item\"><strong>隐私入口始终可见</strong><span>隐私政策、服务说明与删除申请入口在这条链路上持续可访问。</span></article>
          </div>
          <div class=\"trust-strip\">
            <article class=\"trust-card\"><strong>步骤更短</strong><span>先支付，再补详细资料。</span></article>
            <article class=\"trust-card\"><strong>进度可追踪</strong><span>资料、通知和交付状态都可站内查看。</span></article>
            <article class=\"trust-card\"><strong>入口可核查</strong><span>隐私政策、服务说明、删除申请入口全程可见。</span></article>
          </div>
          <form id=\"checkout-form\">
            <div class=\"grid\">
              <div class=\"field\">
                <label>考生姓名<span class=\"required\">*</span></label>
                <input name=\"candidate_name\" required maxlength=\"32\" placeholder=\"请输入考生姓名\" />
                <div class=\"error\" data-error=\"candidate_name\"></div>
              </div>
              <div class=\"field\">
                <label>手机号<span class=\"required\">*</span></label>
                <input name=\"customer_phone\" required inputmode=\"tel\" maxlength=\"20\" placeholder=\"请输入便于联系的手机号\" />
                <div class=\"error\" data-error=\"customer_phone\"></div>
              </div>
            </div>
            <div class=\"grid\">
              <div class=\"field\">
                <label>称呼</label>
                <input name=\"customer_name\" maxlength=\"32\" placeholder=\"可选，例如：张同学 / 张家长\" />
              </div>
              <div class=\"field\">
                <label>邮箱（接收通知）</label>
                <input name=\"customer_email\" type=\"email\" maxlength=\"120\" placeholder=\"可选，用于接收交付提醒\" />
              </div>
            </div>
            <div class=\"grid\">
              <div class=\"field\">
                <label>考试省份</label>
                <select name=\"candidate_province\">{province_html}</select>
                <div class=\"hint\">如果你暂时还没决定，也可以支付后在资料向导中补充。</div>
              </div>
              <div class=\"field\">
                <label>备注</label>
                <textarea name=\"notes\" maxlength=\"500\" placeholder=\"可选，例如希望重点关注的城市、专业或顾虑\"></textarea>
              </div>
            </div>
            <div class=\"actions\">
              <button type=\"submit\" id=\"submit-btn\">立即支付 ¥{amount / 100:.0f}</button>
              <span class=\"hint\">提交后会进入支付与资料完善流程。</span>
            </div>
          </form>
          <p id=\"result\"></p>
          <div class=\"service-note\">服务保障：支付后可进入资料向导继续补充详细信息；提交资料后，后续状态、通知与交付入口都将在站内持续更新。</div>
          {_render_footer_links()}
        </section>

        <aside class=\"panel summary\">
          <h2>订单摘要</h2>
          <p>你当前选择的是 <strong>{escape(service_label)}</strong>。这一步先确认下单人与考生基础信息，支付成功后再继续补完整资料。</p>
          <div class=\"summary-badges\">
            <div class=\"summary-badge\"><strong>当前建议</strong><span>如果你已经有现成方案，49 元审核版适合先判断风险；99 元适合直接进入完整线上规划。</span></div>
            <div class=\"summary-badge\"><strong>交付方式</strong><span>站内资料向导、通知状态、在线报告与 PDF 下载入口。</span></div>
          </div>
          <div class=\"summary-list\">
            <div class=\"summary-item\"><strong>适合谁</strong><span>{escape(service_desc)}</span></div>
            <div class=\"summary-item\"><strong>你会得到什么</strong><span>站内资料向导、通知状态、报告在线查看和 PDF 下载入口。</span></div>
            <div class=\"summary-item\"><strong>下单后下一步</strong><span>支付成功 → 进入资料向导 → 查看状态与交付。</span></div>
          </div>
          <div class=\"price-box\">
            <div>
              <div class=\"label\">当前应付</div>
              <div class=\"amount\">¥{amount / 100:.0f}</div>
            </div>
            <div class=\"label\">完成支付后即可继续补完整资料</div>
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
  </body>
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
  <body>
    <main class=\"wrap\">
      <section class=\"panel\">
        <span class=\"eyebrow\">支付成功</span>
        <h1>订单已创建，下一步继续补资料</h1>
        <p class=\"lead\">支付状态：{payment_status}。{escape(next_hint)}</p>
        <div class=\"hero-actions\">
          <a class=\"btn btn-primary\" href=\"{next_href}\">{escape(next_action)}</a>
          <a class=\"btn btn-secondary\" href=\"/portal/{escape(token)}/status\">查看订单进度</a>
        </div>
      </section>
      <section class=\"panel\">
        <h2 style=\"margin:0 0 10px;\">你现在要做什么</h2>
        <div class=\"grid\">
          <div class=\"item\"><strong>补充基础信息</strong><span class=\"meta\">先填分数、位次、选科。</span></div>
          <div class=\"item\"><strong>填写偏好目标</strong><span class=\"meta\">补充城市、专业或院校偏好。</span></div>
          <div class=\"item\"><strong>持续查看进度</strong><span class=\"meta\">资料提交后可继续查看状态、通知和报告。</span></div>
        </div>
      </section>
    </main>
  </body>
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
  <head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>{escape(title)}</title></head>
  <body style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fb;padding:24px;\">
    <main style=\"max-width:640px;margin:0 auto;background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;\">
      <h1>{escape(title)}</h1>
      <p>订单支付单号：{escape(payment_id)}</p>
      <p>支付金额：¥{amount_cents / 100:.2f}</p>
      <form method=\"post\" action=\"/pay/{escape(provider_slug)}/{escape(payment_id)}/complete\">
        <button type=\"submit\" style=\"border:none;border-radius:12px;background:#1f6feb;color:#fff;font-weight:700;padding:12px 18px;cursor:pointer;\">{escape(submit_label)}</button>
      </form>
    </main>
  </body>
</html>
"""


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
    return RedirectResponse(url=f"/portal/{portal_token}/payment-success", status_code=303)


def _render_info_page(
    order: Order, token: str, payload: dict[str, Any], stage: str
) -> str:
    consent_version = str(payload.get("consent_version") or "t12-web-mvp-v1")
    consent_scope = str(payload.get("consent_scope") or "web-self-service-order-intake")
    privacy_checked = "checked" if payload.get("privacy_accepted") else ""
    service_terms_checked = "checked" if payload.get("service_terms_accepted") else ""
    guardian_checked = "checked" if payload.get("guardian_confirmed") else ""
    attachments = payload.get("attachments") or []
    missing_items: list[str] = []
    if not payload.get("candidate_score"):
        missing_items.append("分数")
    if not payload.get("candidate_rank"):
        missing_items.append("位次")
    if not payload.get("candidate_subjects"):
        missing_items.append("选科")
    if not payload.get("target_cities") and not payload.get("target_majors") and not payload.get("university_preferences"):
        missing_items.append("至少一个偏好目标")
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
  <body>
    <main class=\"wrap\">
      <section class=\"hero\">
        <section class=\"panel main-panel\">
          <span class=\"eyebrow\">资料填写向导</span>
          <h1>考生资料填写</h1>
          <p class=\"helper\" style=\"margin:8px 0 0;\">资料填写向导</p>
          <p class=\"lead\">支付完成后，请按向导逐步补充分数、位次、偏好与已有方案信息。我们会把这份资料作为后续方案分析与交付的基础。</p>
          <section class=\"progress-box\"><strong>当前还需要补充：</strong><span>{escape("、".join(missing_items) or "资料已基本完整，可以继续提交")}</span></section>

          <section class=\"wizard-head\">
            <h2>四步资料向导</h2>
            <p>你不需要一次性完成所有内容。可以先保存草稿，再回来继续补充；最后一步同时完成协议确认与提交。</p>
            <ol class=\"wizard-steps\">
              <li data-step-badge=\"1\">基础信息</li>
              <li data-step-badge=\"2\">偏好与目标</li>
              <li data-step-badge=\"3\">已有方案与附件</li>
              <li data-step-badge=\"4\">确认并提交</li>
            </ol>
          </section>

          <form id=\"intake-form\">
            <section class=\"step-panel\" data-step=\"1\">
              <h3>基础信息</h3>
              <p>先确认最影响志愿方案判断的基本数据：分数、位次、选科。</p>
              <div class=\"field-grid\">
                <div class=\"field\"><label>高考分数</label><input name=\"candidate_score\" value=\"{escape(str(payload.get("candidate_score") or ""))}\" /><span class=\"helper\">如暂未最终确认，也可先保存草稿。</span></div>
                <div class=\"field\"><label>位次</label><input name=\"candidate_rank\" value=\"{escape(str(payload.get("candidate_rank") or ""))}\" /><span class=\"helper\">建议填写与成绩单一致的最新位次。</span></div>
              </div>
              <div class=\"field\"><label>选科（逗号分隔）</label><input name=\"candidate_subjects\" value=\"{escape(",".join(payload.get("candidate_subjects") or []))}\" /><span class=\"helper\">例如：物理,化学,生物</span></div>
            </section>

            <section class=\"step-panel\" data-step=\"2\" style=\"display:none;\">
              <h3>偏好与目标</h3>
              <p>告诉我们你更看重什么，后续方案会围绕这些目标来解释选择逻辑。</p>
              <div class=\"field\"><label>兴趣方向</label><input name=\"candidate_interests\" value=\"{escape(str(payload.get("candidate_interests") or ""))}\" /></div>
              <div class=\"field-grid\">
                <div class=\"field\"><label>目标城市（逗号分隔）</label><input name=\"target_cities\" value=\"{escape(",".join(payload.get("target_cities") or []))}\" /></div>
                <div class=\"field\"><label>目标专业（逗号分隔）</label><input name=\"target_majors\" value=\"{escape(",".join(payload.get("target_majors") or []))}\" /></div>
              </div>
              <div class=\"field\"><label>院校偏好说明</label><textarea name=\"university_preferences\">{escape(str(payload.get("university_preferences") or ""))}</textarea></div>
            </section>

            <section class=\"step-panel\" data-step=\"3\" style=\"display:none;\">
              <h3>已有方案与附件</h3>
              <p>如果你已经拿到其他平台、老师或 AI 生成的方案，可以在这里上传并说明担心点。</p>
              <div class=\"field\"><label>已有方案说明</label><textarea name=\"existing_plan_summary\">{escape(str(payload.get("existing_plan_summary") or ""))}</textarea></div>
              <div class=\"field\"><label>备注</label><textarea name=\"guardian_notes\">{escape(str(payload.get("guardian_notes") or ""))}</textarea></div>
              <section class=\"upload-box\">
                <h4 style=\"margin:0 0 10px; font-size:18px;\">已上传附件</h4>
                <p class=\"helper\" style=\"margin:0 0 12px;\">支持继续补充方案附件、成绩截图或其他参考资料。</p>
                <div id=\"attachment-panel\">
                  <input type=\"file\" name=\"files\" multiple />
                  <div class=\"actions\" style=\"margin-top:12px;\">
                    <button type=\"button\" onclick=\"uploadAttachment()\">上传方案与资料附件</button>
                  </div>
                </div>
                <ul class=\"attachment-list\">{attachments_html}</ul>
              </section>
            </section>

            <section class=\"step-panel\" data-step=\"4\" style=\"display:none;\">
              <h3>确认并提交</h3>
              <p>请确认监护人已知情并同意将资料用于志愿填报服务，并在下方快速复核关键信息后提交。</p>
              <input type=\"hidden\" name=\"consent_version\" value=\"{escape(consent_version)}\" />
              <input type=\"hidden\" name=\"consent_scope\" value=\"{escape(consent_scope)}\" />
              <div class=\"check-list\">
                <label><input type=\"checkbox\" name=\"privacy_accepted\" {privacy_checked} /> <span>我已阅读并同意隐私政策草案</span></label>
                <label><input type=\"checkbox\" name=\"service_terms_accepted\" {service_terms_checked} /> <span>我已阅读并同意服务说明与免责声明</span></label>
                <label><input type=\"checkbox\" name=\"guardian_confirmed\" {guardian_checked} /> <span>我确认监护人已知情并同意提交资料</span></label>
              </div>
              <div class=\"compliance-note\">当前资料状态会随提交结果同步更新；未勾选必要同意项时，系统不会进入正式处理阶段。</div>
              <div id=\"confirm-summary\" class=\"summary-box\"></div>
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
          <span class=\"status-pill\">{escape(stage_title)}</span>
          <p style=\"margin-top:12px;\">{escape(stage_subtitle)}</p>
          <div class=\"status-list\">
            <div class=\"status-item\"><strong>订单号</strong><span>{escape(order.id)}</span></div>
            <div class=\"status-item\"><strong>当前服务版本</strong><span>{escape(order.service_version)}</span></div>
            <div class=\"status-item\"><strong>你可以怎么做</strong><span>保存草稿、继续补资料，或在最后一步统一提交进入后续处理。</span></div>
          </div>
          <div class=\"compliance-note\">提交资料即表示：监护人已知情并同意将考生资料用于志愿填报服务；当前版本号：{escape(consent_version)}</div>
        </aside>
      </section>
    </main>
    <script>
      let currentStep = 1;
      const totalSteps = 4;

      function collectPayload(mode) {{
        const form = new FormData(document.getElementById('intake-form'));
        const subjects = String(form.get('candidate_subjects') || '').split(',').map(s => s.trim()).filter(Boolean);
        const targetCities = String(form.get('target_cities') || '').split(',').map(s => s.trim()).filter(Boolean);
        const targetMajors = String(form.get('target_majors') || '').split(',').map(s => s.trim()).filter(Boolean);
        return {{
          mode,
          candidate_score: form.get('candidate_score') ? Number(form.get('candidate_score')) : null,
          candidate_rank: form.get('candidate_rank') ? Number(form.get('candidate_rank')) : null,
          candidate_subjects: subjects,
          candidate_interests: form.get('candidate_interests') || null,
          target_cities: targetCities,
          target_majors: targetMajors,
          university_preferences: form.get('university_preferences') || null,
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
          ['高考分数', payload.candidate_score ?? '待补充'],
          ['位次', payload.candidate_rank ?? '待补充'],
          ['选科', (payload.candidate_subjects || []).join('、') || '待补充'],
          ['兴趣方向', payload.candidate_interests || '待补充'],
          ['目标城市', (payload.target_cities || []).join('、') || '待补充'],
          ['目标专业', (payload.target_majors || []).join('、') || '待补充'],
          ['院校偏好', payload.university_preferences || '待补充'],
          ['已有方案说明', payload.existing_plan_summary || '待补充'],
        ];
        document.getElementById('confirm-summary').innerHTML = list.map(([label, value]) => `<div style="padding:8px 0;border-bottom:1px solid #e5edf7;"><strong>${{label}}：</strong><span>${{String(value)}}</span></div>`).join('');
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

      async function submitIntake(mode) {{
        const payload = collectPayload(mode);
        const resultNode = document.getElementById('result');
        resultNode.textContent = mode === 'draft' ? '正在保存草稿…' : '正在提交资料…';
        const resp = await fetch('/portal/{escape(token)}/info', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
        }});
        const body = await resp.json();
        if (!resp.ok) {{
          resultNode.textContent = body.detail || body.message || '提交失败，请检查资料后重试。';
          return;
        }}
        resultNode.textContent = mode === 'draft' ? '草稿已保存，可稍后继续补充。' : '资料提交成功，正在进入订单状态页…';
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
  </body>
</html>
"""


def _render_status_page(token: str, context: dict[str, Any]) -> str:
    order = context["order"]
    stage = str(context["stage"])
    primary_action_label = "继续补充资料"
    primary_action_href = f"/portal/{escape(token)}/info"
    if stage in {"processing", "info_submitted"}:
        primary_action_label = "查看当前进度"
        primary_action_href = f"/portal/{escape(token)}/status#delivery-status"
    elif stage in {"report_ready", "completed"}:
        if context["report_html_ready"]:
            primary_action_label = "查看报告"
            primary_action_href = f"/portal/{escape(token)}/report"
        else:
            primary_action_label = "下载 PDF"
            primary_action_href = f"/portal/{escape(token)}/report.pdf"
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
        <p class=\"meta\">发送时间：{sent_at}</p>
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
      <section class=\"panel\">
        <h2>当前资料摘要</h2>
        <ul class=\"summary-list\">{"".join(summary_items)}</ul>
        <h3>已上传附件</h3>
        <ul class=\"attachment-list\">{attachment_html}</ul>
      </section>"""
    payment_status = escape(str(context.get("payment_status") or "pending"))
    delivery_html = f"""
      <section class=\"panel\">
        <h2>支付与交付状态</h2>
        <div class=\"status-grid\">
          <div class=\"status-item\"><strong>支付状态</strong><span>{payment_status}</span></div>
          <div class=\"status-item\"><strong>资料状态</strong><span>{escape(context["stage_title"])}</span></div>
          <div class=\"status-item\"><strong>HTML 报告</strong><span>{"已就绪" if context["report_html_ready"] else "未就绪"}</span></div>
          <div class=\"status-item\"><strong>PDF 报告</strong><span>{"已就绪" if context["report_pdf_ready"] else "未就绪"}</span></div>
          <div class=\"status-item\"><strong>交付阶段</strong><span>{escape(context["stage"])}</span></div>
        </div>
      </section>"""
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
  <body>
    <main class=\"wrap\">
      <section class=\"hero\">
        <section class=\"panel\">
          <span class=\"eyebrow\">订单进度总览</span>
          <h1>{escape(context["stage_title"])}</h1>
          <p class=\"lead\">{escape(context["stage_subtitle"])}</p>
          <span class=\"stage-pill\">当前阶段：{escape(context["stage"])}</span>
          <div class=\"hero-actions\">
            <a class=\"hero-btn hero-btn-primary\" href=\"{primary_action_href}\">{escape(primary_action_label)}</a>
            <a class=\"hero-btn hero-btn-secondary\" href=\"/portal/{escape(token)}/info\">填写 / 更新资料</a>
          </div>
          <div class=\"hero-meta\">
            <div class=\"hero-meta-item\"><strong>订单号</strong><span>{escape(order.id)}</span></div>
            <div class=\"hero-meta-item\"><strong>服务版本</strong><span>{escape(order.service_version)}</span></div>
            <div class=\"hero-meta-item\"><strong>当前订单状态</strong><span>{escape(order.status)}</span></div>
          </div>
        </section>
        <aside class=\"panel\">
          <h2>下一步建议</h2>
          <ul class=\"action-list\">
            <li>如资料还未完善，可返回资料页继续补充。</li>
            <li>如报告尚未就绪，请以后续通知与状态页更新为准。</li>
            <li>如交付已完成，可优先查看报告与 PDF 下载入口。</li>
          </ul>
        </aside>
      </section>

      <section class=\"sections\">
        {summary_html}
        <div id=\"delivery-status\">{delivery_html}</div>
        {station_notice_html}
        <section class=\"panel\">
          <h2>下一步操作</h2>
          <ul class=\"action-list\">
            <li><a href=\"/portal/{escape(token)}/info\">填写 / 更新资料</a></li>
            <li><a href=\"/portal/{escape(token)}/notifications\">查看通知记录</a></li>
            {report_links}
          </ul>
        </section>
      </section>
    </main>
  </body>
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
  <body>
    <main class=\"wrap\">
      <section class=\"panel\">
        <div class=\"toolbar\"><div><h1>通知审计</h1><p class=\"meta\">订单号：{escape(order.id)} · 服务版本：{escape(order.service_version)}</p></div><div><a href=\"/portal/{escape(token)}/status\">返回订单状态页</a></div></div>
        <p class=\"meta\">这里只展示通知摘要，方便你确认系统是否已经发出站内提醒或邮件通知；原始 payload 与附件路径不会在前台显示。</p>
      </section>
      <section class=\"panel\" style=\"overflow:auto\">
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
  </body>
</html>
"""


def _render_report_page(order: Order, settings: Settings) -> str:
    if (
        order.audit_report
        and _is_trusted_report_path(order.audit_report, settings)
        and Path(order.audit_report).is_file()
    ):
        path = Path(order.audit_report)
        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".html":
            return content
        if path.suffix.lower() == ".json":
            pretty = json.dumps(json.loads(content), ensure_ascii=False, indent=2)
            return f"<html><body><h1>志愿方案报告</h1><pre>{escape(pretty)}</pre></body></html>"
        return f"<html><body><h1>志愿方案报告</h1><pre>{escape(content)}</pre></body></html>"
    if (
        order.plan_file
        and _is_trusted_report_path(order.plan_file, settings)
        and Path(order.plan_file).is_file()
    ):
        content = Path(order.plan_file).read_text(encoding="utf-8")
        return f"<html><body><h1>志愿方案报告</h1><pre>{escape(content)}</pre></body></html>"
    raise HTTPException(status_code=404, detail="report not found")


def _render_deletion_request_page(token: str, order: Order) -> str:
    return f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>删除申请</title><link rel='stylesheet' href='/static/portal-ui.css' /><style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}}.wrap{{max-width:920px;margin:0 auto;display:grid;gap:16px}}.panel{{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}}.eyebrow{{display:inline-flex;padding:6px 10px;border-radius:999px;background:#fff7e6;color:#8a5a00;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}.lead{{color:#5b6b88;line-height:1.8}}.field{{display:flex;flex-direction:column;gap:6px;margin-bottom:14px}}input,textarea{{width:100%;padding:12px;border-radius:12px;border:1px solid #cfd7e6}}textarea{{min-height:120px;resize:vertical}}.check{{display:flex;gap:10px;align-items:flex-start;margin:12px 0}}button{{border:none;border-radius:14px;background:#1f6feb;color:#fff;font-weight:700;padding:13px 18px;cursor:pointer}}#result{{margin-top:14px;min-height:24px;color:#5b6b88;white-space:pre-wrap}}</style></head>
<body><main class='wrap'>
<section class='panel'><span class='eyebrow'>删除申请</span><h1>提交删除申请</h1><p class='lead'>可用于申请删除资料、附件或交付物。提交后，系统会保留必要审计记录，并由人工核验订单与监护人信息后处理。</p></section>
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
</main></body></html>"""
