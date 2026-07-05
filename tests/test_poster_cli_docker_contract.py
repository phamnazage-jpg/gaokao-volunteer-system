from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_poster_cli_dockerfile_targets_dedicated_cli_entrypoint() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile.poster").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "fonts-noto-cjk" in dockerfile
    assert "requirements-admin.txt" in dockerfile
    assert "COPY data /app/data" in dockerfile
    assert "COPY scripts/gaokao-poster /app/scripts/gaokao-poster" in dockerfile
    assert 'ENTRYPOINT ["python", "/app/scripts/gaokao-poster"]' in dockerfile
    assert 'CMD ["--help"]' in dockerfile


def test_compose_declares_poster_cli_service_profile() -> None:
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "gaokao-poster:" in compose
    assert "dockerfile: Dockerfile.poster" in compose
    assert "localhost/gaokao-volunteer-system-poster:latest" in compose
    assert 'profiles: ["poster"]' in compose
    assert "./reports:/work/reports" in compose


def test_ci_builds_poster_cli_docker_image() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "Validate Poster CLI Docker contract" in workflow
    assert "tests/test_poster_cli_docker_contract.py" in workflow
    assert "Build Poster CLI Docker image" in workflow
    assert "docker build -f Dockerfile.poster -t gaokao-poster-cli:test ." in workflow
