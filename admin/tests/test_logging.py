"""T9.3 结构化日志测试.

覆盖:
- JsonLogFormatter: 时间 / 级别 / logger / ctx / exc
- log_event / log_event_exc: 结构化字段注入、异常捕获
- request context: bind / clear / middleware 隔离
- FastAPI 端到端: BusinessError 触发 JSON 日志, 含 code/path/method/request_id
"""

from __future__ import annotations

import io
import json
import logging
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from admin.errors import (
    AUTH_INVALID_CREDENTIALS,
    BusinessError,
    register_exception_handler,
)
from admin.logging_utils import (
    JsonLogFormatter,
    bind_request_context,
    clear_request_context,
    configure_logging,
    current_context,
    log_event,
    log_event_exc,
    reset_logging_for_tests,
)


class TestJsonLogFormatter:
    def test_formats_basic_record_with_ctx(self):
        formatter = JsonLogFormatter()
        token = bind_request_context(request_id="req_test", path="/api/x", method="GET")
        try:
            record = logging.LogRecord(
                name="admin.errors",
                level=logging.WARNING,
                pathname=__file__,
                lineno=10,
                msg="hello %s",
                args=("world",),
                exc_info=None,
            )
            record.ctx = {"code": "E01101", "event": "business_error"}
            payload = json.loads(formatter.format(record))
        finally:
            clear_request_context(token)

        assert payload["level"] == "warning"
        assert payload["logger"] == "admin.errors"
        assert payload["msg"] == "hello world"
        assert payload["ts"].endswith("Z")
        assert payload["ctx"]["code"] == "E01101"
        assert payload["ctx"]["event"] == "business_error"
        assert payload["ctx"]["request_id"] == "req_test"
        assert payload["ctx"]["path"] == "/api/x"
        assert payload["ctx"]["method"] == "GET"

    def test_formats_exception(self):
        formatter = JsonLogFormatter()
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            record = logging.LogRecord(
                name="admin.errors",
                level=logging.ERROR,
                pathname=__file__,
                lineno=20,
                msg="failed",
                args=(),
                exc_info=sys.exc_info(),
            )
        payload = json.loads(formatter.format(record))
        assert payload["level"] == "error"
        assert payload["exc"]["type"] == "RuntimeError"
        assert payload["exc"]["message"] == "boom"
        assert "RuntimeError: boom" in payload["exc"]["traceback"]


class TestContextBinding:
    def test_bind_and_clear(self):
        assert current_context() == {}
        token = bind_request_context(request_id="req_1", path="/a", method="POST")
        try:
            assert current_context() == {
                "request_id": "req_1",
                "path": "/a",
                "method": "POST",
            }
        finally:
            clear_request_context(token)
        assert current_context() == {}


class TestLogEvent:
    def test_log_event_emits_json_with_ctx(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)
        logger = logging.getLogger("admin.errors")

        log_event(
            logger,
            logging.WARNING,
            "business_error",
            msg="business error mapped",
            code="E01101",
            path="/api/auth/login",
            method="POST",
            status=401,
        )

        line = stream.getvalue().strip()
        payload = json.loads(line)
        assert payload["level"] == "warning"
        assert payload["msg"] == "business error mapped"
        assert payload["ctx"]["event"] == "business_error"
        assert payload["ctx"]["code"] == "E01101"
        assert payload["ctx"]["path"] == "/api/auth/login"
        assert payload["ctx"]["method"] == "POST"
        assert payload["ctx"]["status"] == 401

    def test_log_event_rejects_reserved_field(self):
        logger = logging.getLogger("admin.errors")
        with pytest.raises(ValueError, match="collides with LogRecord builtin"):
            log_event(logger, logging.INFO, "bad", name="oops")

    def test_log_event_exc_includes_traceback(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)
        logger = logging.getLogger("admin.errors")

        try:
            raise ValueError("x")
        except ValueError:
            log_event_exc(
                logger,
                logging.ERROR,
                "unhandled_exception",
                exc_info=sys.exc_info(),
                msg="unhandled",
                path="/boom",
                method="GET",
            )

        payload = json.loads(stream.getvalue().strip())
        assert payload["level"] == "error"
        assert payload["ctx"]["event"] == "unhandled_exception"
        assert payload["exc"]["type"] == "ValueError"
        assert payload["exc"]["message"] == "x"

    def test_large_log_stays_valid_json(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)
        logger = logging.getLogger("admin.errors")

        log_event(
            logger,
            logging.WARNING,
            "oversized_payload",
            msg="payload too large",
            fields=["x" * 12000],
        )

        encoded = stream.getvalue().strip()
        payload = json.loads(encoded)
        assert payload["msg"] == "payload too large"
        assert payload["ctx"]["event"] == "oversized_payload"
        assert payload["ctx"].get("truncated") is True
        assert len(encoded.encode("utf-8")) <= 8 * 1024

    def test_huge_message_is_also_capped(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)
        logger = logging.getLogger("admin.errors")

        logger.error("m" * 20000)

        encoded = stream.getvalue().strip()
        payload = json.loads(encoded)
        assert payload["ctx"]["truncated"] is True
        assert len(encoded.encode("utf-8")) <= 8 * 1024


class TestFastAPIStructuredIntegration:
    def test_business_error_log_contains_request_context(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)

        app = FastAPI()

        from admin.app import request_context_middleware

        app.middleware("http")(request_context_middleware)

        @app.get("/boom")
        async def _boom():
            raise BusinessError(AUTH_INVALID_CREDENTIALS)

        register_exception_handler(app)

        with TestClient(app) as client:
            resp = client.get("/boom")

        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "E01101"

        lines = [
            json.loads(line) for line in stream.getvalue().splitlines() if line.strip()
        ]
        business_logs = [
            line
            for line in lines
            if line.get("ctx", {}).get("event") == "business_error"
        ]
        assert business_logs, stream.getvalue()
        payload = business_logs[-1]
        assert payload["logger"] == "admin.errors"
        assert payload["ctx"]["code"] == "E01101"
        assert payload["ctx"]["path"] == "/boom"
        assert payload["ctx"]["method"] == "GET"
        assert payload["ctx"]["status"] == 401
        assert payload["ctx"]["request_id"].startswith("req_")

    def test_validation_error_log_contains_request_context(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)

        app = FastAPI()

        from pydantic import BaseModel
        from admin.app import request_context_middleware

        app.middleware("http")(request_context_middleware)

        class Payload(BaseModel):
            username: str

        @app.post("/validate")
        async def _validate(payload: Payload):
            return {"username": payload.username}

        register_exception_handler(app)

        with TestClient(app) as client:
            resp = client.post("/validate", json={})

        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "E03001"

        lines = [
            json.loads(line) for line in stream.getvalue().splitlines() if line.strip()
        ]
        validation_logs = [
            line
            for line in lines
            if line.get("ctx", {}).get("event") == "validation_error"
        ]
        assert validation_logs, stream.getvalue()
        payload = validation_logs[-1]
        assert payload["logger"] == "admin.errors"
        assert payload["ctx"]["path"] == "/validate"
        assert payload["ctx"]["method"] == "POST"
        assert payload["ctx"]["request_id"].startswith("req_")
        assert payload["ctx"]["code_count"] >= 1
