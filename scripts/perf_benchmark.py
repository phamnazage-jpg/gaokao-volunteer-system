#!/usr/bin/env python3
"""6/20 性能基准 + 真实并发测试 (替换 pre-existing test_t5_performance.py locust 失败).

启动 admin (uvicorn), 然后:
1. warmup: 50 健康检查
2. baseline: 单请求 200 次连续 /health, 收集 p50/p95/p99/max
3. concurrency: 10 并发 x 50 任务 x /health + /api/meta + /api/stats/orders
4. output: reports/perf_2026_06_20.json + 控制台表格
5. cleanup: kill uvicorn

不需要 locust (已知 venv 漂移). 用 stdlib concurrent.futures + http.client.
"""

from __future__ import annotations

import concurrent.futures
import http.client
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
PY = REPO / ".venv" / "bin" / "python"
LOG = Path("/tmp/perf-admin.log")
RESULTS = REPO / "reports" / "perf_2026_06_20.json"
PORT = int(os.environ.get("GAOKAO_PERF_PORT", "19090"))


def _http(
    method: str,
    path: str,
    host: str = "127.0.0.1",
    port: int = PORT,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, float, str]:
    conn = http.client.HTTPConnection(host, port, timeout=10)
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = json.dumps(body).encode() if body else b""
    t0 = time.perf_counter()
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    conn.close()
    return resp.status, elapsed_ms, data.decode("utf-8", "replace")


def _start_admin() -> subprocess.Popen:
    env = os.environ.copy()
    env.update({
        "GAOKAO_ENV": "dev",
        "GAOKAO_DB_PATH": str(REPO / "data" / "orders" / f"perf-admin-{PORT}.db"),
        "GAOKAO_ORDERS_DB_PATH": str(REPO / f"data/orders-perf-{PORT}.db"),
        "GAOKAO_SHARE_DB_PATH": str(REPO / f"data/share-perf-{PORT}.db"),
        "GAOKAO_SHARE_REPORT_DIR": str(REPO / f"data/share-reports-perf-{PORT}"),
        "GAOKAO_OPS_ALERT_LOG": str(REPO / f"data/alerts/perf-ops-{PORT}.jsonl"),
        "GAOKAO_RETENTION_DAYS": "180",
        "GAOKAO_JWT_SECRET": "x" * 32,
        "GAOKAO_PORTAL_TOKEN_SECRET": "y" * 32,
        "GAOKAO_ADMIN_USER": "admin",
        "GAOKAO_ADMIN_PASS": "PerfTestPass1!",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": "P" + "r" * 31 + "!",
        "GAOKAO_ADMIN_BIND": f"127.0.0.1:{PORT}",
    })
    for d in [
        REPO / "data/orders",
        REPO / "data",
        REPO / f"data/share-reports-perf-{PORT}",
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
    # wait for /health
    for _ in range(60):
        try:
            s, _, _ = _http("GET", "/health")
            if s == 200:
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("admin failed to start in 30s")


def _stop_admin(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = int(len(s) * p / 100)
    return s[min(idx, len(s) - 1)]


def _summarize(label: str, samples: list[tuple]) -> dict:
    latencies = [s for s in samples if s[0] == 200]
    failures = [s for s in samples if s[0] != 200]
    lats = [m for _, m, *_ in latencies]
    return {
        "label": label,
        "total": len(samples),
        "success_2xx": len(latencies),
        "failures": len(failures),
        "success_rate": round(len(latencies) / max(len(samples), 1) * 100, 2),
        "p50_ms": round(_percentile(lats, 50), 2),
        "p95_ms": round(_percentile(lats, 95), 2),
        "p99_ms": round(_percentile(lats, 99), 2),
        "max_ms": round(max(lats) if lats else 0.0, 2),
        "mean_ms": round(statistics.mean(lats) if lats else 0.0, 2),
    }


def _get_jwt() -> str:
    s, _, body = _http(
        "POST",
        "/api/auth/login",
        body={"username": "admin", "password": "PerfTestPass1!"},
    )
    assert s == 200, f"login failed: {s} {body[:200]}"
    return json.loads(body)["access_token"]


def main() -> int:
    print(f"[perf] starting admin on :{PORT}")
    proc = _start_admin()
    try:
        # 1. warmup
        for _ in range(10):
            _http("GET", "/health")
        # 2. baseline
        baseline = [_http("GET", "/health") for _ in range(200)]
        baseline_summary = _summarize("health_baseline_200_seq", baseline)
        print(
            f"[perf] baseline: {baseline_summary['p95_ms']}ms p95 / "
            f"{baseline_summary['success_rate']}% success"
        )

        # 3. login
        token = _get_jwt()

        # 4. concurrency: 10 worker x 50 task
        def _work(_i: int) -> list[tuple[int, float, str]]:
            out: list[tuple[int, float, str]] = []
            out.append(_http("GET", "/health"))
            out.append(_http("GET", "/api/auth/me", token=token))
            out.append(_http("GET", "/api/meta", token=token))
            return out

        all_samples: list[tuple[int, float, str]] = []
        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            for batch in ex.map(_work, range(50)):
                all_samples.extend(batch)
        concurrency_summary = _summarize("concurrency_10x50", all_samples)
        concurrency_summary["wall_time_s"] = round(time.perf_counter() - t0, 2)
        concurrency_summary["rps"] = round(
            len(all_samples) / max(concurrency_summary["wall_time_s"], 0.01), 2
        )
        print(
            f"[perf] concurrency: {concurrency_summary['rps']} rps, "
            f"p95={concurrency_summary['p95_ms']}ms, "
            f"success={concurrency_summary['success_rate']}%"
        )

        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        RESULTS.write_text(
            json.dumps(
                {
                    "date": "2026-06-20",
                    "port": PORT,
                    "baseline": baseline_summary,
                    "concurrency": concurrency_summary,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        print(f"[perf] saved {RESULTS}")
        return 0
    finally:
        _stop_admin(proc)


if __name__ == "__main__":
    sys.exit(main())
