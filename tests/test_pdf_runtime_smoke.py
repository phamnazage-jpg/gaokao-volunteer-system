from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_weasyprint_pdf_smoke(tmp_path: Path) -> None:
    from weasyprint import HTML  # type: ignore[import-untyped]

    out = tmp_path / "smoke.pdf"
    HTML(string="<h1>smoke</h1>").write_pdf(out)

    assert out.exists()
    assert out.stat().st_size > 0


def test_ci_includes_pdf_runtime_smoke_gate() -> None:
    text = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "tests/test_pdf_runtime_smoke.py" in text


def test_dockerfile_installs_pdf_runtime_system_libs() -> None:
    text = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    for needle in (
        "apt-get update",
        "libpango-1.0-0",
        "libpangoft2-1.0-0",
        "libharfbuzz-subset0",
    ):
        assert needle in text


def test_dev_verify_skip_pre_existing_still_mentions_locust_probe_only() -> None:
    text = (PROJECT_ROOT / "scripts" / "dev-verify.sh").read_text(encoding="utf-8")
    assert "test_admin_locust_10_concurrency_success_rate_above_95" in text
