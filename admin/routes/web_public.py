"""用户端 Web 自助 MVP 公共入口页面与 Portal 路由。"""

from __future__ import annotations

import json
import logging
from html import escape
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request
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
from data.orders.dao import OrderNotFound, OrdersDAO
from data.orders.intake_schema import IntakePayload
from data.orders.intake_store import IntakeStore
from data.orders.models import Order
from data.orders.public_flow import (
    PublicOrderCreate,
    create_public_order,
)
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
    "refund_pending": ("退款申请中", "退款申请已登记，等待处理结果。"),
    "refunded": ("已退款", "该订单已完成退款。"),
    "payment_failed": ("支付失败", "支付未成功，请重新发起支付。"),
}
_SERVICE_PRICES = {
    "audit": 4900,
    "basic": 4900,
    "standard": 9900,
    "premium": 19900,
}


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


@router.get("/", include_in_schema=False)
def landing_page() -> HTMLResponse:
    return HTMLResponse(_render_landing_page())


@router.get("/pricing", include_in_schema=False)
def pricing_page() -> HTMLResponse:
    return HTMLResponse(_render_pricing_page())


@router.get("/checkout/{service_version}", include_in_schema=False)
def checkout_page(service_version: ServiceVersion) -> HTMLResponse:
    return HTMLResponse(_render_checkout_page(service_version))


@router.post("/api/public/orders", response_model=PublicOrderCreated, status_code=201)
def create_public_order_endpoint(
    payload: PublicOrderCreate,
    settings: Settings = Depends(get_settings_dep),
) -> PublicOrderCreated:
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order = create_public_order(dao, payload)
    portal_token = issue_portal_token(order.id, settings.jwt_secret)
    payment_service = _payment_service(settings)
    checkout = payment_service.create_checkout(order.id, portal_token=portal_token)
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
    token: str,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    return _render_simulated_payment_page(
        payment_id, token, settings, provider_slug="mock"
    )


@router.post("/pay/mock/{payment_id}/complete", include_in_schema=False)
def complete_mock_payment(
    payment_id: str,
    token: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    return _complete_simulated_payment(
        payment_id, token, settings, provider_slug="mock"
    )


@router.get("/pay/alipay-sim/{payment_id}", include_in_schema=False)
def alipay_sim_payment_page(
    payment_id: str,
    token: str,
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    return _render_simulated_payment_page(
        payment_id, token, settings, provider_slug="alipay-sim"
    )


@router.post("/pay/alipay-sim/{payment_id}/complete", include_in_schema=False)
def complete_alipay_sim_payment(
    payment_id: str,
    token: str,
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    return _complete_simulated_payment(
        payment_id, token, settings, provider_slug="alipay-sim"
    )


@router.get("/portal/payment-return", include_in_schema=False)
def payment_return_page(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> RedirectResponse:
    _resolve_order_from_token(token, settings)
    return RedirectResponse(url=f"/portal/{token}/status", status_code=303)


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


@router.post("/portal/{token}/info", response_model=PortalIntakeResponse)
def submit_order_info(
    token: str,
    payload: IntakePayload,
    settings: Settings = Depends(get_settings_dep),
) -> PortalIntakeResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    if context["stage"] == "pending_payment":
        raise HTTPException(status_code=409, detail="payment required before intake")
    if context["stage"] in {
        "processing",
        "report_ready",
        "completed",
        "refund_pending",
        "refunded",
    }:
        raise HTTPException(
            status_code=409, detail="intake is read-only at current stage"
        )
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
    if updates:
        with OrdersDAO.connect(settings.orders_db_path) as dao:
            dao.update(
                order.id, updates, actor="portal", reason=f"portal_{record.status}"
            )
    refreshed_order = _resolve_order_from_token(token, settings)
    refreshed_context = _build_portal_context(refreshed_order, settings)
    return PortalIntakeResponse(
        intake_status=record.status,
        stage=refreshed_context["stage"],
        order_id=order.id,
    )


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
    return HTMLResponse(_render_report_page(order))


@router.get("/portal/{token}/report.pdf", include_in_schema=False)
def report_pdf_download(
    token: str, settings: Settings = Depends(get_settings_dep)
) -> FileResponse:
    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    if context["stage"] not in {"report_ready", "completed"}:
        raise HTTPException(status_code=409, detail="report not ready")
    if not order.pdf_path or not Path(order.pdf_path).is_file():
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
        private_key_path=settings.payment_private_key_path,
        alipay_public_key_path=settings.payment_alipay_public_key_path,
    )


def _resolve_order_from_token(token: str, settings: Settings) -> Order:
    try:
        payload = verify_portal_token(token, settings.jwt_secret)
    except PortalTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        try:
            return dao.get(str(payload["order_id"]))
        except OrderNotFound as exc:
            raise HTTPException(status_code=404, detail="order not found") from exc


def _build_portal_context(order: Order, settings: Settings) -> dict[str, Any]:
    payment_service = _payment_service(settings)
    payment = payment_service.get_payment_by_order(order.id)
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(order.id)
    finally:
        intake_store.close()

    stage = "pending_payment"
    report_html_ready = bool(order.audit_report and Path(order.audit_report).is_file())
    report_pdf_ready = bool(order.pdf_path and Path(order.pdf_path).is_file())
    report_artifacts_ready = report_html_ready and report_pdf_ready
    if payment is not None and payment.status == "refund_pending":
        stage = "refund_pending"
    elif order.status == "refunded" or (
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
    return {
        "stage": stage,
        "stage_title": title,
        "stage_subtitle": subtitle,
        "payment": payment,
        "intake": intake,
        "report_html_ready": report_html_ready,
        "report_pdf_ready": report_pdf_ready,
        "order": order,
    }


def _render_landing_page() -> str:
    return """<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>高考志愿填报智能系统 - 用户端 Web 自助服务</title>
    <style>
      body { margin: 0; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background: linear-gradient(180deg,#0b1020,#121a31 65%,#f7f9fc 65%); color: #e8edf7; }
      .wrap { max-width: 1080px; margin: 0 auto; padding: 48px 20px 72px; }
      .hero { display: grid; gap: 20px; }
      h1 { margin: 0; font-size: 42px; }
      .sub { color: #9fb0d0; line-height: 1.7; }
      .btn { display:inline-flex; padding:12px 18px; border-radius:12px; text-decoration:none; font-weight:700; }
      .btn-primary { background:#7c9cff; color:#fff; }
      .btn-secondary { border:1px solid rgba(159,176,208,.18); color:#fff; }
      .grid { display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); margin-top:28px; }
      .card { background:rgba(18,26,49,.84); border:1px solid rgba(159,176,208,.18); border-radius:18px; padding:20px; }
      .section { background:#f7f9fc; color:#172033; border-radius:28px; padding:28px; margin-top:32px; }
    </style>
  </head>
  <body>
    <main class=\"wrap\">
      <section class=\"hero\">
        <h1>高考志愿填报智能系统</h1>
        <p class=\"sub\">用户端 Web 自助服务已接入公开套餐、下单、Mock 支付沙箱、资料填写、订单状态页与报告查看/下载链路。</p>
        <div>
          <a class=\"btn btn-primary\" href=\"/pricing\">查看服务套餐</a>
          <a class=\"btn btn-secondary\" href=\"/dashboard\">进入运营后台</a>
        </div>
        <div class=\"grid\">
          <article class=\"card\"><strong>49元 AI方案审核</strong><p class=\"sub\">适合已拿到其他 AI 方案，需要快速校验政策、扎堆和数据来源的用户。</p></article>
          <article class=\"card\"><strong>99元 完整志愿方案</strong><p class=\"sub\">适合需要从资料收集到完整方案输出的标准 Web 自助用户。</p></article>
          <article class=\"card\"><strong>199元 深度辅导版</strong><p class=\"sub\">适合需要人工介入、反复沟通和多轮修订的复杂场景。</p></article>
        </div>
      </section>
      <section class=\"section\">
        <h2>当前自助流程建设重点</h2>
        <ul>
          <li>公开套餐页与下单入口</li>
          <li>系统内支付与回调验签</li>
          <li>支付后资料填写与订单状态页</li>
          <li>站内查看报告 + PDF 交付</li>
        </ul>
      </section>
    </main>
  </body>
</html>
"""


def _render_pricing_page() -> str:
    return """<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>服务套餐 - 高考志愿填报智能系统</title>
    <style>
      body { margin: 0; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f4f7fb; color:#172033; }
      .wrap { max-width:1080px; margin:0 auto; padding:40px 20px 72px; }
      .grid { display:grid; gap:18px; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); margin-top:28px; }
      .card { background:#fff; border:1px solid #dbe3f0; border-radius:18px; padding:22px; box-shadow:0 10px 30px rgba(23,32,51,.06); }
      .price { font-size:30px; font-weight:800; margin:10px 0; }
      .button { display:inline-flex; margin-top:16px; padding:11px 16px; border-radius:12px; background:#1f6feb; color:#fff; text-decoration:none; font-weight:700; }
      .notice { margin-top:26px; padding:16px 18px; border-radius:14px; background:#fff7e6; color:#8a5a00; border:1px solid #f4d39b; }
    </style>
  </head>
  <body>
    <main class=\"wrap\">
      <h1>服务套餐</h1>
      <p>当前页面已接入最小 Web 自助闭环，可直接进入下单与支付沙箱。</p>
      <section class=\"grid\">
        <article class=\"card\" data-package=\"audit\">
          <h2>49元 AI方案审核</h2>
          <div class=\"price\">¥49</div>
          <a class=\"button\" href=\"/checkout/audit\">立即下单</a>
        </article>
        <article class=\"card\" data-package=\"standard\">
          <h2>99元 完整志愿方案</h2>
          <div class=\"price\">¥99</div>
          <a class=\"button\" href=\"/checkout/standard\">立即下单</a>
        </article>
        <article class=\"card\" data-package=\"premium\">
          <h2>199元 深度辅导版</h2>
          <div class=\"price\">¥199</div>
          <a class=\"button\" href=\"/checkout/premium\">立即下单</a>
        </article>
      </section>
      <div class=\"notice\">支付接入建设中：当前使用 Mock 支付沙箱完成本地闭环验证，后续可切换真实 provider。</div>
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
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>下单 - {escape(service_label)}</title>
    <style>
      body {{ font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f4f7fb; color:#172033; margin:0; }}
      .wrap {{ max-width:760px; margin:0 auto; padding:32px 20px; }}
      .panel {{ background:#fff; border:1px solid #dbe3f0; border-radius:18px; padding:22px; }}
      input, textarea {{ width:100%; padding:12px; border-radius:10px; border:1px solid #cfd7e6; margin-top:8px; margin-bottom:14px; }}
      button {{ border:none; border-radius:12px; background:#1f6feb; color:#fff; font-weight:700; padding:12px 18px; cursor:pointer; }}
    </style>
  </head>
  <body>
    <main class=\"wrap\">
      <section class=\"panel\">
        <h1>{escape(service_label)}</h1>
        <p>提交后会自动创建订单并跳转到支付页。</p>
        <form id=\"checkout-form\">
          <label>家长称呼<input name=\"customer_name\" required /></label>
          <label>手机号<input name=\"customer_phone\" required /></label>
          <label>考生姓名<input name=\"candidate_name\" /></label>
          <label>省份<input name=\"candidate_province\" value=\"湖南\" required /></label>
          <label>备注<textarea name=\"notes\"></textarea></label>
          <button type=\"submit\">创建订单并去支付（¥{amount / 100:.0f}）</button>
        </form>
        <p id=\"result\"></p>
      </section>
    </main>
    <script>
      document.getElementById('checkout-form').addEventListener('submit', async function (event) {{
        event.preventDefault();
        const form = new FormData(event.target);
        const payload = {{
          service_version: '{service_version}',
          amount_cents: {amount},
          customer_name: form.get('customer_name'),
          customer_phone: form.get('customer_phone'),
          candidate_name: form.get('candidate_name'),
          candidate_province: form.get('candidate_province'),
          notes: form.get('notes'),
        }};
        const resp = await fetch('/api/public/orders', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
        }});
        const body = await resp.json();
        if (!resp.ok) {{
          document.getElementById('result').textContent = body.message || body.detail || '下单失败';
          return;
        }}
        window.location.href = body.checkout_url;
      }});
    </script>
  </body>
</html>
"""


def _render_mock_payment_page(payment_id: str, amount_cents: int, token: str) -> str:
    return _render_simulated_payment_html(
        title="Mock 支付沙箱",
        provider_slug="mock",
        payment_id=payment_id,
        amount_cents=amount_cents,
        token=token,
        submit_label="模拟支付成功并返回订单页",
    )


def _render_alipay_sim_payment_page(
    payment_id: str, amount_cents: int, token: str
) -> str:
    return _render_simulated_payment_html(
        title="支付宝模拟收银台",
        provider_slug="alipay-sim",
        payment_id=payment_id,
        amount_cents=amount_cents,
        token=token,
        submit_label="模拟支付宝支付成功并返回订单页",
    )


def _render_simulated_payment_html(
    *,
    title: str,
    provider_slug: str,
    payment_id: str,
    amount_cents: int,
    token: str,
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
      <form method=\"post\" action=\"/pay/{escape(provider_slug)}/{escape(payment_id)}/complete?token={escape(token)}\">
        <button type=\"submit\" style=\"border:none;border-radius:12px;background:#1f6feb;color:#fff;font-weight:700;padding:12px 18px;cursor:pointer;\">{escape(submit_label)}</button>
      </form>
    </main>
  </body>
</html>
"""


def _render_simulated_payment_page(
    payment_id: str,
    token: str,
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
        body = _render_mock_payment_page(payment_id, payment.amount_cents, token)
    elif provider_slug == "alipay-sim":
        body = _render_alipay_sim_payment_page(payment_id, payment.amount_cents, token)
    else:
        raise HTTPException(
            status_code=404, detail="unsupported simulated payment page"
        )
    return HTMLResponse(body)


def _complete_simulated_payment(
    payment_id: str,
    token: str,
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
    try:
        portal_payload = verify_portal_token(token, settings.jwt_secret)
    except PortalTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if (
        str(portal_payload["order_id"]) != payment.order_id
        or payment.checkout_token != token
    ):
        raise HTTPException(status_code=403, detail="payment token mismatch")
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
    return RedirectResponse(url=f"/portal/{token}/status", status_code=303)


def _render_info_page(
    order: Order, token: str, payload: dict[str, Any], stage: str
) -> str:
    consent_version = str(payload.get("consent_version") or "t12-web-mvp-v1")
    consent_scope = str(payload.get("consent_scope") or "web-self-service-order-intake")
    privacy_checked = "checked" if payload.get("privacy_accepted") else ""
    service_terms_checked = "checked" if payload.get("service_terms_accepted") else ""
    guardian_checked = "checked" if payload.get("guardian_confirmed") else ""
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>考生资料填写</title></head>
  <body style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fb;padding:24px;\">
    <main style=\"max-width:760px;margin:0 auto;background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;\">
      <h1>考生资料填写</h1>
      <p>当前阶段：{escape(_STAGE_META[stage][0])}</p>
      <p style=\"background:#fff7e6;border:1px solid #f4d39b;border-radius:12px;padding:12px 14px;color:#8a5a00;\">提交资料即表示：监护人已知情并同意将考生资料用于志愿填报服务；当前版本号：{escape(consent_version)}</p>
      <form id=\"intake-form\">
        <label>高考分数<input name=\"candidate_score\" value=\"{escape(str(payload.get("candidate_score") or ""))}\" /></label><br/>
        <label>位次<input name=\"candidate_rank\" value=\"{escape(str(payload.get("candidate_rank") or ""))}\" /></label><br/>
        <label>选科（逗号分隔）<input name=\"candidate_subjects\" value=\"{escape(",".join(payload.get("candidate_subjects") or []))}\" /></label><br/>
        <label>兴趣方向<input name=\"candidate_interests\" value=\"{escape(str(payload.get("candidate_interests") or ""))}\" /></label><br/>
        <label>家长备注<textarea name=\"guardian_notes\">{escape(str(payload.get("guardian_notes") or ""))}</textarea></label><br/>
        <input type=\"hidden\" name=\"consent_version\" value=\"{escape(consent_version)}\" />
        <input type=\"hidden\" name=\"consent_scope\" value=\"{escape(consent_scope)}\" />
        <label><input type=\"checkbox\" name=\"privacy_accepted\" {privacy_checked} /> 我已阅读并同意隐私政策草案</label><br/>
        <label><input type=\"checkbox\" name=\"service_terms_accepted\" {service_terms_checked} /> 我已阅读并同意服务说明与免责声明</label><br/>
        <label><input type=\"checkbox\" name=\"guardian_confirmed\" {guardian_checked} /> 我确认监护人已知情并同意提交资料</label><br/>
        <button type=\"button\" onclick=\"submitIntake('draft')\">保存草稿</button>
        <button type=\"button\" onclick=\"submitIntake('submit')\">提交资料</button>
      </form>
      <p><a href=\"/portal/{escape(token)}/status\">返回订单状态页</a></p>
      <pre id=\"result\"></pre>
    </main>
    <script>
      async function submitIntake(mode) {{
        const form = new FormData(document.getElementById('intake-form'));
        const subjects = String(form.get('candidate_subjects') || '').split(',').map(s => s.trim()).filter(Boolean);
        const payload = {{
          mode,
          candidate_score: form.get('candidate_score') ? Number(form.get('candidate_score')) : null,
          candidate_rank: form.get('candidate_rank') ? Number(form.get('candidate_rank')) : null,
          candidate_subjects: subjects,
          candidate_interests: form.get('candidate_interests') || null,
          guardian_notes: form.get('guardian_notes') || null,
          consent_version: form.get('consent_version') || null,
          consent_scope: form.get('consent_scope') || null,
          privacy_accepted: form.get('privacy_accepted') === 'on',
          service_terms_accepted: form.get('service_terms_accepted') === 'on',
          guardian_confirmed: form.get('guardian_confirmed') === 'on',
        }};
        const resp = await fetch('/portal/{escape(token)}/info', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
        }});
        const body = await resp.json();
        document.getElementById('result').textContent = JSON.stringify(body, null, 2);
        if (resp.ok && mode === 'submit') window.location.href = '/portal/{escape(token)}/status';
      }}
    </script>
  </body>
</html>
"""


def _render_status_page(token: str, context: dict[str, Any]) -> str:
    order = context["order"]
    report_links = ""
    if context["report_html_ready"]:
        report_links += (
            f'<li><a href="/portal/{escape(token)}/report">查看在线报告</a></li>'
        )
    if context["report_pdf_ready"]:
        report_links += (
            f'<li><a href="/portal/{escape(token)}/report.pdf">下载 PDF</a></li>'
        )
    if not report_links:
        report_links = "<li>报告生成中，交付物就绪后这里会显示查看/下载入口。</li>"
    return f"""<!doctype html>
<html lang=\"zh-CN\"><head><meta charset=\"utf-8\" /><title>订单状态</title></head>
  <body style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;margin:0;padding:32px 20px;color:#172033;\">
    <main style=\"max-width:760px;margin:0 auto;display:grid;gap:16px;\">
      <section style=\"background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;\">
        <h1>{escape(context["stage_title"])}</h1>
        <p>{escape(context["stage_subtitle"])}</p>
        <p>订单号：{escape(order.id)}</p>
        <p>服务版本：{escape(order.service_version)}</p>
        <p>当前订单状态：{escape(order.status)}</p>
      </section>
      <section style=\"background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;\">
        <h2>下一步操作</h2>
        <ul>
          <li><a href=\"/portal/{escape(token)}/info\">填写/更新资料</a></li>
          {report_links}
        </ul>
      </section>
    </main>
  </body>
</html>
"""


def _render_report_page(order: Order) -> str:
    if order.audit_report and Path(order.audit_report).is_file():
        path = Path(order.audit_report)
        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".html":
            return content
        if path.suffix.lower() == ".json":
            pretty = json.dumps(json.loads(content), ensure_ascii=False, indent=2)
            return f"<html><body><h1>志愿方案报告</h1><pre>{escape(pretty)}</pre></body></html>"
        return f"<html><body><h1>志愿方案报告</h1><pre>{escape(content)}</pre></body></html>"
    if order.plan_file and Path(order.plan_file).is_file():
        content = Path(order.plan_file).read_text(encoding="utf-8")
        return f"<html><body><h1>志愿方案报告</h1><pre>{escape(content)}</pre></body></html>"
    raise HTTPException(status_code=404, detail="report not found")
