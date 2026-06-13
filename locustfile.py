"""T11.1 Locust 性能基准脚本。

目标：对 T6.1 FastAPI 管理后台骨架做最小真实压测，验证计划中的
"10 并发"目标，并记录各端点的延迟/错误率基线。

压测模型：
- AdminBrowseUser：模拟已登录后台管理员，覆盖 /me /meta /orders /stats
- LoginBurstUser：模拟登录高峰，持续打 /api/auth/login

运行示例：
    GAOKAO_JWT_SECRET=$(python3 - <<'PY'
    print('x'*64)
    PY
    ) \
    locust -f locustfile.py --host http://127.0.0.1:18080 \
      --headless -u 10 -r 2 -t 1m --csv reports/perf/t11_1
"""

from __future__ import annotations

import os
from typing import Optional

from locust import HttpUser, between, task


ADMIN_USER = os.getenv("GAOKAO_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("GAOKAO_ADMIN_PASS", "admin123")


class AuthenticatedHttpUser(HttpUser):
    abstract = True
    wait_time = between(0.3, 1.2)
    token: Optional[str] = None

    def on_start(self) -> None:
        self.login()

    def login(self) -> None:
        with self.client.post(
            "/api/auth/login",
            json={"username": ADMIN_USER, "password": ADMIN_PASS},
            name="POST /api/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"login failed: {resp.status_code} {resp.text[:200]}")
                self.token = None
                return
            data = resp.json()
            token = data.get("access_token")
            if not token:
                resp.failure("login response missing access_token")
                self.token = None
                return
            self.token = token
            self.client.headers.update({"Authorization": f"Bearer {token}"})
            resp.success()


class AdminBrowseUser(AuthenticatedHttpUser):
    weight = 4

    @task(5)
    def me(self) -> None:
        self.client.get("/api/auth/me", name="GET /api/auth/me")

    @task(4)
    def meta(self) -> None:
        self.client.get("/api/meta", name="GET /api/meta")

    @task(6)
    def list_orders(self) -> None:
        self.client.get("/api/orders?limit=50&offset=0", name="GET /api/orders")

    @task(3)
    def order_stats(self) -> None:
        self.client.get("/api/stats/orders", name="GET /api/stats/orders")

    @task(1)
    def detail_missing(self) -> None:
        with self.client.get(
            "/api/orders/non-existent-order-id",
            name="GET /api/orders/{id} [404]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()
            else:
                resp.failure(f"expected 404, got {resp.status_code}")


class LoginBurstUser(HttpUser):
    weight = 1
    wait_time = between(1.0, 3.0)

    @task(4)
    def login(self) -> None:
        self.client.post(
            "/api/auth/login",
            json={"username": ADMIN_USER, "password": ADMIN_PASS},
            name="POST /api/auth/login",
        )

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
