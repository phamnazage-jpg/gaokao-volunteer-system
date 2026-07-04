from __future__ import annotations


def test_openapi_exposes_react_sprint3_json_contracts(app):
    paths = app.openapi()["paths"]

    required = {
        "/api/share-link",
        "/api/share-link/latest",
        "/api/share-link/{code}/revoke",
        "/api/share-link/{code}/stats",
        "/api/data-query/score-line",
        "/api/data-query/rank-estimator",
        "/api/data-query/majors",
        "/api/data-query/schools",
        "/api/review/start",
        "/api/review/{review_id}/status",
        "/api/review/action",
        "/api/poster/generate",
        "/api/llm/config",
        "/api/llm/{provider}/enhance",
        "/api/llm/enhance/{plan_id}/status",
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
    assert poster.json()["posterUrl"].startswith("http://testserver/static/posters/")

    llm_config = client.get("/api/llm/config")
    assert llm_config.status_code == 200, llm_config.text
    assert "claude" in llm_config.json()["availableProviders"]

    llm_status = client.get("/api/llm/enhance/plan-001/status")
    assert llm_status.status_code == 200, llm_status.text
    assert llm_status.json().keys() >= {"planId", "status", "progress", "currentStep", "updatedAt"}
    assert llm_status.json()["progress"] == 100
