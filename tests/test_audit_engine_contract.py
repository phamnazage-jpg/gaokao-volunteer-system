from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "data" / "rules" / "cli.py"


def test_audit_run_output_declares_actual_checks_only(tmp_path: Path) -> None:
    truth_root = tmp_path / "truth"
    catalog_root = tmp_path / "catalog"
    plan_path = tmp_path / "plan.json"

    (truth_root / "province_rules").mkdir(parents=True)
    (catalog_root / "majors" / "2025").mkdir(parents=True)
    (truth_root / "province_rules" / "湖南.yaml").write_text(
        """
province: 湖南
rules:
  - rule_id: hunan-max-volunteers
    province: 湖南
    module: province_limits
    title: 志愿上限
    severity: fatal
    status: active
    source_type: official
    source_url: https://example.com/hunan
    effective_date: 2026-06-01
    reviewed_at: 2026-06-01T00:00:00+00:00
    value:
      key: max_volunteers
      max_volunteers: 45
""",
        encoding="utf-8",
    )
    (catalog_root / "majors" / "2025" / "majors.json").write_text(
        json.dumps(
            {
                "version": "2025",
                "majors": [
                    {"code": "080901", "name": "计算机科学与技术", "status": "active"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    plan_path.write_text(
        json.dumps(
            {
                "majors": ["计算机科学与技术"],
                "volunteers": [f"志愿{i}" for i in range(46)],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            str(REPO_ROOT / ".venv" / "bin" / "python"),
            str(CLI),
            "audit",
            "run",
            "--province",
            "湖南",
            "--plan",
            str(plan_path),
            "--truth-root",
            str(truth_root),
            "--catalog-root",
            str(catalog_root),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 1
    output = proc.stdout + proc.stderr
    assert "major" in output.lower()
    assert "crowd" not in output.lower()
    assert "overall_score" not in output
    assert "data_issues" not in output
