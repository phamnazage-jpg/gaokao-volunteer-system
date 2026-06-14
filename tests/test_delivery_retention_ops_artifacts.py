from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_delivery_retention_ops_artifacts_exist_and_reference_scripts():
    runbook = PROJECT_ROOT / "docs/DELIVERY_RETENTION_OPS_RUNBOOK.md"
    dispatch_service = PROJECT_ROOT / "deploy/systemd/gaokao-delivery-dispatch.service"
    dispatch_timer = PROJECT_ROOT / "deploy/systemd/gaokao-delivery-dispatch.timer"
    watchdog_service = PROJECT_ROOT / "deploy/systemd/gaokao-delivery-watchdog.service"
    watchdog_timer = PROJECT_ROOT / "deploy/systemd/gaokao-delivery-watchdog.timer"
    retention_service = PROJECT_ROOT / "deploy/systemd/gaokao-retention-cleanup.service"
    retention_timer = PROJECT_ROOT / "deploy/systemd/gaokao-retention-cleanup.timer"
    cron_file = PROJECT_ROOT / "deploy/cron/gaokao-jobs.crontab"
    env_example = PROJECT_ROOT / "deploy/systemd/gaokao-jobs.env.example"

    for path in (
        runbook,
        dispatch_service,
        dispatch_timer,
        watchdog_service,
        watchdog_timer,
        retention_service,
        retention_timer,
        cron_file,
        env_example,
    ):
        assert path.is_file(), path

    assert "gaokao-delivery-dispatch.py" in dispatch_service.read_text(encoding="utf-8")
    assert "gaokao-delivery-watchdog.py" in watchdog_service.read_text(encoding="utf-8")
    assert "--retention-days" in retention_service.read_text(encoding="utf-8")

    cron_text = cron_file.read_text(encoding="utf-8")
    assert "gaokao-delivery-dispatch.py" in cron_text
    assert "gaokao-delivery-watchdog.py" in cron_text
    assert "gaokao-retention-cleanup.py --retention-days" in cron_text

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "systemd" in runbook_text
    assert "cron" in runbook_text
    assert "gaokao-retention-cleanup.py --retention-days 180" in runbook_text
