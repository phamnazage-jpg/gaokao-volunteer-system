from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJ))

from data.share.poster import build_poster_payload, save_poster  # noqa: E402


SAMPLE_REPORT = {
    "report_id": "R-POSTER-001",
    "title": "578分 湖南 志愿方案",
    "candidate_name": "李雷",
    "score": 578,
    "province": "湖南",
    "year": 2026,
    "recommendations": [
        {"school": "江西财经大学", "major": "会计学", "prob": 35},
        {"school": "湖南师范大学", "major": "金融学", "prob": 52},
        {"school": "湘潭大学", "major": "法学", "prob": 68},
        {"school": "长沙理工大学", "major": "工商管理", "prob": 76},
    ],
}


def test_build_poster_payload_masks_name_and_limits_recommendations() -> None:
    payload = build_poster_payload(
        SAMPLE_REPORT,
        code="ABC123",
        share_url="https://gk.example.com/s/ABC123",
    )

    assert payload.report_id == "R-POSTER-001"
    assert payload.title == "578分 湖南 志愿方案"
    assert payload.candidate_name == "李*"
    assert payload.score_line == "578分 · 湖南 · 2026"
    assert payload.share_url == "https://gk.example.com/s/ABC123"
    assert len(payload.recommendations) == 3
    assert payload.recommendations[0].school == "江西财经大学"
    assert payload.recommendations[-1].school == "湘潭大学"


def test_save_poster_png_creates_1080x1920_image(tmp_path: Path) -> None:
    out = tmp_path / "poster.png"

    result = save_poster(
        SAMPLE_REPORT,
        code="ABC123",
        share_url="https://gk.example.com/s/ABC123",
        output_path=out,
    )

    assert result.output_path == out
    assert out.exists()
    with Image.open(out) as img:
        assert img.size == (1080, 1920)
        assert img.format == "PNG"
        colors = img.convert("RGB").getcolors(maxcolors=2_500_000)
        assert colors is not None
        assert len(colors) > 10


def test_save_poster_jpg_respects_output_extension(tmp_path: Path) -> None:
    out = tmp_path / "poster.jpg"

    result = save_poster(
        SAMPLE_REPORT,
        code="ABC123",
        share_url="https://gk.example.com/s/ABC123",
        output_path=out,
        mask_name=False,
    )

    assert result.output_path == out
    with Image.open(out) as img:
        assert img.size == (1080, 1920)
        assert img.format == "JPEG"
