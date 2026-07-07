from __future__ import annotations
import json
from pathlib import Path

from admin.tests.test_order_status_page import _mark_paid, _seed_order
from data.customer_portal.token import issue_portal_token
from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore




def test_openapi_exposes_react_sprint3_json_contracts(app):
    paths = app.openapi()["paths"]

    required = {
        "/api/share-link",
        "/api/share-link/latest",
        "/api/share-link/{code}/revoke",
        "/api/share-link/{code}/stats",
        "/api/admin/share-links",
        "/api/admin/share-links/{code}",
        "/api/admin/posters",
        "/api/data-query/score-line",
        "/api/data-query/rank-estimator",
        "/api/data-query/majors",
        "/api/data-query/schools",
        "/api/review/start",
        "/api/review/{review_id}/status",
        "/api/review/action",
        "/api/poster/generate",
        "/api/poster/{job_id}/status",
        "/api/llm/config",
        "/api/llm/{provider}/enhance",
        "/api/llm/enhance/{plan_id}/status",
        "/api/chat/send",
        "/api/chat/stream",
        "/api/chat/history",
        "/api/consultations",
        "/api/consultations/{consultation_id}",
        "/api/plans",
        "/api/plans/{plan_id}",
        "/api/assessment",
        "/api/audit/submit",
        "/api/audit/{audit_id}/status",
        "/api/portal/{token}/cwb",
        "/api/portal/{token}/full-plan",
    }

    missing = sorted(required - set(paths))
    assert missing == []


def test_react_sprint3_json_contracts_return_frontend_shapes(client, auth_headers):
    score_line = client.get(
        "/api/data-query/score-line",
        params={"province": "湖南", "year": 2026, "scoreType": "physics"},
    )
    assert score_line.status_code == 200, score_line.text
    assert score_line.json()["lines"][0].keys() >= {"batch", "score", "rank"}

    review = client.post(
        "/api/review/start",
        json={"planId": "plan-001", "reviewerId": "reviewer-1"},
    )
    assert review.status_code == 200, review.text
    review_body = review.json()
    assert review_body["id"].startswith("rvw_")
    assert review_body["status"] == "in_progress"

    action = client.post(
        "/api/review/action",
        json={"action": "approve", "reviewId": review_body["id"], "comment": "ok"},
    )
    assert action.status_code == 200, action.text
    assert action.json()["status"] == "approved"

    poster = client.post(
        "/api/poster/generate",
        json={"planId": "plan-001", "template": "classic"},
    )
    assert poster.status_code == 200, poster.text
    poster_body = poster.json()
    assert poster_body["posterUrl"].startswith("http://testserver/static/posters/")
    assert poster_body["jobId"].startswith("poster_")

    poster_status = client.get(f"/api/poster/{poster_body['jobId']}/status")
    assert poster_status.status_code == 200, poster_status.text
    assert poster_status.json().keys() >= {"jobId", "status", "progress", "posterUrl", "updatedAt"}
    assert poster_status.json()["status"] == "completed"

    llm_config = client.get("/api/llm/config")
    assert llm_config.status_code == 200, llm_config.text
    assert "claude" in llm_config.json()["availableProviders"]

    llm_status = client.get("/api/llm/enhance/plan-001/status")
    assert llm_status.status_code == 200, llm_status.text
    assert llm_status.json().keys() >= {"planId", "status", "progress", "currentStep", "updatedAt"}
    assert llm_status.json()["progress"] == 100


def _assert_plan_shape(body: dict[str, object]) -> None:
    assert body.keys() >= {"id", "name", "rush", "stable", "safe", "createdAt"}
    assert isinstance(body["id"], str)
    assert isinstance(body["name"], str)
    assert isinstance(body["rush"], list)
    assert isinstance(body["stable"], list)
    assert isinstance(body["safe"], list)
    assert isinstance(body["createdAt"], str)


def _assert_timestamp(value: object) -> None:
    assert isinstance(value, str)
    assert value


def _assert_chat_message_shape(message: dict[str, object]) -> None:
    assert message.keys() >= {"id", "role", "content", "timestamp"}
    assert isinstance(message["id"], str)
    assert message["role"] in {"user", "assistant", "system"}
    assert isinstance(message["content"], str)
    _assert_timestamp(message["timestamp"])


def _assert_admin_share_link_shape(item: dict[str, object]) -> None:
    assert item.keys() >= {"code"}
    assert isinstance(item["code"], str)
    assert item["code"]
    assert item.get("result_type") in {"review_result", "report", None} or item.get("resultType") in {"review_result", "report"}
    for numeric_key in ["access_count", "views", "unique_visitors", "uniqueVisitors"]:
        if numeric_key in item and item[numeric_key] is not None:
            value: object = item[numeric_key]
            assert isinstance(value, int)
            assert value >= 0


def _assert_admin_share_link_page(body: dict[str, object], *, limit: int, offset: int) -> None:
    assert body.keys() >= {"total", "limit", "offset", "items"}
    assert body["limit"] == limit
    assert body["offset"] == offset
    total: object = body["total"]
    assert isinstance(total, int)
    items: object = body["items"]
    assert isinstance(items, list)
    assert total >= len(items)
    for item in items:
        assert isinstance(item, dict)
        _assert_admin_share_link_shape(item)


def _assert_admin_poster_shape(item: dict[str, object]) -> None:
    assert item.keys() >= {"status", "progress"}
    assert item.get("id") or item.get("jobId") or item.get("job_id")
    assert item["status"] in {"queued", "processing", "completed", "failed"}
    assert isinstance(item["progress"], int)
    assert 0 <= item["progress"] <= 100
    if "template" in item and item["template"] is not None:
        assert item["template"] in {"classic", "modern", "minimal"}


def _assert_admin_poster_page(body: dict[str, object], *, limit: int, offset: int) -> None:
    assert body.keys() >= {"total", "limit", "offset", "items"}
    assert body["limit"] == limit
    assert body["offset"] == offset
    total: object = body["total"]
    assert isinstance(total, int)
    items: object = body["items"]
    assert isinstance(items, list)
    assert total >= len(items)
    for item in items:
        assert isinstance(item, dict)
        _assert_admin_poster_shape(item)


def _assert_portal_token(settings, order_id: str = "GKO-20260706-PORTAL") -> str:
    order = _seed_order(settings.orders_db_path, order_id=order_id)
    _mark_paid(settings, order)
    IntakeStore.for_db(settings.orders_db_path).save(
        order_id=order.id,
        payload={
            "candidate_province": "湖南",
            "candidate_score": 578,
            "candidate_rank": 12345,
            "candidate_subjects": ["物理", "化学", "生物"],
        },
        submit=True,
    )
    return issue_portal_token(order.id, settings.portal_token_secret)


def _create_report_share_link(client, auth_headers, settings, order_id: str = "GKO-20260706-SHARE") -> str:
    order = _seed_order(settings.orders_db_path, order_id=order_id)
    _mark_paid(settings, order)
    report_root = Path(settings.share_report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / f"{order_id}.html"
    pdf_path = report_root / f"{order_id}.pdf"
    report_path.write_text("<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\ncontract\n")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.update(
            order.id,
            {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
            actor="test",
            reason="contract_seed_report",
        )
        dao.transition_status(order.id, "serving", actor="test", reason="processing")
        dao.transition_status(order.id, "delivered", actor="test", reason="report_ready")
    token = issue_portal_token(order.id, settings.portal_token_secret)

    created = client.post(
        "/api/share-link",
        headers=auth_headers,
        json={"result_type": "report", "target_token": token, "permission": "read", "ttl_days": 7},
    )
    assert created.status_code == 201, created.text
    return created.json()["share_url"].rsplit("/", 1)[1]


def _chat_stream_content(response) -> str:
    content_type = response.headers.get("content-type", "")
    raw = response.text.strip()
    assert raw

    if "application/json" in content_type:
        payload = response.json()
        content = payload.get("content") or payload.get("delta")
        assert isinstance(content, str)
        return content

    chunks: list[str] = []
    for block in raw.split("\n\n"):
        data_lines = [line.removeprefix("data:").strip() for line in block.splitlines() if line.startswith("data:")]
        if not data_lines:
            continue
        data = "\n".join(data_lines)
        if data == "[DONE]":
            continue
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            chunks.append(data)
            continue
        content = payload.get("delta") or payload.get("content")
        if content:
            chunks.append(content)

    return "".join(chunks)


def test_consultations_list_returns_frontend_shape(client):
    response = client.get("/api/consultations")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body.keys() >= {"consultations", "total"}
    assert isinstance(body["consultations"], list)
    assert isinstance(body["total"], int)
    assert body["total"] >= len(body["consultations"])

    if body["consultations"]:
        consultation = body["consultations"][0]
        assert consultation.keys() >= {"id", "title", "messageCount", "createdAt", "updatedAt"}


def test_plans_list_returns_frontend_shape(client):
    response = client.get("/api/plans")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body.keys() >= {"plans", "total"}
    assert isinstance(body["plans"], list)
    assert isinstance(body["total"], int)
    assert body["total"] >= len(body["plans"])

    if body["plans"]:
        _assert_plan_shape(body["plans"][0])


def test_plan_detail_returns_plan_shape(client):
    response = client.get("/api/plans/plan-001")

    assert response.status_code == 200, response.text
    _assert_plan_shape(response.json())


def test_chat_stream_returns_content_bearing_json_or_sse(client):
    response = client.post("/api/chat/stream", json={"message": "测试"})

    assert response.status_code == 200, response.text
    assert _chat_stream_content(response)




def test_admin_share_links_list_and_detail_return_frontend_shapes(client, auth_headers, settings):
    code = _create_report_share_link(client, auth_headers, settings)

    list_response = client.get(
        "/api/admin/share-links",
        headers=auth_headers,
        params={"limit": 20, "offset": 0},
    )
    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    _assert_admin_share_link_page(list_body, limit=20, offset=0)
    assert any(item["code"] == code for item in list_body["items"])

    detail_response = client.get(f"/api/admin/share-links/{code}", headers=auth_headers)
    assert detail_response.status_code == 200, detail_response.text
    detail_body = detail_response.json()
    assert detail_body.keys() >= {"link", "stats", "trend", "auditLogs"}
    _assert_admin_share_link_shape(detail_body["link"])
    assert detail_body["link"]["code"] == code
    assert detail_body["stats"].keys() >= {"views", "uniqueVisitors", "lastAccessedAt"}
    assert isinstance(detail_body["stats"]["views"], int)
    assert isinstance(detail_body["stats"]["uniqueVisitors"], int)
    assert isinstance(detail_body["trend"], list)
    for point in detail_body["trend"]:
        assert point.keys() >= {"date", "views"}
        assert isinstance(point["date"], str)
        assert isinstance(point["views"], int)
    assert isinstance(detail_body["auditLogs"], list)
    for entry in detail_body["auditLogs"]:
        assert entry.keys() >= {"id", "action"}
        assert isinstance(entry["action"], str)


def test_admin_posters_list_returns_frontend_shape(client, auth_headers):
    created = client.post(
        "/api/poster/generate",
        json={"planId": "plan-001", "template": "classic"},
    )
    assert created.status_code == 200, created.text

    response = client.get(
        "/api/admin/posters",
        headers=auth_headers,
        params={"limit": 20, "offset": 0},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    _assert_admin_poster_page(body, limit=20, offset=0)
    assert any((item.get("jobId") or item.get("job_id") or item.get("id")) == created.json()["jobId"] for item in body["items"])


def test_plan_create_update_delete_contract(client):
    plan_payload = {
        "name": "Sprint 3 契约方案",
        "profile": {
            "province": "湖南",
            "score": 578,
            "rank": 12345,
            "subjects": ["物理", "化学", "生物"],
        },
        "rush": [
            {
                "university": "中南大学",
                "major": "计算机科学与技术",
                "estScore": 590,
                "probability": 0.35,
                "risk": "冲刺",
                "riskType": "rush",
                "reason": "分差较小，适合作为冲刺志愿。",
            }
        ],
        "stable": [],
        "safe": [],
    }

    created = client.post("/api/plans", json=plan_payload)
    assert created.status_code == 200, created.text
    created_body = created.json()
    _assert_plan_shape(created_body)
    assert created_body["name"] == plan_payload["name"]
    assert created_body["rush"][0].keys() >= {"university", "major", "estScore", "probability", "risk", "riskType", "reason"}

    updated = client.put(f"/api/plans/{created_body['id']}", json={"name": "已更新契约方案"})
    assert updated.status_code == 200, updated.text
    updated_body = updated.json()
    _assert_plan_shape(updated_body)
    assert updated_body["id"] == created_body["id"]
    assert updated_body["name"] == "已更新契约方案"

    deleted = client.delete(f"/api/plans/{created_body['id']}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"success": True}

    missing = client.get(f"/api/plans/{created_body['id']}")
    assert missing.status_code == 404, missing.text


def test_consultation_create_update_delete_and_chat_history_contract(client):
    created = client.post("/api/consultations", json={"title": "Sprint 3 咨询"})
    assert created.status_code == 200, created.text
    created_body = created.json()
    assert created_body.keys() >= {"id", "title", "createdAt"}
    assert created_body["title"] == "Sprint 3 咨询"
    _assert_timestamp(created_body["createdAt"])

    updated = client.patch(
        f"/api/consultations/{created_body['id']}",
        json={
            "title": "已更新咨询",
            "messages": [
                {"id": "msg-user", "role": "user", "content": "请看我的方案", "timestamp": "2026-07-06T00:00:00Z"},
                {"id": "msg-assistant", "role": "assistant", "content": "可以。", "timestamp": "2026-07-06T00:00:01Z"},
            ],
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json() == {"success": True}

    history = client.get("/api/chat/history", params={"sessionId": created_body["id"]})
    assert history.status_code == 200, history.text
    history_body = history.json()
    assert history_body.keys() >= {"sessionId", "messages"}
    assert history_body["sessionId"] == created_body["id"]
    assert isinstance(history_body["messages"], list)
    assert len(history_body["messages"]) == 2
    for message in history_body["messages"]:
        _assert_chat_message_shape(message)

    deleted = client.delete(f"/api/consultations/{created_body['id']}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"success": True}

    missing_history = client.get("/api/chat/history", params={"sessionId": created_body["id"]})
    assert missing_history.status_code == 404, missing_history.text


def test_assessment_and_audit_contracts_return_frontend_shapes(client):
    assessment = client.post(
        "/api/assessment",
        json={
            "province": "湖南",
            "score": 578,
            "rank": 12345,
            "subjects": ["物理", "化学", "生物"],
        },
    )
    assert assessment.status_code == 200, assessment.text
    assessment_body = assessment.json()
    assert assessment_body.keys() >= {"assessmentId", "estimatedRank", "recommendedPlans"}
    assert isinstance(assessment_body["assessmentId"], str)
    assert isinstance(assessment_body["estimatedRank"], int)
    assert isinstance(assessment_body["recommendedPlans"], list)
    for plan in assessment_body["recommendedPlans"]:
        _assert_plan_shape(plan)

    audit = client.post(
        "/api/audit/submit",
        json={"planId": "plan-001", "planContent": "冲刺：中南大学；稳妥：湖南大学；保底：长沙理工大学。"},
    )
    assert audit.status_code == 200, audit.text
    audit_body = audit.json()
    assert audit_body.keys() >= {"auditId", "status", "risks", "score"}
    assert isinstance(audit_body["auditId"], str)
    assert audit_body["status"] in {"pending", "processing", "completed", "failed"}
    assert isinstance(audit_body["risks"], list)
    assert 0 <= audit_body["score"] <= 100
    for risk in audit_body["risks"]:
        assert risk.keys() >= {"index", "level", "title", "description"}
        assert risk["level"] in {"低", "中", "高"}

    status = client.get(f"/api/audit/{audit_body['auditId']}/status")
    assert status.status_code == 200, status.text
    assert status.json().keys() >= {"auditId", "status"}
    assert status.json()["auditId"] == audit_body["auditId"]
    assert status.json()["status"] in {"pending", "processing", "completed", "failed"}
    if "progress" in status.json():
        assert 0 <= status.json()["progress"] <= 100


def test_portal_cwb_and_full_plan_return_frontend_json_shapes(client, settings):
    token = _assert_portal_token(settings)

    cwb = client.get(f"/api/portal/{token}/cwb", headers={"accept": "application/json"})
    assert cwb.status_code == 200, cwb.text
    assert cwb.headers["content-type"].startswith("application/json")
    cwb_body = cwb.json()
    assert cwb_body.keys() >= {"token", "province", "year", "scoreType", "score", "rank", "equivalentScore"}
    assert cwb_body["token"] == token
    assert cwb_body["province"] == "湖南"
    assert isinstance(cwb_body["year"], int)
    assert cwb_body["scoreType"] in {"physics", "history"}
    assert isinstance(cwb_body["score"], (int, float))
    assert isinstance(cwb_body["rank"], int)
    assert isinstance(cwb_body["equivalentScore"], (int, float))

    full_plan = client.get(f"/api/portal/{token}/full-plan", headers={"accept": "application/json"})
    assert full_plan.status_code == 200, full_plan.text
    assert full_plan.headers["content-type"].startswith("application/json")
    full_plan_body = full_plan.json()
    assert full_plan_body.keys() >= {"token", "plan", "createdAt"}
    assert full_plan_body["token"] == token
    assert full_plan_body["plan"].keys() >= {"id", "title", "schools"}
    assert isinstance(full_plan_body["plan"]["id"], str)
    assert isinstance(full_plan_body["plan"]["title"], str)
    assert isinstance(full_plan_body["plan"]["schools"], list)
    for school in full_plan_body["plan"]["schools"]:
        assert school.keys() >= {"id", "name", "majors", "admissionProbability"}
        assert isinstance(school["id"], str)
        assert isinstance(school["name"], str)
        assert isinstance(school["majors"], list)
        assert school["admissionProbability"] in {"冲", "稳", "保"}
    _assert_timestamp(full_plan_body["createdAt"])