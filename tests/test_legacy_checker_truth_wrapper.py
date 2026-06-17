from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_CHECKER_PATH = PROJECT_ROOT / "scripts" / "gaokao-checker"
TRUTH_ROOT = PROJECT_ROOT / "rules" / "_truth"


def test_legacy_checker_honors_overridden_truth_root(tmp_path: Path) -> None:
    truth_root = tmp_path / "truth"
    shutil.copytree(TRUTH_ROOT, truth_root)

    hunan_path = truth_root / "province" / "hunan.yaml"
    hunan_doc = yaml.safe_load(hunan_path.read_text(encoding="utf-8"))
    hunan_doc["rules"]["max_volunteers"]["value"]["max_volunteers"] = 99
    hunan_path.write_text(
        yaml.safe_dump(hunan_doc, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    probe = (
        "import importlib.util; from importlib.machinery import SourceFileLoader; "
        f"loader=SourceFileLoader('legacy_gaokao_checker_wrapper', {str(LEGACY_CHECKER_PATH)!r}); "
        "spec=importlib.util.spec_from_loader(loader.name, loader); "
        "module=importlib.util.module_from_spec(spec); "
        "assert spec is not None and spec.loader is not None; "
        "spec.loader.exec_module(module); "
        "print(module.PROVINCE_RULES['湖南']['max_volunteers'])"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env={**dict(), **{"GAOKAO_RULES_TRUTH_ROOT": str(truth_root)}},
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "99"


def test_legacy_checker_detects_earliest_province_signal_not_later_school_name() -> (
    None
):
    probe = (
        "import importlib.util; from importlib.machinery import SourceFileLoader; "
        f"loader=SourceFileLoader('legacy_gaokao_checker_wrapper', {str(LEGACY_CHECKER_PATH)!r}); "
        "spec=importlib.util.spec_from_loader(loader.name, loader); "
        "module=importlib.util.module_from_spec(spec); "
        "assert spec is not None and spec.loader is not None; "
        "spec.loader.exec_module(module); "
        "print(module.detect_province('湖南578分考生志愿方案，目标院校含江西财经大学'))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "湖南"


def test_legacy_checker_cli_still_checks_plan_file_via_wrapper(tmp_path: Path) -> None:
    plan = tmp_path / "plan.txt"
    plan.write_text(
        "湖南578分考生志愿方案\n本次共填报45个学校志愿：\n志愿01：江西财经大学，会计学\n录取概率35%\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(LEGACY_CHECKER_PATH), str(plan)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "湖南" in proc.stdout
    assert "致命错误" in proc.stdout
