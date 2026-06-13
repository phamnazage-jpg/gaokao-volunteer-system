from __future__ import annotations

from data.payments.provider_requirements import build_provider_readiness_report


def test_mock_provider_report_is_ready_without_credentials():
    report = build_provider_readiness_report("mock", env={})
    assert report.provider == "mock"
    assert report.ready is True
    assert report.missing_env_vars == []


def test_alipay_sim_report_is_ready_without_real_credentials():
    report = build_provider_readiness_report("alipay_sim", env={})
    assert report.provider == "alipay_sim"
    assert report.ready is True
    assert report.missing_env_vars == []


def test_alipay_provider_report_detects_missing_credentials():
    report = build_provider_readiness_report("alipay", env={})
    assert report.provider == "alipay"
    assert report.ready is False
    assert "GAOKAO_PAYMENT_APP_ID" in report.missing_env_vars
    assert "GAOKAO_PAYMENT_PRIVATE_KEY_PATH" in report.missing_env_vars


def test_unsupported_provider_note_is_explicit():
    report = build_provider_readiness_report("unknown-provider", env={})
    assert report.ready is True
    assert report.notes == ["unsupported provider: unknown-provider"]


def test_alipay_provider_report_detects_missing_key_files(tmp_path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "alipay_public.pem"
    private_key.write_text("private", encoding="utf-8")
    env = {
        "GAOKAO_PAYMENT_APP_ID": "20260001",
        "GAOKAO_PAYMENT_PRIVATE_KEY_PATH": str(private_key),
        "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH": str(public_key),
        "GAOKAO_PAYMENT_NOTIFY_URL": "https://example.com/notify",
        "GAOKAO_PAYMENT_RETURN_URL": "https://example.com/return",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": "secret",
    }
    report = build_provider_readiness_report("alipay", env=env)
    assert report.ready is False
    assert report.missing_files == ["GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH"]
