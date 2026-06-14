#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${1:-${GAOKAO_BACKUP_ROOT:-${ROOT_DIR}/var/backups}}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SNAPSHOT_DIR="${BACKUP_ROOT}/backup-${TIMESTAMP}"
KEEP_COUNT="${GAOKAO_BACKUP_KEEP:-7}"
ADMIN_DB="${GAOKAO_DB_PATH:-${ROOT_DIR}/data/orders/admin.db}"
ORDERS_DB="${GAOKAO_ORDERS_DB_PATH:-${ROOT_DIR}/data/orders.db}"
SHARE_DB="${GAOKAO_SHARE_DB_PATH:-${ROOT_DIR}/data/share/short_links.db}"
SHARE_REPORT_DIR="${GAOKAO_SHARE_REPORT_DIR:-${ROOT_DIR}/data/share/reports}"
EXAMPLE_REPORT_DIR="${ROOT_DIR}/data/examples"
ENV_FILE="${GAOKAO_BACKUP_ENV_FILE:-}"
CONFIG_DIR="${GAOKAO_BACKUP_CONFIG_DIR:-}"
SECRETS_DIR="${GAOKAO_BACKUP_SECRETS_DIR:-}"

log() {
  printf '[backup-snapshot] %s\n' "$1"
}

copy_file_to() {
  local src="$1"
  local dest="$2"
  if [[ -n "$src" && -f "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    log "copied file: $src -> $dest"
  else
    log "skip missing file: ${src:-<empty>}"
  fi
}

copy_dir_to() {
  local src="$1"
  local dest="$2"
  if [[ -n "$src" && -d "$src" ]]; then
    mkdir -p "$dest"
    cp -R "$src/." "$dest/"
    log "copied directory: $src -> $dest"
  else
    log "skip missing directory: ${src:-<empty>}"
  fi
}

write_manifest() {
  ADMIN_DB="$ADMIN_DB" \
  ORDERS_DB="$ORDERS_DB" \
  SHARE_DB="$SHARE_DB" \
  SHARE_REPORT_DIR="$SHARE_REPORT_DIR" \
  EXAMPLE_REPORT_DIR="$EXAMPLE_REPORT_DIR" \
  ENV_FILE="$ENV_FILE" \
  CONFIG_DIR="$CONFIG_DIR" \
  SECRETS_DIR="$SECRETS_DIR" \
  python3 - "$SNAPSHOT_DIR" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
manifest_path = root / "manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


manifest = {
    "generated_at": root.name.removeprefix("backup-"),
    "snapshot_dir": str(root),
    "source_paths": {
        "admin_db": os.environ.get("ADMIN_DB", ""),
        "orders_db": os.environ.get("ORDERS_DB", ""),
        "share_db": os.environ.get("SHARE_DB", ""),
        "share_report_dir": os.environ.get("SHARE_REPORT_DIR", ""),
        "example_report_dir": os.environ.get("EXAMPLE_REPORT_DIR", ""),
        "env_file": os.environ.get("ENV_FILE", ""),
        "config_dir": os.environ.get("CONFIG_DIR", ""),
        "secrets_dir": os.environ.get("SECRETS_DIR", ""),
    },
    "files": [],
}

for path in sorted(root.rglob("*")):
    if not path.is_file() or path == manifest_path:
        continue
    manifest["files"].append(
        {
            "path": str(path.relative_to(root)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    )

manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(manifest_path)
PY
}

prune_old_snapshots() {
  local backup_root="$1"
  local keep_count="$2"
  if ! [[ "$keep_count" =~ ^[0-9]+$ ]] || (( keep_count < 1 )); then
    log "invalid GAOKAO_BACKUP_KEEP=$keep_count, skip prune"
    return
  fi

  mapfile -t snapshots < <(find "$backup_root" -mindepth 1 -maxdepth 1 -type d -name 'backup-*' | sort)
  local total="${#snapshots[@]}"
  if (( total <= keep_count )); then
    return
  fi

  local prune_count=$((total - keep_count))
  local i
  for ((i = 0; i < prune_count; i++)); do
    rm -rf "${snapshots[$i]}"
    log "pruned old snapshot: ${snapshots[$i]}"
  done
}

main() {
  mkdir -p "$SNAPSHOT_DIR"
  log "snapshot dir: $SNAPSHOT_DIR"

  copy_file_to "$ADMIN_DB" "$SNAPSHOT_DIR/db/$(basename "$ADMIN_DB")"
  copy_file_to "$ORDERS_DB" "$SNAPSHOT_DIR/db/$(basename "$ORDERS_DB")"
  copy_file_to "$SHARE_DB" "$SNAPSHOT_DIR/db/$(basename "$SHARE_DB")"
  copy_dir_to "$SHARE_REPORT_DIR" "$SNAPSHOT_DIR/files/reports"
  copy_dir_to "$EXAMPLE_REPORT_DIR" "$SNAPSHOT_DIR/files/examples"
  copy_file_to "$ENV_FILE" "$SNAPSHOT_DIR/config/.env"
  copy_dir_to "$CONFIG_DIR" "$SNAPSHOT_DIR/config/deploy"
  copy_dir_to "$SECRETS_DIR" "$SNAPSHOT_DIR/secrets"

  local manifest_path
  manifest_path="$(write_manifest)"
  log "manifest written: $manifest_path"

  prune_old_snapshots "$BACKUP_ROOT" "$KEEP_COUNT"
  log "backup snapshot finished"
  printf '%s\n' "$SNAPSHOT_DIR"
}

main "$@"
