"""gaokao-order-manager CLI tests (T4.3/T4.5).

覆盖 create/list/show/update/pay/deliver/stats/export 主链路，并验证默认输出走遮罩模式。
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from data.orders.cli import main as cli_main

os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-cli")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "gaokao-order-manager"


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "orders.db"


def _run_cli(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=merged_env,
    )


def _load_json(stdout: str) -> dict:
    return json.loads(stdout)


def test_create_list_show_update_pay_deliver_stats_flow(tmp_db_path: Path) -> None:
    create = _run_cli(
        "--db",
        str(tmp_db_path),
        "create",
        "--source",
        "web",
        "--service-version",
        "standard",
        "--amount-cents",
        "9900",
        "--customer-name",
        "张三",
        "--customer-phone",
        "13800001234",
        "--candidate-name",
        "李同学",
        "--candidate-id-card",
        "430102200501011234",
        "--candidate-province",
        "湖南",
        "--candidate-score",
        "578",
        "--candidate-rank",
        "12345",
        "--candidate-subject",
        "物理",
        "--candidate-subject",
        "化学",
        "--note",
        "首单",
        "--tag",
        "VIP",
    )
    assert create.returncode == 0, create.stderr
    created = _load_json(create.stdout)
    order_id = created["order"]["id"]
    assert created["order"]["status"] == "pending"
    assert created["order"]["customer_phone"] == "138****1234"
    assert created["order"]["candidate_id_card"] == "430102********1234"

    listed = _run_cli("--db", str(tmp_db_path), "list")
    assert listed.returncode == 0, listed.stderr
    listed_payload = _load_json(listed.stdout)
    assert listed_payload["count"] == 1
    assert listed_payload["orders"][0]["id"] == order_id
    assert listed_payload["orders"][0]["customer_phone"] == "138****1234"

    shown = _run_cli("--db", str(tmp_db_path), "show", order_id)
    assert shown.returncode == 0, shown.stderr
    shown_payload = _load_json(shown.stdout)
    assert shown_payload["order"]["id"] == order_id
    assert shown_payload["order"]["notes"] == "首单"

    updated = _run_cli(
        "--db",
        str(tmp_db_path),
        "update",
        order_id,
        "--assigned-consultant",
        "consultant-a",
        "--note",
        "已分配顾问",
        "--tag",
        "已跟进",
        "--tag",
        "VIP",
    )
    assert updated.returncode == 0, updated.stderr
    updated_payload = _load_json(updated.stdout)
    assert updated_payload["order"]["assigned_consultant"] == "consultant-a"
    assert updated_payload["order"]["notes"] == "已分配顾问"
    assert updated_payload["order"]["tags"] == ["已跟进", "VIP"]

    paid = _run_cli("--db", str(tmp_db_path), "pay", order_id, "--reason", "wechat-pay")
    assert paid.returncode == 0, paid.stderr
    paid_payload = _load_json(paid.stdout)
    assert paid_payload["order"]["status"] == "paid"
    assert paid_payload["order"]["paid_at"] is not None

    delivered = _run_cli(
        "--db",
        str(tmp_db_path),
        "deliver",
        order_id,
        "--reason",
        "report-ready",
    )
    assert delivered.returncode == 0, delivered.stderr
    delivered_payload = _load_json(delivered.stdout)
    assert delivered_payload["order"]["status"] == "delivered"
    assert delivered_payload["order"]["started_at"] is not None
    assert delivered_payload["order"]["delivered_at"] is not None
    assert [item["to_status"] for item in delivered_payload["history"]] == [
        "pending",
        "paid",
        "serving",
        "delivered",
    ]

    stats = _run_cli("--db", str(tmp_db_path), "stats")
    assert stats.returncode == 0, stats.stderr
    stats_payload = _load_json(stats.stdout)
    assert stats_payload["total_orders"] == 1
    assert stats_payload["by_status"]["delivered"] == 1
    assert stats_payload["by_source"]["web"] == 1
    assert stats_payload["by_service_version"]["standard"] == 1


def test_show_missing_order_returns_nonzero_and_message(tmp_db_path: Path) -> None:
    result = _run_cli("--db", str(tmp_db_path), "show", "missing-order")
    assert result.returncode == 1
    assert "missing-order" in result.stderr


def test_update_requires_at_least_one_mutation_field(tmp_db_path: Path) -> None:
    created = _run_cli(
        "--db",
        str(tmp_db_path),
        "create",
        "--source",
        "web",
        "--service-version",
        "basic",
        "--amount-cents",
        "4900",
    )
    order_id = _load_json(created.stdout)["order"]["id"]

    result = _run_cli("--db", str(tmp_db_path), "update", order_id)
    assert result.returncode == 2
    assert "至少指定一个可更新字段" in result.stderr


def test_module_main_full_flow_covers_core_commands(
    tmp_db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    create_code = cli_main(
        [
            "--db",
            str(tmp_db_path),
            "create",
            "--source",
            "wechat",
            "--service-version",
            "basic",
            "--amount-cents",
            "4900",
            "--customer-phone",
            "13911112222",
            "--tag",
            "直连",
        ]
    )
    assert create_code == 0
    created_payload = _load_json(capsys.readouterr().out)
    order_id = created_payload["order"]["id"]

    assert cli_main(["--db", str(tmp_db_path), "list"]) == 0
    list_payload = _load_json(capsys.readouterr().out)
    assert list_payload["count"] == 1

    assert (
        cli_main(
            [
                "--db",
                str(tmp_db_path),
                "update",
                order_id,
                "--assigned-consultant",
                "consultant-b",
                "--note",
                "待支付",
            ]
        )
        == 0
    )
    update_payload = _load_json(capsys.readouterr().out)
    assert update_payload["order"]["assigned_consultant"] == "consultant-b"

    assert cli_main(["--db", str(tmp_db_path), "show", order_id]) == 0
    show_payload = _load_json(capsys.readouterr().out)
    assert show_payload["order"]["customer_phone"] == "139****2222"

    assert cli_main(["--db", str(tmp_db_path), "pay", order_id]) == 0
    pay_payload = _load_json(capsys.readouterr().out)
    assert pay_payload["order"]["status"] == "paid"

    assert cli_main(["--db", str(tmp_db_path), "deliver", order_id]) == 0
    deliver_payload = _load_json(capsys.readouterr().out)
    assert deliver_payload["order"]["status"] == "delivered"

    stats_code = cli_main(["--db", str(tmp_db_path), "--human", "stats"])
    captured = capsys.readouterr()
    assert stats_code == 0
    assert "total_orders: 1" in captured.out
    assert '"wechat": 1' in captured.out


def test_upgrade_command_creates_delta_order_and_marks_source(
    tmp_db_path: Path,
) -> None:
    created = _run_cli(
        "--db",
        str(tmp_db_path),
        "create",
        "--source",
        "web",
        "--service-version",
        "basic",
        "--amount-cents",
        "4900",
        "--customer-name",
        "张三",
        "--customer-phone",
        "13800001234",
        "--candidate-name",
        "李同学",
        "--note",
        "49 元首单",
        "--tag",
        "首单",
    )
    assert created.returncode == 0, created.stderr
    order_id = _load_json(created.stdout)["order"]["id"]

    upgraded = _run_cli(
        "--db",
        str(tmp_db_path),
        "upgrade",
        order_id,
        "--service-version",
        "standard",
        "--target-amount-cents",
        "9900",
        "--reason",
        "upgrade_to_standard",
    )
    assert upgraded.returncode == 0, upgraded.stderr
    upgraded_payload = _load_json(upgraded.stdout)
    upgrade_order = upgraded_payload["order"]
    source_order = upgraded_payload["source_order"]

    assert upgrade_order["upgrade_from"] == order_id
    assert upgrade_order["service_version"] == "standard"
    assert upgrade_order["amount_cents"] == 5000
    assert upgrade_order["status"] == "pending"
    assert upgrade_order["customer_phone"] == "138****1234"
    assert source_order["id"] == order_id
    assert "upgraded" in source_order["tags"]
    assert upgrade_order["id"] in (source_order["notes"] or "")

    listed = _run_cli("--db", str(tmp_db_path), "list")
    listed_payload = _load_json(listed.stdout)
    assert listed_payload["count"] == 2


def test_export_command_writes_minimal_csv_report(tmp_db_path: Path) -> None:
    created = _run_cli(
        "--db",
        str(tmp_db_path),
        "create",
        "--source",
        "school",
        "--service-version",
        "premium",
        "--amount-cents",
        "19900",
        "--customer-name",
        "王家长",
    )
    assert created.returncode == 0, created.stderr
    order_id = _load_json(created.stdout)["order"]["id"]

    export_path = tmp_db_path.parent / "orders-report.csv"
    exported = _run_cli(
        "--db",
        str(tmp_db_path),
        "export",
        "--output",
        str(export_path),
        "--status",
        "pending",
        "--source",
        "school",
    )
    assert exported.returncode == 0, exported.stderr
    payload = _load_json(exported.stdout)
    assert payload["format"] == "csv"
    assert payload["rows"] == 1
    assert payload["output"] == str(export_path)
    assert export_path.exists()

    with export_path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows == [
        {
            "订单号": order_id,
            "渠道": "school",
            "金额": "199.00",
            "状态": "pending",
            "创建时间": rows[0]["创建时间"],
        }
    ]
    assert rows[0]["创建时间"]


def test_module_main_missing_show_returns_error(
    tmp_db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = cli_main(["--db", str(tmp_db_path), "show", "missing-order"])
    captured = capsys.readouterr()
    assert result == 1
    assert "missing-order" in captured.err

def test_export_command_neutralizes_csv_formula_injection(tmp_db_path: Path) -> None:
    created = _run_cli(
        "--db",
        str(tmp_db_path),
        "create",
        "--source",
        "=malicious-channel",
        "--service-version",
        "premium",
        "--amount-cents",
        "19900",
        "--customer-name",
        "=cmd|'/C calc'!A0",
    )
    assert created.returncode == 0, created.stderr

    export_path = tmp_db_path.parent / "orders-formula-safe.csv"
    exported = _run_cli(
        "--db",
        str(tmp_db_path),
        "export",
        "--output",
        str(export_path),
    )
    assert exported.returncode == 0, exported.stderr

    with export_path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    for row in rows:
        for value in row.values():
            if value:
                assert not value.startswith(("=", "+", "-", "@")), value
    assert rows[0]["渠道"].startswith("'=")

