#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SKIP_INSTALL="${GAOKAO_SKIP_INSTALL:-0}"
# P1 整改板完成后, 我们仍把 P2 pre-existing tests (locust / 解释器漂移)
# 视为已知遗留问题。X-06 引入 ``--skip-pre-existing`` 以便在本地一键
# 验证时跳过它们; 默认行为不变 (仍然跑全量), 避免掩盖回归。
SKIP_PRE_EXISTING="${GAOKAO_SKIP_PRE_EXISTING:-0}"
# 已知 pre-existing failures (2026-06-14 review 标注, 不属于 P1/P2 必修):
# - tests/test_delivery_dispatcher.py: cli subprocess 走系统 python3 失败
# - tests/test_retention_cleanup.py: 同上
# - tests/test_backup_workflow.py: 同样 subprocess 解释器问题
# - tests/test_t5_performance.py: locust 不可用
PRE_EXISTING_IGNORES=(
  "tests/test_t5_performance.py::test_admin_locust_10_concurrency_success_rate_above_95"
)

log() {
  printf '[dev-verify] %s\n' "$1"
}

python_version_of() {
  "$1" --version 2>&1 | tr -d '\r'
}

ensure_python_bin_matches_venv() {
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    return
  fi
  local venv_version
  local target_version
  venv_version="$(python_version_of "${VENV_DIR}/bin/python")"
  target_version="$(python_version_of "${PYTHON_BIN}")"
  if [[ "${venv_version}" != "${target_version}" ]]; then
    log "python bin drift detected: venv=${venv_version} target=${target_version}"
    log "remove ${VENV_DIR} and rerun, or point PYTHON_BIN at a matching interpreter"
    return 1
  fi
}

ensure_venv() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    log "creating venv at ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
  ensure_python_bin_matches_venv
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  if ! python -m pip --version >/dev/null 2>&1; then
    log "venv missing pip, recreating ${VENV_DIR}"
    rm -rf "${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
  fi
  if [[ "${SKIP_INSTALL}" != "1" ]]; then
    python -m pip install --upgrade pip >/dev/null
  fi
}

install_requirements() {
  if [[ "${SKIP_INSTALL}" == "1" ]]; then
    log "skip install enabled"
    return
  fi
  log "installing requirements"
  pip install -c "${ROOT_DIR}/constraints.txt" -r "${ROOT_DIR}/requirements-admin.txt" -r "${ROOT_DIR}/requirements-dev.txt"
}

run_checks() {
  cd "${ROOT_DIR}"
  log "running pytest with coverage gate"
  # Single source of truth threshold: matches scripts/check_coverage_gate.py
  if [[ "${SKIP_PRE_EXISTING}" == "1" ]]; then
    log "skip pre-existing failures: --skip-pre-existing"
    for node in "${PRE_EXISTING_IGNORES[@]}"; do
      PYTEST_IGNORE_ARGS+=("--deselect" "$node")
    done
  fi
  python -m pytest admin/tests tests data \
    --ignore=.venv \
    --ignore=.worktrees \
    --cov=admin \
    --cov=data \
    --cov=skills \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-fail-under=80 \
    -q \
    "${PYTEST_IGNORE_ARGS[@]}"

  log "running core coverage verifier"
  python scripts/check_coverage_gate.py coverage.xml

  log "running ruff"
  python -m ruff check . --exclude .venv,.worktrees

  log "running mypy"
  python -m mypy .
}

main() {
  while (( $# > 0 )); do
    case "$1" in
      --skip-install)
        SKIP_INSTALL=1
        shift
        ;;
      --skip-pre-existing)
        SKIP_PRE_EXISTING=1
        shift
        ;;
      -h|--help)
        cat <<'EOF'
Usage: bash scripts/dev-verify.sh [--skip-install] [--skip-pre-existing]

Default: ensure venv, install requirements, run full pytest with coverage gate + ruff + mypy.

Flags:
  --skip-install      Skip the venv / pip install step (use existing venv).
  --skip-pre-existing Skip the 8 tests flagged in 2026-06-14 review as
                      pre-existing failures driven by environment drift
                      (subprocess 解释器 / locust 不可用); they are not
                      part of any current P1/P2 remediation target.
EOF
        exit 0
        ;;
      *)
        printf 'unexpected argument: %s\n' "$1" >&2
        exit 1
        ;;
    esac
  done

  ensure_venv
  install_requirements
  run_checks
  log "all checks passed"
}

if [[ "${GAOKAO_SOURCE_ONLY:-0}" != "1" ]]; then
  main "$@"
fi
