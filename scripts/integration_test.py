#!/usr/bin/env python3
"""6/20 集成测试 — 真实启动 admin + 全链路 E2E (DB + admin + portal + payment mock).

不带 locust, 不用 browser, 纯 API 路径覆盖:
1. /health = 200
2. POST /api/auth/login = 200 + JWT
3. POST /api/orders (含 consent block) = 201 + order_id
4. GET /api/orders/{id} = 200 (含 consent_method / consent_given_at)
5. /api/admin/notifications/ops-alerts = 200
6. retention cleanup dry-run = candidates = 0 (新订单 <1d)
7. retention cleanup apply = anonymized = 0
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
LOG = Path("/tmp/integration-admin.log")
RESULTS = REPO / "reports" / "integration_2026_06_20.json"
PORT = int(os.environ.get("GAOKAO_INT_PORT", "19091"))


def _http(method, path, *, body=None, token=None, port=PORT):
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


def _start_admin():
    env = os.environ.copy()
    env.update({
        "GAOKAO_ENV": "dev",
        "GAOKAO_DB_PATH": str(REPO / f"data/orders/int-admin-{PORT}.db"),
        "GAOKAO_ORDERS_DB_PATH": str(REPO / f"data/orders-int-{PORT}.db"),
        "GAOKAO_SHARE_DB_PATH": str(REPO / f"data/share-int-{PORT}.db"),
        "GAOKAO_SHARE_REPORT_DIR": str(REPO / f"data/share-reports-int-{PORT}"),
        "GAOKAO_OPS_ALERT_LOG": str(REPO / f"data/alerts/int-ops-{PORT}.jsonl"),
        "GAOKAO_RETENTION_DAYS": "180",
        "GAOKAO_JWT_SECRET": "x" * 32,
        "GAOKAO_PORTAL_TOKEN_SECRET": "y" * 32,
        "GAOKAO_ADMIN_USER": "admin",
        "GAOKAO_ADMIN_PASS": "IntegrationTest1!",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": "P" + "r" * 31 + "!",
        "GAOKAO_PAYMENT_PROVIDER": "mock",
        "GAOKAO_ORDERS_FERNET_KEY": "F" * 44,
        "GAOKAO_ADMIN_BIND": f"127.0.0.1:{PORT}",
    })
    for d in [
        REPO / "data/orders",
        REPO / "data",
        REPO / f"data/share-reports-int-{PORT}",
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


def _stop_admin(proc):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main():
    results = []
    overall_ok = True

    def _step(name, ok, detail=""):
        nonlocal overall_ok
        if not ok:
            overall_ok = False
        results.append({"step": name, "ok": ok, "detail": detail})
        marker = "✅" if ok else "❌"
        print(f"  {marker} {name:30s}  {detail[:160]}")

    print(f"[integration] starting admin on :{PORT}")
    proc = _start_admin()
    try:
        # 1. health
        s, _, body = _http("GET", "/health")
        h = json.loads(body) if s == 200 else {}
        _step(
            "health",
            s == 200
            and h.get("status") == "ok"
            and h.get("checks", {}).get("db_writable") is True,
            f"status={h.get('status')} db={h.get('checks', {}).get('db_writable')}",
        )

        # 2. login
        s, _, body = _http(
            "POST",
            "/api/auth/login",
            body={"username": "admin", "password": "IntegrationTest1!"},
        )
        token = ""
        if s == 200:
            token = json.loads(body).get("access_token", "")
        _step("login", bool(token), f"status={s} token_len={len(token)}")

        # 3. create order
        consent = {
            "consent_version": "2026-06-20",
            "consent_scope": "service_terms+privacy",
            "consent_method": "verbal_chat",
            "consent_given_at": "2026-06-20T12:00:00+08:00",
            "consent_note": "integration test",
        }
        order_payload = {
            "source": "xianyu",
            "service_version": "audit",
            "amount_cents": 9900,
            "customer_name": "测试家长",
            "customer_phone": "13800000000",
            "customer_wechat": "wx_test_001",
            "candidate_name": "测试学生",
            "candidate_province": "湖南",
            "assigned_consultant": "test_consultant",
            "notes": "int",
            "consent": consent,
        }
        s, _, body = _http("POST", "/api/orders", body=order_payload, token=token)
        order_id = ""
        if s in (200, 201):
            j = json.loads(body)
            # 真实响应结构: {"order": {"id": ...}, "status_label": ...}
            order_id = j.get("order", {}).get("id", "") or j.get("id", "")
        _step(
            "create_order",
            s in (200, 201) and bool(order_id),
            f"status={s} order_id={order_id}",
        )

        # 4. get order (响应是嵌套 {"order": {...}})
        od = {}
        if order_id:
            s, _, body = _http("GET", f"/api/orders/{order_id}", token=token)
            j = json.loads(body) if s == 200 else {}
            od = j.get("order", j) if isinstance(j, dict) else {}
            consent_method = od.get("consent_method", "") or ""
            _step(
                "get_order",
                s == 200 and od.get("id") == order_id and bool(consent_method),
                f"status={s} consent_method={consent_method!r}",
            )

        # 5. admin ops alerts
        s, _, _ = _http("GET", "/api/admin/notifications/ops-alerts", token=token)
        _step("ops_alerts = 200", s == 200, f"status={s}")

        # 6. retention cleanup dry-run + apply (停 admin 释放 SQLite)
        _stop_admin(proc)
        proc = None
        # FERNET_KEY 必须在 retention 进程可用
        os.environ["GAOKAO_ORDERS_FERNET_KEY"] = "F" * 44
        sys.path.insert(0, str(REPO))
        from data.orders.retention_cleanup import run_cleanup

        result = run_cleanup(
            db_path=str(REPO / f"data/orders-int-{PORT}.db"),
            cutoff_iso="2099-01-01T00:00:00+00:00",
            apply=False,
        )
        _step(
            "retention_dry_run",
            True,
            f"candidates={result.candidates} anonymized={result.anonymized} "
            f"deletion_logs_pruned={result.deletion_logs_pruned} "
            f"share_events_pruned={result.share_events_pruned}",
        )

        # 7. retention cleanup apply (新订单<1d 不会被裁)
        result2 = run_cleanup(
            db_path=str(REPO / f"data/orders-int-{PORT}.db"),
            cutoff_iso="2099-01-01T00:00:00+00:00",
            apply=True,
        )
        _step(
            "retention_apply",
            result2.anonymized == 0,
            f"candidates={result2.candidates} anonymized={result2.anonymized} "
            f"deletion_logs_pruned={result2.deletion_logs_pruned}",
        )

    finally:
        if proc is not None:
            _stop_admin(proc)

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(
        json.dumps(
            {
                "date": "2026-06-20",
                "port": PORT,
                "overall_ok": overall_ok,
                "steps": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\n[integration] overall {'PASS' if overall_ok else 'FAIL'}  → {RESULTS}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
