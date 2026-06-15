from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data.notifications.smtp_sender import SMTPDeliverySender, SMTPSettings
from data.orders.models import utc_now_iso


@dataclass
class OpsAlertResult:
    log_written: bool
    emails_sent: int = 0


class OpsAlertSink:
    def __init__(
        self,
        *,
        log_path: str,
        recipients: list[str] | None = None,
        email_sender: Any | None = None,
    ) -> None:
        self._log_path = Path(log_path)
        self._recipients = recipients or []
        self._email_sender = email_sender

    def emit(self, *, alert_type: str, title: str, body: str, details: dict[str, Any]) -> OpsAlertResult:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": utc_now_iso(),
            "alert_type": alert_type,
            "title": title,
            "body": body,
            "details": details,
        }
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        emails_sent = 0
        if self._email_sender is not None and self._recipients:
            for recipient in self._recipients:
                self._email_sender.send_report_ready(
                    recipient=recipient,
                    order_id=str(details.get("order_id") or "ops-alert"),
                    subject=title,
                    body=body,
                )
                emails_sent += 1
        return OpsAlertResult(log_written=True, emails_sent=emails_sent)


def build_alert_sink_from_settings(settings) -> OpsAlertSink:
    sender = None
    if settings.smtp_host and settings.smtp_sender:
        sender = SMTPDeliverySender(
            SMTPSettings(
                host=settings.smtp_host,
                port=settings.smtp_port,
                sender=settings.smtp_sender,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
                use_ssl=settings.smtp_use_ssl,
            )
        )
    return OpsAlertSink(
        log_path=settings.ops_alert_log_path,
        recipients=settings.alert_recipients,
        email_sender=sender,
    )
