from __future__ import annotations

from data.customer_portal.token import issue_portal_token
from data.orders.intake_store import IntakeStore
from admin.tests.order_test_helpers import _mark_paid, _seed_order


def test_portal_info_api_accepts_draft_and_submit(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260708-INFO-API")
    _mark_paid(settings, order)
    token = issue_portal_token(order.id, settings.portal_token_secret)

    draft = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "draft",
            "candidate_province": "湖南",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "privacy_accepted": False,
            "service_terms_accepted": False,
            "guardian_confirmed": False,
        },
    )
    assert draft.status_code == 200, draft.text
    assert draft.json()["intake_status"] == "draft"
    assert draft.json()["stage"] == "info_required"

    submit = client.post(
        f"/portal/{token}/info",
        json={
            "mode": "submit",
            "candidate_province": "湖南",
            "candidate_score": 578,
            "candidate_rank": 12034,
            "candidate_subjects": ["物理", "化学", "生物"],
            "target_cities": ["长沙"],
            "target_majors": ["计算机科学与技术"],
            "consent_version": "api-v1",
            "consent_scope": "portal-info-api",
            "privacy_accepted": True,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        },
    )
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["intake_status"] == "submitted"
    assert body["stage"] in {"info_submitted", "processing"}

    store = IntakeStore.for_db(settings.orders_db_path)
    try:
        saved = store.get(order.id)
    finally:
        store.close()
    assert saved is not None
    assert saved.payload["candidate_province"] == "湖南"
    assert saved.payload["privacy_accepted"] is True


def test_portal_info_api_rejects_before_payment(client, settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-20260708-INFO-NOPAY")
    token = issue_portal_token(order.id, settings.portal_token_secret)

    resp = client.post(
        f"/portal/{token}/info",
        json={"mode": "draft", "candidate_province": "湖南"},
    )
    assert resp.status_code == 409
    assert "payment required" in resp.text
