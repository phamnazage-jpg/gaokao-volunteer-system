from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_ADMIN = REPO_ROOT / "requirements-admin.txt"
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"


def test_yaml_runtime_dependency_is_declared_for_rules_truth_phase() -> None:
    admin = REQUIREMENTS_ADMIN.read_text(encoding="utf-8")
    dev = REQUIREMENTS_DEV.read_text(encoding="utf-8")
    combined = admin + "\n" + dev

    assert "PyYAML" in combined or "pyyaml" in combined


def test_yaml_type_stubs_are_declared_for_mypy_gate() -> None:
    dev = REQUIREMENTS_DEV.read_text(encoding="utf-8")

    assert "types-PyYAML" in dev
