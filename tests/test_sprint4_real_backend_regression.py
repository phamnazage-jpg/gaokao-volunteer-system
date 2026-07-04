from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "sprint4_real_backend_regression.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sprint4_real_backend_regression", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_sprint4_real_backend_regression_script_declares_5_modules() -> None:
    assert SCRIPT.exists(), "T-B-27 regression script is missing"
    module = _load_module()

    module_names = [check.module for check in module.build_checks()]

    assert module_names == ["share", "data-query", "review", "llm", "poster"]


def test_sprint4_real_backend_regression_has_base_url_cli() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "--base-url" in text
    assert "docker compose up --build -d gaokao-admin" in text
