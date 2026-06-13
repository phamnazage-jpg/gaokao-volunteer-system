"""gaokao-audit 扎堆检测器。

复用 data.crowd_db 下已经验证过的检测算法与报告格式转换，
对 audit skill 暴露稳定的类接口：CrowdDetector / CrowdRisk。
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, cast

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_BASE_DETECTOR = importlib.import_module("data.crowd_db.crowd_detector")
_RISK_REPORT = importlib.import_module("data.crowd_db.risk_report")
_LOADER_MODULE = importlib.import_module("data.crowd_db.loader")

_CrowdDBLoaderCtor = cast(Any, _LOADER_MODULE.CrowdDBLoader)
_RiskFindingCtor = cast(Any, _BASE_DETECTOR.RiskFinding)
_detect_crowd_risk = _BASE_DETECTOR.detect_crowd_risk
finding_to_risk_dict = _RISK_REPORT.finding_to_risk_dict


class _CrowdDBLoaderProto(Protocol):
    def find_recommendations(
        self, province: str, score: int
    ) -> List[Dict[str, Any]]: ...

    def load_metadata(self, province: str) -> Dict[str, Any]: ...


class _RiskFindingProto(Protocol):
    school: str
    major: str | None
    frequency: int
    platforms: List[str]
    predicted_increase: int
    risk_level: str
    alternatives: List[Dict[str, Any]]


@dataclass
class CrowdRisk:
    """审核流水线使用的扎堆风险记录。"""

    school: str
    major: str
    frequency: int
    platforms: List[str] = field(default_factory=list)
    predicted_increase: int = 0
    risk_level: str = "low"
    alternatives: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def risk_level_label(self) -> str:
        labels = {
            "high": "🔴 高风险",
            "medium": "🟡 中风险",
            "low": "🟢 低风险",
        }
        return labels.get(self.risk_level, self.risk_level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school": self.school,
            "major": self.major,
            "frequency": self.frequency,
            "platforms": list(self.platforms),
            "predicted_increase": self.predicted_increase,
            "risk_level": self.risk_level,
            "risk_level_label": self.risk_level_label,
            "alternatives": list(self.alternatives),
        }


class CrowdDetector:
    """方案扎堆风险检测器。"""

    def __init__(self, loader: Optional[_CrowdDBLoaderProto] = None):
        self.loader: _CrowdDBLoaderProto = loader or _CrowdDBLoaderCtor()

    def detect_risks(
        self,
        volunteers: List[Dict[str, str]],
        province: str,
        score: int,
    ) -> List[CrowdRisk]:
        findings = _detect_crowd_risk(
            volunteers,
            user_score=score,
            province=province,
            loader=self.loader,
        )
        return [self._from_finding(finding) for finding in findings]

    def get_risk_label(self, frequency: int) -> str:
        if frequency >= 4:
            return "🔴 高风险"
        if frequency >= 2:
            return "🟡 中风险"
        return "🟢 低风险"

    def format_for_report(
        self,
        risks: List[CrowdRisk],
        province: str | None = None,
    ) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for risk in risks:
            payload = finding_to_risk_dict(
                self._to_finding(risk),
                provenance=self._load_provenance(province),
            )
            # 兼容旧计划中的字段名 name，同时保留当前模板用的 school。
            payload["name"] = payload["school"]
            formatted.append(payload)
        return formatted

    def _from_finding(self, finding: _RiskFindingProto) -> CrowdRisk:
        return CrowdRisk(
            school=finding.school,
            major=finding.major or "",
            frequency=int(finding.frequency),
            platforms=list(finding.platforms),
            predicted_increase=int(finding.predicted_increase),
            risk_level=finding.risk_level,
            alternatives=list(finding.alternatives),
        )

    def _to_finding(self, risk: CrowdRisk) -> Any:
        return _RiskFindingCtor(
            school=risk.school,
            major=risk.major or None,
            frequency=int(risk.frequency),
            risk_level=risk.risk_level,
            platforms=list(risk.platforms),
            predicted_increase=int(risk.predicted_increase),
            alternatives=list(risk.alternatives),
        )

    def _load_provenance(self, province: str | None) -> Optional[Dict[str, Any]]:
        if not province:
            return None
        load_metadata = getattr(self.loader, "load_metadata", None)
        if not callable(load_metadata):
            return None
        metadata = load_metadata(province)
        return metadata if isinstance(metadata, dict) else None
