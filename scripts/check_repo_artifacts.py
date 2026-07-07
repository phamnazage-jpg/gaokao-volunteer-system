#!/usr/bin/env python3
"""Detect untracked or accidental runtime artifacts before delivery."""
from __future__ import annotations

import subprocess
from pathlib import Path

FORBIDDEN_PATTERNS = (
    "test-results/",
    ".turbo/cache/",
    ".db-shm",
    ".db-wal",
)


def main() -> int:
    proc = subprocess.run(["git", "status", "--short"], text=True, capture_output=True, check=True)
    bad = []
    for line in proc.stdout.splitlines():
        path = line[3:] if len(line) > 3 else line
        if any(pattern in path for pattern in FORBIDDEN_PATTERNS):
            bad.append(line)
    if bad:
        print("forbidden artifacts in git status:")
        for item in bad:
            print(item)
        return 1
    print("repo artifact check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
