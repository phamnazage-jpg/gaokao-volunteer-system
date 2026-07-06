#!/usr/bin/env bash
set -euo pipefail

# gaokao-production-doctor.sh
# 检查生产部署前置条件，返回 ready / not-ready + 缺失项清单。
# 用法: bash scripts/gaokao-production-doctor.sh [--env-file .env]

ENV_FILE="${1:-}"
if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
  set -a; source "$ENV_FILE"; set +a
fi

PASS=0
FAIL=0
MISSING=()

check() {
  local name="$1"
  local value="${!2:-}"
  if [ -n "$value" ] && [ "$value" != "mock" ] && [ "$value" != "dev" ]; then
    echo "  [PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] $name (empty or placeholder)"
    FAIL=$((FAIL + 1))
    MISSING+=("$name")
  fi
}

echo "=== Gaokao Production Readiness Doctor ==="
echo ""

echo "--- Environment ---"
check "GAOKAO_ENV" GAOKAO_ENV

echo ""
echo "--- Security Keys ---"
check "GAOKAO_JWT_SECRET" GAOKAO_JWT_SECRET
check "GAOKAO_PORTAL_TOKEN_SECRET" GAOKAO_PORTAL_TOKEN_SECRET
check "GAOKAO_ORDERS_FERNET_KEY" GAOKAO_ORDERS_FERNET_KEY
check "GAOKAO_ADMIN_PASS" GAOKAO_ADMIN_PASS

echo ""
echo "--- Payment (alipay) ---"
check "GAOKAO_PAYMENT_PROVIDER" GAOKAO_PAYMENT_PROVIDER
check "GAOKAO_PAYMENT_APP_ID" GAOKAO_PAYMENT_APP_ID
check "GAOKAO_PAYMENT_PRIVATE_KEY_PATH" GAOKAO_PAYMENT_PRIVATE_KEY_PATH
check "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH" GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH
check "GAOKAO_PAYMENT_NOTIFY_URL" GAOKAO_PAYMENT_NOTIFY_URL
check "GAOKAO_PAYMENT_RETURN_URL" GAOKAO_PAYMENT_RETURN_URL
check "GAOKAO_PAYMENT_WEBHOOK_SECRET" GAOKAO_PAYMENT_WEBHOOK_SECRET

echo ""
echo "--- LLM ---"
check "GAOKAO_LLM_PROVIDER" GAOKAO_LLM_PROVIDER
check "GAOKAO_LLM_API_KEY" GAOKAO_LLM_API_KEY

echo ""
echo "--- SMTP / Alert ---"
check "GAOKAO_SMTP_HOST" GAOKAO_SMTP_HOST
check "GAOKAO_SMTP_SENDER" GAOKAO_SMTP_SENDER
check "GAOKAO_ALERT_RECIPIENTS" GAOKAO_ALERT_RECIPIENTS

echo ""
echo "--- Summary ---"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "MISSING: ${MISSING[*]}"
  echo ""
  echo "RESULT: NOT READY — 请补全上述缺失的外部凭证后重新运行。"
  exit 1
else
  echo "RESULT: READY — 所有前置条件已满足，可以执行生产部署。"
  exit 0
fi
