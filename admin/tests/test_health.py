from __future__ import annotations


def test_health_endpoint_returns_minimal_readiness_only(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
