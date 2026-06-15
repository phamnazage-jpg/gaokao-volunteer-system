#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SKIP_INSTALL="${GAOKAO_SKIP_INSTALL:-0}"

log() {
  printf '[dev-verify] %s\n' "$1"
}

ensure_venv() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    log "creating venv at ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  python -m pip install --upgrade pip >/dev/null
}

install_requirements() {
  if [[ "${SKIP_INSTALL}" == "1" ]]; then
    log "skip install enabled"
    return
  fi
  log "installing requirements"
  pip install -r "${ROOT_DIR}/requirements-admin.txt" -r "${ROOT_DIR}/requirements-dev.txt"
}

run_checks() {
  cd "${ROOT_DIR}"
  log "running pytest with coverage gate"
  # Single source of truth threshold: matches scripts/check_coverage_gate.py
  python -m pytest admin/tests tests data \
    --ignore=.venv \
    --ignore=.worktrees \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-fail-under=80 \
    -q

  log "running core coverage verifier"
  python scripts/check_coverage_gate.py coverage.xml

  log "running ruff"
  python -m ruff check . --exclude .venv,.worktrees

  log "running mypy"
  python -m mypy .
}

main() {
  ensure_venv
  install_requirements
  run_checks
  log "all checks passed"
}

main "$@"
