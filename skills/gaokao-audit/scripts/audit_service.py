"""gaokao-audit 审核服务主类。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Sequence

from .checker_integration import CheckerIntegration
from .crowd_detector import CrowdDetector, CrowdRisk
from .plan_parser import ParsedPlan, PlanParser

_ALLOWED_FORMATS = {"text", "pdf_text", "screenshot_ocr"}


@dataclass
class AuditResult:
    """审核结果。"""

    province: str | None = None
    candidate_score: int | None = None
    candidate_rank: int | None = None
    subjects: str | None = None
    source: str | None = None
    volunteers: List[Dict[str, Any]] = field(default_factory=list)

    policy_errors: List[Dict[str, Any]] = field(default_factory=list)
    policy_serious_warnings: List[Dict[str, Any]] = field(default_factory=list)
    policy_general_warnings: List[Dict[str, Any]] = field(default_factory=list)
    crowd_risks: List[CrowdRisk] = field(default_factory=list)
    data_issues: List[Dict[str, str]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    overall_score: int = 100

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["crowd_risks"] = [risk.to_dict() for risk in self.crowd_risks]
        return payload


class AuditService:
    """组合解析、政策检查、扎堆检测与 LLM 风险分析的审核主服务。"""

    def __init__(
        self,
        parser: PlanParser | None = None,
        checker: CheckerIntegration | None = None,
        detector: CrowdDetector | None = None,
        llm_client: Any = None,
    ) -> None:
        self.parser = parser or PlanParser()
        self.checker = checker or CheckerIntegration()
        self.detector = detector or CrowdDetector()
        self._llm_client = llm_client

    def audit(self, plan_text: str, format: str = "text") -> AuditResult:
        if format not in _ALLOWED_FORMATS:
            raise ValueError(f"unsupported format: {format}")

        parsed = self.parser.parse_text(plan_text)
        check_result = self.checker.check(plan_text, province=parsed.province)
        crowd_risks = self._detect_crowd_risks(parsed)
        data_issues = self._check_data_trace(parsed)
        policy_errors = list(check_result["errors"].get("fatal", []))
        policy_serious_warnings = list(check_result["errors"].get("serious", []))
        policy_general_warnings = list(check_result["errors"].get("warning", []))
        warning_count = len(policy_general_warnings)
        serious_count = len(policy_serious_warnings)

        suggestions = self._generate_suggestions(
            policy_errors=policy_errors,
            crowd_risks=crowd_risks,
            data_issues=data_issues,
            warning_count=warning_count,
            serious_count=serious_count,
        )
        overall_score = self._calculate_score(
            policy_errors=policy_errors,
            crowd_risks=crowd_risks,
            data_issues=data_issues,
            warning_count=warning_count,
            serious_count=serious_count,
        )

        result = AuditResult(
            province=parsed.province,
            candidate_score=parsed.score,
            candidate_rank=parsed.rank,
            subjects=parsed.subjects,
            source=parsed.source,
            volunteers=list(parsed.volunteers),
            policy_errors=policy_errors,
            policy_serious_warnings=policy_serious_warnings,
            policy_general_warnings=policy_general_warnings,
            crowd_risks=crowd_risks,
            data_issues=data_issues,
            suggestions=suggestions,
            overall_score=overall_score,
        )

        # LLM 增强审核：如果 LLM 已配置，调用 LLM 做深度风险分析，增强 suggestions
        llm_suggestions = self._llm_enhance_audit(result, plan_text)
        if llm_suggestions:
            result.suggestions = llm_suggestions + result.suggestions

        return result

    def build_report_payload(
        self,
        result: AuditResult,
        *,
        audit_time: str,
        report_id: str,
    ) -> Dict[str, Any]:
        payload = result.to_dict()
        payload["crowd_risks"] = self.detector.format_for_report(
            result.crowd_risks,
            province=result.province,
        )
        payload["candidate_info"] = self._build_candidate_info(result)
        payload["audit_time"] = audit_time
        payload["report_id"] = report_id
        payload["fatal_count"] = len(result.policy_errors)
        payload["warning_count"] = (
            len(result.policy_serious_warnings)
            + len(result.crowd_risks)
            + len(result.data_issues)
        )
        payload["info_count"] = len(result.policy_general_warnings)
        return payload

    def _llm_enhance_audit(self, result: AuditResult, plan_text: str) -> List[str]:
        """如果 LLM 已配置，调用 LLM 做深度风险分析，返回额外建议列表。"""
        if self._llm_client is None or not getattr(
            self._llm_client, "is_configured", False
        ):
            return []
        try:
            from data.llm.prompts import build_audit_prompt
            import json as _json

            system, user = build_audit_prompt(
                province=result.province or "未知",
                score=result.candidate_score,
                rank=result.candidate_rank,
                subjects=[result.subjects] if result.subjects else [],
                existing_plan=plan_text[:2000],
                crowd_db_recs=None,
            )
            resp = self._llm_client.chat_with_system(system, user, temperature=0.3)
            data = _json.loads(resp.content)
            llm_findings = [
                str(x).strip()
                for x in (data.get("key_findings") or [])
                if str(x).strip()
            ]
            llm_suggestions = [
                str(x).strip()
                for x in (data.get("suggestions") or [])
                if str(x).strip()
            ]
            combined: List[str] = []
            if llm_findings:
                combined.append("🤖 LLM 风险分析发现：")
                combined.extend(f"  • {f}" for f in llm_findings[:3])
            if llm_suggestions:
                combined.append("🤖 LLM 建议操作：")
                combined.extend(f"  • {s}" for s in llm_suggestions[:3])
            return combined
        except Exception:
            return []

    def _detect_crowd_risks(self, parsed: ParsedPlan) -> List[CrowdRisk]:
        if not parsed.province or not parsed.score or not parsed.volunteers:
            return []
        return self.detector.detect_risks(
            parsed.volunteers,
            province=parsed.province,
            score=parsed.score,
        )

    def _check_data_trace(self, parsed: ParsedPlan) -> List[Dict[str, str]]:
        issues: List[Dict[str, str]] = []
        if not parsed.source:
            issues.append({
                "location": "AI来源",
                "description": "未明确标注AI来源（千问/元宝/百度/豆包）",
                "recommendation": "补充原始方案来自哪个大厂AI，避免人工复核时误判来源。",
            })
        if (
            parsed.score
            and "2025" not in parsed.raw_text
            and "2024" not in parsed.raw_text
        ):
            issues.append({
                "location": "分数/位次依据",
                "description": "未明确数据年份（建议标注2025年参考位次）",
                "recommendation": "补充分数线或位次所对应的年份，避免跨年份数据混用。",
            })
        return issues

    def _build_candidate_info(self, result: AuditResult) -> str:
        parts: List[str] = []
        if result.province:
            parts.append(result.province)
        if result.candidate_score is not None:
            parts.append(f"{result.candidate_score}分")
        if result.subjects:
            parts.append(result.subjects)
        return " ".join(parts) or "未提供"

    def _generate_suggestions(
        self,
        *,
        policy_errors: Sequence[Dict[str, Any]],
        crowd_risks: Sequence[CrowdRisk],
        data_issues: Sequence[Dict[str, str]],
        warning_count: int,
        serious_count: int,
    ) -> List[str]:
        suggestions: List[str] = []

        high_risks = [risk for risk in crowd_risks if risk.risk_level == "high"]
        medium_risks = [risk for risk in crowd_risks if risk.risk_level == "medium"]

        if policy_errors:
            suggestions.append(
                f"存在 {len(policy_errors)} 个政策错误，必须修正后才能使用该方案"
            )
        if serious_count:
            suggestions.append(
                f"存在 {serious_count} 个严重合规提醒，建议逐项人工复核院校专业组与调剂规则"
            )
        if high_risks:
            suggestions.append(
                f"检测到 {len(high_risks)} 所高风险扎堆院校，建议优先替换为低风险替代方案"
            )
        elif medium_risks:
            suggestions.append(
                f"检测到 {len(medium_risks)} 所中风险扎堆院校，建议调整冲稳保比例降低集中度"
            )
        if data_issues:
            suggestions.append("建议核实数据来源与年份，避免引用无出处或跨年份数据")
        elif warning_count:
            suggestions.append(
                f"存在 {warning_count} 个一般提醒，建议交付前再次核对表述与填写细节"
            )
        if not suggestions:
            suggestions.append("方案整体风险可控，建议结合个人偏好做小幅微调")

        return suggestions

    def _calculate_score(
        self,
        *,
        policy_errors: Sequence[Dict[str, Any]],
        crowd_risks: Sequence[CrowdRisk],
        data_issues: Sequence[Dict[str, str]],
        warning_count: int,
        serious_count: int,
    ) -> int:
        score = 100
        score -= len(policy_errors) * 15
        score -= serious_count * 8
        score -= warning_count * 3
        score -= len(data_issues) * 3

        for risk in crowd_risks:
            if risk.risk_level == "high":
                score -= 10
            elif risk.risk_level == "medium":
                score -= 5
            else:
                score -= 1

        return max(0, min(100, score))


def audit_plan(plan_content: str, plan_format: str = "text") -> AuditResult:
    """技术架构文档中的便捷入口。"""

    return AuditService().audit(plan_content, format=plan_format)
