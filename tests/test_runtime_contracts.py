from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
CONSTRAINTS = PROJECT_ROOT / "constraints.txt"


def test_ci_cache_key_tracks_all_runtime_requirement_inputs() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-admin.txt" in text
    assert "requirements-dev.txt" in text
    assert "constraints.txt" in text
    assert "hashFiles(" in text


def test_dockerfile_installs_with_constraints_and_runtime_env_contract() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "constraints.txt" in text
    assert "requirements-admin.txt" in text
    assert 'GAOKAO_ADMIN_BIND' in text
    assert 'GAOKAO_ADMIN_PORT' in text


def test_constraints_file_locks_runtime_and_dev_packages() -> None:
    text = CONSTRAINTS.read_text(encoding="utf-8")
    for needle in (
        "fastapi==",
        "uvicorn==",
        "weasyprint==",
        "pytest==",
        "ruff==",
        "mypy==",
    ):
        assert needle in text
