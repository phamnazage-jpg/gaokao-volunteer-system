"""T5.1 端到端业务场景测试。

覆盖 5 条主链路：
1. 咨询 -> 方案生成
2. 审核 -> 报告
3. 订单 -> 交付
4. 升级流程
5. 数据溯源展示
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_AUDIT_CLI = importlib.import_module("skills.gaokao-audit.scripts.audit_cli")
_REPORT_GENERATOR = importlib.import_module(
    "skills.gaokao-audit.scripts.report_generator"
)
_ReportGeneratorBase = cast(type[Any], _REPORT_GENERATOR.ReportGenerator)
_TRACE_CLI = importlib.import_module("data.crowd_db.cli")

SAMPLE_PLAN = (
    PROJECT_ROOT
    / "skills"
    / "gaokao-audit"
    / "tests"
    / "fixtures"
    / "sample_xianyu.txt"
)
QUICK_SCRIPT = PROJECT_ROOT / "scripts" / "gaokao-quick-3min.py"
ORDER_SCRIPT = PROJECT_ROOT / "scripts" / "gaokao-order-manager"
TRACE_SCRIPT = PROJECT_ROOT / "scripts" / "gaokao-data-trace"

os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-t5-e2e")


class _CaptureReportGenerator(_ReportGeneratorBase):  # type: ignore[valid-type, misc]
    last_html: str = ""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            now_text=lambda: "2026-06-13 10:00",
            report_id_factory=lambda: "AUDIT-T5-E2E-001",
            **kwargs,
        )

    def generate_pdf(self, result, output_path: str, **kwargs: object) -> str:
        html = self.render_html(result, **kwargs)
        type(self).last_html = html
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"%PDF-1.4\nt5 fake pdf\n")
        return str(target)


@pytest.fixture(scope="module")
def quick_module():
    spec = importlib.util.spec_from_file_location("gaokao_quick_3min", QUICK_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tmp_orders_db(tmp_path: Path) -> Path:
    return tmp_path / "orders.db"


@pytest.fixture
def order_env() -> dict[str, str]:
    return {"GAOKAO_ORDERS_FERNET_KEY": os.environ["GAOKAO_ORDERS_FERNET_KEY"]}


def _run_script(
    script: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=merged_env,
    )


def _extract_json(stdout: str) -> dict:
    lines = stdout.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("{"):
            return json.loads("\n".join(lines[index:]))
    raise AssertionError(f"stdout 中未找到 JSON 输出: {stdout}")


def test_consultation_to_plan_generation_flow(quick_module) -> None:
    reply = """1. 李明
2. 浙江
3. 612
4. 15230
5. R
6. 物理、数学
7. C
8. ③
9. ①
10. ②
"""

    info = quick_module.parse_quick_response(reply)
    summary = quick_module.generate_quick_summary(info)
    recommendation = quick_module.generate_quick_recommendation(info)

    assert info["basic"]["name"] == "李明"
    assert info["basic"]["province"] == "浙江"
    assert info["exam"]["score"] == 612
    assert info["exam"]["rank"] == 15230
    assert info["profile"]["type_code"] == "R"
    assert "✅ 核心信息完整！可以开始推荐" in summary
    assert "📊 高考：612分" in summary
    assert "📊 位次：15230名" in summary
    assert "计算机科学与技术" in recommendation
    assert "物理数学强 → 计算机、电子信息、自动化" in recommendation


def test_audit_to_report_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "audit-report.pdf"
    monkeypatch.setattr(_AUDIT_CLI, "ReportGenerator", _CaptureReportGenerator)

    exit_code = _AUDIT_CLI.main(
        [
            str(SAMPLE_PLAN),
            "--output",
            str(output_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    payload = _extract_json(captured.out)

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF-1.4")
    assert payload["province"] == "湖南"
    assert payload["candidate_score"] == 578
    assert payload["crowd_risks"]
    assert "AUDIT-T5-E2E-001" in _CaptureReportGenerator.last_html
    assert "免责声明" in _CaptureReportGenerator.last_html


def test_order_to_delivery_flow_records_artifacts(
    tmp_orders_db: Path,
    tmp_path: Path,
    order_env: dict[str, str],
) -> None:
    plan_path = tmp_path / "plan.md"
    report_path = tmp_path / "audit.json"
    pdf_path = tmp_path / "report.pdf"
    plan_path.write_text("咨询后生成的志愿方案", encoding="utf-8")
    report_path.write_text('{"overall_score": 88}', encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\nreport\n")

    created = _run_script(
        ORDER_SCRIPT,
        "--db",
        str(tmp_orders_db),
        "create",
        "--source",
        "xianyu",
        "--service-version",
        "audit",
        "--amount-cents",
        "4900",
        "--customer-name",
        "王家长",
        "--customer-phone",
        "13800001234",
        "--candidate-name",
        "李明",
        "--candidate-province",
        "湖南",
        "--candidate-score",
        "578",
        "--candidate-rank",
        "26800",
        env=order_env,
    )
    assert created.returncode == 0, created.stderr
    order_id = json.loads(created.stdout)["order"]["id"]

    updated = _run_script(
        ORDER_SCRIPT,
        "--db",
        str(tmp_orders_db),
        "update",
        order_id,
        "--assigned-consultant",
        "long-teacher",
        "--plan-file",
        str(plan_path),
        "--audit-report",
        str(report_path),
        "--pdf-path",
        str(pdf_path),
        "--note",
        "方案与审核报告已归档",
        env=order_env,
    )
    assert updated.returncode == 0, updated.stderr
    updated_payload = json.loads(updated.stdout)
    assert updated_payload["order"]["plan_file"] == str(plan_path)
    assert updated_payload["order"]["audit_report"] == str(report_path)
    assert updated_payload["order"]["pdf_path"] == str(pdf_path)

    paid = _run_script(
        ORDER_SCRIPT,
        "--db",
        str(tmp_orders_db),
        "pay",
        order_id,
        "--reason",
        "xianyu-paid",
        env=order_env,
    )
    assert paid.returncode == 0, paid.stderr

    delivered = _run_script(
        ORDER_SCRIPT,
        "--db",
        str(tmp_orders_db),
        "deliver",
        order_id,
        "--reason",
        "pdf-delivered",
        env=order_env,
    )
    assert delivered.returncode == 0, delivered.stderr
    delivered_payload = json.loads(delivered.stdout)
    assert delivered_payload["order"]["status"] == "delivered"
    assert delivered_payload["order"]["delivered_at"] is not None
    assert delivered_payload["order"]["plan_file"] == str(plan_path)
    assert delivered_payload["order"]["pdf_path"] == str(pdf_path)


def test_upgrade_flow_creates_delta_order(
    tmp_orders_db: Path,
    order_env: dict[str, str],
) -> None:
    created = _run_script(
        ORDER_SCRIPT,
        "--db",
        str(tmp_orders_db),
        "create",
        "--source",
        "wechat",
        "--service-version",
        "audit",
        "--amount-cents",
        "4900",
        "--customer-name",
        "王家长",
        "--customer-phone",
        "13900001234",
        env=order_env,
    )
    assert created.returncode == 0, created.stderr
    source_order_id = json.loads(created.stdout)["order"]["id"]

    upgraded = _run_script(
        ORDER_SCRIPT,
        "--db",
        str(tmp_orders_db),
        "upgrade",
        source_order_id,
        "--service-version",
        "standard",
        "--target-amount-cents",
        "9900",
        "--reason",
        "upgrade_to_standard",
        env=order_env,
    )
    assert upgraded.returncode == 0, upgraded.stderr
    payload = json.loads(upgraded.stdout)

    assert payload["order"]["upgrade_from"] == source_order_id
    assert payload["order"]["service_version"] == "standard"
    assert payload["order"]["amount_cents"] == 5000
    assert payload["source_order"]["id"] == source_order_id
    assert "upgraded" in payload["source_order"]["tags"]


def test_traceability_display_flow(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = _TRACE_CLI.main(["--human", "长沙理工大学"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "query: 长沙理工大学" in captured.out
    assert "湖南 / 2026年数据 / 长沙理工大学 / 会计学" in captured.out
    assert "source_type: report (⚠️报告)" in captured.out
    assert "source_url: https://" in captured.out
    assert "confidence: 0.85" in captured.out


def test_traceability_json_entrypoint_matches_cli_contract() -> None:
    result = _run_script(TRACE_SCRIPT, "长沙理工大学")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["query"] == "长沙理工大学"
    assert payload["match_count"] >= 1
    assert any(match["province"] == "湖南" for match in payload["matches"])
