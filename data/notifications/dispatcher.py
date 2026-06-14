from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from data.notifications.email_service import (
    DeliveryNotificationEvent,
    DeliveryNotificationService,
)


@dataclass
class DispatchResult:
    processed: int = 0
    sent: int = 0
    failed: int = 0


class DeliveryDispatcher:
    def __init__(self, service: DeliveryNotificationService) -> None:
        self._service = service

    @classmethod
    def for_db(cls, db_path: str) -> "DeliveryDispatcher":
        return cls(DeliveryNotificationService.for_db(db_path))

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
            failure_reason = self._validate_event(event)
            if failure_reason is not None:
                self._service.mark_failed(
                    event.order_id, failure_reason, event_type=event.event_type
                )
                result.failed += 1
                continue
            self._service.mark_sent(event.order_id, event_type=event.event_type)
            result.sent += 1
        return result

    @staticmethod
    def _validate_event(event: DeliveryNotificationEvent) -> str | None:
        try:
            payload = json.loads(event.payload_json)
        except json.JSONDecodeError:
            return "delivery payload invalid"
        report_path = payload.get("audit_report") or payload.get("plan_file")
        pdf_path = payload.get("pdf_path")
        if not report_path or not Path(str(report_path)).is_file():
            return "delivery artifact missing"
        if not pdf_path or not Path(str(pdf_path)).is_file():
            return "delivery artifact missing"
        return None
