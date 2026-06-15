from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from admin.auth import get_current_user
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser


router = APIRouter(prefix="/api/admin/notifications", tags=["notifications"])
page_router = APIRouter(tags=["notifications-ui"])

class NotificationEventResponse(BaseModel):
    order_id: str
    event_type: str
    channel: str
    status: str
    attempt_count: int
    last_attempt_at: str | None = None
    failure_reason: str | None = None
    created_at: str
    payload: dict[str, Any] | str | None = None


class NotificationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    filters: dict[str, Any]
    items: list[NotificationEventResponse]


class OpsAlertEventResponse(BaseModel):
    created_at: str
    alert_type: str
    title: str
    body: str
    details: dict[str, Any]


class OpsAlertListResponse(BaseModel):
    total: int
    items: list[OpsAlertEventResponse]


@router.get("/ops-alerts", response_model=OpsAlertListResponse, summary="运维告警列表")
def list_ops_alerts(
    limit: int = Query(50, ge=1, le=200),
    _: AdminUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    path = Path(settings.ops_alert_log_path)
    items: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            if isinstance(item, dict):
                items.append(item)
    return {"total": len(items), "items": items}


@page_router.get("/admin/ops-alerts", include_in_schema=False)
def ops_alert_audit_page(
    _: AdminUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    payload = list_ops_alerts(limit=200, _=_, settings=settings)
    rows = []
    for item in payload["items"]:
        details = escape(json.dumps(item.get("details") or {}, ensure_ascii=False, indent=2))
        rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('created_at') or '-'))}</td>"
            f"<td>{escape(str(item.get('alert_type') or '-'))}</td>"
            f"<td>{escape(str(item.get('title') or '-'))}</td>"
            f"<td>{escape(str(item.get('body') or '-'))}</td>"
            f"<td><pre style='white-space:pre-wrap;max-width:520px'>{details}</pre></td>"
            "</tr>"
        )
    rows_html = "".join(rows) or "<tr><td colspan='5'>暂无运维告警</td></tr>"
    html = f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8' /><title>运维告警审计</title></head>
<body style='font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;margin:0;padding:32px 20px;color:#172033;'>
<main style='max-width:1280px;margin:0 auto;display:grid;gap:16px;'>
<section style='background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;'>
  <h1>运维告警审计</h1>
  <p>日志路径：{escape(settings.ops_alert_log_path)}</p>
  <p>SMTP 告警收件人数量：{len(settings.alert_recipients)}</p>
  <p>IM Webhook 数量：{len(settings.alert_webhook_urls)}</p>
</section>
<section style='background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;overflow:auto;'>
  <table style='width:100%;border-collapse:collapse;'>
    <thead><tr><th>时间</th><th>类型</th><th>标题</th><th>摘要</th><th>details</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</section>
</main>
</body></html>"""
    return HTMLResponse(html)


@router.get("", response_model=NotificationListResponse, summary="通知审计列表")
def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    _: AdminUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    from data.notifications.email_service import DeliveryNotificationService

    service = DeliveryNotificationService.for_db(settings.orders_db_path)
    try:
        conn = service._conn
        sql = (
            "SELECT order_id, event_type, channel, payload_json, status, attempt_count, last_attempt_at, failure_reason, created_at "
            "FROM delivery_notifications WHERE 1=1"
        )
        params: list[Any] = []
        if order_id:
            sql += " AND order_id=?"
            params.append(order_id)
        if status:
            sql += " AND status=?"
            params.append(status)
        if channel:
            sql += " AND channel=?"
            params.append(channel)
        count_sql = f"SELECT COUNT(*) FROM ({sql})"
        total = int(conn.execute(count_sql, tuple(params)).fetchone()[0])
        sql += " ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?"
        rows = conn.execute(sql, tuple(params + [limit, offset])).fetchall()
    finally:
        service.close()

    items = []
    for row in rows:
        payload = None
        raw = row["payload_json"]
        if raw:
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw
        items.append(
            {
                "order_id": row["order_id"],
                "event_type": row["event_type"],
                "channel": row["channel"],
                "status": row["status"],
                "attempt_count": int(row["attempt_count"]),
                "last_attempt_at": row["last_attempt_at"],
                "failure_reason": row["failure_reason"],
                "created_at": row["created_at"],
                "payload": payload,
            }
        )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {"order_id": order_id, "status": status, "channel": channel},
        "items": items,
    }


@page_router.get("/admin/notifications", include_in_schema=False)
def notification_audit_admin_page(
    limit: int = Query(50, ge=1, le=200),
    order_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    _: AdminUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> HTMLResponse:
    payload = list_notifications(
        limit=limit,
        offset=0,
        order_id=order_id,
        status=status,
        channel=channel,
        _=_,
        settings=settings,
    )
    rows = []
    for item in payload["items"]:
        body = escape(json.dumps(item.get("payload"), ensure_ascii=False, indent=2))
        rows.append(
            "<tr>"
            f"<td>{escape(str(item['order_id']))}</td>"
            f"<td>{escape(str(item['channel']))}</td>"
            f"<td>{escape(str(item['event_type']))}</td>"
            f"<td>{escape(str(item['status']))}</td>"
            f"<td>{escape(str(item['attempt_count']))}</td>"
            f"<td>{escape(str(item.get('last_attempt_at') or '-'))}</td>"
            f"<td>{escape(str(item.get('failure_reason') or '-'))}</td>"
            f"<td><pre style='white-space:pre-wrap;max-width:480px'>{body}</pre></td>"
            "</tr>"
        )
    rows_html = "".join(rows) or "<tr><td colspan='8'>暂无通知事件</td></tr>"
    html = f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8' /><title>后台通知审计</title></head>
<body style='font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;margin:0;padding:32px 20px;color:#172033;'>
<main style='max-width:1280px;margin:0 auto;display:grid;gap:16px;'>
<section style='background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;'>
  <h1>后台通知审计</h1>
  <p>总数：{payload['total']}</p>
  <p>筛选：order_id={escape(str(order_id or '-'))} / status={escape(str(status or '-'))} / channel={escape(str(channel or '-'))}</p>
</section>
<section style='background:#fff;border:1px solid #dbe3f0;border-radius:18px;padding:24px;overflow:auto;'>
  <table style='width:100%;border-collapse:collapse;'>
    <thead><tr><th>订单</th><th>渠道</th><th>事件</th><th>状态</th><th>尝试次数</th><th>最后尝试</th><th>失败原因</th><th>payload</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</section>
</main>
</body></html>"""
    return HTMLResponse(html)
