"""闲鱼 Webhook 接收端 (T8.1 §3.1)

只使用 Python 标准库 ``http.server.BaseHTTPRequestHandler`` 实现，避免引入
Flask / FastAPI 等额外依赖（与项目 "无第三方运行时依赖" 约定一致）。

提供的入口:

- :class:`XianyuWebhookHandler` — BaseHTTPRequestHandler 子类，处理
  ``POST /webhook/xianyu`` 请求
- :func:`make_server` — 返回 ``http.server.HTTPServer`` 实例
- :func:`run` — 阻塞启动（CLI 用）

设计要点:

- 验签失败 / 时间戳过期 / 缺头 → 401 / 408 / 400 + 写审计
- 同一 event_id 已 accepted → 返回 200 + 写审计 ``decision='duplicate'``，避免
  闲鱼侧重试导致重复入库
- 单 IP 限流 60 req/min（5.3），超出 → 429 + Retry-After
- 任何异常路径都不抛回客户端，返回结构化 JSON;500 响应统一带 ``rejected=true``
- :func:`_client_ip` 默认使用 ``client_address``，仅在显式信任反向代理头时才采纳
  ``X-Forwarded-For``，避免攻击者伪造来源 IP 绕过限流/污染审计

数据库:

- 默认从环境变量 ``GAOKAO_ORDERS_DB_PATH`` 读取；缺省 ``data/orders.db``
- 自动确保 webhook_audit + orders schema 已应用
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

from data.orders.schema import apply_schema

from .audit import (
    WebhookAuditEntry,
    apply_audit_schema,
    count_by_event,
    record,
)
from .dao_extension import upsert_by_external_id
from .signature import (
    SignatureError,
    get_webhook_secret,
    verify,
)
from .xianyu_adapter import (
    XianyuEventError,
    parse_event,
    to_order,
    target_status,
)

DEFAULT_DB_PATH = Path("data/orders.db")
DEFAULT_PORT = 8080
RATE_LIMIT_PER_MINUTE = 60
ROUTE_PATH = "/webhook/xianyu"

# 模块级限流器（线程安全）
_RATE_LOCK = threading.Lock()
_RATE_BUCKETS: dict[str, deque] = {}


def _default_db_path() -> str:
    p = os.environ.get("GAOKAO_ORDERS_DB_PATH")
    return p if p else str(DEFAULT_DB_PATH)


def _trust_x_forwarded_for() -> bool:
    raw = os.environ.get("GAOKAO_TRUST_X_FORWARDED_FOR", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _check_rate_limit(ip: str, *, now: float | None = None) -> bool:
    """单 IP 60 req/min 限流。返回 True 表示放行。"""
    if now is None:
        now = time.time()
    with _RATE_LOCK:
        bucket = _RATE_BUCKETS.setdefault(ip, deque())
        cutoff = now - 60.0
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            return False
        bucket.append(now)
        return True


def reset_rate_limit_for_tests() -> None:
    with _RATE_LOCK:
        _RATE_BUCKETS.clear()


def _open_db(db_path: str) -> sqlite3.Connection:
    """打开 DB 并确保两张 schema 都在。"""
    path = Path(db_path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    # 先用既有 schema helper 建表，再以跨线程可复用的连接重新打开。
    # webhook server 在测试/运行时会由主线程创建、由 server 线程处理请求；
    # 默认 sqlite3 连接带 check_same_thread=True，会在请求线程执行 SQL 时抛
    # ProgrammingError，导致 500 且审计写入被吞掉。
    bootstrap = apply_schema(path)
    bootstrap.close()

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    apply_audit_schema(conn)
    return conn


# 用工厂函数为每个 server 实例创建一个 DB 连接（简单做法，单进程）
_DB_CONN: Optional[sqlite3.Connection] = None
_DB_CONN_LOCK = threading.Lock()


def _get_db(db_path: str) -> sqlite3.Connection:
    global _DB_CONN
    with _DB_CONN_LOCK:
        if _DB_CONN is None:
            _DB_CONN = _open_db(db_path)
        return _DB_CONN


def close_db_for_tests() -> None:
    """单测 teardown 关闭全局连接。"""
    global _DB_CONN
    with _DB_CONN_LOCK:
        if _DB_CONN is not None:
            _DB_CONN.close()
            _DB_CONN = None


def _client_ip(headers, client_address=None) -> str:
    """解析请求来源 IP。

    优先级:
    1. ``X-Forwarded-For`` 头的最左侧条目(代理链最近的客户端)
    2. ``client_address`` 元组(``BaseHTTPRequestHandler.client_address``)
    3. ``"unknown"``(本地测试 / 单元测试未传入)

    攻击者可以省略 ``X-Forwarded-For`` 来绕过单 IP 限流,因此回退到
    socket 层的 client_address 是必要的。空字符串/None 也视为缺失。
    """
    fwd = headers.get("X-Forwarded-For", "") if headers else ""
    if _trust_x_forwarded_for() and fwd:
        first = fwd.split(",")[0].strip()
        if first:
            return first
    if client_address is not None:
        try:
            host = client_address[0]
            if host:
                return str(host)
        except (IndexError, TypeError):
            pass
    return "unknown"


def _build_handler(db_path: str):
    """返回 BaseHTTPRequestHandler 子类，绑定 db_path。"""

    class XianyuWebhookHandler(BaseHTTPRequestHandler):
        # 关闭 BaseHTTPRequestHandler 默认日志（写 stderr 噪音大）
        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

        # 路由分发
        def do_POST(self):  # noqa: N802
            if self.path != ROUTE_PATH:
                self._respond(404, {"error": "not_found", "path": self.path})
                return
            # 顶层兜底:即使 _handle_webhook 内部 try/except 漏掉任何异常,
            # 也必须返回结构化 JSON 500 而不是 BaseHTTPRequestHandler 默认栈。
            try:
                self._handle_webhook()
            except Exception as e:  # pragma: no cover - 注入测试覆盖
                self._handle_unexpected_error(e)

        def do_GET(self):  # noqa: N802
            if self.path == "/healthz":
                self._respond(200, {"status": "ok"})
            else:
                self._respond(404, {"error": "not_found", "path": self.path})

        # ---- 业务 ----
        def _handle_webhook(self) -> None:
            remote = _client_ip(self.headers, self.client_address)
            if not _check_rate_limit(remote):
                self._respond(
                    429,
                    {"error": "rate_limited"},
                    extra_headers={"Retry-After": "60"},
                )
                return

            body = self._read_body()
            if body is None:
                # 413 已通过 _read_body 内部返回
                return

            sig = self.headers.get("X-Signature", "")
            ts = self.headers.get("X-Timestamp", "")
            nonce = self.headers.get("X-Nonce", "")

            try:
                verify(body, sig, ts, nonce)
            except SignatureError as e:
                self._audit(
                    decision="rejected",
                    reject_reason=str(e),
                    raw_body=body,
                    remote_addr=remote,
                )
                # 时间戳过期 → 408；签名错误 → 401
                code = 408 if "timestamp" in str(e) else 401
                self._respond(
                    code,
                    {
                        "error": "rejected",
                        "rejected": True,
                        "reason": str(e),
                    },
                )
                return

            # 解析
            try:
                event = parse_event(body)
            except XianyuEventError as e:
                self._audit(
                    decision="parse_error",
                    reject_reason=str(e),
                    raw_body=body,
                    remote_addr=remote,
                )
                self._respond(400, {"error": "parse_error", "reason": str(e)})
                return

            # PII 字段丢弃记录
            if event.pii_dropped_fields:
                self._audit(
                    decision="rejected",
                    event_id=event.event_id,
                    reject_reason=(
                        f"pii_dropped: {','.join(event.pii_dropped_fields)}"
                    ),
                    raw_body=body,
                    remote_addr=remote,
                )
                self._respond(
                    400,
                    {
                        "error": "pii_dropped",
                        "fields": event.pii_dropped_fields,
                    },
                )
                return

            # 幂等：同一 event_id 之前已 accepted → 视为 duplicate
            db = _get_db(db_path)
            try:
                if count_by_event(db, "xianyu", event.event_id) > 0:
                    self._audit(
                        decision="duplicate",
                        event_id=event.event_id,
                        raw_body=body,
                        remote_addr=remote,
                    )
                    self._respond(200, {"status": "duplicate"})
                    return

                order = to_order(event)
                result = upsert_by_external_id(
                    db,
                    order,
                    actor="xianyu_webhook",
                    reason=f"event_{event.event_id}_to_{target_status(event)}",
                )
                if result.action == "illegal_transition":
                    self._audit(
                        decision="rejected",
                        event_id=event.event_id,
                        reject_reason=(f"illegal_transition: {result.error}"),
                        order_id=result.order_id,
                        raw_body=body,
                        remote_addr=remote,
                    )
                    self._respond(
                        409,
                        {
                            "error": "illegal_transition",
                            "reason": result.error,
                            "order_id": result.order_id,
                        },
                    )
                    return
                self._audit(
                    decision="accepted",
                    event_id=event.event_id,
                    order_id=result.order_id,
                    raw_body=body,
                    remote_addr=remote,
                )
                self._respond(
                    200,
                    {
                        "status": result.action,
                        "order_id": result.order_id,
                    },
                )
            except Exception as e:  # 兜底：DB 异常不抛回客户端
                self._audit(
                    decision="rejected",
                    event_id=event.event_id,
                    reject_reason=f"server_error: {type(e).__name__}",
                    raw_body=body,
                    remote_addr=remote,
                )
                self._respond(
                    500,
                    {"error": "server_error", "rejected": True},
                )

        def _handle_unexpected_error(self, e: BaseException) -> None:
            """do_POST 顶层兜底:写审计 + 返回 JSON 500。"""
            try:
                remote = _client_ip(self.headers, self.client_address)
            except Exception:
                remote = "unknown"
            try:
                self._audit(
                    decision="rejected",
                    reject_reason=f"top_level_error: {type(e).__name__}",
                    remote_addr=remote,
                )
            except Exception:
                pass
            try:
                self._respond(
                    500,
                    {"error": "server_error", "rejected": True},
                )
            except Exception:
                # 连 JSON 都写不出去时,至少不要让 BaseHTTPRequestHandler
                # 把 socket 异常回吐给客户端
                pass

        # ---- helpers ----
        def _read_body(self) -> Optional[bytes]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._respond(400, {"error": "invalid_content_length"})
                return None
            if length < 0 or length > 1_048_576:  # 1 MiB 上限
                self._respond(413, {"error": "body_too_large"})
                return None
            try:
                return self.rfile.read(length) if length > 0 else b""
            except Exception:
                self._respond(400, {"error": "read_error"})
                return None

        def _audit(
            self,
            *,
            decision: str,
            raw_body: Optional[bytes] = None,
            event_id: Optional[str] = None,
            reject_reason: Optional[str] = None,
            order_id: Optional[str] = None,
            remote_addr: Optional[str] = None,
        ) -> None:
            try:
                db = _get_db(db_path)
                record(
                    db,
                    WebhookAuditEntry(
                        channel="xianyu",
                        decision=decision,
                        event_id=event_id,
                        reject_reason=reject_reason,
                        order_id=order_id,
                        raw_body=raw_body,
                        remote_addr=remote_addr,
                    ),
                )
            except Exception:
                # 审计失败不影响主响应
                pass

        def _respond(
            self,
            status: int,
            body: dict,
            *,
            extra_headers: Optional[dict] = None,
        ) -> None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

    return XianyuWebhookHandler


def make_server(
    *,
    host: str = "0.0.0.0",
    port: int = DEFAULT_PORT,
    db_path: str | None = None,
) -> HTTPServer:
    """构造 HTTPServer 实例（未启动）。"""
    if db_path is None:
        db_path = _default_db_path()
    handler_cls = _build_handler(db_path)
    # 预热 DB 连接
    _get_db(db_path)
    return HTTPServer((host, port), handler_cls)


def run(
    *,
    host: str = "0.0.0.0",
    port: int = DEFAULT_PORT,
    db_path: str | None = None,
) -> None:
    """阻塞启动。"""
    server = make_server(host=host, port=port, db_path=db_path)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        close_db_for_tests()
        server.server_close()


def main(argv: Optional[list[str]] = None) -> int:
    """CLI: ``python -m data.channel_sync.webhook_server --port 8080``"""
    parser = argparse.ArgumentParser(description="闲鱼 Webhook 接收端 (T8.1)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--db-path",
        default=None,
        help="SQLite DB 路径；默认 $GAOKAO_ORDERS_DB_PATH 或 data/orders.db",
    )
    args = parser.parse_args(argv)
    # 启动期就检查密钥
    get_webhook_secret()
    run(host=args.host, port=args.port, db_path=args.db_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
