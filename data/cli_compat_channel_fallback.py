"""Thin import shim for `scripts/gaokao-channel-fallback`.

`data.channel_sync.monitor.main` already accepts the subcommand
(`check` / `manual-template`) directly, so this shim is just a
forwarder with project-root sys.path bootstrap.
"""

from __future__ import annotations

import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.channel_sync.monitor import main as _monitor_main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    return _monitor_main(list(argv))
