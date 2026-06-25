"""用户端 Portal 资料页测试。"""

from __future__ import annotations

from data.orders.dao import OrdersDAO


def test_info_page_wizard_actions_outside_form_for_sticky_bottom(client, settings):
    """资料页移动端关键操作按钮必须放在 form 之外。"""
    from data.orders.dao import OrdersDAO
    from data.orders.public_flow import PublicOrderCreate, create_public_order
    from data.customer_portal.token import issue_portal_token

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order = create_public_order(
            dao,
            PublicOrderCreate(
                service_version="standard",
                amount_cents=9900,
                customer_name="Sticky 用户",
                customer_phone="13800138000",
                candidate_name="Sticky-User",
                candidate_province="湖南",
            ),
        )
    token = issue_portal_token(order.id, settings.portal_token_secret)
    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    body = resp.text
    form_end = body.find("</form>")
    wizard_start = body.find('<div class="wizard-actions">')
    assert form_end > 0
    assert wizard_start > 0
    assert wizard_start > form_end
    for label in ["保存草稿", "下一步", "上一步", "确认并提交资料"]:
        assert label in body
    assert "safe-area-inset-bottom" in body


def test_confirm_summary_does_not_use_innerhtml_for_user_fields(client, settings):
    from data.orders.dao import OrdersDAO
    from data.orders.public_flow import PublicOrderCreate, create_public_order
    from data.customer_portal.token import issue_portal_token

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order = create_public_order(
            dao,
            PublicOrderCreate(
                service_version="standard",
                amount_cents=9900,
                customer_name="Summary 用户",
                customer_phone="13800138000",
                candidate_name="Summary-User",
                candidate_province="湖南",
            ),
        )
    token = issue_portal_token(order.id, settings.portal_token_secret)
    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "confirm-summary').innerHTML" not in body
    assert "replaceChildren" in body
    assert "createElement('div')" in body


def test_portal_info_page_renders_candidate_province_field(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["portal_info_url"].split("/portal/")[1].split("/info")[0]

    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    assert 'name="candidate_province"' in resp.text
    assert "candidate_province: form.get('candidate_province')" in resp.text


def test_portal_info_page_step1_no_longer_requires_preference_target(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["portal_info_url"].split("/portal/")[1].split("/info")[0]

    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    assert "至少一个偏好目标" not in resp.text


def test_submit_order_info_minimal_step1_marks_profile_complete_and_persists_province(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload
    from data.orders.intake_store import IntakeStore

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_info_url"].split("/portal/")[1].split("/info")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    result = submit_order_info(
        token,
        IntakePayload(
            mode="submit",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            consent_version="portal-v1",
            consent_scope="step1",
            privacy_accepted=True,
            service_terms_accepted=True,
            guardian_confirmed=True,
        ),
        settings,
    )

    assert result.intake_status == "submitted"
    assert result.profile_minimum_complete is True

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order = dao.get(body["order_id"])
    assert order.candidate_province == "湖南"
    assert order.candidate_score == 578
    assert order.candidate_rank == 12345
    assert order.candidate_subjects == ["物理", "化学", "生物"]

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
    finally:
        intake_store.close()
    assert intake is not None
    assert intake.payload["candidate_province"] == "湖南"


def test_submit_order_info_returns_profile_missing_fields_when_step1_incomplete(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_info_url"].split("/portal/")[1].split("/info")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    result = submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
        ),
        settings,
    )

    assert result.profile_minimum_complete is False
    assert result.profile_missing_fields == ["candidate_rank"]


def test_portal_info_page_renders_step2_to_step4_fields(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["portal_info_url"].split("/portal/")[1].split("/info")[0]

    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert 'name="school_region_preferences"' in body
    assert 'name="school_preference_types"' in body
    assert 'name="target_schools"' in body
    assert 'name="disliked_majors"' in body
    assert 'name="priority_strategy"' in body
    assert 'name="graduation_plan"' in body
    assert 'name="tuition_preference"' in body
    assert 'name="employment_region_preferences"' in body


def test_portal_info_page_renders_target_cities_field(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["portal_info_url"].split("/portal/")[1].split("/info")[0]

    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    assert 'name="target_cities"' in resp.text


def test_submit_order_info_persists_step2_to_step4_preferences(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload
    from data.orders.intake_store import IntakeStore

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_info_url"].split("/portal/")[1].split("/info")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    result = submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            school_region_preferences=["长三角", "珠三角"],
            school_preference_types=["985", "双一流"],
            target_schools=["浙江大学", "中山大学"],
            disliked_majors=["土木工程"],
            priority_strategy="major_first",
            graduation_plan="就业优先",
            tuition_preference="10000-20000",
            employment_region_preferences=["上海", "深圳"],
        ),
        settings,
    )

    assert result.intake_status == "draft"

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
    finally:
        intake_store.close()

    assert intake is not None
    assert intake.payload["school_region_preferences"] == ["长三角", "珠三角"]
    assert intake.payload["school_preference_types"] == ["985", "双一流"]
    assert intake.payload["target_schools"] == ["浙江大学", "中山大学"]
    assert intake.payload["disliked_majors"] == ["土木工程"]
    assert intake.payload["priority_strategy"] == "major_first"
    assert intake.payload["graduation_plan"] == "就业优先"
    assert intake.payload["tuition_preference"] == "10000-20000"
    assert intake.payload["employment_region_preferences"] == ["上海", "深圳"]


def test_portal_info_page_renders_p2_deep_preference_fields(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["portal_info_url"].split("/portal/")[1].split("/info")[0]

    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert 'name="family_background"' in body
    assert 'name="industry_resources"' in body
    assert 'name="extra_notes"' in body


def test_submit_order_info_persists_p2_deep_preference_fields(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload
    from data.orders.intake_store import IntakeStore

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_info_url"].split("/portal/")[1].split("/info")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    result = submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            family_background="父母支持省内发展",
            industry_resources="有本地制造业实习资源",
            extra_notes="希望后续优先考虑长沙与深圳双城路径",
        ),
        settings,
    )

    assert result.intake_status == "draft"

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
    finally:
        intake_store.close()

    assert intake is not None
    assert intake.payload["family_background"] == "父母支持省内发展"
    assert intake.payload["industry_resources"] == "有本地制造业实习资源"
    assert intake.payload["extra_notes"] == "希望后续优先考虑长沙与深圳双城路径"


def test_submit_order_info_creates_profile_version_history_without_duplicate_snapshots(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload
    from data.orders.intake_store import IntakeStore

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_info_url"].split("/portal/")[1].split("/info")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    initial_payload = IntakePayload(
        mode="draft",
        candidate_province="湖南",
        candidate_subjects=["物理", "化学", "生物"],
        candidate_score=578,
        candidate_rank=12345,
        target_cities=["长沙", "深圳"],
    )
    submit_order_info(token, initial_payload, settings)
    submit_order_info(token, initial_payload, settings)
    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=579,
            candidate_rank=12001,
            target_cities=["长沙", "深圳"],
        ),
        settings,
    )
    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=579,
            candidate_rank=12001,
            target_cities=["长沙", "深圳", "上海"],
            family_background="家长更希望省内优先",
        ),
        settings,
    )

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
    finally:
        intake_store.close()

    assert intake is not None
    versions = intake.payload["profile_versions"]
    assert intake.payload["latest_profile_version_id"] == versions[-1]["profile_version_id"]
    assert len(versions) == 3
    assert versions[0]["stage_label"] == "初始档案方案"
    assert versions[1]["stage_label"] == "查分后校准方案"
    assert versions[2]["stage_label"] == "正式填报前调整方案"



def test_portal_info_page_renders_interest_assessment_fields(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["portal_info_url"].split("/portal/")[1].split("/info")[0]

    resp = client.get(f"/portal/{token}/info")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert 'name="interest_assessment_type"' in body
    assert 'name="interest_assessment_result"' in body
    assert 'name="interest_assessment_notes"' in body


def test_submit_order_info_persists_interest_assessment_fields(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload
    from data.orders.intake_store import IntakeStore

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_info_url"].split("/portal/")[1].split("/info")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    result = submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            interest_assessment_type="holland",
            interest_assessment_result="R型+I型",
            interest_assessment_notes="适合作为专业推荐补充因子，不作为唯一判断",
        ),
        settings,
    )

    assert result.intake_status == "draft"

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
    finally:
        intake_store.close()

    assert intake is not None
    assert intake.payload["interest_assessment_type"] == "holland"
    assert intake.payload["interest_assessment_result"] == "R型+I型"
    assert intake.payload["interest_assessment_notes"] == "适合作为专业推荐补充因子，不作为唯一判断"


def test_order_status_page_shows_profile_minimum_complete_badge(client, settings):
    from admin.routes.web_public import submit_order_info
    from data.orders.intake_schema import IntakePayload

    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    submit_order_info(
        token,
        IntakePayload(
            mode="submit",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            consent_version="portal-v1",
            consent_scope="step1",
            privacy_accepted=True,
            service_terms_accepted=True,
            guardian_confirmed=True,
        ),
        settings,
    )

    resp = client.get(f"/portal/{token}/status")
    assert resp.status_code == 200, resp.text
    assert "Step 1 最小建档：已完成" in resp.text
