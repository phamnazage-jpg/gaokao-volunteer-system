from __future__ import annotations

from data.crowd_db.loader import CrowdDBLoader


def test_build_quality_summary_returns_expected_shape():
    from data.crowd_db.quality_summary import build_quality_summary

    summary = build_quality_summary(CrowdDBLoader(warn_low_confidence=False))

    assert summary["total_provinces"] == 27
    assert summary["by_quality_level"]
    assert set(summary["by_quality_level"]).issuperset({"high", "usable", "skeleton"})
    assert len(summary["provinces"]) == 27
    first = summary["provinces"][0]
    assert set(first).issuperset({
        "province",
        "confidence",
        "quality_level",
        "quality_label",
        "data_year",
        "source_type",
    })


def test_quality_summary_cli_human_output(capsys):
    from data.crowd_db.quality_summary import main

    code = main(["--human"])
    captured = capsys.readouterr()
    assert code == 0
    assert "province_count: 27" in captured.out
    assert "quality_counts:" in captured.out
    assert "湖南" in captured.out
