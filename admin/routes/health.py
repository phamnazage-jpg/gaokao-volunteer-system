"""健康检查路由 (T6.1 + 6/20 加固).

PRODUCTION_DEPLOYMENT_CHECKLIST §4 提到 curl /health 用于运维就绪检查。
6/20 加固: 返回 checks 子对象覆盖 DB 可写 + 磁盘可写 + 配置就绪
三项 readiness 指标, 同时不暴露环境/路径/版本细节。
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from admin.config import Settings, get_settings_dep, is_jwt_secret_secure


router = APIRouter(tags=["health"])


def _check_db_writable(settings: Settings) -> bool:
    """检查 orders DB 路径可写 (创建临时表测试)。

    不修改真实 schema, 仅做 connect + CREATE TEMP TABLE + DROP。
    """
    try:
        db_path = settings.orders_db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=2.0)
        try:
            conn.execute("CREATE TEMP TABLE _health_check (x INTEGER)")
            conn.execute("INSERT INTO _health_check (x) VALUES (1)")
            row = conn.execute("SELECT x FROM _health_check").fetchone()
            conn.execute("DROP TABLE _health_check")
            conn.commit()
            return bool(row and row[0] == 1)
        finally:
            conn.close()
    except Exception:
        return False


def _check_disk_writable(settings: Settings) -> bool:
    """检查 ops alert 日志目录可写 (创建临时文件 + 删除)。"""
    try:
        log_path = Path(settings.ops_alert_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            prefix="_health_disk_", suffix=".tmp", dir=str(log_path.parent)
        )
        try:
            os.write(fd, b"ok")
            os.fsync(fd)
        finally:
            os.close(fd)
            os.unlink(tmp)
        return True
    except Exception:
        return False


def _check_settings_valid(settings: Settings) -> bool:
    """检查 prod fail-closed 通过 (JWT + admin password + payment)。"""
    secure, _ = is_jwt_secret_secure(settings)
    return secure


@router.get("/health", summary="健康检查")
def health(settings: Settings = Depends(get_settings_dep)) -> JSONResponse:
    """公开端点。只返回 readiness, 不暴露环境/路径/版本细节。

    返回结构:
    - status: "ok" 或 "degraded"（任一 readiness 检查失败时降级）
    - checks: {db_writable, disk_writable, settings_valid} 子对象

    readiness 语义（2026-06-27 P1-4 修复）:
    - 所有 checks 通过 → status="ok", HTTP 200
    - 任一 check 失败 → status="degraded", HTTP 503
    - K8s/systemd readiness probe 应判 HTTP status，不只判 status 字段
    """
    checks = {
        "db_writable": _check_db_writable(settings),
        "disk_writable": _check_disk_writable(settings),
        "settings_valid": _check_settings_valid(settings),
    }
    all_ok = all(checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        },
    )
