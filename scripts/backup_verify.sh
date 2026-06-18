#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_BACKUP_DIR=""
VERIFY_DIR=""
SKIP_SMOKE="0"
ADMIN_DB="${GAOKAO_DB_PATH:-${ROOT_DIR}/data/orders/admin.db}"
ORDERS_DB="${GAOKAO_ORDERS_DB_PATH:-${ROOT_DIR}/data/orders.db}"
SHARE_DB="${GAOKAO_SHARE_DB_PATH:-${ROOT_DIR}/data/share/short_links.db}"
SHARE_REPORT_DIR="${GAOKAO_SHARE_REPORT_DIR:-${ROOT_DIR}/data/share/reports}"
EXAMPLE_REPORT_DIR="${ROOT_DIR}/data/examples"
PORTAL_UPLOAD_DIR="${GAOKAO_PORTAL_UPLOAD_DIR:-${ROOT_DIR}/data/portal_uploads}"
ORDER_ARTIFACT_HELPER="${ROOT_DIR}/scripts/backup_collect_order_artifacts.py"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/backup_verify.sh [verify_dir]
  bash scripts/backup_verify.sh --from-backup /path/to/backup-dir [--skip-smoke]

Default mode copies live SQLite/files into a temporary verify dir, then validates:
- SQLite files are readable
- manifest checksums (if manifest.json exists)
- restore smoke via FastAPI TestClient (unless --skip-smoke)
EOF
}

log() {
  printf '[backup-verify] %s\n' "$1"
}

copy_if_exists() {
  local src="$1"
  local dest_dir="$2"
  if [[ -f "$src" ]]; then
    mkdir -p "$dest_dir"
    cp "$src" "$dest_dir/"
    log "copied file: $src"
  else
    log "skip missing file: $src"
  fi
}

copy_dir_if_exists() {
  local src="$1"
  local dest_dir="$2"
  if [[ -d "$src" ]]; then
    mkdir -p "$dest_dir"
    cp -R "$src/." "$dest_dir/"
    log "copied directory: $src"
  else
    log "skip missing directory: $src"
  fi
}

copy_order_artifacts_if_possible() {
  local orders_db="$1"
  local dest_dir="$2"
  if [[ ! -f "$orders_db" ]]; then
    log "skip order artifacts, missing orders db: $orders_db"
    return
  fi
  mkdir -p "$dest_dir"
  local summary
  summary="$(python3 "$ORDER_ARTIFACT_HELPER" --orders-db "$orders_db" --output-dir "$dest_dir")"
  log "copied order artifacts: $summary"
}

stage_live_sources() {
  log "verify dir: $VERIFY_DIR"
  copy_if_exists "$ADMIN_DB" "$VERIFY_DIR/db"
  copy_if_exists "$ORDERS_DB" "$VERIFY_DIR/db"
  copy_if_exists "$SHARE_DB" "$VERIFY_DIR/db"
  copy_dir_if_exists "$SHARE_REPORT_DIR" "$VERIFY_DIR/files/reports"
  copy_dir_if_exists "$EXAMPLE_REPORT_DIR" "$VERIFY_DIR/files/examples"
  copy_dir_if_exists "$PORTAL_UPLOAD_DIR" "$VERIFY_DIR/files/portal_uploads"
  copy_order_artifacts_if_possible "$ORDERS_DB" "$VERIFY_DIR/files/order_artifacts"
}

stage_existing_backup() {
  if [[ ! -d "$SOURCE_BACKUP_DIR" ]]; then
    printf 'backup dir not found: %s\n' "$SOURCE_BACKUP_DIR" >&2
    exit 1
  fi
  log "staging backup dir: $SOURCE_BACKUP_DIR -> $VERIFY_DIR"
  mkdir -p "$VERIFY_DIR"
  cp -R "$SOURCE_BACKUP_DIR/." "$VERIFY_DIR/"
}

verify_manifest_if_present() {
  local manifest_path="$1"
  if [[ ! -f "$manifest_path" ]]; then
    log "skip missing manifest: $manifest_path"
    return
  fi

  log "verifying manifest checksums"
  python3 - "$manifest_path" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1]).resolve()
root = manifest_path.parent
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
errors: list[str] = []
for item in manifest.get("files", []):
    rel = item["path"]
    target = root / rel
    if not target.is_file():
        errors.append(f"missing file: {rel}")
        continue
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest != item["sha256"]:
        errors.append(f"sha256 mismatch: {rel}")
if errors:
    for err in errors:
        print(err)
    raise SystemExit(1)
print(f"manifest_ok files={len(manifest.get('files', []))}")
PY
}

verify_sqlite_file() {
  local db_path="$1"
  if [[ ! -f "$db_path" ]]; then
    return 0
  fi
  python3 - <<'PY' "$db_path"
import sqlite3
import sys
from pathlib import Path

p = Path(sys.argv[1])
conn = sqlite3.connect(p)
try:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    print(f"sqlite_ok path={p} tables={','.join(tables) if tables else 'none'}")
finally:
    conn.close()
PY
}

verify_artifacts() {
  log "verifying copied sqlite files"
  if [[ -d "$VERIFY_DIR/db" ]]; then
    while IFS= read -r -d '' db_file; do
      verify_sqlite_file "$db_file"
    done < <(find "$VERIFY_DIR/db" -type f -name '*.db' -print0 | sort -z)
  fi

  log "verifying copied report artifacts"
  if [[ -d "$VERIFY_DIR/files" ]]; then
    find "$VERIFY_DIR/files" -type f | sort | sed 's#^#[backup-verify] artifact: #'
  fi
}

run_restore_smoke() {
  if [[ "$SKIP_SMOKE" == "1" ]]; then
    log "skip restore smoke"
    return
  fi

  log "running restore smoke"
  # Prefer the project virtualenv if present so the smoke step uses
  # the same dependency set as the rest of the project.  Falling back
  # to ``python3`` is fine for dev environments where the user has
  # already installed admin / test requirements globally.
  local python_bin="${ROOT_DIR}/.venv/bin/python"
  if [[ ! -x "$python_bin" ]]; then
    python_bin="python3"
  fi
  "$python_bin" "$ROOT_DIR/scripts/backup_restore_smoke.py" --backup-dir "$VERIFY_DIR"
}

parse_args() {
  while (( $# > 0 )); do
    case "$1" in
      --from-backup)
        SOURCE_BACKUP_DIR="$2"
        shift 2
        ;;
      --skip-smoke)
        SKIP_SMOKE="1"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        if [[ -n "$VERIFY_DIR" ]]; then
          printf 'unexpected argument: %s\n' "$1" >&2
          exit 1
        fi
        VERIFY_DIR="$1"
        shift
        ;;
    esac
  done
}

main() {
  parse_args "$@"
  VERIFY_DIR="${VERIFY_DIR:-$(mktemp -d /tmp/gaokao-backup-verify-XXXXXX)}"

  if [[ -n "$SOURCE_BACKUP_DIR" ]]; then
    stage_existing_backup
  else
    mkdir -p "$VERIFY_DIR"
    stage_live_sources
  fi

  verify_manifest_if_present "$VERIFY_DIR/manifest.json"
  verify_artifacts
  run_restore_smoke
  log "backup verification finished"
}

main "$@"
