"""FastAPI 应用工厂 (T6.1).

用法:
    # 开发模式
    python3 -m admin.app --port 8000

    # 编程模式
    from admin.app import create_app
    app = create_app()
"""

from __future__ import annotations

import argparse
import logging
import secrets
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from admin.config import (
    Settings,
    is_default_admin_password_secure,
    is_jwt_secret_secure,
    load_settings,
)
from admin.db import bootstrap_admin, ensure_schema
from admin.errors import register_exception_handler
from admin.logging_utils import (
    bind_request_context,
    clear_request_context,
    configure_logging,
)
from admin.routes import (
    auth_router,
    cases_router,
    health_router,
    meta_router,
    orders_router,
    stats_router,
    ui_router,
    users_router,
)
from data.cases.schema import apply_schema as apply_cases_schema
from data.orders.schema import apply_schema as apply_orders_schema


logger = logging.getLogger("admin")


def _validate_and_log_settings(settings: Settings) -> None:
    """启动时校验配置并打印关键提示。"""
    secure, reason = is_jwt_secret_secure(settings)
    if not secure:
        if settings.env == "prod":
            logger.error("JWT 密钥不安全: %s — 拒绝启动生产环境!", reason)
            raise RuntimeError(f"JWT secret insecure in prod: {reason}")
        logger.warning("JWT 密钥提示: %s", reason)
    admin_secure, admin_reason = is_default_admin_password_secure(settings)
    if not admin_secure:
        if settings.env == "prod":
            logger.error("默认管理员密码不安全: %s — 拒绝启动生产环境!", admin_reason)
            raise RuntimeError(
                f"default admin password insecure in prod: {admin_reason}"
            )
        logger.warning("默认管理员密码提示: %s", admin_reason)
    logger.info(
        "Admin API 启动: env=%s db=%s jwt_exp_min=%d",
        settings.env,
        settings.db_path,
        settings.jwt_expire_minutes,
    )


def _setup_database(settings: Settings) -> None:
    """应用启动时: 初始化 admin/orders schema + bootstrap admin。"""
    ensure_schema(settings.db_path)
    cases_conn = apply_cases_schema(settings.db_path)
    cases_conn.close()
    orders_conn = apply_orders_schema(settings.orders_db_path)
    orders_conn.close()
    created, msg = bootstrap_admin(settings)
    if created:
        logger.warning("Bootstrap 管理员: %s", msg)
    else:
        logger.info("Bootstrap: %s", msg)


async def request_context_middleware(request: Request, call_next):
    """为每个请求绑定 per-request 上下文 (T9.3).

    - 注入 ``request_id`` (16 字符 URL-safe 随机串)
    - 注入 ``path`` / ``method`` 给后续 handler 日志消费
    - 退出时 ``clear_request_context`` 避免泄漏到下一个请求
    """
    token = bind_request_context(
        request_id=f"req_{secrets.token_hex(8)}",
        path=request.url.path,
        method=request.method,
    )
    try:
        return await call_next(request)
    finally:
        clear_request_context(token)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """构造 FastAPI app 实例。

    Args:
        settings: 可选外部传入;None 时从环境加载

    Returns:
        配置好的 FastAPI 应用
    """
    if settings is None:
        settings = load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _validate_and_log_settings(app.state.settings)
        _setup_database(app.state.settings)
        yield

    app = FastAPI(
        title="高考志愿填报管理后台 API",
        version="0.1.0",
        description=(
            "管理后台 MVP API。\n\n"
            "**认证流程**: `POST /api/auth/login` → 获取 Bearer JWT →\n"
            "请求头 `Authorization: Bearer *** 访问受保护路由。\n\n"
            "**详细字段**: 订单完整字段见 `data/orders/models.py::Order`。\n"
            "**T6.1 范围**: 仅启动骨架 + 鉴权 + Swagger。订单/用户/案例/仪表盘"
            "CRUD 在 T6.2-T6.6 增量补齐。"
        ),
        contact={"name": "Hermes Agent"},
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )

    app.state.settings = settings

    # T9.3: per-request 上下文 (request_id / path / method)
    app.middleware("http")(request_context_middleware)

    # 注册路由（统一 /api 前缀已由各 router 处理）
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(cases_router)
    app.include_router(orders_router)
    app.include_router(stats_router)
    app.include_router(ui_router)
    app.include_router(meta_router)
    app.include_router(users_router)

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 注册全局错误处理 (T9.2) — 业务异常 → 标准响应体 + 中文文案
    register_exception_handler(app)

    return app


def main(argv: Optional[list] = None) -> int:
    """命令行入口:`python3 -m admin.app [--port 8000] [--host 0.0.0.0]`"""
    parser = argparse.ArgumentParser(
        prog="admin",
        description="高考志愿填报管理后台 FastAPI 服务",
    )
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认 8000)")
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
    )
    parser.add_argument(
        "--log-format",
        default="json",
        choices=["json", "plain"],
        help="日志格式: json (生产) / plain (开发) — 默认 json",
    )
    args = parser.parse_args(argv)

    # T9.3: 安装结构化日志 formatter (幂等)
    configure_logging(level=args.log_level.upper(), fmt=args.log_format)

    settings = load_settings()
    app = create_app(settings)

    logger.info("启动 uvicorn: %s:%d", args.host, args.port)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
