"""gaokao-audit 报告生成器测试。"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Protocol, cast

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_AUDIT_SERVICE = importlib.import_module("skills.gaokao-audit.scripts.audit_service")
AuditResult = _AUDIT_SERVICE.AuditResult

_CROWD_DETECTOR = importlib.import_module("skills.gaokao-audit.scripts.crowd_detector")
CrowdRisk = _CROWD_DETECTOR.CrowdRisk

_REPORT_GENERATOR = importlib.import_module(
    "skills.gaokao-audit.scripts.report_generator"
)
ReportGenerator = _REPORT_GENERATOR.ReportGenerator


class _ReportGeneratorProto(Protocol):
    def render_html(self, result: Any, **kwargs: object) -> str: ...

    def generate_pdf(self, result: Any, output_path: str, **kwargs: object) -> str: ...

    def generate_html(self, result: Any, output_path: str) -> str: ...

    def _default_report_id(self) -> str: ...


@pytest.fixture
def generator() -> _ReportGeneratorProto:
    return cast(
        _ReportGeneratorProto,
        ReportGenerator(
            now_text=lambda: "2026-06-12 21:45",
            report_id_factory=lambda: "AUDIT-UNIT-REPORT",
        ),
    )


@pytest.fixture
def sample_result() -> Any:
    return AuditResult(
        province="湖南",
        candidate_score=578,
        candidate_rank=26800,
        subjects="物理+化学+生物",
        source="百度AI志愿助手",
        volunteers=[
            {"index": 1, "school": "长沙理工大学", "major": "会计学"},
        ],
        policy_errors=[],
        crowd_risks=[
            CrowdRisk(
                school="长沙理工大学",
                major="会计学",
                frequency=4,
                platforms=["千问", "元宝", "百度", "豆包"],
                predicted_increase=18,
                risk_level="high",
                alternatives=[
                    {"school": "湖南工商大学", "score": 95},
                ],
            ),
        ],
        data_issues=[
            {
                "location": "分数/位次依据",
                "description": "未明确数据年份（建议标注2025年参考位次）",
                "recommendation": "补充分数线或位次所对应的年份。",
            }
        ],
        suggestions=["检测到 1 所高风险扎堆院校，建议优先替换为低风险替代方案"],
        overall_score=75,
    )


def test_render_html_renders_template_payload(
    generator: _ReportGeneratorProto, sample_result: Any
) -> None:
    html = generator.render_html(sample_result)

    assert isinstance(html, str)
    assert "AUDIT-UNIT-REPORT" in html
    assert "2026-06-12 21:45" in html
    assert "湖南 578分 物理+化学+生物" in html
    assert "长沙理工大学" in html
    assert "免责声明" in html
    assert "{{" not in html


def test_generate_pdf_uses_weasyprint_writer(
    tmp_path: Path,
    generator: _ReportGeneratorProto,
    sample_result: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    written: dict[str, str] = {}

    class FakeHTML:
        def __init__(self, *, string: str, base_url: str) -> None:
            written["html"] = string
            written["base_url"] = base_url

        def write_pdf(self, target: str) -> None:
            Path(target).write_bytes(b"%PDF-1.4\nmock pdf bytes\n")
            written["target"] = target

    monkeypatch.setattr(_REPORT_GENERATOR, "_load_weasyprint_html", lambda: FakeHTML)

    output_path = tmp_path / "audit_report.pdf"
    pdf_path = generator.generate_pdf(sample_result, str(output_path))

    assert pdf_path == str(output_path)
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF-1.4")
    assert written["target"] == str(output_path)
    assert "长沙理工大学" in written["html"]
    assert written["base_url"].endswith("skills/gaokao-audit/templates")


def test_generate_html_writes_file(
    tmp_path: Path,
    generator: _ReportGeneratorProto,
    sample_result: Any,
) -> None:
    output_path = tmp_path / "audit_report.html"

    html_path = generator.generate_html(sample_result, str(output_path))

    assert html_path == str(output_path)
    assert output_path.exists()
    rendered = output_path.read_text(encoding="utf-8")
    assert "AUDIT-UNIT-REPORT" in rendered
    assert "百度AI志愿助手" in rendered


def test_load_weasyprint_html_uses_import_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeModule:
        HTML = object()

    monkeypatch.setattr(
        _REPORT_GENERATOR, "import_module", lambda name: FakeModule, raising=False
    )

    html_cls = _REPORT_GENERATOR._load_weasyprint_html()

    assert html_cls is FakeModule.HTML


def test_default_report_id_uses_expected_prefix() -> None:
    generator = cast(_ReportGeneratorProto, ReportGenerator())

    report_id = generator._default_report_id()

    assert report_id.startswith("AUDIT-")
    assert len(report_id.split("-")) >= 3
