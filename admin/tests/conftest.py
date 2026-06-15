"""pytest 配置 (T6.1).

提供 fixture:
- settings: 内存 SQLite + 安全 JWT 密钥 + 短过期
- app: FastAPI 实例(lifespan 已运行 → admin 表已建 + bootstrap 用户)
- client: httpx TestClient
- auth_token: 登录后的 Bearer JWT
- auth_headers: {"Authorization": f"Bearer ..."}
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 确保项目根在 sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def secure_secret() -> str:
    """64-char 安全 JWT 密钥。"""
    return "x" * 64  # 确定性,便于测试断言


@pytest.fixture
def settings(tmp_path, secure_secret, monkeypatch):
    """隔离的 Settings 实例:tmp_path SQLite + 安全密钥 + 短过期。

    用真实文件而不是 :memory: 是因为 admin/db.py 中每次 get_connection
    都新建连接,:memory: 在 SQLite 下不共享状态。
    """
    db_path = str(tmp_path / "admin.db")
    orders_db_path = str(tmp_path / "orders.db")
    share_db_path = str(tmp_path / "short_links.db")
    share_report_dir = str(tmp_path / "share_reports")
    portal_upload_dir = str(tmp_path / "portal_uploads")
    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", db_path)
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", orders_db_path)
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", share_db_path)
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", share_report_dir)
    monkeypatch.setenv("GAOKAO_PORTAL_UPLOAD_DIR", portal_upload_dir)
    monkeypatch.setenv("GAOKAO_PORTAL_UPLOAD_MAX_BYTES", "5242880")
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", secure_secret)
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")

    from admin.config import load_settings

    return load_settings()


@pytest.fixture
def orders_db(settings):
    """T6.2 起:管理后台统计端点会读 orders 表,因此 conftest 顺带建一个
    空 orders DB (T4.1 schema),后续 dashboard 测试可在里面塞 fixture 数据。
    """
    from data.orders.schema import apply_schema

    conn = apply_schema(settings.orders_db_path)
    conn.close()
    return settings.orders_db_path


@pytest.fixture(autouse=True)
def _auto_orders_db(settings, orders_db):
    """所有测试都默认有空 orders DB 可用,避免 T6.2 端点在不相关测试里
    报 'no such table: orders'。``orders_db`` 显式依赖确保已建。
    """
    return orders_db


@pytest.fixture(autouse=True)
def _reset_login_rate_limit():
    from admin.routes.auth import reset_login_rate_limit_for_tests

    reset_login_rate_limit_for_tests()
    yield
    reset_login_rate_limit_for_tests()


@pytest.fixture
def app(settings):
    """FastAPI 实例（lifespan 已运行）。"""
    from admin.app import create_app

    return create_app(settings)


@pytest.fixture
def client(app):
    """httpx TestClient。"""
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client) -> str:
    """登录后返回 Bearer JWT。"""
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-pass-123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
