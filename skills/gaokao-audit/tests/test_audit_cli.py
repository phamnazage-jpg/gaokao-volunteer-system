"""gaokao-audit CLI tests."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_AUDIT_CLI = importlib.import_module("skills.gaokao-audit.scripts.audit_cli")

SCRIPT_PATH = _REPO_ROOT / "scripts" / "gaokao-audit"
SAMPLE_PLAN = (
    _REPO_ROOT / "skills" / "gaokao-audit" / "tests" / "fixtures" / "sample_xianyu.txt"
)


class _FakeReportGenerator:
    def __init__(self, **_: object) -> None:
        pass

    def generate_pdf(self, result, output_path: str, **_: object) -> str:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"%PDF-1.4\ncli fake pdf\n")
        return str(target)


def test_main_generates_pdf_and_prints_report_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(_AUDIT_CLI, "ReportGenerator", _FakeReportGenerator)
    output_path = tmp_path / "audit-report.pdf"

    exit_code = _AUDIT_CLI.main([str(SAMPLE_PLAN), "--output", str(output_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF-1.4")
    assert str(output_path) in captured.out
    assert "综合评分" in captured.out


def test_main_missing_input_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_path = tmp_path / "missing.txt"

    exit_code = _AUDIT_CLI.main([str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert str(missing_path) in captured.err


def test_wrapper_script_generates_real_pdf(tmp_path: Path) -> None:
    output_path = tmp_path / "wrapper-report.pdf"
    fake_site = tmp_path / "fake_site"
    fake_site.mkdir()
    (fake_site / "weasyprint.py").write_text(
        "from pathlib import Path\n"
        "class HTML:\n"
        "    def __init__(self, *, string: str, base_url: str) -> None:\n"
        "        self.string = string\n"
        "        self.base_url = base_url\n"
        "    def write_pdf(self, target: str) -> None:\n"
        "        Path(target).write_bytes(b'%PDF-1.4\\nwrapper fake pdf\\n')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(fake_site)
        if not existing_pythonpath
        else f"{fake_site}{os.pathsep}{existing_pythonpath}"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(SAMPLE_PLAN),
            "--output",
            str(output_path),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert str(output_path) in result.stdout
