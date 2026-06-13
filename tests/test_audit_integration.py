"""gaokao-audit 端到端集成测试。"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, cast

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_AUDIT_CLI = importlib.import_module("skills.gaokao-audit.scripts.audit_cli")
_REPORT_GENERATOR = importlib.import_module(
    "skills.gaokao-audit.scripts.report_generator"
)
_ReportGeneratorBase = cast(type[Any], _REPORT_GENERATOR.ReportGenerator)

SAMPLE_PLAN = (
    _REPO_ROOT / "skills" / "gaokao-audit" / "tests" / "fixtures" / "sample_xianyu.txt"
)


class _CaptureReportGenerator(_ReportGeneratorBase):  # type: ignore[valid-type, misc]
    last_html: str = ""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            now_text=lambda: "2026-06-12 23:40",
            report_id_factory=lambda: "AUDIT-E2E-001",
            **kwargs,
        )

    def generate_pdf(self, result, output_path: str, **kwargs: object) -> str:
        html = self.render_html(result, **kwargs)
        type(self).last_html = html
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"%PDF-1.4\ne2e fake pdf\n")
        return str(target)


def _extract_json(stdout: str) -> dict:
    lines = stdout.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("{"):
            return json.loads("\n".join(lines[index:]))
    raise AssertionError(f"stdout 中未找到 JSON 输出: {stdout}")


def test_audit_cli_end_to_end_generates_pdf_and_report_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "audit-e2e.pdf"
    monkeypatch.setattr(_AUDIT_CLI, "ReportGenerator", _CaptureReportGenerator)

    exit_code = _AUDIT_CLI.main([
        str(SAMPLE_PLAN),
        "--output",
        str(output_path),
        "--json",
    ])
    captured = capsys.readouterr()
    payload = _extract_json(captured.out)
    rendered_html = _CaptureReportGenerator.last_html

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF-1.4")

    assert "输入文件" in captured.out
    assert str(output_path) in captured.out
    assert "综合评分" in captured.out

    assert payload["province"] == "湖南"
    assert payload["candidate_score"] == 578
    assert payload["source"] == "百度AI"
    assert len(payload["volunteers"]) == 6
    assert payload["policy_errors"] == []
    assert payload["policy_serious_warnings"]
    assert payload["crowd_risks"]
    risk_schools = {item["school"] for item in payload["crowd_risks"]}
    assert "湖南师范大学" in risk_schools
    assert payload["overall_score"] < 100

    assert "AUDIT-E2E-001" in rendered_html
    assert "湖南 578分 物理+化学+生物" in rendered_html
    assert any(school in rendered_html for school in risk_schools)
    assert "免责声明" in rendered_html
    assert "本审核仅供建议，最终填报以官方公布为准" in rendered_html
