from __future__ import annotations

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_passes_prod_critical_gaokao_env_vars() -> None:
    compose = yaml.safe_load(
        (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    )
    service_env = compose["services"]["gaokao-admin"]["environment"]

    required_keys = {
        "GAOKAO_ENV",
        "GAOKAO_ADMIN_BIND",
        "GAOKAO_ADMIN_PORT",
        "GAOKAO_ADMIN_USER",
        "GAOKAO_ADMIN_PASS",
        "GAOKAO_JWT_SECRET",
        "GAOKAO_PORTAL_TOKEN_SECRET",
        "GAOKAO_ORDERS_FERNET_KEY",
        "GAOKAO_PAYMENT_PROVIDER",
        "GAOKAO_PAYMENT_BASE_URL",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET",
        "GAOKAO_PAYMENT_NOTIFY_URL",
        "GAOKAO_PAYMENT_RETURN_URL",
        "GAOKAO_PAYMENT_APP_ID",
        "GAOKAO_PAYMENT_PRIVATE_KEY_PATH",
        "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH",
        "GAOKAO_OPS_ALERT_LOG",
    }

    missing = sorted(required_keys - set(service_env))
    assert not missing, f"docker-compose.yml missing gaokao env pass-through: {missing}"


def test_docker_compose_ports_follow_admin_bind_and_port() -> None:
    compose = yaml.safe_load(
        (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    )
    ports = compose["services"]["gaokao-admin"]["ports"]
    assert ports == ["${GAOKAO_ADMIN_BIND:-127.0.0.1}:${GAOKAO_ADMIN_PORT:-8000}:${GAOKAO_ADMIN_PORT:-8000}"]
