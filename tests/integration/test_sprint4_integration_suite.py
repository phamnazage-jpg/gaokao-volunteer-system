from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGRESSION_SCRIPT = PROJECT_ROOT / "scripts" / "sprint4_real_backend_regression.py"


def _load_regression_module():
    spec = importlib.util.spec_from_file_location("sprint4_real_backend_regression", REGRESSION_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_t_b_27_real_backend_suite_covers_five_react_modules() -> None:
    module = _load_regression_module()

    checks = module.build_checks()

    assert [check.module for check in checks] == ["share", "data-query", "review", "llm", "poster"]
    assert all("/api/" in check.description for check in checks)


def test_t_c_44_poster_cli_docker_delivery_is_wired() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile.poster").read_text(encoding="utf-8")
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert 'ENTRYPOINT ["python", "/app/scripts/gaokao-poster"]' in dockerfile
    assert "gaokao-poster:" in compose
    assert "dockerfile: Dockerfile.poster" in compose
    assert "docker build -f Dockerfile.poster -t gaokao-poster-cli:test ." in workflow


def test_frontend_contract_gate_includes_sprint4_poster_status_path() -> None:
    codegen_check = (PROJECT_ROOT / "apps" / "web" / "scripts" / "codegen-check.ts").read_text(encoding="utf-8")
    generated_types = (PROJECT_ROOT / "apps" / "web" / "src" / "types" / "api-generated.d.ts").read_text(
        encoding="utf-8",
    )

    assert "/api/poster/{job_id}/status" in generated_types
    assert "/api/share-link/{code}/stats" in codegen_check
    assert "/api/poster/generate" in codegen_check
