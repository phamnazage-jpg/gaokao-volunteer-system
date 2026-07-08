"""Legacy backend-rendered public pages are intentionally removed.

The React/Vite app is the user-facing frontend. The FastAPI service keeps API
and data endpoints only; old HTML page routes should not keep rendering stale UI.
"""


def test_legacy_public_get_pages_are_removed(client):
    removed_paths = [
        "/",
        "/pricing",
        "/checkout/standard",
        "/privacy",
        "/service-terms",
        "/deletion-policy",
        "/policy-center",
        "/same-score-reference",
        "/my-orders",
        "/my-reports",
        "/data-query",
        "/score-line-query",
        "/rank-estimator",
        "/majors-query",
        "/schools-query",
        "/compare-reports",
    ]
    for path in removed_paths:
        resp = client.get(path)
        assert resp.status_code == 404, path


def test_public_order_api_is_still_registered(client):
    resp = client.post("/api/public/orders", json={})
    assert resp.status_code in {400, 422}


def test_health_route_still_registered(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_portal_api_helpers_are_still_importable():
    from admin.routes.web_public import _build_portal_context, _load_latest_review_result, _resolve_order_from_token

    assert callable(_build_portal_context)
    assert callable(_load_latest_review_result)
    assert callable(_resolve_order_from_token)
