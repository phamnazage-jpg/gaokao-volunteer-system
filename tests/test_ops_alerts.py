from __future__ import annotations

import json
from pathlib import Path

from data.notifications.ops_alerts import OpsAlertSink


def test_ops_alert_sink_appends_jsonl(tmp_path: Path):
    log_path = tmp_path / "alerts.jsonl"
    sink = OpsAlertSink(log_path=str(log_path), recipients=[])
    result = sink.emit(
        alert_type="test_alert",
        title="Test Alert",
        body="body",
        details={"order_id": "O-1", "failed": 2},
    )

    assert result.log_written is True
    assert result.emails_sent == 0
    content = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    payload = json.loads(content[0])
    assert payload["alert_type"] == "test_alert"
    assert payload["details"]["order_id"] == "O-1"


def test_ops_alert_sink_can_use_fake_email_sender(tmp_path: Path):
    log_path = tmp_path / "alerts.jsonl"

    class FakeSender:
        def __init__(self) -> None:
            self.sent: list[dict[str, str]] = []

        def send_report_ready(self, *, recipient: str, order_id: str, subject: str, body: str) -> dict[str, str]:
            payload = {
                "recipient": recipient,
                "order_id": order_id,
                "subject": subject,
                "body": body,
            }
            self.sent.append(payload)
            return payload

    sender = FakeSender()
    sink = OpsAlertSink(log_path=str(log_path), recipients=["ops@example.com"], email_sender=sender)
    result = sink.emit(
        alert_type="watchdog_failed",
        title="watchdog failed",
        body="something failed",
        details={"order_id": "O-2"},
    )

    assert result.emails_sent == 1
    assert len(sender.sent) == 1
    assert sender.sent[0]["recipient"] == "ops@example.com"


def test_ops_alert_sink_can_use_fake_webhook_sender(tmp_path: Path):
    log_path = tmp_path / "alerts.jsonl"

    class FakeWebhookSender:
        def __init__(self) -> None:
            self.payloads: list[dict] = []

        def send(self, payload: dict) -> int:
            self.payloads.append(payload)
            return 2

    sender = FakeWebhookSender()
    sink = OpsAlertSink(log_path=str(log_path), recipients=[], webhook_sender=sender)
    result = sink.emit(
        alert_type="watchdog_failed",
        title="watchdog failed",
        body="something failed",
        details={"order_id": "O-3"},
    )

    assert result.webhooks_sent == 2
    assert len(sender.payloads) == 1
    assert sender.payloads[0]["alert_type"] == "watchdog_failed"
