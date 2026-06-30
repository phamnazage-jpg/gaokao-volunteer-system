from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "gaokao-poster"


SAMPLE_REPORT_JSON = """{
  \"report_id\": \"R-CLI-POSTER-001\",
  \"title\": \"578分 湖南 志愿方案\",
  \"candidate_name\": \"李雷\",
  \"score\": 578,
  \"province\": \"湖南\",
  \"year\": 2026,
  \"recommendations\": [
    {\"school\": \"江西财经大学\", \"major\": \"会计学\", \"prob\": 35},
    {\"school\": \"湖南师范大学\", \"major\": \"金融学\", \"prob\": 52},
    {\"school\": \"湘潭大学\", \"major\": \"法学\", \"prob\": 68}
  ]
}"""


def test_poster_cli_help_lists_expected_flags() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--report-json" in proc.stdout
    assert "--code" in proc.stdout
    assert "--output" in proc.stdout


def test_poster_cli_generates_png(tmp_path: Path) -> None:
    report_json = tmp_path / "report.json"
    output = tmp_path / "poster.png"
    report_json.write_text(SAMPLE_REPORT_JSON, encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--report-json",
            str(report_json),
            "--code",
            "ABC123",
            "--base-url",
            "https://gk.example.com",
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.exists()
    with Image.open(output) as img:
        assert img.size == (1080, 1920)
        assert img.format == "PNG"
