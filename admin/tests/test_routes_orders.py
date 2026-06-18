"""订单管理路由测试 (T6.4).

覆盖:
- 手工录单 POST /api/orders
- 订单列表 / 详情
- PATCH 业务字段更新 + 状态流转
- refunded 退款流转
- CSV 导出
"""

from __future__ import annotations

import csv
from io import StringIO

import pytest

from data.orders.dao import OrdersDAO
from data.orders.intake_store import IntakeStore
from data.orders.models import Order


@pytest.fixture(autouse=True)
def _orders_fernet_key(monkeypatch):
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-admin-orders")


def _seed_order(settings, **overrides) -> Order:
    payload = {
        "id": overrides.pop("id", "GKO-20260612-SEED"),
        "source": "web",
        "external_id": None,
        "service_version": "basic",
        "amount_cents": 4900,
        "status": "pending",
        "customer_name": "张三",
        "customer_phone": "13800001234",
        "customer_wechat": "zhangsanwx",
        "candidate_name": "李同学",
        "candidate_id_card": "430102200501011234",
        "candidate_province": "湖南",
        "candidate_score": 578,
        "tags": ["首单"],
        "notes": "待跟进",
    }
    payload.update(overrides)
    order = Order(**payload)
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        return dao.create(order, actor="test", reason="seed")


def test_create_order_returns_masked_payload_with_history(client, auth_headers):
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            "source": "wechat",
            "external_id": "WX-001",
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "王家长",
            "customer_phone": "13900001111",
            "customer_wechat": "parentwx",
            "candidate_name": "王同学",
            "candidate_id_card": "110101200701011234",
            "candidate_province": "北京",
            "candidate_score": 640,
            "candidate_subjects": ["物理", "化学"],
            "notes": "手工补录",
            "tags": ["渠道补单"],
        },
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["action"] == "created"
    assert body["order"]["source"] == "wechat"
    assert body["order"]["status"] == "pending"
    assert body["order"]["customer_phone"] == "139****1111"
    assert body["order"]["candidate_id_card"] == "110101********1234"
    assert "customer_phone_hash" not in body["order"]
    assert body["history"][0]["from_status"] is None
    assert body["history"][0]["to_status"] == "pending"


def test_list_and_detail_return_real_orders_with_masking(
    client, auth_headers, settings
):
    created = _seed_order(settings, id="GKO-20260612-LIST")

    list_resp = client.get(
        "/api/orders",
        headers=auth_headers,
        params={"status": "pending", "limit": 10, "offset": 0},
    )
    assert list_resp.status_code == 200, list_resp.text
    payload = list_resp.json()
    assert len(payload) == 1
    assert payload[0]["id"] == created.id
    assert payload[0]["customer_phone"] == "138****1234"
    assert payload[0]["intake_status"] is None
    assert payload[0]["intake_submitted_at"] is None

    detail_resp = client.get(f"/api/orders/{created.id}", headers=auth_headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["order"]["id"] == created.id
    assert detail["order"]["customer_wechat"] == "zh******wx"
    assert detail["order"]["intake_status"] is None
    assert detail["order"]["intake_submitted_at"] is None
    assert detail["history"][0]["to_status"] == "pending"
    assert set(detail["available_next_statuses"]) == {"paid", "refunded"}


def test_detail_exposes_submitted_intake_state(client, auth_headers, settings):
    created = _seed_order(settings, id="GKO-20260612-INTAKE-DETAIL")
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        record = intake_store.save(
            order_id=created.id,
            payload={"candidate_score": 578, "guardian_notes": "尽快处理"},
            submit=True,
        )
    finally:
        intake_store.close()

    list_resp = client.get(
        "/api/orders",
        headers=auth_headers,
        params={"status": "pending", "limit": 10, "offset": 0},
    )
    assert list_resp.status_code == 200, list_resp.text
    payload = list_resp.json()
    assert payload[0]["intake_status"] == "submitted"
    assert payload[0]["intake_submitted_at"] == record.submitted_at

    detail_resp = client.get(f"/api/orders/{created.id}", headers=auth_headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["order"]["intake_status"] == "submitted"
    assert detail["order"]["intake_submitted_at"] == record.submitted_at


def test_patch_updates_business_fields_and_status_transition(
    client, auth_headers, settings
):
    created = _seed_order(settings, id="GKO-20260612-PATCH")

    resp = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={
            "updates": {
                "assigned_consultant": "consultant-a",
                "notes": "已联系家长",
                "tags": ["已跟进", "VIP"],
            },
            "to_status": "paid",
            "reason": "manual_pay",
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["order"]["assigned_consultant"] == "consultant-a"
    assert body["order"]["notes"] == "已联系家长"
    assert body["order"]["tags"] == ["已跟进", "VIP"]
    assert body["order"]["status"] == "paid"
    assert body["order"]["paid_at"] is not None
    assert [item["to_status"] for item in body["history"]] == ["pending", "paid"]


def test_patch_refund_flow_appends_history(client, auth_headers, settings):
    created = _seed_order(settings, id="GKO-20260612-REFUND")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(created.id, "paid", actor="test", reason="seed_pay")

    resp = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={"to_status": "refunded", "reason": "manual_refund"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["order"]["status"] == "refunded"
    assert [item["to_status"] for item in body["history"]] == [
        "pending",
        "paid",
        "refunded",
    ]
    assert body["available_next_statuses"] == []


def test_patch_invalid_transition_returns_conflict(client, auth_headers, settings):
    created = _seed_order(settings, id="GKO-20260612-CONFLICT")

    resp = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={"to_status": "completed", "reason": "skip_steps"},
    )

    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "E02301"


def test_patch_paid_to_serving_requires_submitted_intake(
    client, auth_headers, settings
):
    created = _seed_order(settings, id="GKO-20260612-NEED-INTAKE")
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(created.id, "paid", actor="test", reason="seed_pay")

    blocked = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={"to_status": "serving", "reason": "begin_processing"},
    )
    assert blocked.status_code == 422
    blocked_body = blocked.json()
    assert blocked_body["code"] == "E03001"
    assert blocked_body["detail"]["required_intake_status"] == "submitted"

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake_store.save(
            order_id=created.id,
            payload={"candidate_score": 588, "guardian_notes": "资料已确认"},
            submit=True,
        )
    finally:
        intake_store.close()

    allowed = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={"to_status": "serving", "reason": "begin_processing"},
    )
    assert allowed.status_code == 200, allowed.text
    allowed_body = allowed.json()
    assert allowed_body["order"]["status"] == "serving"
    assert allowed_body["order"]["intake_status"] == "submitted"


def test_patch_order_rejects_audit_report_outside_allowed_report_dir(
    client, auth_headers, settings
):
    created = _seed_order(settings, id="GKO-20260612-UNTRUSTED-HTML")

    resp = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={
            "updates": {"audit_report": "/etc/hosts"},
            "reason": "attach_report",
        },
    )

    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "E03001"
    assert "untrusted artifact" in body["detail"]["reason"]


def test_patch_order_rejects_pdf_path_outside_allowed_report_dir(
    client, auth_headers, settings
):
    created = _seed_order(settings, id="GKO-20260612-UNTRUSTED-PDF")

    resp = client.patch(
        f"/api/orders/{created.id}",
        headers=auth_headers,
        json={
            "updates": {"pdf_path": "/etc/hosts"},
            "reason": "attach_report",
        },
    )

    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "E03001"
    assert "untrusted artifact" in body["detail"]["reason"]


def test_viewer_cannot_list_orders(client, viewer_headers, settings):
    _seed_order(settings, id="GKO-20260612-VIEWER-LIST")

    resp = client.get("/api/orders", headers=viewer_headers)

    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "E01301"


def test_viewer_cannot_patch_order(client, viewer_headers, settings):
    created = _seed_order(settings, id="GKO-20260612-VIEWER-PATCH")

    resp = client.patch(
        f"/api/orders/{created.id}",
        headers=viewer_headers,
        json={"updates": {"notes": "viewer should fail"}, "reason": "forbidden"},
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "E01301"


def test_export_orders_csv_returns_masked_rows(client, auth_headers, settings):
    _seed_order(
        settings,
        id="GKO-20260612-CSV",
        source="school",
        service_version="premium",
        amount_cents=19900,
    )

    resp = client.get(
        "/api/orders/export",
        headers=auth_headers,
        params={"status": "pending", "source": "school"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in resp.headers["content-disposition"]

    rows = list(csv.DictReader(StringIO(resp.text)))
    assert len(rows) == 1
    assert rows[0]["id"] == "GKO-20260612-CSV"
    assert rows[0]["customer_phone"] == "138****1234"
    assert rows[0]["candidate_id_card"] == "430102********1234"
    assert rows[0]["status"] == "pending"


def test_export_orders_csv_neutralizes_formula_injection_values(
    client, auth_headers, settings
):
    _seed_order(
        settings,
        id="GKO-20260612-CSV-FORMULA",
        customer_name="=cmd|' /C calc'!A0",
        candidate_name="+SUM(1,2)",
        notes="@SUM(A1:A2)",
        external_id="-10+20",
    )

    resp = client.get("/api/orders/export", headers=auth_headers)

    assert resp.status_code == 200, resp.text
    rows = list(csv.DictReader(StringIO(resp.text)))
    assert len(rows) == 1
    assert not rows[0]["customer_name"].startswith(("=", "+", "-", "@"))
    assert not rows[0]["candidate_name"].startswith(("=", "+", "-", "@"))
    assert rows[0]["notes"] == "'@SUM(A1:A2)"
    assert rows[0]["external_id"] == "'-10+20"
