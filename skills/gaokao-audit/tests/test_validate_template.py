"""Pytest wrapper for scripts/validate_template.py.

Keeps the T1.2 milestone with a runnable test in the `tests/` package
even before T1.3 lands the parser tests. This addresses the T1.1 review
finding: "no vacuous tests" — this test must be able to fail with a
clear reason if the template regresses.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "validate_template.py"
)


def test_audit_report_template_renders():
    """The audit_report.html template must parse and render with mock data."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"validate_template.py failed (exit {result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    # Sanity: the validator must have printed the success marker
    assert "audit_report.html template is well-formed" in result.stdout, (
        f"validator output missing success marker:\n{result.stdout}"
    )
