#!/usr/bin/env python3
"""Sprint 4 T-B-27 real backend regression.

Usage:
  # Run against an already-started compose service:
  #   docker compose up --build -d gaokao-admin
  #   python scripts/sprint4_real_backend_regression.py --base-url http://127.0.0.1:8000 --share-code <code>
  #
  # Or let the script start a temporary local uvicorn backend:
  #   python scripts/sprint4_real_backend_regression.py

The gate verifies that five React-facing backend modules return HTTP 200 over
real HTTP, not TestClient mocks: share, data-query, review, llm, poster.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = Path(tempfile.gettempdir()) / "gaokao-sprint4-real-backend-regression.json"


@dataclass(frozen=True)
class RegressionCheck:
    module: str
    description: str


@dataclass(frozen=True)
class StepResult:
    module: str
    ok: bool
    status: int
    detail: str


def build_checks() -> list[RegressionCheck]:
    return [
        RegressionCheck("share", "GET /api/share-link/{code}/stats"),
        RegressionCheck("data-query", "GET /api/data-query/score-line"),
        RegressionCheck("review", "POST /api/review/start"),
        RegressionCheck("llm", "GET /api/llm/config"),
        RegressionCheck("poster", "POST /api/poster/generate"),
    ]


def _request(base_url: str, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    url = base_url.rstrip("/") + path
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return exc.code, parsed


def _check_share(base_url: str, share_code: str) -> StepResult:
    status, body = _request(base_url, "GET", f"/api/share-link/{urllib.parse.quote(share_code)}/stats")
    ok = status == 200 and {"views", "uniqueVisitors"}.issubset(body)
    return StepResult("share", ok, status, f"code={share_code} body_keys={sorted(body)}")


def _check_data_query(base_url: str) -> StepResult:
    query = urllib.parse.urlencode({"province": "Hunan", "year": 2026, "scoreType": "physics"})
    status, body = _request(base_url, "GET", f"/api/data-query/score-line?{query}")
    ok = status == 200 and isinstance(body.get("lines"), list) and len(body["lines"]) > 0
    return StepResult("data-query", ok, status, f"lines={len(body.get('lines', []))}")


def _check_review(base_url: str) -> StepResult:
    status, body = _request(base_url, "POST", "/api/review/start", {"planId": "sprint4-plan", "reviewerId": "sprint4"})
    review_id = str(body.get("id") or "")
    if status != 200 or not review_id:
        return StepResult("review", False, status, f"start_failed body={body}")
    action_status, action_body = _request(
        base_url,
        "POST",
        "/api/review/action",
        {"action": "approve", "reviewId": review_id, "comment": "sprint4 regression"},
    )
    ok = action_status == 200 and action_body.get("status") == "approved"
    return StepResult("review", ok, action_status, f"review_id={review_id} status={action_body.get('status')}")


def _check_llm(base_url: str) -> StepResult:
    status, body = _request(base_url, "GET", "/api/llm/config")
    ok = status == 200 and isinstance(body.get("availableProviders"), list)
    return StepResult("llm", ok, status, f"providers={body.get('availableProviders')}")


def _check_poster(base_url: str) -> StepResult:
    status, body = _request(base_url, "POST", "/api/poster/generate", {"planId": "sprint4-plan", "template": "classic"})
    ok = status == 200 and str(body.get("posterUrl") or "").startswith(("http://", "https://"))
    return StepResult("poster", ok, status, f"posterUrl={body.get('posterUrl')}")


def run_regression(base_url: str, share_code: str) -> list[StepResult]:
    return [
        _check_share(base_url, share_code),
        _check_data_query(base_url),
        _check_review(base_url),
        _check_llm(base_url),
        _check_poster(base_url),
    ]


def _wait_for_health(base_url: str) -> None:
    for _ in range(60):
        try:
            status, body = _request(base_url, "GET", "/health")
            if status == 200 and body.get("status") == "ok":
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"backend did not become healthy: {base_url}/health")


def _seed_share_link(share_db_path: Path) -> str:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from data.share.short_link import ShortLinkService

    link = ShortLinkService(db_path=str(share_db_path)).create(
        report_id="sprint4-real-backend-report",
        owner_id="sprint4",
        permission="read",
        ttl_days=7,
        note="sprint4-real-backend-regression",
    )
    return link.code


def _local_env(tmp_dir: Path, port: int) -> tuple[dict[str, str], Path]:
    share_db_path = tmp_dir / "share" / "short_links.db"
    env = os.environ.copy()
    env.update(
        {
            "GAOKAO_ENV": "dev",
            "GAOKAO_DB_PATH": str(tmp_dir / "orders" / "admin.db"),
            "GAOKAO_ORDERS_DB_PATH": str(tmp_dir / "orders.db"),
            "GAOKAO_SHARE_DB_PATH": str(share_db_path),
            "GAOKAO_SHARE_REPORT_DIR": str(tmp_dir / "share" / "reports"),
            "GAOKAO_OPS_ALERT_LOG": str(tmp_dir / "ops-alerts.jsonl"),
            "GAOKAO_JWT_SECRET": "x" * 32,
            "GAOKAO_PORTAL_TOKEN_SECRET": "y" * 32,
            "GAOKAO_ADMIN_USER": "admin",
            "GAOKAO_ADMIN_PASS": "Sprint4Backend1!",
            "GAOKAO_PAYMENT_WEBHOOK_SECRET": "P" + "r" * 31 + "!",
            "GAOKAO_PAYMENT_PROVIDER": "mock",
            "GAOKAO_PAYMENT_BASE_URL": "https://example.com",
            "GAOKAO_ORDERS_FERNET_KEY": "F" * 44,
            "GAOKAO_ADMIN_PORT": str(port),
        }
    )
    for path in [tmp_dir / "orders", tmp_dir / "share" / "reports"]:
        path.mkdir(parents=True, exist_ok=True)
    return env, share_db_path


def _start_local_backend(port: int, tmp_dir: Path) -> tuple[subprocess.Popen[bytes], str, str]:
    env, share_db_path = _local_env(tmp_dir, port)
    share_code = _seed_share_link(share_db_path)
    log_path = tmp_dir / "uvicorn.log"
    log = log_path.open("wb")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "admin.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=REPO,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_health(base_url)
    except Exception:
        proc.terminate()
        raise
    return proc, base_url, share_code


def _stop_process(proc: subprocess.Popen[bytes]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _write_report(report_path: Path, base_url: str, results: list[StepResult]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "gate": "Sprint 4 T-B-27 real backend 5 modules 200",
                "base_url": base_url,
                "overall_ok": all(step.ok for step in results),
                "steps": [step.__dict__ for step in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Existing backend base URL, for example http://127.0.0.1:8000")
    parser.add_argument("--share-code", help="Existing share code for /api/share-link/{code}/stats when using --base-url")
    parser.add_argument("--port", type=int, default=int(os.environ.get("GAOKAO_SPRINT4_BACKEND_PORT", "19127")))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(os.environ.get("GAOKAO_SPRINT4_BACKEND_REPORT", str(DEFAULT_REPORT))),
        help="JSON report path. Defaults to the system temp directory.",
    )
    args = parser.parse_args(argv)

    proc: subprocess.Popen[bytes] | None = None
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.base_url:
            base_url = args.base_url.rstrip("/")
            if not args.share_code:
                raise SystemExit("--share-code is required when --base-url points at an already-running backend")
            share_code = args.share_code
        else:
            temp_dir = tempfile.TemporaryDirectory(prefix="gaokao-sprint4-backend-", ignore_cleanup_errors=True)
            proc, base_url, share_code = _start_local_backend(args.port, Path(temp_dir.name))

        results = run_regression(base_url, share_code)
        _write_report(args.report, base_url, results)
        for step in results:
            marker = "PASS" if step.ok else "FAIL"
            print(f"{marker:4s} {step.module:10s} status={step.status} {step.detail}")
        print(f"report={args.report}")
        return 0 if all(step.ok for step in results) else 1
    finally:
        if proc is not None:
            _stop_process(proc)
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
