"""结构化 JSON 日志 (T9.3).

职责:
- ``JsonLogFormatter``     : 把 ``LogRecord`` 编码成单行 JSON (含 ctx / exc)
- ``log_event(...)``       : 业务代码一行写结构化事件, 自动走 ctx 字段
- ``bind_request_context`` : per-request 上下文, 通过 ``contextvars`` 跨异步安全传递
- ``configure_logging``    : 在 CLI 入口 / 测试夹具里安装 formatter

设计要点 (详见 docs/plans/T9-error-handling.md §4):
- 零第三方依赖, 仅 stdlib ``logging`` + ``contextvars`` + ``json``
- 不破坏既有 ``logger.info("msg %s", x)`` 形态, 但鼓励 ``log_event`` 走结构化
- 单元测试可直接读 ``LogRecord``, 不依赖 formatter 编码

schema (顶层)::

    {
      "ts":     "2026-06-12T16:30:01.234Z",  # ISO-8601 UTC with ms
      "level":  "warning",
      "logger": "admin.errors",
      "msg":    "...",                       # 渲染后的文本
      "ctx":    {...},                        # 结构化字段 (per-request 上下文 + log_event fields)
      "exc":    {"type":..., "message":..., "traceback":...}  # 异常时才有
    }
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---------------- per-request 上下文 (ContextVar) ----------------
#
# 异步安全: contextvars 在 asyncio 任务切换时自动跟随, 不同请求之间不会污染.
# 同步代码同样工作 (Python 3.7+).

_request_ctx: ContextVar[Dict[str, Any]] = ContextVar("admin_request_ctx", default={})


def bind_request_context(**fields: Any) -> Token[Dict[str, Any]]:
    """写入 per-request 上下文, 返回 token 用于 ``clear_request_context``.

    用法 (FastAPI middleware)::

        @app.middleware("http")
        async def ctx_middleware(request, call_next):
            token = bind_request_context(
                request_id=generate_request_id(),
                path=request.url.path,
                method=request.method,
            )
            try:
                return await call_next(request)
            finally:
                clear_request_context(token)
    """
    base = dict(_request_ctx.get())
    base.update(fields)
    return _request_ctx.set(base)


def clear_request_context(token: Token[Dict[str, Any]]) -> None:
    """释放 ``bind_request_context`` 写入的上下文."""
    _request_ctx.reset(token)


def current_context() -> Dict[str, Any]:
    """读取当前 per-request 上下文的快照 (拷贝)."""
    return dict(_request_ctx.get())


# ---------------- JsonLogFormatter ----------------


# LogRecord 默认有 20+ 属性, 不应直接整对象 dict().
# 安全白名单: 只有这些键允许作为 ctx 字段透传.
_CTX_SAFE_KEYS = frozenset(
    {
        "code",
        "path",
        "method",
        "request_id",
        "user_id",
        "status",
        "event",
        "duration_ms",
        "code_count",
        "http_status",
        "fields",
        "function",
    }
)


# 单条日志最大体积, 超过截断 (防 traceback 巨大撑爆日志).
_MAX_TRACEBACK_CHARS = 4096
_MAX_LOG_BYTES = 8 * 1024


class JsonLogFormatter(logging.Formatter):
    """把 ``LogRecord`` 编码为单行 JSON 字符串.

    字段顺序 (稳定)::

        ts, level, logger, msg, ctx, exc?

    设计权衡:
    - ``msg`` 字段保留渲染后的纯文本, 兼容 ``grep`` / 旧日志栈.
    - ``ctx`` 字段把结构化字段从 ``LogRecord.__dict__`` / ``extra`` 抽出来,
      排障时可以 ``jq '.ctx.code'`` 直接取值.
    - ``exc`` 仅在 ``record.exc_info`` 存在时输出, 且对 ``traceback`` 长度设上限.
    """

    def __init__(self, *, ensure_ascii: bool = False) -> None:
        super().__init__()
        self._ensure_ascii = ensure_ascii

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003 - stdlib API
        payload: Dict[str, Any] = {
            "ts": _format_ts(record.created),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }

        ctx = _extract_ctx(record)
        ctx.update(current_context())
        if ctx:
            payload["ctx"] = ctx

        if record.exc_info:
            payload["exc"] = _format_exc(record)

        text = json.dumps(payload, ensure_ascii=self._ensure_ascii, default=str)
        if len(text.encode("utf-8")) <= _MAX_LOG_BYTES:
            return text

        compact = _compact_payload(payload)
        text = json.dumps(compact, ensure_ascii=self._ensure_ascii, default=str)
        if len(text.encode("utf-8")) <= _MAX_LOG_BYTES:
            return text

        # 仍然过大时，保底只保留基础字段，避免输出非法 JSON。
        fallback = {
            "ts": payload["ts"],
            "level": payload["level"],
            "logger": payload["logger"],
            "msg": _truncate_text(str(payload["msg"]), 512),
            "ctx": {"truncated": True},
        }
        if "exc" in payload:
            fallback["exc"] = {
                "type": payload["exc"].get("type", "Unknown"),
                "message": _truncate_text(str(payload["exc"].get("message", "")), 256),
                "traceback": "...truncated",
                "truncated": True,
            }
        return json.dumps(fallback, ensure_ascii=self._ensure_ascii, default=str)


# ---------------- log_event helper ----------------


# LogRecord.__dict__ 已存在的属性 (LogRecord 自带, 与 extra 冲突时优先 builtin).
# 避免 ``extra={"name": ...}`` 把 record.name 覆盖掉.
_RESERVED_LOGRECORD_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "asctime",
        "message",
        "taskName",
    }
)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    msg: Optional[str] = None,
    **fields: Any,
) -> None:
    """写一条结构化事件. ``fields`` 会作为 ``ctx`` 字段进入 JSON 输出.

    Args:
        logger: 目标 logger
        level:  级别 (e.g. ``logging.WARNING``)
        event:  事件名 (e.g. ``"business_error"``), 进入 ``ctx.event``
        msg:    可选人类可读摘要; 缺省用 ``event``
        **fields: 结构化字段 (e.g. ``code="E01101", path="/api/x"``)

    行为约束:
    - ``event`` 必填, 防业务代码写散日志
    - ``fields`` 不可覆盖 LogRecord 保留字段 (会抛 ``ValueError``)
    - ``ctx`` 是 dict 字段, 不会与 LogRecord 自带属性冲突

    注意: 不会自动捕获 ``sys.exc_info()``. 需要记录异常时, 用
    ``log_event_exc(logger, level, event, exc_info=sys.exc_info(), ...)``,
    或直接 ``logger.exception(...)`` + ``extra={"ctx": {...}}``.
    """
    if not event:
        raise ValueError("log_event: 'event' is required")

    safe_fields: Dict[str, Any] = {}
    for k, v in fields.items():
        if k in _RESERVED_LOGRECORD_KEYS:
            raise ValueError(
                f"log_event: field name {k!r} collides with LogRecord builtin"
            )
        safe_fields[k] = v
    safe_fields.setdefault("event", event)

    summary = msg if msg is not None else event
    # 强制 ctx 作为独立字段进入 record.__dict__, formatter 提取时优先取它.
    safe_fields["ctx"] = safe_fields.get("ctx", {})
    if not isinstance(safe_fields["ctx"], dict):
        # 业务误传: 强制转 dict, 防 json.dumps 失败.
        safe_fields["ctx"] = {"value": safe_fields["ctx"]}

    logger.log(level, summary, extra={"ctx": safe_fields})


def log_event_exc(
    logger: logging.Logger,
    level: int,
    event: str,
    exc_info: Any,
    *,
    msg: Optional[str] = None,
    **fields: Any,
) -> None:
    """``log_event`` 的异常版本 — 显式传入 ``exc_info`` (如 ``sys.exc_info()``).

    用法::

        try:
            ...
        except Exception:
            log_event_exc(logger, logging.ERROR, "unhandled_exception",
                          exc_info=sys.exc_info(),
                          path=request.url.path, method=request.method)
            raise
    """
    if not event:
        raise ValueError("log_event_exc: 'event' is required")
    safe_fields: Dict[str, Any] = {}
    for k, v in fields.items():
        if k in _RESERVED_LOGRECORD_KEYS:
            raise ValueError(
                f"log_event_exc: field name {k!r} collides with LogRecord builtin"
            )
        safe_fields[k] = v
    safe_fields.setdefault("event", event)
    safe_fields["ctx"] = safe_fields.get("ctx", {})
    if not isinstance(safe_fields["ctx"], dict):
        safe_fields["ctx"] = {"value": safe_fields["ctx"]}

    summary = msg if msg is not None else event
    logger.log(level, summary, exc_info=exc_info, extra={"ctx": safe_fields})


# ---------------- configure_logging ----------------


# uvicorn 自带 access / error logger, 我们也接管它们, 避免 plain / json 混用.
_ADMIN_LOGGER_NAMES = (
    "admin",
    "admin.errors",
    "admin.auth",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)


_configure_lock = threading.Lock()
_configured = False


def configure_logging(
    level: str = "INFO",
    fmt: str = "json",
    *,
    stream=None,
) -> None:
    """为 ``admin.*`` / uvicorn logger 安装 JSON formatter.

    Args:
        level: 全局日志级别字符串 (``"DEBUG"`` / ``"INFO"`` / ...). 默认 INFO.
        fmt:   ``"json"`` (默认) 或 ``"plain"`` (开发友好).
        stream: 输出流, 默认 ``sys.stderr``.

    幂等: 多次调用不会重复安装 handler.
    """
    global _configured
    with _configure_lock:
        if _configured:
            return
        _configured = True

        if stream is None:
            stream = sys.stderr

        handler = logging.StreamHandler(stream)
        if fmt == "json":
            handler.setFormatter(JsonLogFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )

        root = logging.getLogger()
        root.setLevel(getattr(logging, level.upper(), logging.INFO))
        # 清空 uvicorn 0.x 默认配置的 handler, 避免重复输出.
        for h in list(root.handlers):
            root.removeHandler(h)
        root.addHandler(handler)

        # 让 uvicorn 日志走 root, 不再各自打 access log.
        for name in _ADMIN_LOGGER_NAMES:
            lg = logging.getLogger(name)
            lg.handlers.clear()
            lg.propagate = True


def reset_logging_for_tests() -> None:
    """测试夹具: 解开 ``configure_logging`` 的幂等锁.

    单元测试中如需多次重新配置, 在 ``teardown`` 调用一次.
    """
    global _configured
    with _configure_lock:
        _configured = False


def configure_from_env() -> None:
    """从环境变量安装配置 (``ADMIN_LOG_FORMAT`` / ``ADMIN_LOG_LEVEL``)."""
    fmt = os.environ.get("ADMIN_LOG_FORMAT", "json").lower()
    level = os.environ.get("ADMIN_LOG_LEVEL", "INFO")
    configure_logging(level=level, fmt=fmt)


# ---------------- 内部工具 ----------------


def _format_ts(epoch_seconds: float) -> str:
    """epoch → ``2026-06-12T16:30:01.234Z``."""
    dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    # millisecond 精度, 与 Loki / ELK 默认格式一致.
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{dt.microsecond // 1000:03d}Z"


def _extract_ctx(record: logging.LogRecord) -> Dict[str, Any]:
    """从 record 抽 ctx 字段.

    优先级:
    1. ``record.ctx`` (log_event 写入)
    2. ``record.__dict__`` 中白名单键 (兼容 ``logger.info("...", extra={...})``)
    """
    ctx_obj = getattr(record, "ctx", None)
    if isinstance(ctx_obj, dict):
        return dict(ctx_obj)

    out: Dict[str, Any] = {}
    for k in _CTX_SAFE_KEYS:
        v = getattr(record, k, None)
        if v is not None:
            out[k] = v
    return out


def _format_exc(record: logging.LogRecord) -> Dict[str, Any]:
    """序列化异常信息, traceback 超过 4KB 截断."""
    exc_info = record.exc_info
    if not exc_info:
        # 调用方在 ``record.exc_info`` 存在的前提下调用, 这里只是防御.
        return {"type": "Unknown", "message": "", "traceback": ""}
    exc_type, exc_value, _tb = exc_info
    tb_text = ""
    if record.exc_text:
        tb_text = record.exc_text
    else:
        import traceback as _tb_mod

        tb_text = "".join(_tb_mod.format_exception(exc_type, exc_value, _tb))
    truncated = False
    if len(tb_text) > _MAX_TRACEBACK_CHARS:
        tb_text = tb_text[:_MAX_TRACEBACK_CHARS] + "\n...truncated"
        truncated = True
    payload: Dict[str, Any] = {
        "type": exc_type.__name__ if exc_type else "Unknown",
        "message": str(exc_value) if exc_value is not None else "",
        "traceback": tb_text,
    }
    if truncated:
        payload["truncated"] = True
    return payload


def _compact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """压缩过大的日志 payload, 保持 JSON 可解析。"""
    compact = dict(payload)
    compact["msg"] = _truncate_text(str(compact.get("msg", "")), 512)
    ctx = compact.get("ctx")
    if isinstance(ctx, dict):
        compact_ctx: Dict[str, Any] = {}
        for key, value in ctx.items():
            compact_ctx[key] = _compact_value(value)
        compact_ctx["truncated"] = True
        compact["ctx"] = compact_ctx
    else:
        compact["ctx"] = {"truncated": True}

    exc = compact.get("exc")
    if isinstance(exc, dict):
        compact_exc = dict(exc)
        compact_exc["message"] = _truncate_text(
            str(compact_exc.get("message", "")), 256
        )
        compact_exc["traceback"] = _truncate_text(
            str(compact_exc.get("traceback", "")), _MAX_TRACEBACK_CHARS
        )
        compact_exc["truncated"] = True
        compact["exc"] = compact_exc

    return compact


def _compact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, 256)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    rendered = json.dumps(value, ensure_ascii=False, default=str)
    return _truncate_text(rendered, 256)


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 12:
        return text[:limit]
    return text[: limit - 12] + "...truncated"


# ---------------- 内部常量 (给测试 / admin.app 复用) ----------------


__all__ = [
    "JsonLogFormatter",
    "bind_request_context",
    "clear_request_context",
    "configure_from_env",
    "configure_logging",
    "current_context",
    "log_event",
    "log_event_exc",
    "reset_logging_for_tests",
]
