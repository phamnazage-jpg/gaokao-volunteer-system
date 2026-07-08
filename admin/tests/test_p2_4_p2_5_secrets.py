"""P2-4 portal token secret 分离 + P2-5 payment webhook secret fail-closed.

验收:
- Portal token 使用独立 secret 配置,不再复用后台 JWT secret。
- Payment webhook secret 在生产环境 (env=prod) 缺失/默认值时 fail-closed。
- 开发/测试场景保持兼容。
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# P2-4: portal token secret 与后台 JWT secret 分离
# ---------------------------------------------------------------------------


def _reload_settings():
    """重新加载 Settings(确保读取最新环境变量)。"""
    import os
    from admin.config import load_settings

    # LLM 是生产必需项；本测试聚焦 portal/payment secret，不希望被 LLM 校验提前拦截
    os.environ.setdefault("GAOKAO_LLM_PROVIDER", "dashscope")
    os.environ.setdefault("GAOKAO_LLM_API_KEY", "sk-test")

    return load_settings()


def test_settings_exposes_independent_portal_token_secret(monkeypatch):
    """Settings 应该有独立的 portal_token_secret 字段,默认与 jwt_secret 不同。"""
    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "a" * 64)
    monkeypatch.delenv("GAOKAO_PORTAL_TOKEN_SECRET", raising=False)
    settings = _reload_settings()
    assert hasattr(settings, "portal_token_secret")
    # 关键验收:portal token secret 不能等于后台 jwt secret
    assert settings.portal_token_secret != settings.jwt_secret


def test_settings_honors_explicit_portal_token_secret(monkeypatch):
    """GAOKAO_PORTAL_TOKEN_SECRET 显式设置时,Settings 必须采用。"""
    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "a" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "b" * 64)
    settings = _reload_settings()
    assert settings.portal_token_secret == "b" * 64


def test_portal_token_secret_fails_closed_when_missing_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)
    monkeypatch.delenv("GAOKAO_PORTAL_TOKEN_SECRET", raising=False)

    with pytest.raises(RuntimeError, match=r"GAOKAO_PORTAL_TOKEN_SECRET"):
        _reload_settings()


def test_portal_token_secret_fails_closed_when_equal_to_jwt_secret_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "J" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "J" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)

    with pytest.raises(RuntimeError, match=r"portal token secret"):
        _reload_settings()


def test_portal_token_secret_fails_closed_when_using_dev_default_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv(
        "GAOKAO_PORTAL_TOKEN_SECRET",
        "dev-only-portal-token-secret-do-not-use-in-prod",
    )
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)

    with pytest.raises(RuntimeError, match=r"GAOKAO_PORTAL_TOKEN_SECRET"):
        _reload_settings()


def test_portal_token_issued_via_issue_endpoint_cannot_be_verified_with_jwt_secret(
    route_client,
):
    """下单签发的 portal token 必须不能用后台 jwt_secret 验签通过。

    这是 P2-4 的核心安全不变量:portal token 与 admin JWT 走不同 secret。
    """
    from data.customer_portal.token import verify_portal_token, PortalTokenError

    resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "customer_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    settings = route_client.app.state.settings

    # 关键断言:用 jwt_secret 验签应当失败(因为 secret 已经分离)
    with pytest.raises(PortalTokenError):
        verify_portal_token(token, settings.jwt_secret)

    # 应当能用独立的 portal_token_secret 验签
    payload = verify_portal_token(token, settings.portal_token_secret)
    assert payload["order_id"].startswith("GKO-")


def test_public_order_issue_endpoint_returns_portal_urls(route_client):
    """公共下单 API 仍返回 portal 能力 URL；旧 portal HTML GET 页面已删除。"""
    resp = route_client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_email": "parent@example.com",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["portal_status_url"].startswith("/portal/")
    assert body["portal_info_url"].startswith("/portal/")



def test_payment_webhook_secret_fails_closed_when_missing_in_prod(monkeypatch):
    """生产环境 GAOKAO_PAYMENT_WEBHOOK_SECRET 缺失/空字符串必须 fail-closed。"""
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)  # 满足 jwt secret prod 校验
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.delenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", raising=False)

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_WEBHOOK_SECRET"):
        _reload_settings()


def test_payment_webhook_secret_fails_closed_when_using_legacy_default_in_prod(
    monkeypatch,
):
    """生产环境若仍使用 dev 默认 secret (dev-mock-payment-secret) 必须 fail-closed。"""
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "dev-mock-payment-secret")

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_WEBHOOK_SECRET"):
        _reload_settings()


def test_payment_webhook_secret_fails_closed_when_empty_in_prod(monkeypatch):
    """生产环境显式空字符串也要 fail-closed。"""
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "")

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_WEBHOOK_SECRET"):
        _reload_settings()


def test_payment_webhook_secret_is_weak_rejected_in_prod(monkeypatch):
    """生产环境 webhook secret 太短 (< 16 字符) 也要 fail-closed。"""
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "short")

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_WEBHOOK_SECRET"):
        _reload_settings()


def test_payment_webhook_secret_accepted_in_prod_when_strong(monkeypatch):
    """生产环境若 secret 强且非默认,允许通过。"""
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv(
        "GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32
    )  # 64 chars
    settings = _reload_settings()
    assert settings.payment_webhook_secret == "P" + "r" * 31 + "!" * 32


def test_payment_webhook_secret_dev_default_still_works(monkeypatch):
    """dev 环境保留 dev 默认,测试可继续运行。"""
    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.delenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", raising=False)
    settings = _reload_settings()
    # dev 默认 secret 应能加载成功(用于本地开发/测试)
    assert settings.payment_webhook_secret == "dev-mock-payment-secret"


def test_payment_provider_mock_fails_closed_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "mock")

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_PROVIDER"):
        _reload_settings()


def test_payment_provider_alipay_sim_fails_closed_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay_sim")

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_PROVIDER"):
        _reload_settings()


def test_payment_provider_unknown_value_fails_closed_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" + "r" * 31 + "!" * 32)
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "foo")

    with pytest.raises(RuntimeError, match=r"GAOKAO_PAYMENT_PROVIDER=foo"):
        _reload_settings()
