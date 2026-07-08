from __future__ import annotations

import subprocess
import sys


def test_llm_domain_data_coverage_gate_passes() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/check_llm_domain_data_coverage.py"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "llm domain data coverage ok" in proc.stdout
