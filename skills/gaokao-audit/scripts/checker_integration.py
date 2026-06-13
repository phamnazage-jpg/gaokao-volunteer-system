"""规范检查集成。

复用 gaokao-spec-checker 的 27 省规则库，并把字符串报告转换为
T1.5 可继续消费的结构化结果。
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from typing import Any, Dict, List

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_SPEC_CHECKER = importlib.import_module(
    "skills.gaokao-spec-checker.scripts.spec_checker_v2"
)
GaokaoSpecCheckerV2 = _SPEC_CHECKER.GaokaoSpecCheckerV2
PROVINCE_RULES = _SPEC_CHECKER.PROVINCE_RULES
detect_province = _SPEC_CHECKER.detect_province


class CheckerIntegration:
    """规范检查集成器。"""

    def check(self, plan_text: str, province: str | None = None) -> Dict[str, Any]:
        """执行规范检查并返回结构化结果。"""
        checker = GaokaoSpecCheckerV2(province=province)
        report = checker.auto_detect_and_check(plan_text)
        resolved_province = checker.province
        supported = bool(resolved_province and resolved_province in PROVINCE_RULES)
        mode = checker.province_rule["mode"] if checker.province_rule else None

        errors = self._build_errors(checker, report, supported=supported)
        summary = self._summarize(errors)

        return {
            "province": resolved_province,
            "supported": supported,
            "mode": mode,
            "errors": errors,
            "summary": summary,
            "raw_report": report,
        }

    def format_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转成审核流水线更易消费的平铺结构。"""
        return {
            "province": result["province"],
            "supported": result["supported"],
            "mode": result["mode"],
            "policy_errors": result["errors"].get("fatal", []),
            "serious_errors": result["errors"].get("serious", []),
            "warnings": result["errors"].get("warning", []),
            "info": result["errors"].get("info", []),
            "fatal_count": result["summary"]["fatal_count"],
            "serious_count": result["summary"]["serious_count"],
            "warning_count": result["summary"]["warning_count"],
            "info_count": result["summary"]["info_count"],
            "total_count": result["summary"]["total_count"],
            "has_fatal": result["summary"]["fatal_count"] > 0,
        }

    def _build_errors(
        self,
        checker: Any,
        report: str,
        *,
        supported: bool,
    ) -> Dict[str, List[Dict[str, str]]]:
        if supported:
            return {
                "fatal": list(checker.errors.get("fatal", [])),
                "serious": list(checker.errors.get("serious", [])),
                "warning": list(checker.errors.get("warning", [])),
                "info": [],
            }

        return {
            "fatal": [],
            "serious": [],
            "warning": [],
            "info": self._extract_info_items(report),
        }

    def _extract_info_items(self, report: str) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        for line in report.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("║"):
                title = stripped.strip("║ ")
                if title:
                    items.append({"description": title})
                continue
            if stripped.startswith(
                (
                    "╔",
                    "╚",
                    "【支持检测的省份】",
                    "【已支持的省份】",
                    "【解决方式】",
                    "【后续计划】",
                )
            ):
                continue
            if re.fullmatch(
                r"[北京天津河北山西内蒙古辽宁吉林黑龙江上海江苏浙江安徽福建江西山东河南湖北湖南广东广西海南重庆四川贵州云南西藏陕西甘肃青海宁夏新疆、，\s]+",
                stripped,
            ):
                continue
            items.append({"description": stripped})
        return items

    def _summarize(self, errors: Dict[str, List[Dict[str, str]]]) -> Dict[str, int]:
        fatal_count = len(errors.get("fatal", []))
        serious_count = len(errors.get("serious", []))
        warning_count = len(errors.get("warning", []))
        info_count = len(errors.get("info", []))
        return {
            "fatal_count": fatal_count,
            "serious_count": serious_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "total_count": fatal_count + serious_count + warning_count + info_count,
        }
