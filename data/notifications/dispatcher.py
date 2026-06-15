from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from data.notifications.email_service import (
    DeliveryNotificationEvent,
    DeliveryNotificationService,
)
from data.notifications.smtp_sender import SMTPDeliverySender
from data.orders.models import utc_now_iso


@dataclass
class DispatchResult:
    processed: int = 0
    sent: int = 0
    failed: int = 0


class DeliveryDispatcher:
    def __init__(
        self,
        service: DeliveryNotificationService,
        *,
        email_sender: SMTPDeliverySender | None = None,
    ) -> None:
        self._service = service
        self._email_sender = email_sender

    @classmethod
    def for_db(
        cls,
        db_path: str,
        *,
        email_sender: SMTPDeliverySender | None = None,
    ) -> "DeliveryDispatcher":
        return cls(
            DeliveryNotificationService.for_db(db_path),
            email_sender=email_sender,
        )

    def close(self) -> None:
        self._service.close()

    def dispatch_ready_events(
        self,
        *,
        channel: str = "station",
        statuses: tuple[str, ...] = ("ready", "failed"),
        limit: int = 100,
    ) -> DispatchResult:
        result = DispatchResult()
        events = self._service.list_pending_events(
            channel=channel,
            statuses=statuses,
            limit=limit,
        )
        for event in events:
            result.processed += 1
            payload, failure_reason = self._validate_event(event)
            if failure_reason is not None:
                self._service.mark_failed(
                    event.order_id, failure_reason, event_type=event.event_type
                )
                result.failed += 1
                continue
            assert payload is not None
            sent_at = utc_now_iso()
            try:
                rendered_payload = self._deliver_event(
                    event,
                    payload=payload,
                    sent_at=sent_at,
                )
            except Exception as exc:
                self._service.mark_failed(
                    event.order_id,
                    str(exc),
                    event_type=event.event_type,
                )
                result.failed += 1
                continue
            self._service.mark_sent(
                event.order_id,
                event_type=event.event_type,
                payload_json=json.dumps(rendered_payload, ensure_ascii=False),
                sent_at=sent_at,
            )
            result.sent += 1
        return result

    @staticmethod
    def _validate_event(
        event: DeliveryNotificationEvent,
    ) -> tuple[dict[str, object] | None, str | None]:
        try:
            payload = json.loads(event.payload_json)
        except json.JSONDecodeError:
            return None, "delivery payload invalid"
        report_path = payload.get("audit_report") or payload.get("plan_file")
        pdf_path = payload.get("pdf_path")
        if not report_path or not Path(str(report_path)).is_file():
            return None, "delivery artifact missing"
        if not pdf_path or not Path(str(pdf_path)).is_file():
            return None, "delivery artifact missing"
        if event.channel == "email" and not payload.get("customer_email"):
            return None, "delivery recipient missing"
        return payload, None

    def _deliver_event(
        self,
        event: DeliveryNotificationEvent,
        *,
        payload: dict[str, object],
        sent_at: str,
    ) -> dict[str, object]:
        rendered = dict(payload)
        if event.channel == "station":
            rendered["station_notice"] = {
                "title": "报告已就绪",
                "body": f"订单 {event.order_id} 的志愿报告已就绪，可在当前状态页查看在线报告并下载 PDF。",
                "sent_at": sent_at,
            }
            return rendered
        if event.channel == "email":
            if self._email_sender is None:
                raise ValueError("email sender not configured")
            recipient = str(payload["customer_email"])
            subject = f"高考志愿报告已就绪 - {event.order_id}"
            body = (
                f"您好，订单 {event.order_id} 的志愿报告已就绪。"
                "请登录当前 portal 状态页查看在线报告并下载 PDF。"
            )
            send_result = self._email_sender.send_report_ready(
                recipient=recipient,
                order_id=event.order_id,
                subject=subject,
                body=body,
            )
            rendered["email_notice"] = {
                **send_result,
                "sent_at": sent_at,
            }
            return rendered
        return rendered
