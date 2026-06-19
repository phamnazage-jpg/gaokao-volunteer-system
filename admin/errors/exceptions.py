"""业务异常 + FastAPI 集成 (T9.2).

职责:
- BusinessError        : 业务异常类, 携带 ErrorCode
- error_response(...)   : 渲染为标准响应体 (与 OpenAPI 文档契约)
- register_exception_handler(app) : 把 BusinessError / HTTPException / 兜底异常
  全部统一到 { code, message, suggestion, severity, retryable, detail } 形状
"""

from __future__ import annotations

import inspect
import logging
import sys
from functools import wraps
from typing import Any, Callable, Mapping, Optional, TypeVar, cast

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from admin.errors.codes import ErrorCode, FALLBACK_CODE
from admin.errors.registry import Message, get_message
from admin.logging_utils import log_event, log_event_exc


logger = logging.getLogger("admin.errors")
F = TypeVar("F", bound=Callable[..., Any])


def catch(
    code: ErrorCode,
    *,
    reraise: bool = False,
) -> Callable[[F], F]:
    """捕获函数内部异常并统一记录/翻译为 ``BusinessError``.

    - ``BusinessError`` 直接透传，不重复包裹。
    - 其它 ``Exception`` 先打结构化异常日志，再按 ``reraise`` 决定：
      - ``False``: 转成 ``BusinessError(code)``
      - ``True``: 记录后原样抛出
    - 同时支持同步/异步函数。
    """

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except BusinessError:
                    raise
                except Exception as exc:
                    _log_caught_exception(func.__name__, code, exc)
                    if reraise:
                        raise
                    raise BusinessError(code) from exc

            return cast(F, async_wrapper)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except BusinessError:
                raise
            except Exception as exc:
                _log_caught_exception(func.__name__, code, exc)
                if reraise:
                    raise
                raise BusinessError(code) from exc

        return cast(F, sync_wrapper)

    return decorator


def _log_caught_exception(function_name: str, code: ErrorCode, exc: Exception) -> None:
    log_event_exc(
        logger,
        logging.ERROR,
        "caught_exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        msg=f"Caught exception in {function_name}",
        code=str(code),
        function=function_name,
    )


# ---------------- 响应体契约 ----------------
#
# {
#   "code":       "E01101",   # 业务错误码 (T9.1)
#   "message":    "...",      # 给用户看的中文消息 (T9.2)
#   "suggestion": "...",      # 给用户的解决建议 (T9.2)
#   "severity":   "warn",     # info/warn/error
#   "retryable":  false,      # 是否可重试
#   "detail":     {...}       # 可选, 调试用上下文 (生产环境按 env 开关)
# }


# ---------------- 异常类 ----------------


class BusinessError(Exception):
    """业务异常 — 路由层抛出会被全局 handler 捕获并渲染.

    使用示例::

        if user is None:
            raise BusinessError(AUTH_INVALID_CREDENTIALS)
        if not user.is_active:
            raise BusinessError(AUTH_ACCOUNT_DISABLED, detail={"user_id": user.id})
    """

    def __init__(
        self,
        code: ErrorCode,
        *,
        detail: Optional[Mapping[str, Any]] = None,
        locale: str = "zh-CN",
        http_status: Optional[int] = None,
    ) -> None:
        super().__init__(str(code))
        self.code = code
        self.detail = dict(detail) if detail else None
        self.locale = locale
        self.http_status = http_status  # 显式覆盖时用, 如某些 4xx 业务码强制 401


def error_response(
    code: str,
    message: Message,
    *,
    detail: Optional[Mapping[str, Any]] = None,
    include_detail: bool = False,
) -> dict:
    """组装标准响应体."""
    body = {
        "code": code,
        "message": message.message,
        "suggestion": message.suggestion,
        "severity": message.severity,
        "retryable": message.retryable,
    }
    if include_detail and detail:
        body["detail"] = dict(detail)
    return body


# ---------------- HTTP 状态码映射 ----------------
#
# 业务码 → 默认 HTTP 状态码. 同一 HTTP 状态可对应多个业务码, 但不同业务码
# 渲染的中文文案不同 (T9.1 决策: 业务码与 HTTP 状态码解耦).

# 兼容 starlette 新旧命名 (HTTP_422_UNPROCESSABLE_ENTITY → HTTP_422_UNPROCESSABLE_CONTENT).
# 旧 starlette 没有 HTTP_422_UNPROCESSABLE_CONTENT, 但 HTTP_422 数值就是 422.
_HTTP_422: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422


_DEFAULT_HTTP_STATUS: Mapping[str, int] = {
    # 01 用户域
    "E01101": status.HTTP_401_UNAUTHORIZED,
    "E01102": status.HTTP_403_FORBIDDEN,
    "E01201": status.HTTP_401_UNAUTHORIZED,
    "E01202": status.HTTP_401_UNAUTHORIZED,
    "E01301": status.HTTP_403_FORBIDDEN,
    # 02 业务域
    "E02001": status.HTTP_404_NOT_FOUND,
    "E02002": status.HTTP_409_CONFLICT,
    "E02301": status.HTTP_409_CONFLICT,
    "E02501": status.HTTP_429_TOO_MANY_REQUESTS,
    # 03 数据域
    "E03001": _HTTP_422,
    "E03002": status.HTTP_404_NOT_FOUND,
    "E03003": status.HTTP_500_INTERNAL_SERVER_ERROR,
    # 04 第三方域
    "E04001": status.HTTP_502_BAD_GATEWAY,
    "E04002": status.HTTP_504_GATEWAY_TIMEOUT,
    # 05 系统域
    "E05001": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "E05002": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "E05003": status.HTTP_503_SERVICE_UNAVAILABLE,
}

_WWW_AUTHENTICATE_BEARER_CODES = {
    "E01201",  # AUTH_TOKEN_EXPIRED
    "E01202",  # AUTH_TOKEN_INVALID
}


def http_status_for(code: str) -> int:
    """业务码 → HTTP 状态码 (无显式映射时默认 400)."""
    return _DEFAULT_HTTP_STATUS.get(code, status.HTTP_400_BAD_REQUEST)


# ---------------- FastAPI handler ----------------


def register_exception_handler(app: FastAPI) -> None:
    """注册全局异常 handler (在 create_app 内调用)."""

    @app.exception_handler(BusinessError)
    async def _handle_business_error(request: Request, exc: BusinessError):
        code_str = str(exc.code)
        msg = get_message(code_str, locale=exc.locale)
        http_status = exc.http_status or http_status_for(code_str)
        body = error_response(
            code=code_str,
            message=msg,
            detail=exc.detail,
            include_detail=exc.detail is not None,
        )
        log_event(
            logger,
            logging.WARNING,
            "business_error",
            msg=f"BusinessError code={code_str} status={http_status}",
            code=code_str,
            path=request.url.path,
            method=request.method,
            status=http_status,
        )
        headers = None
        if code_str in _WWW_AUTHENTICATE_BEARER_CODES:
            headers = {"WWW-Authenticate": "Bearer"}
        return JSONResponse(status_code=http_status, content=body, headers=headers)

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(request: Request, exc: HTTPException):
        """未升级为 BusinessError 的 FastAPI 内置异常 — 走兜底文案.

        目的: 即使路由层忘了用 BusinessError, 用户也能看到中文提示, 而不是裸 500.
        """
        fallback_code_str = str(FALLBACK_CODE)
        msg = get_message(fallback_code_str)
        # detail 是字符串时透传, 否则只记日志不暴露给用户
        original_detail = exc.detail if isinstance(exc.detail, str) else None
        body = error_response(
            code=fallback_code_str,
            message=msg,
            detail={"http_status": exc.status_code, "reason": original_detail}
            if original_detail
            else None,
            include_detail=original_detail is not None,
        )
        log_event(
            logger,
            logging.WARNING,
            "http_exception_fallback",
            msg=f"HTTPException status={exc.status_code} mapped to BusinessError",
            path=request.url.path,
            method=request.method,
            status=exc.status_code,
        )
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError):
        """422 pydantic 校验失败 → DATA_VALIDATION_FAILED 业务码."""
        from admin.errors.codes import DATA_VALIDATION_FAILED

        msg = get_message(str(DATA_VALIDATION_FAILED))
        # 错误字段摘要: 取每个错误的 loc + msg, 不暴露内部值
        field_errors = [
            {
                "field": ".".join(str(p) for p in err.get("loc", [])),
                "reason": err.get("msg"),
            }
            for err in exc.errors()
        ]
        body = error_response(
            code=str(DATA_VALIDATION_FAILED),
            message=msg,
            detail={"fields": field_errors},
            include_detail=True,
        )
        log_event(
            logger,
            logging.INFO,
            "validation_error",
            msg=f"ValidationError fields={len(field_errors)}",
            path=request.url.path,
            method=request.method,
            code_count=len(field_errors),
        )
        return JSONResponse(
            status_code=_HTTP_422,
            content=body,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception):
        """任何未捕获异常 → SYS_INTERNAL_ERROR + 兜底文案.

        注意: 不在响应里暴露 traceback / 异常类名 (信息泄露面), 仅日志记录.
        """
        from admin.errors.codes import SYS_INTERNAL_ERROR

        msg = get_message(str(SYS_INTERNAL_ERROR))
        log_event_exc(
            logger,
            logging.ERROR,
            "unhandled_exception",
            exc_info=sys.exc_info(),
            msg="Unhandled exception (mapped to SYS_INTERNAL_ERROR)",
            path=request.url.path,
            method=request.method,
        )
        body = error_response(
            code=str(SYS_INTERNAL_ERROR),
            message=msg,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body,
        )
