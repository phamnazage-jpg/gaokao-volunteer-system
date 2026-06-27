from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "score_range_fullchain_100_e2e.py"


def _load_module():
    assert SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location(
        "score_range_fullchain_100_e2e", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_batch_plan_marks_smoke_fullchain_and_boundary_memberships() -> None:
    mod = _load_module()
    cases = [
        {
            "id": 2,
            "province": "北京",
            "expected_path": "fullchain",
            "public_supported": True,
        },
        {
            "id": 7,
            "province": "广西",
            "expected_path": "contract_boundary",
            "public_supported": False,
        },
        {
            "id": 40,
            "province": "海南",
            "expected_path": "fullchain",
            "public_supported": True,
        },
        {
            "id": 50,
            "province": "内蒙古",
            "expected_path": "contract_boundary",
            "public_supported": False,
        },
    ]

    plan = mod.build_batch_plan(cases)
    memberships = {entry["id"]: entry["batches"] for entry in plan["cases"]}

    assert memberships[2] == ["smoke", "fullchain"]
    assert memberships[7] == ["smoke", "boundary"]
    assert memberships[40] == ["fullchain"]
    assert memberships[50] == ["boundary"]
    assert plan["summary"] == {
        "case_count": 4,
        "smoke_case_count": 2,
        "fullchain_case_count": 2,
        "boundary_case_count": 2,
    }


def test_select_cases_filters_batch_without_duplicates() -> None:
    mod = _load_module()
    cases = [
        {
            "id": 2,
            "province": "北京",
            "expected_path": "fullchain",
            "public_supported": True,
        },
        {
            "id": 7,
            "province": "广西",
            "expected_path": "contract_boundary",
            "public_supported": False,
        },
        {
            "id": 40,
            "province": "海南",
            "expected_path": "fullchain",
            "public_supported": True,
        },
        {
            "id": 50,
            "province": "内蒙古",
            "expected_path": "contract_boundary",
            "public_supported": False,
        },
    ]
    planned = mod.build_batch_plan(cases)["cases"]

    assert [row["id"] for row in mod.select_cases(planned, "smoke")] == [2, 7]
    assert [row["id"] for row in mod.select_cases(planned, "fullchain")] == [2, 40]
    assert [row["id"] for row in mod.select_cases(planned, "boundary")] == [7, 50]
    assert [row["id"] for row in mod.select_cases(planned, "all")] == [2, 7, 40, 50]


def test_default_output_path_is_batch_specific() -> None:
    mod = _load_module()

    smoke = mod.default_output_path("smoke")
    fullchain = mod.default_output_path("all")
    boundary = mod.default_output_path("boundary")

    # P1-7 修复后默认写入 /tmp（不再带日期后缀）
    assert smoke.name == "score_range_fullchain_100_e2e_smoke.json"
    assert fullchain.name == "score_range_fullchain_100_e2e.json"
    assert boundary.name == "score_range_fullchain_100_e2e_boundary.json"
    assert smoke != fullchain
