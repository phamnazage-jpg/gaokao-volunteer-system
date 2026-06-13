"""gaokao-audit 审核服务测试。"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Protocol, cast

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_AUDIT_SERVICE = importlib.import_module("skills.gaokao-audit.scripts.audit_service")
AuditResult = _AUDIT_SERVICE.AuditResult
AuditService = _AUDIT_SERVICE.AuditService

_CROWD_DETECTOR = importlib.import_module("skills.gaokao-audit.scripts.crowd_detector")
CrowdRisk = _CROWD_DETECTOR.CrowdRisk


class _AuditServiceProto(Protocol):
    def audit(self, plan_text: str, format: str = "text") -> Any: ...

    def build_report_payload(
        self,
        result: Any,
        *,
        audit_time: str,
        report_id: str,
    ) -> dict[str, Any]: ...


@pytest.fixture
def service() -> _AuditServiceProto:
    return cast(_AuditServiceProto, AuditService())


@pytest.fixture
def sample_plan_text() -> str:
    return """
百度AI志愿助手为您推荐

考生信息
省份：湖南
高考分数：578
位次：约26800
选科：物理+化学+生物

推荐院校
1. 湖南师范大学 - 会计学
2. 长沙理工大学 - 会计学
3. 江西财经大学 - 会计学
4. 湘潭大学 - 工商管理
5. 湖南工商大学 - 财务管理
"""


def test_audit_plan_basic(service: _AuditServiceProto, sample_plan_text: str) -> None:
    result = service.audit(sample_plan_text, format="text")

    assert isinstance(result, AuditResult)
    assert result.province == "湖南"
    assert result.candidate_score == 578
    assert result.candidate_rank == 26800
    assert result.subjects == "物理+化学+生物"
    assert result.source is not None
    assert len(result.volunteers) == 5


def test_audit_detects_policy_and_crowd_risk(
    service: _AuditServiceProto, sample_plan_text: str
) -> None:
    result = service.audit(sample_plan_text, format="text")

    assert result.policy_errors == []
    assert len(result.policy_serious_warnings) >= 1
    assert any("rule" in item for item in result.policy_serious_warnings)
    assert len(result.crowd_risks) >= 1
    assert any(risk.risk_level == "high" for risk in result.crowd_risks)


def test_audit_calculates_score_and_suggestions(
    service: _AuditServiceProto, sample_plan_text: str
) -> None:
    result = service.audit(sample_plan_text, format="text")

    assert 0 <= result.overall_score <= 100
    assert result.overall_score < 90
    assert result.suggestions
    assert any("政策" in item or "扎堆" in item for item in result.suggestions)


def test_audit_to_dict_serializes_crowd_risks(
    service: _AuditServiceProto, sample_plan_text: str
) -> None:
    payload = service.audit(sample_plan_text, format="text").to_dict()

    assert payload["province"] == "湖南"
    assert "overall_score" in payload
    assert "policy_errors" in payload
    assert isinstance(payload["crowd_risks"], list)
    assert payload["crowd_risks"]
    assert isinstance(payload["crowd_risks"][0], dict)
    assert payload["crowd_risks"][0]["school"]
    assert payload["crowd_risks"][0]["risk_level"] in {"high", "medium", "low"}


def test_audit_marks_data_trace_issues_when_year_missing(
    service: _AuditServiceProto,
) -> None:
    text = """
腾讯元宝志愿建议
省份：湖南
高考分数：578
位次：26800
选科：物理+化学+生物
1. 湖南工商大学 - 财务管理
"""

    result = service.audit(text, format="text")

    assert result.data_issues
    assert any("年份" in item["description"] for item in result.data_issues)
    assert all("location" in item for item in result.data_issues)


def test_audit_result_to_dict_handles_manual_crowd_risk() -> None:
    result = AuditResult(
        province="湖南",
        crowd_risks=[
            CrowdRisk(
                school="湖南师范大学",
                major="会计学",
                frequency=4,
                platforms=["百度", "元宝"],
                predicted_increase=15,
                risk_level="high",
                alternatives=[{"school": "湖南工商大学", "major": "会计学"}],
            )
        ],
    )

    payload = result.to_dict()

    assert payload["crowd_risks"][0]["school"] == "湖南师范大学"
    assert payload["crowd_risks"][0]["risk_level_label"] == "🔴 高风险"


def test_build_report_payload_renders_template(
    service: _AuditServiceProto, sample_plan_text: str
) -> None:
    result = service.audit(sample_plan_text, format="text")
    payload = service.build_report_payload(
        result,
        audit_time="2026-06-12 21:30",
        report_id="AUDIT-UNIT-001",
    )

    assert payload["candidate_info"] == "湖南 578分 物理+化学+生物"
    assert payload["fatal_count"] == 0
    assert payload["warning_count"] >= len(result.crowd_risks)
    assert payload["crowd_risks"]
    assert payload["crowd_risks"][0]["risk_emoji"] in {"🔴", "🟡", "🟢"}
    assert payload["data_issues"][0]["location"]

    env = Environment(
        loader=FileSystemLoader(
            os.path.join(_REPO_ROOT, "skills", "gaokao-audit", "templates")
        ),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("audit_report.html")
    rendered = template.render(**payload)

    assert "AUDIT-UNIT-001" in rendered
    assert payload["crowd_risks"][0]["school"] in rendered
    assert payload["crowd_risks"][0]["risk_emoji"] in rendered
