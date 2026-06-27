#!/usr/bin/env python3
"""支付 provider readiness doctor.

检查真实支付 acceptance 所需的全部前置条件是否就绪。
返回 ready / missing_env_vars / missing_files / notes。

用法:
    python3 scripts/payment_readiness_doctor.py
    python3 scripts/payment_readiness_doctor.py --json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REQUIRED_ENV_VARS = [
    "GAOKAO_PAYMENT_APP_ID",
    "GAOKAO_PAYMENT_MERCHANT_ID",
    "GAOKAO_PAYMENT_PRIVATE_KEY_PATH",
    "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH",
    "GAOKAO_PAYMENT_NOTIFY_URL",
    "GAOKAO_PAYMENT_RETURN_URL",
    "GAOKAO_PAYMENT_WEBHOOK_SECRET",
    "GAOKAO_ORDERS_FERNET_KEY",
    "GAOKAO_JWT_SECRET",
    "GAOKAO_PORTAL_TOKEN_SECRET",
    "GAOKAO_ADMIN_PASS",
]

REQUIRED_FILE_ENV_VARS = [
    ("GAOKAO_PAYMENT_PRIVATE_KEY_PATH", "应用私钥文件"),
    ("GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH", "支付宝公钥文件"),
]

REQUIRED_URL_PREFIX = "https://"


def check() -> dict:
    missing_env = []
    notes = []

    for var in REQUIRED_ENV_VARS:
        val = os.environ.get(var, "")
        if not val:
            missing_env.append(var)

    # 检查 URL 是否 HTTPS
    notify_url = os.environ.get("GAOKAO_PAYMENT_NOTIFY_URL", "")
    if notify_url and not notify_url.startswith(REQUIRED_URL_PREFIX):
        notes.append(
            f"GAOKAO_PAYMENT_NOTIFY_URL 应为 HTTPS（当前: {notify_url[:30]}...）"
        )

    return_url = os.environ.get("GAOKAO_PAYMENT_RETURN_URL", "")
    if return_url and not return_url.startswith(REQUIRED_URL_PREFIX):
        notes.append(
            f"GAOKAO_PAYMENT_RETURN_URL 应为 HTTPS（当前: {return_url[:30]}...）"
        )

    # JWT secret 长度
    jwt = os.environ.get("GAOKAO_JWT_SECRET", "")
    if jwt and len(jwt) < 32:
        notes.append(f"GAOKAO_JWT_SECRET 长度不足 32（当前 {len(jwt)}）")

    # Portal token secret 与 JWT 不同
    portal = os.environ.get("GAOKAO_PORTAL_TOKEN_SECRET", "")
    if jwt and portal and jwt == portal:
        notes.append("GAOKAO_PORTAL_TOKEN_SECRET 与 GAOKAO_JWT_SECRET 相同，必须分离")

    # 检查密钥文件是否存在
    missing_files = []
    for var, desc in REQUIRED_FILE_ENV_VARS:
        path = os.environ.get(var, "")
        if path and not Path(path).is_file():
            missing_files.append({"var": var, "path": path, "desc": desc})

    ready = len(missing_env) == 0 and len(missing_files) == 0 and len(notes) == 0

    return {
        "ready": ready,
        "missing_env_vars": missing_env,
        "missing_files": missing_files,
        "notes": notes,
        "total_required": len(REQUIRED_ENV_VARS),
        "total_satisfied": len(REQUIRED_ENV_VARS) - len(missing_env),
    }


def main() -> int:
    as_json = "--json" in sys.argv
    result = check()

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "READY" if result["ready"] else "NOT READY"
        print(f"[payment-doctor] {status}")
        print(
            f"  env vars satisfied: {result['total_satisfied']}/{result['total_required']}"
        )
        if result["missing_env_vars"]:
            print(f"  missing env vars: {', '.join(result['missing_env_vars'])}")
        if result["missing_files"]:
            for f in result["missing_files"]:
                print(f"  missing file: {f['var']} → {f['path']} ({f['desc']})")
        if result["notes"]:
            for n in result["notes"]:
                print(f"  note: {n}")
        if not result["ready"]:
            print("\n  参考 .env.payment.example 获取完整配置模板")
            print("  参考 docs/PAYMENT_PROVIDER_ONBOARDING.md 获取接入步骤")

    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
