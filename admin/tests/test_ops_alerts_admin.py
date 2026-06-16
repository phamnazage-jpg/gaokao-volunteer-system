from __future__ import annotations

from pathlib import Path

from data.notifications.ops_alerts import OpsAlertSink


def test_admin_ops_alert_list_and_page(client, auth_headers, settings, tmp_path: Path):
    sink = OpsAlertSink(log_path=settings.ops_alert_log_path)
    sink.emit(
        alert_type="delivery_watchdog_failed",
        title="Gaokao delivery watchdog detected failed events",
        body="station failed once",
        details={"channel": "station", "failed": 1},
    )

    api = client.get("/api/admin/notifications/ops-alerts", headers=auth_headers)
    assert api.status_code == 200, api.text
    body = api.json()
    assert body["total"] == 1
    assert body["items"][0]["alert_type"] == "delivery_watchdog_failed"
    assert body["items"][0]["details"]["channel"] == "station"

    page = client.get("/admin/ops-alerts", headers=auth_headers)
    assert page.status_code == 200, page.text
    assert "运维告警审计" in page.text
    assert '/static/portal-ui.css' in page.text
    assert "告警来源文件" in page.text
    assert "详细上下文" in page.text
    assert "delivery_watchdog_failed" in page.text
    assert "station failed once" in page.text
    assert "SMTP 告警收件人数量" in page.text
    assert "IM Webhook 数量" in page.text
