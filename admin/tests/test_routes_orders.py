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
            "consent": {
                "consent_method": "verbal_chat",
                "consent_note": "微信沟通后家长口头同意",
            },
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
    assert body["order"]["consent_method"] == "verbal_chat"
    assert body["order"]["consent_given_at"] is not None
    assert body["history"][0]["from_status"] is None
    assert body["history"][0]["to_status"] == "pending"


# ---------------------------------------------------------------------------
# A-2: 后台/外部渠道补录同意审计统一化（2026-06-20 落地）
#
# LEGAL_PRIVACY_BASELINE §6 要求所有订单创建路径必须记录同意审计字段。
# portal 路径已自动落 consent_channel=portal / consent_operator=guardian
# （见 web_public.py + intake_store.save）。
# admin 代录/外部渠道补录路径必须在请求体里显式带 consent 块, 否则拒绝
# (HTTP 422)。
# ---------------------------------------------------------------------------


_XIANYU_BASE = {
    "source": "xianyu",
    "external_id": "XY-A2-001",
    "service_version": "standard",
    "amount_cents": 9900,
    "customer_name": "陈家长",
    "customer_phone": "13900002222",
    "candidate_name": "陈同学",
    "candidate_province": "广东",
    "candidate_score": 595,
}


@pytest.mark.parametrize("source", ["xianyu", "wechat", "school", "web"])
def test_create_order_rejects_missing_consent_block(client, auth_headers, source):
    """A-2 RED: 任何 source 补录都必须在请求体里带 consent 块, 否则 422。"""
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={**_XIANYU_BASE, "source": source, "external_id": f"TEST-{source}"},
    )
    assert resp.status_code == 422, resp.text
    body_str = resp.text
    # 项目对 422 走自定义 exception handler, detail 可能是 dict 或 str
    # 只要 body 里出现 "consent" 字段名就算合规
    assert "consent" in body_str, f"422 错误体未提及 consent 字段: {body_str}"


def test_create_order_writes_intake_record_with_consent_audit(
    client, auth_headers, settings
):
    """A-2 RED: 合规补录成功后, 必须能在 order_intakes 表查到 consent 审计字段。"""
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            **_XIANYU_BASE,
            "external_id": "XY-A2-002",
            "consent": {
                "consent_method": "phone_recording",
                "consent_note": "闲鱼沟通后电话确认",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    order_id = resp.json()["order"]["id"]

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        record = intake_store.get(order_id)
    finally:
        intake_store.close()

    assert record is not None, f"order_intakes 表未创建 {order_id} 记录"
    assert record.status == "draft"
    assert record.submitted_at is None
    # 同意审计字段必须落库, 与 portal 路径字段同口径
    assert record.payload.get("consent_channel") == "xianyu"
    assert record.payload.get("consent_operator") == "admin_import"
    assert record.payload.get("consent_method") == "phone_recording"
    assert record.payload.get("consent_given_at") is not None
    assert record.payload.get("consent_note") == "闲鱼沟通后电话确认"


def test_create_order_uses_settings_consent_version(client, auth_headers, settings):
    """consent_version / consent_scope 不再硬编码, 而是从 Settings 读取。

    锁定: 默认值 = privacy-policy-v2026.06.25 / xianyu-channel-intake
    （升级隐私政策时只需改环境变量 GAOKAO_CONSENT_VERSION, 无需改代码）
    """
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            **_XIANYU_BASE,
            "external_id": "XY-CONSENT-VER-001",
            "consent": {
                "consent_method": "phone_recording",
                "consent_note": "consent_version 来源测试",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    order_id = resp.json()["order"]["id"]

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        record = intake_store.get(order_id)
    finally:
        intake_store.close()

    assert record is not None
    # 必须来自 settings.consent_version (默认 privacy-policy-v2026.06.25)
    assert record.payload.get("consent_version") == settings.consent_version
    assert record.payload.get("consent_version") == "privacy-policy-v2026.06.25"
    # scope 必须是 f"{source}-{settings.consent_scope_channel_prefix}"
    assert (
        record.payload.get("consent_scope")
        == f"xianyu-{settings.consent_scope_channel_prefix}"
    )


def test_create_order_external_channel_marks_consent_operator_as_admin(
    client, auth_headers, settings
):
    """A-2 RED: 外部渠道(xianyu/wechat/school)的 consent_operator 必须是 admin,
    因为是后台代录而非用户自助 portal。"""
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            **_XIANYU_BASE,
            "external_id": "WECHAT-A2-003",
            "source": "wechat",
            "consent": {"consent_method": "screenshot", "consent_note": "微信截图"},
        },
    )
    assert resp.status_code == 201, resp.text
    order_id = resp.json()["order"]["id"]

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        record = intake_store.get(order_id)
    finally:
        intake_store.close()

    assert record is not None
    assert record.payload.get("consent_channel") == "wechat"
    assert record.payload.get("consent_operator") == "admin_import"


def test_create_order_rejects_invalid_consent_method(client, auth_headers):
    """A-2 RED: consent_method 必须是白名单值。"""
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            **_XIANYU_BASE,
            "external_id": "XY-A2-004",
            "consent": {"consent_method": "telepathy", "consent_note": "非法方法"},
        },
    )
    assert resp.status_code == 422, resp.text


def test_order_detail_returns_consent_method_and_given_at(client, auth_headers):
    """A-2 RED: Order 列表/详情接口直接返回 consent_method + consent_given_at,
    不必后端 join order_intakes 表 (冗余字段落库, 性能 + 一致性)。"""
    create_resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            **_XIANYU_BASE,
            "external_id": "XY-A2-005",
            "consent": {
                "consent_method": "written_form",
                "consent_note": "书面确认单已签字",
            },
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    order_id = create_resp.json()["order"]["id"]

    detail_resp = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()["order"]
    assert detail["consent_method"] == "written_form"
    assert detail["consent_given_at"] is not None


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


def test_detail_exposes_structured_intake_payload(client, auth_headers, settings):
    created = _seed_order(settings, id="GKO-20260624-INTAKE-STRUCT")
    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake_store.save(
            order_id=created.id,
            payload={
                "candidate_score": 578,
                "target_cities": ["长沙", "深圳"],
                "target_schools": ["湖南大学"],
                "family_background": "家长更希望省内优先",
                "interest_assessment_result": "INTJ",
            },
            submit=True,
        )
    finally:
        intake_store.close()

    detail_resp = client.get(f"/api/orders/{created.id}", headers=auth_headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["order"]["intake_status"] == "submitted"
    assert detail["order"]["intake"] is not None
    assert detail["order"]["intake"]["target_cities"] == ["长沙", "深圳"]
    assert detail["order"]["intake"]["target_schools"] == ["湖南大学"]
    assert detail["order"]["intake"]["family_background"] == "家长更希望省内优先"
    assert detail["order"]["intake"]["interest_assessment_result"] == "INTJ"


def test_admin_create_order_defaults_to_draft_intake_state(
    client, auth_headers, settings
):
    resp = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            "source": "wechat",
            "external_id": "ADMIN-DRAFT-001",
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
            "consent": {
                "consent_method": "verbal_chat",
                "consent_note": "后台补录同意",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["order"]["intake_status"] == "draft"
    assert body["order"]["intake_submitted_at"] is None


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
