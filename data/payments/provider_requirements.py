from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass
class ProviderReadinessReport:
    provider: str
    required_env_vars: list[str]
    missing_env_vars: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not self.missing_env_vars and not self.missing_files


_PROVIDER_REQUIREMENTS: dict[str, list[str]] = {
    "mock": [],
    "alipay_sim": [],
    "alipay": [
        "GAOKAO_PAYMENT_APP_ID",
        "GAOKAO_PAYMENT_PRIVATE_KEY_PATH",
        "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH",
        "GAOKAO_PAYMENT_NOTIFY_URL",
        "GAOKAO_PAYMENT_RETURN_URL",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET",
    ],
}

_FILE_ENV_VARS = {
    "GAOKAO_PAYMENT_PRIVATE_KEY_PATH",
    "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH",
}


def supported_providers() -> list[str]:
    return sorted(_PROVIDER_REQUIREMENTS)


def build_provider_readiness_report(
    provider: str,
    env: Mapping[str, str] | None = None,
) -> ProviderReadinessReport:
    env_map = dict(os.environ if env is None else env)
    normalized = (provider or "mock").strip().lower()
    requirements = _PROVIDER_REQUIREMENTS.get(normalized)
    if requirements is None:
        return ProviderReadinessReport(
            provider=normalized,
            required_env_vars=[],
            missing_env_vars=[],
            missing_files=[],
            notes=[f"unsupported provider: {normalized}"],
        )

    report = ProviderReadinessReport(
        provider=normalized, required_env_vars=list(requirements)
    )
    for name in requirements:
        value = env_map.get(name, "").strip()
        if not value:
            report.missing_env_vars.append(name)
            continue
        if name in _FILE_ENV_VARS and not Path(value).is_file():
            report.missing_files.append(name)

    if normalized == "mock":
        report.notes.append("mock provider 仅用于本地/测试闭环，不代表真实收款上线")
    elif normalized == "alipay_sim":
        report.notes.extend([
            "alipay_sim 用于上线前模拟支付宝支付/回调验证，不代表真实支付宝已联通。",
            "上线前仍必须以真实 app_id/证书/notify_url 完成一次真实支付宝测试。",
        ])
    elif normalized == "alipay":
        report.notes.extend([
            "建议先用支付宝作为首个真实 Web 支付 provider；当前架构更贴合 checkout_url 跳转模式。",
            "真实上线前仍需商户主体、产品签约、备案域名与公网 notify_url。",
        ])
    return report
