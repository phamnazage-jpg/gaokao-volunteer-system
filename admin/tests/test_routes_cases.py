"""T6.5 案例管理端点测试。

覆盖:
- 鉴权: /api/cases 全部需要 JWT
- CRUD: 列表 / 创建 / 详情 / 更新 / 删除
- 审核: pending -> approved / rejected
- 分类: success / typical / warning
- 过滤: category / review_status
"""

from __future__ import annotations


def test_cases_requires_auth(client):
    resp = client.get("/api/cases")
    assert resp.status_code == 401


def test_viewer_cannot_create_case(client, viewer_headers):
    resp = client.post(
        "/api/cases",
        headers=viewer_headers,
        json={
            "title": "viewer forbidden",
            "category": "success",
            "summary": "should fail",
            "content": "viewer should not write",
            "tags": ["forbidden"],
        },
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "E01301"



def test_case_crud_review_and_filters(client, auth_headers):
    created = client.post(
        "/api/cases",
        headers=auth_headers,
        json={
            "title": "湖南 620 分逆袭 985",
            "category": "success",
            "summary": "低于校线预期但通过梯度策略成功录取",
            "content": "完整案例内容",
            "tags": ["湖南", "985"],
        },
    )
    assert created.status_code == 201, created.text
    created_body = created.json()
    case_id = created_body["id"]
    assert created_body["review_status"] == "pending"
    assert created_body["category"] == "success"
    assert created_body["tags"] == ["湖南", "985"]

    listed = client.get("/api/cases", headers=auth_headers)
    assert listed.status_code == 200
    list_body = listed.json()
    assert list_body["total"] == 1
    assert list_body["items"][0]["id"] == case_id
    assert list_body["items"][0]["review_status"] == "pending"

    detail = client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["title"] == "湖南 620 分逆袭 985"
    assert detail_body["content"] == "完整案例内容"
    assert detail_body["reviewed_at"] is None

    updated = client.patch(
        f"/api/cases/{case_id}",
        headers=auth_headers,
        json={
            "title": "湖南 620 分典型提分案例",
            "category": "typical",
            "summary": "更新后的摘要",
            "content": "更新后的正文",
            "tags": ["湖南", "梯度"],
        },
    )
    assert updated.status_code == 200, updated.text
    updated_body = updated.json()
    assert updated_body["title"] == "湖南 620 分典型提分案例"
    assert updated_body["category"] == "typical"
    assert updated_body["summary"] == "更新后的摘要"
    assert updated_body["tags"] == ["湖南", "梯度"]

    approved = client.post(
        f"/api/cases/{case_id}/review",
        headers=auth_headers,
        json={"review_status": "approved", "review_note": "可对外展示"},
    )
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()
    assert approved_body["review_status"] == "approved"
    assert approved_body["review_note"] == "可对外展示"
    assert approved_body["reviewer"] == "admin"
    assert approved_body["reviewed_at"]

    filtered = client.get(
        "/api/cases",
        headers=auth_headers,
        params={"category": "typical", "review_status": "approved"},
    )
    assert filtered.status_code == 200
    filtered_body = filtered.json()
    assert filtered_body["total"] == 1
    assert filtered_body["items"][0]["id"] == case_id

    deleted = client.delete(f"/api/cases/{case_id}", headers=auth_headers)
    assert deleted.status_code == 204

    missing = client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert missing.status_code == 404


def test_case_review_rejected_path(client, auth_headers):
    created = client.post(
        "/api/cases",
        headers=auth_headers,
        json={
            "title": "志愿填报警告案例",
            "category": "warning",
            "summary": "错误示范",
            "content": "平行志愿未拉开梯度",
        },
    )
    assert created.status_code == 201, created.text
    case_id = created.json()["id"]

    reviewed = client.post(
        f"/api/cases/{case_id}/review",
        headers=auth_headers,
        json={"review_status": "rejected", "review_note": "证据不足"},
    )
    assert reviewed.status_code == 200, reviewed.text
    body = reviewed.json()
    assert body["review_status"] == "rejected"
    assert body["review_note"] == "证据不足"

    filtered = client.get(
        "/api/cases",
        headers=auth_headers,
        params={"category": "warning", "review_status": "rejected"},
    )
    assert filtered.status_code == 200
    list_body = filtered.json()
    assert list_body["total"] == 1
    assert list_body["items"][0]["category"] == "warning"


def test_case_update_unknown_returns_404(client, auth_headers):
    resp = client.patch(
        "/api/cases/99999",
        headers=auth_headers,
        json={
            "title": "不存在",
            "category": "typical",
            "summary": "占位摘要",
            "content": "占位正文",
            "tags": [],
        },
    )
    assert resp.status_code == 404
