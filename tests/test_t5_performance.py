"""T5.2 性能与并发测试。"""

from __future__ import annotations

import csv
import importlib.util
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

QUICK_SCRIPT = PROJECT_ROOT / "scripts" / "gaokao-quick-3min.py"
LOCUST_FILE = PROJECT_ROOT / "locustfile.py"

_SAMPLE_REPLY = """1. 李明
2. 浙江
3. 612
4. 15230
5. R
6. 物理、数学
7. C
8. ③
9. ①
10. ②
"""


def _load_quick_module():
    spec = importlib.util.spec_from_file_location("gaokao_quick_3min", QUICK_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generate_100_plans() -> float:
    module = _load_quick_module()
    start = time.perf_counter()
    for _ in range(100):
        info = module.parse_quick_response(_SAMPLE_REPLY)
        module.generate_quick_summary(info)
        module.generate_quick_recommendation(info)
    return time.perf_counter() - start


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    raise AssertionError(f"admin app 未在 {timeout}s 内就绪: {base_url}")


@pytest.fixture
def admin_server(tmp_path: Path) -> Iterator[str]:
    port = _find_free_port()
    env = os.environ.copy()
    env.update(
        {
            "GAOKAO_ENV": "dev",
            "GAOKAO_DB_PATH": str(tmp_path / "admin.db"),
            "GAOKAO_ORDERS_DB_PATH": str(tmp_path / "orders.db"),
            "GAOKAO_JWT_SECRET": "x" * 64,
            "GAOKAO_ADMIN_USER": "admin",
            "GAOKAO_ADMIN_PASS": "admin123",
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "admin.app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-format",
            "plain",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_for_health(base_url)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


@pytest.mark.timeout(30)
def test_plan_generation_100_runs_under_5_seconds(benchmark) -> None:
    elapsed = benchmark(_generate_100_plans)
    assert elapsed < 5.0


@pytest.mark.timeout(90)
def test_admin_locust_10_concurrency_success_rate_above_95(
    admin_server: str, tmp_path: Path
) -> None:
    report_prefix = tmp_path / "t5_2"
    command = [
        "locust",
        "-f",
        str(LOCUST_FILE),
        "--host",
        admin_server,
        "--headless",
        "-u",
        "10",
        "-r",
        "2",
        "-t",
        "15s",
        "--csv",
        str(report_prefix),
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    stats_path = report_prefix.with_name(report_prefix.name + "_stats.csv")
    with stats_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    aggregate = next(
        row for row in rows if row.get("Name") == "Aggregated" and not row.get("Type")
    )
    request_count = int(aggregate["Request Count"])
    failure_count = int(aggregate["Failure Count"])
    success_rate = ((request_count - failure_count) / request_count) * 100

    assert request_count > 0
    assert success_rate > 95.0
