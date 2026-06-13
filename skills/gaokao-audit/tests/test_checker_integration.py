"""规范检查集成测试。"""

import importlib
import os
import sys
from typing import Any, Protocol, cast

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_CHECKER_INTEGRATION = importlib.import_module(
    "skills.gaokao-audit.scripts.checker_integration"
)
CheckerIntegration = _CHECKER_INTEGRATION.CheckerIntegration


class _CheckerIntegrationProto(Protocol):
    def check(self, plan_text: str, province: str | None = None) -> dict[str, Any]: ...

    def format_results(self, result: dict[str, Any]) -> dict[str, Any]: ...


@pytest.fixture
def checker() -> _CheckerIntegrationProto:
    return cast(_CheckerIntegrationProto, CheckerIntegration())


def test_check_hunan_plan_returns_structured_fatal_error(
    checker: _CheckerIntegrationProto,
) -> None:
    plan_text = "湖南 578分 45个学校 院校专业组"

    result = checker.check(plan_text, province="湖南")

    assert result["province"] == "湖南"
    assert result["supported"] is True
    assert result["summary"]["fatal_count"] >= 1
    assert any("志愿单位错误" in item["rule"] for item in result["errors"]["fatal"])


def test_check_auto_detects_province_and_preserves_mode(
    checker: _CheckerIntegrationProto,
) -> None:
    plan_text = "浙江考生 620分 80个院校专业组 组内服从调剂"

    result = checker.check(plan_text)

    assert result["province"] == "浙江"
    assert result["mode"] == "专业+学校"
    assert result["summary"]["fatal_count"] >= 1
    assert any("模式错误" in item["rule"] for item in result["errors"]["fatal"])


def test_check_unknown_province_is_graceful(
    checker: _CheckerIntegrationProto,
) -> None:
    result = checker.check("test", province="火星")

    assert result["province"] == "火星"
    assert result["supported"] is False
    assert result["summary"]["fatal_count"] == 0
    assert any("暂不支持" in item["description"] for item in result["errors"]["info"])


def test_check_without_province_returns_info_message(
    checker: _CheckerIntegrationProto,
) -> None:
    result = checker.check("578分考生方案，报考计算机专业")

    assert result["province"] is None
    assert result["supported"] is False
    assert result["summary"]["total_count"] >= 1
    assert any(
        "未检测到省份" in item["description"] for item in result["errors"]["info"]
    )


def test_format_results_exposes_policy_summary(
    checker: _CheckerIntegrationProto,
) -> None:
    raw = checker.check("湖南 578分 45个学校 院校专业组", province="湖南")

    formatted = checker.format_results(raw)

    assert formatted["fatal_count"] == raw["summary"]["fatal_count"]
    assert formatted["warning_count"] == raw["summary"]["warning_count"]
    assert formatted["serious_count"] == raw["summary"]["serious_count"]
    assert formatted["policy_errors"] == raw["errors"]["fatal"]
