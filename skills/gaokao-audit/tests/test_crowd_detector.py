"""gaokao-audit 扎堆检测器测试。"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Protocol, cast

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_CROWD_DETECTOR = importlib.import_module("skills.gaokao-audit.scripts.crowd_detector")
CrowdDetector = _CROWD_DETECTOR.CrowdDetector
CrowdRisk = _CROWD_DETECTOR.CrowdRisk


class _CrowdDetectorProto(Protocol):
    def detect_risks(
        self,
        volunteers: list[dict[str, str]],
        province: str,
        score: int,
    ) -> list[Any]: ...

    def get_risk_label(self, frequency: int) -> str: ...

    def format_for_report(
        self,
        risks: list[Any],
        province: str | None = None,
    ) -> list[dict[str, Any]]: ...


class _StubLoader:
    def __init__(self, recommendations: list[dict[str, Any]]) -> None:
        self._recommendations = recommendations

    def find_recommendations(self, province: str, score: int) -> list[dict[str, Any]]:
        return list(self._recommendations)

    def load_metadata(self, province: str) -> dict[str, Any]:
        return {
            "province": province,
            "source": "stub-source",
            "source_url": "https://example.com/source",
            "source_type": "manual_summary",
            "confidence": 0.9,
            "last_updated": "2026-06-12",
            "data_year": 2025,
        }


@pytest.fixture
def detector() -> _CrowdDetectorProto:
    return cast(_CrowdDetectorProto, CrowdDetector())


def test_detect_risks_with_real_loader_returns_high_risk(
    detector: _CrowdDetectorProto,
) -> None:
    plan = [{"school": "湖南师范大学", "major": "会计学"}]

    risks = detector.detect_risks(plan, province="湖南", score=578)

    assert len(risks) == 1
    risk = risks[0]
    assert isinstance(risk, CrowdRisk)
    assert risk.school == "湖南师范大学"
    assert risk.major == "会计学"
    assert risk.frequency == 4
    assert risk.risk_level == "high"
    assert risk.predicted_increase == 15
    assert len(risk.alternatives) >= 1


def test_detect_risks_supports_school_abbreviation(
    detector: _CrowdDetectorProto,
) -> None:
    plan = [{"school": "湖南师范", "major": "会计学"}]

    risks = detector.detect_risks(plan, province="湖南", score=578)

    assert len(risks) == 1
    assert risks[0].school == "湖南师范大学"


def test_detect_risks_returns_empty_for_unknown_school(
    detector: _CrowdDetectorProto,
) -> None:
    plan = [{"school": "某某不知名学校", "major": "考古学"}]

    risks = detector.detect_risks(plan, province="湖南", score=578)

    assert risks == []


def test_detect_risks_supports_low_risk_via_stub_loader() -> None:
    stub_loader = _StubLoader(
        recommendations=[
            {
                "name": "测试大学",
                "major": "测试专业",
                "frequency": 1,
                "platforms": ["千问"],
                "predicted_increase": 3,
                "alternatives": [
                    {"name": "替代大学", "major": "替代专业", "score": 90}
                ],
            }
        ]
    )
    detector = cast(_CrowdDetectorProto, CrowdDetector(loader=stub_loader))

    risks = detector.detect_risks(
        [{"school": "测试大学", "major": "测试专业"}],
        province="湖南",
        score=578,
    )

    assert len(risks) == 1
    assert risks[0].risk_level == "low"
    assert risks[0].risk_level_label == "🟢 低风险"


def test_get_risk_label_covers_three_levels(detector: _CrowdDetectorProto) -> None:
    assert detector.get_risk_label(4) == "🔴 高风险"
    assert detector.get_risk_label(2) == "🟡 中风险"
    assert detector.get_risk_label(1) == "🟢 低风险"


def test_format_for_report_exposes_template_fields(
    detector: _CrowdDetectorProto,
) -> None:
    risks = detector.detect_risks(
        [{"school": "湖南师范大学", "major": "会计学"}],
        province="湖南",
        score=578,
    )

    formatted = detector.format_for_report(risks, province="湖南")

    assert len(formatted) == 1
    first = formatted[0]
    assert first["school"] == "湖南师范大学"
    assert first["name"] == "湖南师范大学"
    assert first["risk_level"] == "high"
    assert first["risk_level_label"] == "高"
    assert first["risk_emoji"] == "🔴"
    assert first["source_type"] == "report"
    assert first["source_type_icon"] == "⚠️"
    assert all("school" in alt for alt in first["alternatives"])
