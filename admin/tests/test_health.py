from __future__ import annotations


def test_health_endpoint_returns_minimal_readiness_only(client):
    """公开健康检查：保持 `status: ok` 主键 + 详细 checks 字段。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    # 主键契约：status 必须存在且为 ok（PRODUCTION_DEPLOYMENT_CHECKLIST §4）
    assert body.get("status") == "ok"
    # 6/20 加固：增 checks 子对象，断言关键 readiness 字段
    assert "checks" in body
    checks = body["checks"]
    assert checks.get("db_writable") is True
    assert checks.get("disk_writable") is True
    # settings_valid=True 意味着默认 dev 环境允许本地占位密钥，prod 仍由 load_settings fail-closed 测试覆盖
    assert checks.get("settings_valid") is True


def test_load_settings_prod_rejects_dev_jwt_secret(monkeypatch, tmp_path):
    """GAOKAO_ENV=prod 时使用 dev 默认 JWT secret 必须 fail-closed。"""
    import pytest
    from admin.config import load_settings

    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv(
        "GAOKAO_JWT_SECRET", "dev-only-do-not-use-in-prod-please-override-via-env"
    )
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "x" * 32)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "y" * 32)
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "StrongPass1!")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv("GAOKAO_LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("GAOKAO_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(tmp_path / "orders.db"))
    monkeypatch.setenv("GAOKAO_DB_PATH", str(tmp_path / "admin.db"))

    with pytest.raises(RuntimeError, match="JWT.*dev|JWT.*prod|密钥"):
        load_settings()


def test_load_settings_prod_rejects_short_jwt_secret(monkeypatch, tmp_path):
    """GAOKAO_ENV=prod 时 JWT secret 长度 < 32 必须 fail-closed。"""
    import pytest
    from admin.config import load_settings

    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "short_secret_under_32")
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "x" * 32)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "y" * 32)
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "StrongPass1!")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv("GAOKAO_LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("GAOKAO_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(tmp_path / "orders.db"))
    monkeypatch.setenv("GAOKAO_DB_PATH", str(tmp_path / "admin.db"))

    with pytest.raises(RuntimeError, match="JWT.*长度|32"):
        load_settings()


def test_load_settings_prod_rejects_default_admin_password(monkeypatch, tmp_path):
    """GAOKAO_ENV=prod 时 GAOKAO_ADMIN_PASS=admin123 必须 fail-closed。"""
    import pytest
    from admin.config import load_settings

    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "z" * 32)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "x" * 32)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "y" * 32)
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "admin123")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay")
    monkeypatch.setenv("GAOKAO_LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("GAOKAO_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(tmp_path / "orders.db"))
    monkeypatch.setenv("GAOKAO_DB_PATH", str(tmp_path / "admin.db"))

    with pytest.raises(RuntimeError, match="admin|默认管理员密码"):
        load_settings()
