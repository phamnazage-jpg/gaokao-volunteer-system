#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY_DIR="${1:-$(mktemp -d /tmp/gaokao-backup-verify-XXXXXX)}"
ADMIN_DB="${GAOKAO_DB_PATH:-${ROOT_DIR}/data/orders/admin.db}"
ORDERS_DB="${GAOKAO_ORDERS_DB_PATH:-${ROOT_DIR}/data/orders.db}"
SHARE_DB="${GAOKAO_SHARE_DB_PATH:-${ROOT_DIR}/data/share/short_links.db}"
SHARE_REPORT_DIR="${GAOKAO_SHARE_REPORT_DIR:-${ROOT_DIR}/data/share/reports}"
EXAMPLE_REPORT_DIR="${ROOT_DIR}/data/examples"

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
    cp -R "$src" "$dest_dir/"
    log "copied directory: $src"
  else
    log "skip missing directory: $src"
  fi
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

main() {
  mkdir -p "$VERIFY_DIR"
  log "verify dir: $VERIFY_DIR"

  copy_if_exists "$ADMIN_DB" "$VERIFY_DIR/db"
  copy_if_exists "$ORDERS_DB" "$VERIFY_DIR/db"
  copy_if_exists "$SHARE_DB" "$VERIFY_DIR/db"
  copy_dir_if_exists "$SHARE_REPORT_DIR" "$VERIFY_DIR/files"
  copy_dir_if_exists "$EXAMPLE_REPORT_DIR" "$VERIFY_DIR/files"

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

  log "backup verification finished"
}

main "$@"
