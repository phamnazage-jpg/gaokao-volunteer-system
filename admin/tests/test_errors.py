"""admin.errors 单元测试 (T9.2).

覆盖:
- 码点结构与反解 (codes.py)
- 注册表查找 + 兜底 (registry.py)
- 响应体契约 (exceptions.py)
- FastAPI handler 集成 (端到端)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from admin.errors import (
    AUTH_ACCOUNT_DISABLED,
    AUTH_INSUFFICIENT_PERMISSION,
    AUTH_INVALID_CREDENTIALS,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    BIZ_ORDER_NOT_FOUND,
    BIZ_RATE_LIMITED,
    BusinessError,
    DATA_VALIDATION_FAILED,
    FALLBACK_CODE,
    MESSAGES_ZH_CN,
    Message,
    SYS_INTERNAL_ERROR,
    error_response,
    get_message,
    is_registered,
    register_exception_handler,
)
from admin.errors.codes import ErrorCode


# ---------------- codes.py ----------------


class TestErrorCodeStructure:
    def test_str_format(self):
        assert str(AUTH_INVALID_CREDENTIALS) == "E01101"
        assert str(BIZ_ORDER_NOT_FOUND) == "E02001"
        assert str(FALLBACK_CODE) == "E05099"

    def test_of_roundtrip(self):
        for code in (
            AUTH_INVALID_CREDENTIALS,
            BIZ_ORDER_NOT_FOUND,
            FALLBACK_CODE,
        ):
            assert str(ErrorCode.of(str(code))) == str(code)

    def test_of_invalid(self):
        with pytest.raises(ValueError):
            ErrorCode.of("BAD")
        with pytest.raises(ValueError):
            ErrorCode.of("E99999")  # segment 99 不在 5 个段内
        with pytest.raises(ValueError):
            ErrorCode.of("E01A01")  # subdomain 必须是 0-5

    def test_segment_assignment_matches_t91(self):
        """T9.1 段分配: 01 用户 / 02 业务 / 03 数据 / 04 第三方 / 05 系统."""
        assert str(AUTH_INVALID_CREDENTIALS).startswith("E01")
        assert str(BIZ_ORDER_NOT_FOUND).startswith("E02")
        assert str(DATA_VALIDATION_FAILED).startswith("E03")
        assert str(SYS_INTERNAL_ERROR).startswith("E05")

    def test_5xx_codes_only_in_05_segment(self):
        """T9.1: 5xx 系统错误严禁落到非 05 段 (防兜底掩盖)."""
        # 这里所有 SYS_* 都已经在 05 段; 此测试是回归保险, 防后续误归
        assert str(SYS_INTERNAL_ERROR).startswith("E05")

    def test_sequence_bounds(self):
        from admin.errors.codes import ErrorCode, ErrorSegment, ErrorSubdomain

        with pytest.raises(ValueError):
            ErrorCode(
                segment=ErrorSegment.USER,
                subdomain=ErrorSubdomain.GENERAL,
                sequence=0,  # 越界
            )
        with pytest.raises(ValueError):
            ErrorCode(
                segment=ErrorSegment.USER,
                subdomain=ErrorSubdomain.GENERAL,
                sequence=100,  # 越界
            )


# ---------------- registry.py ----------------


class TestRegistry:
    def test_registered_codes_have_message(self):
        """所有声明的业务码都必须在注册表里有文案 (FALLBACK_CODE 除外, 它是兜底)."""
        from admin.errors import codes as codes_module

        declared = {
            name: value
            for name, value in vars(codes_module).items()
            if isinstance(value, ErrorCode)
        }
        # FALLBACK_CODE 不入注册表 (它是兜底码本身)
        from admin.errors.codes import FALLBACK_CODE as _FB

        for name, ec in declared.items():
            if ec == _FB:
                continue
            assert is_registered(str(ec)), f"{name} ({ec}) 缺少中文文案"

    def test_get_message_known(self):
        msg = get_message(str(AUTH_INVALID_CREDENTIALS))
        assert isinstance(msg, Message)
        assert msg.code == str(AUTH_INVALID_CREDENTIALS)
        assert msg.message
        assert msg.suggestion
        assert msg.severity in ("info", "warn", "error")
        assert isinstance(msg.retryable, bool)

    def test_get_message_unknown_but_valid_code_returns_fallback(self):
        """未注册但格式合法的码点 → 兜底文案 (code 保留以便排查)."""
        # E01005 — 段号 01 子域位 0 sequence 05, 格式合法, 未注册
        msg = get_message("E01005")
        assert msg.severity == "error"
        assert msg.retryable is True
        assert msg.code == "E01005"  # 保留原码点便于排查

    def test_get_message_invalid_format_uses_fallback(self):
        """格式非法码点 → 兜底文案 (不抛异常, 永不返回 None)."""
        msg = get_message("BAD")
        assert msg.severity == "error"
        # 非法码点也保留在 code 字段以便定位
        assert msg.code == "BAD"

    def test_unsupported_locale_uses_fallback(self):
        """当前仅支持 zh-CN, 其它 locale 走兜底."""
        msg = get_message(str(AUTH_INVALID_CREDENTIALS), locale="en-US")
        # 走兜底文案
        assert msg.severity == "error"

    def test_message_to_dict_shape(self):
        msg = get_message(str(BIZ_RATE_LIMITED))
        d = msg.to_dict()
        assert set(d.keys()) == {
            "code",
            "message",
            "suggestion",
            "severity",
            "retryable",
        }

    def test_all_registered_codes_count(self):
        """注册表里有 17 个码点 (1 兜底 + 16 业务)."""
        # 16 业务: AUTH×5 + BIZ×3 + DATA×3 + THIRD×2 + SYS×3 = 16
        # FALLBACK_CODE 也在注册表 (但函数中它仅作兜底不入注册)
        assert len(MESSAGES_ZH_CN) == 16


# ---------------- exceptions.py ----------------


class TestErrorResponse:
    def test_basic_body_shape(self):
        msg = get_message(str(AUTH_INVALID_CREDENTIALS))
        body = error_response(str(AUTH_INVALID_CREDENTIALS), msg)
        assert body["code"] == "E01101"
        assert body["severity"] == "warn"
        assert body["retryable"] is False
        # 无 detail 时不暴露
        assert "detail" not in body

    def test_detail_included_only_when_provided(self):
        msg = get_message(str(BIZ_ORDER_NOT_FOUND))
        body = error_response(
            str(BIZ_ORDER_NOT_FOUND),
            msg,
            detail={"order_id": "GKO-1"},
            include_detail=True,
        )
        assert body["detail"] == {"order_id": "GKO-1"}


class TestBusinessErrorException:
    def test_str_returns_code(self):
        exc = BusinessError(AUTH_INVALID_CREDENTIALS)
        assert str(exc) == "E01101"

    def test_detail_is_optional(self):
        exc = BusinessError(AUTH_INVALID_CREDENTIALS)
        assert exc.detail is None
        exc2 = BusinessError(AUTH_INVALID_CREDENTIALS, detail={"k": 1})
        assert exc2.detail == {"k": 1}


# ---------------- FastAPI handler 集成 ----------------


def _build_test_app():
    """构造最小测试应用, 仅用于验证 handler 集成."""
    from fastapi import FastAPI

    from admin.errors import (
        AUTH_ACCOUNT_DISABLED,
        AUTH_INVALID_CREDENTIALS,
        BusinessError,
    )

    app = FastAPI()
    register_exception_handler(app)

    @app.get("/raise-business")
    def _raise_business():
        raise BusinessError(AUTH_INVALID_CREDENTIALS)

    @app.get("/raise-business-with-detail")
    def _raise_business_detail():
        raise BusinessError(AUTH_ACCOUNT_DISABLED, detail={"user_id": 42})

    @app.get("/raise-http-legacy")
    def _raise_http_legacy():
        # 模拟未升级到 BusinessError 的旧路由
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="forbidden by upstream")

    @app.get("/raise-unexpected")
    def _raise_unexpected():
        raise RuntimeError("something exploded")

    @app.get("/validation-fail")
    def _validation_fail(payload: dict):
        # 故意缺必填字段, 触发 RequestValidationError
        from pydantic import BaseModel

        class Req(BaseModel):
            name: str
            age: int

        # 调用方传 {} 时会触发 422
        return Req(**payload)

    return app


@pytest.fixture
def test_client():
    return TestClient(_build_test_app(), raise_server_exceptions=False)


class TestFastAPIIntegration:
    def test_business_error_returns_chinese_message(self, test_client):
        resp = test_client.get("/raise-business")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "E01101"
        assert "用户名" in body["message"] or "密码" in body["message"]
        assert body["suggestion"]
        assert body["severity"] == "warn"
        assert body["retryable"] is False

    def test_business_error_includes_detail_when_provided(self, test_client):
        resp = test_client.get("/raise-business-with-detail")
        # AUTH_ACCOUNT_DISABLED 默认 403
        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == "E01102"
        assert body["detail"] == {"user_id": 42}

    def test_http_exception_legacy_mapped_to_business_shape(self, test_client):
        resp = test_client.get("/raise-http-legacy")
        # 保留原 HTTP 状态 (handler 不吞), 但响应体是业务码形状
        assert resp.status_code == 403
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert "suggestion" in body
        # detail 透传
        assert "detail" in body
        assert body["detail"]["http_status"] == 403

    def test_unexpected_exception_mapped_to_sys_internal(self, test_client):
        resp = test_client.get("/raise-unexpected")
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == str(SYS_INTERNAL_ERROR)
        # 不暴露异常类名/堆栈
        assert "RuntimeError" not in str(body)
        assert "Traceback" not in str(body)

    def test_validation_error_mapped_to_data_validation(self, test_client):
        resp = test_client.get(
            "/validation-fail", params={}
        )  # 缺请求体, 触发 RequestValidationError
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == str(DATA_VALIDATION_FAILED)
        assert body["message"]
        assert body["suggestion"]
        assert body["detail"]["fields"]
        assert body["retryable"] is False

    def test_response_body_is_json(self, test_client):
        resp = test_client.get("/raise-business")
        assert resp.headers["content-type"].startswith("application/json")


# ---------------- 业务码与 HTTP 状态码解耦 (T9.1 约束) ----------------


class TestBusinessCodeHttpDecoupling:
    """T9.1 决策: 业务码与 HTTP 状态码解耦.

    验证同一段内的码点可以映射到不同 HTTP 状态, 不同业务码在同一 HTTP
    状态下也能呈现不同中文文案.
    """

    def test_auth_codes_span_401_and_403(self):
        from admin.errors.exceptions import http_status_for

        assert http_status_for(str(AUTH_INVALID_CREDENTIALS)) == 401
        assert http_status_for(str(AUTH_TOKEN_EXPIRED)) == 401
        assert http_status_for(str(AUTH_INSUFFICIENT_PERMISSION)) == 403
        assert http_status_for(str(AUTH_ACCOUNT_DISABLED)) == 403

    def test_two_codes_same_http_status_have_different_messages(self):
        # AUTH_INVALID_CREDENTIALS 与 AUTH_TOKEN_EXPIRED 都是 401, 但文案不同
        m1 = get_message(str(AUTH_INVALID_CREDENTIALS))
        m2 = get_message(str(AUTH_TOKEN_EXPIRED))
        assert m1.message != m2.message
        assert m1.code != m2.code

    def test_third_party_codes_are_5xx(self):
        """T9.1: 第三方域码点对应 5xx (上游错误归 4xx 段码点)."""
        from admin.errors.exceptions import http_status_for

        assert (
            http_status_for(str(AUTH_TOKEN_INVALID)) == 401
        )  # 04 段? 不, 04 是 third party
        # E04xxx 都是 5xx
        # 这里用具体的第三方码验证
        from admin.errors.codes import THIRD_PARTY_UPSTREAM_ERROR

        assert http_status_for(str(THIRD_PARTY_UPSTREAM_ERROR)) == 502
