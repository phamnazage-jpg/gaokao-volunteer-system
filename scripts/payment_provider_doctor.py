from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from data.payments.provider_requirements import build_provider_readiness_report

    provider = os.environ.get("GAOKAO_PAYMENT_PROVIDER", "mock")
    report = build_provider_readiness_report(provider)
    print(
        json.dumps(
            {
                "provider": report.provider,
                "ready": report.ready,
                "required_env_vars": report.required_env_vars,
                "missing_env_vars": report.missing_env_vars,
                "missing_files": report.missing_files,
                "notes": report.notes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if report.notes and any(
        note.startswith("unsupported provider") for note in report.notes
    ):
        return 3
    return 0 if report.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
