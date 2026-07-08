"""pytest 配置 (T6.1).

提供 fixture:
- settings: 内存 SQLite + 安全 JWT 密钥 + 短过期
- app: FastAPI 实例(lifespan 已运行 → admin 表已建 + bootstrap 用户)
- client: httpx TestClient
- auth_token: 登录后的 Bearer JWT
- auth_headers: {"Authorization": f"Bearer ..."}
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlsplit

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

# 确保项目根在 sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass
class RouteResponse:
    status_code: int
    headers: dict[str, str]
    text: str
    _json: object | None = None

    def json(self):
        if self._json is None:
            raise ValueError("response does not contain json payload")
        return self._json


class RouteClient:
    """基于直接路由调用的轻量测试 client，绕开当前环境中的 TestClient 挂起。"""

    def __init__(self, app):
        self.app = app
        self._started = False

    def __enter__(self):
        if not self._started:
            from admin.app import _setup_database, _validate_and_log_settings

            settings = self.app.state.settings
            _validate_and_log_settings(settings)
            _setup_database(settings)
            self._started = True
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @staticmethod
    def _request(
        path: str, *, method: str = "GET", headers: dict[str, str] | None = None
    ):
        split = urlsplit(path)
        raw_headers = [
            (key.lower().encode("utf-8"), value.encode("utf-8"))
            for key, value in (headers or {}).items()
        ]
        return Request(
            {
                "type": "http",
                "method": method,
                "path": split.path,
                "query_string": split.query.encode("utf-8"),
                "headers": raw_headers,
            }
        )

    @staticmethod
    def _html_response(response) -> RouteResponse:
        return RouteResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.body.decode("utf-8"),
        )

    @staticmethod
    def _json_response(
        payload: object,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> RouteResponse:
        return RouteResponse(
            status_code=status_code,
            headers=headers or {"content-type": "application/json"},
            text=json.dumps(payload, ensure_ascii=False),
            _json=payload,
        )

    @staticmethod
    def _redirect_response(response) -> RouteResponse:
        return RouteResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            text="",
        )

    @staticmethod
    def _http_exception_response(exc: HTTPException) -> RouteResponse:
        detail = exc.detail
        if isinstance(detail, str):
            payload = {"detail": {"reason": detail}}
        else:
            payload = {"detail": detail}
        return RouteClient._json_response(
            payload,
            status_code=exc.status_code,
        )

    @staticmethod
    def _validation_error_response(exc: ValidationError) -> RouteResponse:
        from admin.errors.codes import DATA_VALIDATION_FAILED
        from admin.errors.registry import get_message

        msg = get_message(str(DATA_VALIDATION_FAILED))
        payload = {
            "code": str(DATA_VALIDATION_FAILED),
            "message": msg.message,
            "suggestion": msg.suggestion,
            "severity": msg.severity,
            "retryable": msg.retryable,
            "detail": {
                "fields": [
                    {
                        "field": "body." + ".".join(str(part) for part in err["loc"]),
                        "reason": err["msg"],
                    }
                    for err in exc.errors()
                ]
            },
        }
        return RouteClient._json_response(payload, status_code=422)

    def get(self, path: str, **kwargs):
        """Direct-route GET helper for removed legacy page surfaces.

        The React/Vite app is the frontend. Legacy backend-rendered public GET
        pages intentionally return 404 in tests so stale UI cannot be reused.
        API/health/admin routes should use FastAPI TestClient directly.
        """
        split = urlsplit(path)
        route_path = split.path
        removed_public_gets = {
            "/",
            "/pricing",
            "/privacy",
            "/service-terms",
            "/deletion-policy",
            "/policy-center",
            "/same-score-reference",
            "/my-orders",
            "/my-reports",
            "/data-query",
            "/score-line-query",
            "/rank-estimator",
            "/majors-query",
            "/schools-query",
            "/compare-reports",
        }
        removed_portal_suffixes = (
            "/payment-success",
            "/status",
            "/info",
            "/cwb",
            "/full-plan",
            "/report",
            "/report.pdf",
            "/notifications",
            "/deletion-request",
        )
        if route_path in removed_public_gets or route_path.startswith("/checkout/"):
            return self._json_response({"detail": "legacy public page removed"}, status_code=404)
        if route_path.startswith("/portal/") and any(route_path.endswith(suffix) for suffix in removed_portal_suffixes):
            return self._json_response({"detail": "legacy portal HTML page removed"}, status_code=404)
        if route_path == "/portal/payment-return" or route_path == "/review/start":
            return self._json_response({"detail": "legacy public page removed"}, status_code=404)
        raise NotImplementedError(f"unsupported GET path in RouteClient: {path}")

    def post(self, path: str, **kwargs):
        from admin.routes.web_public import (
            complete_mock_payment,
            create_public_order_endpoint,
            mock_payment_webhook,
            review_action_endpoint,
        )
        from data.orders.public_flow import PublicOrderCreate

        split = urlsplit(path)
        route_path = split.path
        settings = self.app.state.settings
        payload = kwargs.get("json")
        form_data = kwargs.get("data") or {}

        try:
            if route_path == "/api/public/orders":
                try:
                    model = PublicOrderCreate.model_validate(payload or {})
                except ValidationError as exc:
                    return self._validation_error_response(exc)
                request = self._request(
                    path, method="POST", headers=kwargs.get("headers")
                )
                created = create_public_order_endpoint(model, request, settings)
                return self._json_response(created.model_dump(), status_code=201)
            if route_path.startswith("/pay/mock/") and route_path.endswith("/complete"):
                payment_id = route_path.split("/pay/mock/", 1)[1].rsplit(
                    "/complete", 1
                )[0]
                redirect = complete_mock_payment(payment_id, settings)
                return self._redirect_response(redirect)
            if route_path == "/api/public/payments/mock/webhook":
                request = self._request(
                    path, method="POST", headers=kwargs.get("headers")
                )
                ack = mock_payment_webhook(payload or {}, request, settings)
                return self._json_response(ack.model_dump())
            if route_path == "/review/action":
                result = review_action_endpoint(
                    token=str(
                        (payload or {}).get("token") or form_data.get("token") or ""
                    ),
                    action=cast(
                        Literal["cwb", "step1", "full_plan"],
                        str(
                            (payload or {}).get("action")
                            or form_data.get("action")
                            or ""
                        ),
                    ),
                    settings=settings,
                )
                return self._redirect_response(result)
        except HTTPException as exc:
            return self._http_exception_response(exc)

        raise NotImplementedError(f"unsupported POST path in RouteClient: {path}")


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
    ops_alert_log = str(tmp_path / "ops-alerts.jsonl")
    deletion_request_log = str(tmp_path / "deletion-requests.jsonl")
    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", db_path)
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", orders_db_path)
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", share_db_path)
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", share_report_dir)
    monkeypatch.setenv("GAOKAO_PORTAL_UPLOAD_DIR", portal_upload_dir)
    monkeypatch.setenv("GAOKAO_PORTAL_UPLOAD_MAX_BYTES", "5242880")
    monkeypatch.setenv("GAOKAO_PORTAL_UPLOAD_MAX_FILES", "5")
    monkeypatch.setenv("GAOKAO_OPS_ALERT_LOG", ops_alert_log)
    monkeypatch.setenv("GAOKAO_ALERT_RECIPIENTS", "")
    monkeypatch.setenv("GAOKAO_ALERT_WEBHOOK_URLS", "")
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", secure_secret)
    monkeypatch.setenv("GAOKAO_LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("GAOKAO_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")
    monkeypatch.setenv("GAOKAO_OPS_ALERT_LOG", ops_alert_log)
    monkeypatch.setenv("GAOKAO_DELETION_REQUEST_LOG", deletion_request_log)

    from admin.config import load_settings
    from data.orders import crypto

    crypto.get_fernet.cache_clear()

    return load_settings()


@pytest.fixture
def orders_db(settings):
    """T6.2 起:管理后台统计端点会读 orders 表,因此 conftest 顺带建一个
    空 orders DB (T4.1 schema),后续 dashboard 测试可在里面塞 fixture 数据。

    T-pending-intake 起: 同时建 order_intakes 表,确保 summary.pending_missing_intake
    的 LEFT JOIN 不会因为缺表而失败。
    """
    from data.orders.intake_store import SCHEMA_SQL as INTAKE_SCHEMA_SQL
    from data.orders.schema import apply_schema

    conn = apply_schema(settings.orders_db_path)
    conn.executescript(INTAKE_SCHEMA_SQL)
    conn.commit()
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
def route_client(app):
    """直接调用路由函数的轻量 client。"""
    with RouteClient(app) as c:
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


@pytest.fixture
def viewer_token(settings):
    from admin.auth import encode_token
    from admin.db import AdminUserRepo

    repo = AdminUserRepo(settings.db_path)
    viewer = repo.create("viewer", "viewer-pass-123", role="viewer")
    return encode_token(viewer, settings)


@pytest.fixture
def viewer_headers(viewer_token) -> dict:
    return {"Authorization": f"Bearer {viewer_token}"}
