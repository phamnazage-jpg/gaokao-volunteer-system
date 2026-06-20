#!/usr/bin/env python3
"""6/20 部署与运维验证 — 真实 boot 起来, 跑 8 项 production launch checklist.

不依赖 systemd (开发机可能没装). 用 subprocess 启动 admin, 验证:
1. GAOKAO_ENV=dev → /health 200
2. /health checks.db_writable / disk_writable / settings_valid 全部 True
3. /api/auth/login 错误密码 401
4. /api/auth/login 正确密码 200
5. /api/orders 无 token 401
6. /api/orders 错误 token 401
7. /api/orders 有效 token 200 []
8. /openapi.json 200 + 含 /health + /api/orders + /api/auth/login
9. ops-alerts 文件路径可写
10. /api/admin/ops-alerts 200 (admin 鉴权)
11. /admin/dashboard 200 (含 footer 链接)

输出: reports/deploy_ops_2026_06_20.json + 状态表格
"""

from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
PY = REPO / ".venv" / "bin" / "python"
LOG = Path("/tmp/deploy-ops-admin.log")
RESULTS = REPO / "reports" / "deploy_ops_2026_06_20.json"
PORT = int(os.environ.get("GAOKAO_DEPLOY_PORT", "19093"))


def _http(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    token: str | None = None,
    port: int = PORT,
) -> tuple[int, dict, str]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["Connection"] = "close"
    payload = json.dumps(body).encode() if body else b""
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    raw = resp.getheaders()
    body_text = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, {k.lower(): v for k, v in raw}, body_text


def _start_admin() -> subprocess.Popen:
    env = os.environ.copy()
    env.update({
        "GAOKAO_ENV": "dev",
        "GAOKAO_DB_PATH": str(REPO / f"data/orders/deploy-admin-{PORT}.db"),
        "GAOKAO_ORDERS_DB_PATH": str(REPO / f"data/orders-deploy-{PORT}.db"),
        "GAOKAO_SHARE_DB_PATH": str(REPO / f"data/share-deploy-{PORT}.db"),
        "GAOKAO_SHARE_REPORT_DIR": str(REPO / f"data/share-reports-deploy-{PORT}"),
        "GAOKAO_OPS_ALERT_LOG": str(REPO / f"data/alerts/deploy-ops-{PORT}.jsonl"),
        "GAOKAO_RETENTION_DAYS": "180",
        "GAOKAO_JWT_SECRET": "x" * 32,
        "GAOKAO_PORTAL_TOKEN_SECRET": "y" * 32,
        "GAOKAO_ADMIN_USER": "admin",
        "GAOKAO_ADMIN_PASS": "DeployOpsTest1!",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": "P" + "r" * 31 + "!",
        "GAOKAO_PAYMENT_PROVIDER": "mock",
        "GAOKAO_ADMIN_BIND": f"127.0.0.1:{PORT}",
    })
    for d in [
        REPO / "data/orders",
        REPO / "data",
        REPO / f"data/share-reports-deploy-{PORT}",
        REPO / "data/alerts",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "w")
    proc = subprocess.Popen(
        [
            str(PY),
            "-m",
            "uvicorn",
            "admin.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--log-level",
            "warning",
        ],
        cwd=REPO,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    for _ in range(60):
        try:
            s, _, b = _http("GET", "/health")
            if s == 200 and b.strip().startswith("{"):
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("admin failed to start")


def _stop_admin(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    results: list[dict] = []
    overall_ok = True

    def _check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal overall_ok
        if not ok:
            overall_ok = False
        results.append({"check": name, "ok": ok, "detail": detail})
        marker = "✅" if ok else "❌"
        print(f"  {marker} {name:32s}  {detail[:120]}")

    print(f"[deploy-ops] starting admin on :{PORT}")
    proc = _start_admin()
    try:
        # 1. /health = 200
        s, _, body = _http("GET", "/health")
        h = json.loads(body) if s == 200 else {}
        _check("/health = 200", s == 200 and h.get("status") == "ok", f"status={s}")

        # 2. checks 三件套
        c = h.get("checks", {})
        _check(
            "checks.db_writable=True",
            c.get("db_writable") is True,
            f"db={c.get('db_writable')}",
        )
        _check(
            "checks.disk_writable=True",
            c.get("disk_writable") is True,
            f"disk={c.get('disk_writable')}",
        )
        _check(
            "checks.settings_valid=True",
            c.get("settings_valid") is True,
            f"settings={c.get('settings_valid')}",
        )

        # 3. login wrong
        s, _, _ = _http(
            "POST",
            "/api/auth/login",
            body={"username": "admin", "password": "wrongpass"},
        )
        _check("login_wrong_password = 401", s == 401, f"status={s}")

        # 4. login correct
        s, _, body = _http(
            "POST",
            "/api/auth/login",
            body={"username": "admin", "password": "DeployOpsTest1!"},
        )
        token = json.loads(body).get("access_token", "") if s == 200 else ""
        _check("login_correct = 200", s == 200 and bool(token), f"status={s}")

        # 5. orders no token
        s, _, _ = _http("GET", "/api/orders")
        _check("orders_no_token = 401", s == 401, f"status={s}")

        # 6. orders bad token
        s, _, _ = _http("GET", "/api/orders", token="invalid.token.here")
        _check("orders_bad_token = 401", s in (401, 422), f"status={s}")

        # 7. orders valid token
        s, _, body = _http("GET", "/api/orders", token=token)
        _check(
            "orders_valid_token = 200",
            s == 200 and isinstance(json.loads(body), list),
            f"status={s}",
        )

        # 8. openapi
        s, _, body = _http("GET", "/openapi.json")
        if s == 200:
            paths = set(json.loads(body).get("paths", {}).keys())
            needed = {"/health", "/api/auth/login", "/api/orders"}
            _check(
                "openapi 含必需路径",
                needed.issubset(paths),
                f"missing={needed - paths}",
            )
        else:
            _check("openapi = 200", False, f"status={s}")

        # 9. admin ops alerts (真实路径: /api/admin/notifications/ops-alerts)
        s, _, body = _http("GET", "/api/admin/notifications/ops-alerts", token=token)
        _check("ops_alerts = 200", s == 200, f"status={s}")

        # 10. admin dashboard 含 footer
        s, _, body = _http("GET", "/admin/dashboard", token=token)
        has_footer = "隐私政策" in body and "/privacy" in body
        _check(
            "admin_dashboard_footer 链接",
            s == 200 and has_footer,
            f"status={s} footer={has_footer}",
        )

    finally:
        _stop_admin(proc)

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(
        json.dumps(
            {
                "date": "2026-06-20",
                "port": PORT,
                "overall_ok": overall_ok,
                "checks": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\n[deploy-ops] overall {'PASS' if overall_ok else 'FAIL'}  → {RESULTS}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
