"""T7.5 分享页 WebUI 端到端测试。"""

from __future__ import annotations

import json
from pathlib import Path

from data.share.short_link import ShortLinkService


SAMPLE_REPORT = {
    "report_id": "R-2026-001",
    "title": "578分 湖南 志愿方案",
    "summary": "冲稳保 45 志愿，适合财经/计算机方向。",
    "candidate_name": "李明",
    "score": 578,
    "rank": 12345,
    "year": 2026,
    "province": "湖南",
    "recommendations": [
        {"school": "江西财经大学", "major": "会计学", "prob": 0.35},
        {"school": "长沙理工大学", "major": "计算机科学与技术", "prob": 0.52},
        {"school": "湘潭大学", "major": "金融学", "prob": 0.61},
    ],
    "volunteers": [
        {"group": 1, "school": "江西财经大学", "majors": ["会计学", "财务管理"]}
    ],
}


def _write_report(report_dir: str, report_id: str, payload: dict) -> None:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{report_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def _create_link(settings, **kwargs):
    svc = ShortLinkService(db_path=settings.share_db_path)
    return svc.create(**kwargs)


def test_share_page_comment_permission_renders_mobile_html(client, settings):
    _write_report(settings.share_report_dir, SAMPLE_REPORT["report_id"], SAMPLE_REPORT)
    link = _create_link(
        settings, report_id=SAMPLE_REPORT["report_id"], permission="comment"
    )

    resp = client.get(f"/s/{link.code}")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert '<meta name="viewport"' in body
    assert "高考志愿填报方案" in body
    assert "578分 湖南 志愿方案" in body
    assert "李*" in body
    assert "江西财经大学" in body
    assert "会计学" in body
    assert "微信内打开也能直接查看" in body


def test_share_page_read_permission_hides_report_details(client, settings):
    _write_report(settings.share_report_dir, SAMPLE_REPORT["report_id"], SAMPLE_REPORT)
    link = _create_link(
        settings, report_id=SAMPLE_REPORT["report_id"], permission="read"
    )

    resp = client.get(f"/s/{link.code}")

    assert resp.status_code == 200
    body = resp.text
    assert "李*" in body
    assert "分享信息受限" in body
    assert "578分 湖南 志愿方案" not in body
    assert "江西财经大学" not in body
    assert "12345" not in body


def test_share_page_password_flow(client, settings):
    _write_report(settings.share_report_dir, SAMPLE_REPORT["report_id"], SAMPLE_REPORT)
    link = _create_link(
        settings,
        report_id=SAMPLE_REPORT["report_id"],
        permission="comment",
        password="s3cr3t",
    )

    required = client.get(f"/s/{link.code}")
    assert required.status_code == 401
    assert "访问密码" in required.text
    assert 'name="pwd"' in required.text

    wrong = client.get(f"/s/{link.code}", params={"pwd": "wrong"})
    assert wrong.status_code == 401
    assert "密码错误" in wrong.text

    ok = client.get(f"/s/{link.code}", params={"pwd": "s3cr3t"})
    assert ok.status_code == 200
    assert "578分 湖南 志愿方案" in ok.text


def test_share_page_not_found_and_revoked_status(client, settings):
    missing = client.get("/s/NOPE42")
    assert missing.status_code == 404
    assert "分享链接不存在" in missing.text

    link = _create_link(
        settings, report_id=SAMPLE_REPORT["report_id"], permission="comment"
    )
    svc = ShortLinkService(db_path=settings.share_db_path)
    assert svc.revoke(link.code) is True

    revoked = client.get(f"/s/{link.code}")
    assert revoked.status_code == 410
    assert "分享已撤销" in revoked.text
