#!/usr/bin/env python3
"""6/20 用户模拟操作测试 — Playwright 走真实 5 跳路径.

路径:
1. /                          landing
2. /pricing                   pricing
3. /privacy                   privacy
4. /portal/{token}/info       portal info 表单 (从 admin API 拿 portal_token)
5. /portal/{token}/status     portal status

桌面 1280x900 + 移动 390x844 双视口截图.
captures 写入 reports/user_simulation_2026_06_20/<page>.png

依赖: .venv 已经装 playwright + chromium.
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
LOG = Path("/tmp/sim-admin.log")
OUT = REPO / "reports" / "user_simulation_2026_06_20"
PORT = int(os.environ.get("GAOKAO_SIM_PORT", "19092"))


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
        "GAOKAO_DB_PATH": str(REPO / f"data/orders/sim-admin-{PORT}.db"),
        "GAOKAO_ORDERS_DB_PATH": str(REPO / f"data/orders-sim-{PORT}.db"),
        "GAOKAO_SHARE_DB_PATH": str(REPO / f"data/share-sim-{PORT}.db"),
        "GAOKAO_SHARE_REPORT_DIR": str(REPO / f"data/share-reports-sim-{PORT}"),
        "GAOKAO_OPS_ALERT_LOG": str(REPO / f"data/alerts/sim-ops-{PORT}.jsonl"),
        "GAOKAO_RETENTION_DAYS": "180",
        "GAOKAO_JWT_SECRET": "x" * 32,
        "GAOKAO_PORTAL_TOKEN_SECRET": "y" * 32,
        "GAOKAO_ADMIN_USER": "admin",
        "GAOKAO_ADMIN_PASS": "SimulationTest1!",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": "P" + "r" * 31 + "!",
        "GAOKAO_PAYMENT_PROVIDER": "mock",
        "GAOKAO_ORDERS_FERNET_KEY": "F" * 44,
        "GAOKAO_ADMIN_BIND": f"127.0.0.1:{PORT}",
    })
    for d in [
        REPO / "data/orders",
        REPO / "data",
        REPO / f"data/share-reports-sim-{PORT}",
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"[sim] starting admin on :{PORT}, output → {OUT}")
    proc = _start_admin()
    overall_ok = True
    try:
        # 1. login + create order via admin API → 拿 portal_token
        s, _, body = _http(
            "POST",
            "/api/auth/login",
            body={"username": "admin", "password": "SimulationTest1!"},
        )
        if s != 200:
            print(f"[sim] login failed: {s} {body[:200]}")
            return 1
        tok = json.loads(body)["access_token"]

        consent = {
            "consent_version": "2026-06-20",
            "consent_scope": "service_terms+privacy",
            "consent_method": "verbal_chat",
            "consent_given_at": "2026-06-20T12:00:00+08:00",
            "consent_note": "user simulation",
        }
        order_payload = {
            "source": "xianyu",
            "service_version": "audit",
            "amount_cents": 9900,
            "customer_name": "模拟家长",
            "customer_phone": "13800000000",
            "customer_wechat": "wx_sim_001",
            "candidate_name": "模拟学生",
            "candidate_province": "湖南",
            "assigned_consultant": "sim_consultant",
            "notes": "sim",
            "consent": consent,
        }
        s, _, body = _http("POST", "/api/orders", body=order_payload, token=tok)
        if s not in (200, 201):
            print(f"[sim] create order failed: {s} {body[:200]}")
            return 1
        j = json.loads(body)
        order_id = j.get("order", {}).get("id", "")
        # portal_token 通过 issue_portal_token (web 路径生成)
        sys.path.insert(0, str(REPO))
        from data.customer_portal.token import issue_portal_token

        portal_token = issue_portal_token(
            order_id, "y" * 32
        )  # 6/20: 复用 GAOKAO_PORTAL_TOKEN_SECRET
        if not portal_token:
            print(f"[sim] issue_portal_token failed for order={order_id}")
            return 1
        print(f"[sim] order={order_id} portal_token length={len(portal_token)}")

        # 2. Playwright 跳
        from playwright.sync_api import sync_playwright

        pages = [
            ("landing", "/"),
            ("pricing", "/pricing"),
            ("privacy", "/privacy"),
            ("portal_info", f"/portal/{portal_token}/info"),
            ("portal_status", f"/portal/{portal_token}/status"),
        ]
        viewports = [("desktop", 1280, 900), ("mobile", 390, 844)]
        captures = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for vname, w, h in viewports:
                ctx = browser.new_context(viewport={"width": w, "height": h})
                page = ctx.new_page()
                page.set_default_timeout(10000)
                for name, path in pages:
                    url = f"http://127.0.0.1:{PORT}{path}"
                    try:
                        resp = page.goto(url, wait_until="networkidle")
                        status = resp.status if resp else -1
                    except Exception as e:
                        page.screenshot(
                            path=str(OUT / f"{vname}_{name}.png"), full_page=True
                        )
                        overall_ok = False
                        captures.append({
                            "viewport": vname,
                            "page": name,
                            "status": -1,
                            "error": str(e)[:80],
                        })
                        continue
                    shot = OUT / f"{vname}_{name}.png"
                    page.screenshot(path=str(shot), full_page=True)
                    title = page.title()[:60]
                    ok = 200 <= status < 400
                    if not ok:
                        overall_ok = False
                    captures.append({
                        "viewport": vname,
                        "page": name,
                        "status": status,
                        "title": title,
                        "shot": str(shot.relative_to(REPO)),
                    })
                    print(f"  [{vname}] {name:20s} {status}  {title!r}")
                ctx.close()
            browser.close()

        (OUT / "captures.json").write_text(
            json.dumps(
                {
                    "date": "2026-06-20",
                    "port": PORT,
                    "order_id": order_id,
                    "portal_token_len": len(portal_token),
                    "overall_ok": overall_ok,
                    "captures": captures,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        print(
            f"\n[sim] overall {'PASS' if overall_ok else 'FAIL'}  → {OUT}/captures.json"
        )
        return 0 if overall_ok else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
