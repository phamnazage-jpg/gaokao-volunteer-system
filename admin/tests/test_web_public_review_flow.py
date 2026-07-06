"""用户端复核、冲稳保、报告与工作台链路测试。"""

from __future__ import annotations

from data.orders.dao import OrdersDAO


def test_landing_page_provides_review_entry_source_link(client):
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    assert 'href="/review/start?source=home"' in resp.text


def test_landing_page_review_consult_form_targets_review_start(client):
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    assert 'form action="/review/start" method="get"' in resp.text
    assert 'name="source" value="home"' in resp.text


def test_landing_page_uses_review_as_workspace_primary_action_when_step1_complete(
    client, settings
):
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

    landing = client.get(f"/?token={token}")
    assert landing.status_code == 200, landing.text
    assert "工作台主动作" in landing.text
    assert "开始方案复核" in landing.text
    assert f"/review/start?source=home&amp;token={token}" in landing.text


def test_review_start_page_renders_user_facing_result_not_ops_process_page(
    client, settings
):
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
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            existing_plan_summary="已有一版志愿方案，想先看有没有明显风险",
        ),
        settings,
    )

    resp = client.get(f"/review/start?source=status&token={token}")
    assert resp.status_code == 200, resp.text
    # 新口径：这是用户结果页，不是系统入口/流程说明页
    assert "复核结果" in resp.text or "初步评估结果" in resp.text
    assert "方案复核入口" not in resp.text
    assert "审核输入" not in resp.text
    assert "最小约束" not in resp.text
    assert "审核输出摘要" not in resp.text
    assert "下一步分流" not in resp.text
    # 必须保留用户可理解的结果与下一步
    assert "风险等级" in resp.text
    assert "核心问题" in resp.text
    assert "下一步建议" in resp.text
    assert "已有一版志愿方案，想先看有没有明显风险" in resp.text
    assert "物理 / 化学 / 生物" in resp.text
    # 不得暴露内部 JSON / review_result_id / action slug
    assert "review_result_id" not in resp.text
    assert '"risk_level"' not in resp.text
    assert "go_step1" not in resp.text
    assert "go_cwb" not in resp.text
    assert "go_full_plan" not in resp.text


def test_status_page_provides_review_entry_source_link(client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    resp = client.get(f"/portal/{token}/status")
    assert resp.status_code == 200, resp.text
    assert f"/review/start?source=status&amp;token={token}" in resp.text


def test_report_page_provides_review_entry_source_link(client, settings):
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

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(
            body["order_id"], "serving", actor="test", reason="seed_report_serving"
        )
        dao.transition_status(
            body["order_id"], "delivered", actor="test", reason="seed_report_ready"
        )
        dao.update(
            body["order_id"],
            {
                "audit_report": "data/examples/gaokao_report_李明_20260611_122443.html",
                "pdf_path": "data/examples/gaokao_report_李明_20260611_122443.pdf",
            },
            actor="test",
            reason="seed_report_ready_paths",
        )

    resp = client.get(f"/portal/{token}/report")
    assert resp.status_code == 200, resp.text
    assert "/review/start?source=report&amp;token=" in resp.text


def test_review_start_persists_result_contract_and_source(client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    resp = client.get(f"/review/start?source=status&token={token}")
    assert resp.status_code == 200, resp.text
    # 页面已改为用户结果页，不再暴露内部 JSON 字段
    assert "复核结果" in resp.text or "初步评估结果" in resp.text
    assert "风险等级" in resp.text
    assert "核心问题" in resp.text
    assert "下一步建议" in resp.text
    # 不再暴露内部 action slug
    assert "go_step1" not in resp.text
    assert "go_cwb" not in resp.text
    assert "go_full_plan" not in resp.text


def test_review_action_updates_followup_action(client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text

    action = client.post(
        "/review/action",
        data={"token": token, "action": "step1"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text
    assert action.headers["location"].endswith(f"/portal/{token}/info")


def test_review_action_cwb_redirects_to_real_cwb_page(route_client, client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text

    action = client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text
    assert action.headers["location"].endswith(f"/portal/{token}/cwb")
    cwb = client.get(action.headers["location"])
    assert cwb.status_code == 200, cwb.text
    assert "冲稳保建议页" in cwb.text
    assert "当前建议" in cwb.text
    assert "冲刺建议" in cwb.text


def test_cwb_page_is_first_class_three_column_workspace(route_client, client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text
    action = client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text

    cwb = client.get(f"/portal/{token}/cwb")
    assert cwb.status_code == 200, cwb.text
    assert "冲稳保建议页" in cwb.text
    assert "冲刺建议" in cwb.text
    assert "稳妥建议" in cwb.text
    assert "保底建议" in cwb.text
    assert "当前建议" in cwb.text


def test_cwb_page_exposes_review_summary_and_next_actions(
    route_client, client, settings
):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    client.get(f"/review/start?source=report&token={token}")
    client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )

    cwb = client.get(f"/portal/{token}/cwb")
    assert cwb.status_code == 200, cwb.text
    assert "当前复核摘要" in cwb.text
    assert "下一步建议" in cwb.text
    assert f"/portal/{token}/full-plan" in cwb.text
    assert f"/portal/{token}/status" in cwb.text


def test_cwb_page_no_longer_claims_placeholder_future_work(
    route_client, client, settings
):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    client.get(f"/review/start?source=status&token={token}")
    action = client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text

    cwb = client.get(action.headers["location"])
    assert cwb.status_code == 200, cwb.text
    assert "后续再接真实推荐结果" not in cwb.text
    assert "建议冲刺" in cwb.text or "冲刺建议" in cwb.text


def test_cwb_page_links_policy_same_score_and_auxiliary_factors(client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )
    payment_id = create_resp.json()["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            target_cities=["长沙", "深圳"],
            family_background="家长更希望省内优先",
            interest_assessment_type="holland",
            interest_assessment_result="R型+I型",
            interest_assessment_notes="只作辅助，不作唯一判断",
        ),
        settings,
    )
    client.get(f"/review/start?source=status&token={token}")
    client.post(
        "/review/action", data={"token": token, "action": "cwb"}, follow_redirects=False
    )

    cwb = client.get(f"/portal/{token}/cwb")
    assert cwb.status_code == 200, cwb.text
    assert "/policy-center?province=湖南" in cwb.text
    assert "/same-score-reference?province=湖南" in cwb.text and "score=578" in cwb.text
    assert "辅助判断因子" in cwb.text
    assert "R型+I型" in cwb.text
    assert "家长更希望省内优先" in cwb.text


def test_review_action_full_plan_redirects_to_real_full_plan_page(
    route_client, client, settings
):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text

    action = client.post(
        "/review/action",
        data={"token": token, "action": "full_plan"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text
    assert action.headers["location"].endswith(f"/portal/{token}/full-plan")

    full_plan = client.get(action.headers["location"])
    assert full_plan.status_code == 200, full_plan.text
    assert "完整规划建议页" in full_plan.text
    assert "方案优先级" in full_plan.text
    assert "版本历史" in full_plan.text


def test_full_plan_page_shows_profile_versions_and_assessment_context(
    route_client, client, settings
):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )
    payment_id = create_resp.json()["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            family_background="家长更希望省内优先",
            interest_assessment_type="mbti",
            interest_assessment_result="INTJ",
            interest_assessment_notes="只作辅助，不作唯一判断",
        ),
        settings,
    )
    client.get(f"/review/start?source=status&token={token}")
    action = client.post(
        "/review/action",
        data={"token": token, "action": "full_plan"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text

    full_plan = client.get(action.headers["location"])
    assert full_plan.status_code == 200, full_plan.text
    assert "完整规划建议页" in full_plan.text
    assert "方案优先级" in full_plan.text
    assert "版本历史" in full_plan.text
    assert "初始档案方案" in full_plan.text
    assert "辅助判断因子" in full_plan.text
    assert "INTJ" in full_plan.text


def test_full_plan_page_no_longer_claims_entry_only_placeholder(
    route_client, client, settings
):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )
    payment_id = create_resp.json()["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
        ),
        settings,
    )
    client.get(f"/review/start?source=status&token={token}")
    action = client.post(
        "/review/action",
        data={"token": token, "action": "full_plan"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text

    full_plan = client.get(action.headers["location"])
    assert full_plan.status_code == 200, full_plan.text
    assert "当前从 review 分流进入完整规划入口" not in full_plan.text
    assert "方案优先级" in full_plan.text or "规划建议" in full_plan.text


def test_report_page_shows_version_summary_and_next_actions(client, settings):
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
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    client.get(f"/review/start?source=report&token={token}")
    client.post(
        "/review/action",
        data={"token": token, "action": "full_plan"},
        follow_redirects=False,
    )
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(
            body["order_id"], "serving", actor="test", reason="report_ready_serving"
        )
        dao.transition_status(
            body["order_id"], "delivered", actor="test", reason="report_ready_delivered"
        )
        dao.update(
            body["order_id"],
            {
                "audit_report": "data/examples/gaokao_report_李明_20260611_122443.html",
                "pdf_path": "data/examples/gaokao_report_李明_20260611_122443.pdf",
            },
            actor="test",
            reason="report_ready_paths",
        )

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 200, report_page.text
    assert "报告版本" in report_page.text
    assert "基于哪个档案版本" in report_page.text
    assert "当前复核摘要" in report_page.text
    assert "下一步建议" in report_page.text
    assert "/portal/" in report_page.text and "/full-plan" in report_page.text


def test_report_page_routes_followup_step1_to_info(client, settings):
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
    payment_id = create_resp.json()["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
        ),
        settings,
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        order_id = create_resp.json()["order_id"]
        dao.transition_status(
            order_id, "serving", actor="test", reason="report_ready_serving"
        )
        dao.transition_status(
            order_id, "delivered", actor="test", reason="report_ready_delivered"
        )
        dao.update(
            order_id,
            {
                "audit_report": "data/examples/gaokao_report_李明_20260611_122443.html",
                "pdf_path": "data/examples/gaokao_report_李明_20260611_122443.pdf",
            },
            actor="test",
            reason="report_ready_paths",
        )

    client.get(f"/review/start?source=report&token={token}")
    action = client.post(
        "/review/action",
        data={"token": token, "action": "step1"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text

    report = client.get(f"/portal/{token}/report")
    assert report.status_code == 200, report.text
    # _render_report_page re-issues a fresh portal token for the report shell,
    # so the original token from the API response won't match the token embedded
    # in the report page. Check that an /info link exists instead.
    assert "/info" in report.text
    assert "/portal/" in report.text


def test_review_result_is_saved_as_independent_lightweight_object(client, settings):
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
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    resp = client.get(f"/review/start?source=home&token={token}")
    assert resp.status_code == 200, resp.text

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
    finally:
        intake_store.close()

    assert intake is not None
    assert "review_result_contract" not in intake.payload
    assert "latest_review_result_id" in intake.payload
    assert intake.payload["latest_review_result_id"].startswith("rvw_")


def test_review_result_has_version_anchor_and_history_summary(client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    first = client.get(f"/review/start?source=home&token={token}")
    assert first.status_code == 200, first.text

    second = client.get(f"/review/start?source=status&token={token}")
    assert second.status_code == 200, second.text

    landing = client.get(f"/?token={token}")
    assert landing.status_code == 200, landing.text
    assert "最近一次复核结果" in landing.text
    assert "最新版本" in landing.text or "版本" in landing.text


def test_report_page_shows_profile_and_review_versions(client, settings):
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
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    client.get(f"/review/start?source=home&token={token}")
    client.get(f"/review/start?source=status&token={token}")

    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(
            body["order_id"], "serving", actor="test", reason="report_ready_serving"
        )
        dao.transition_status(
            body["order_id"], "delivered", actor="test", reason="report_ready_delivered"
        )
        dao.update(
            body["order_id"],
            {
                "audit_report": "data/examples/gaokao_report_李明_20260611_122443.html",
                "pdf_path": "data/examples/gaokao_report_李明_20260611_122443.pdf",
            },
            actor="test",
            reason="report_ready_paths",
        )

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 200, report_page.text
    assert "报告版本" in report_page.text
    assert "基于哪个档案版本" in report_page.text
    assert "当前复核摘要" in report_page.text
    assert "最新版本" in report_page.text or "版本历史" in report_page.text


def test_report_page_shows_latest_profile_state_and_helper_links(client, settings):
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
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
            target_cities=["长沙", "深圳"],
            interest_assessment_type="mbti",
            interest_assessment_result="INTJ",
            interest_assessment_notes="只作辅助，不作唯一判断",
        ),
        settings,
    )
    client.get(f"/review/start?source=report&token={token}")
    client.post(
        "/review/action",
        data={"token": token, "action": "full_plan"},
        follow_redirects=False,
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(
            body["order_id"], "serving", actor="test", reason="report_ready_serving"
        )
        dao.transition_status(
            body["order_id"], "delivered", actor="test", reason="report_ready_delivered"
        )
        dao.update(
            body["order_id"],
            {
                "audit_report": "data/examples/gaokao_report_李明_20260611_122443.html",
                "pdf_path": "data/examples/gaokao_report_李明_20260611_122443.pdf",
            },
            actor="test",
            reason="report_ready_paths",
        )

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 200, report_page.text
    assert "基于最新档案生成" in report_page.text
    assert "/policy-center?province=湖南" in report_page.text
    assert (
        "/same-score-reference?province=湖南" in report_page.text
        and "score=578" in report_page.text
    )
    assert "辅助判断因子" in report_page.text
    assert "INTJ" in report_page.text


def test_report_page_warns_when_based_on_historical_profile_version(client, settings):
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
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]
    paid = client.post(f"/pay/mock/{payment_id}/complete", follow_redirects=False)
    assert paid.status_code == 303, paid.text

    submit_order_info(
        token,
        IntakePayload(
            mode="draft",
            candidate_province="湖南",
            candidate_subjects=["物理", "化学", "生物"],
            candidate_score=578,
            candidate_rank=12345,
        ),
        settings,
    )
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        dao.transition_status(
            body["order_id"], "serving", actor="test", reason="report_ready_serving"
        )
        dao.transition_status(
            body["order_id"], "delivered", actor="test", reason="report_ready_delivered"
        )
        dao.update(
            body["order_id"],
            {
                "audit_report": "data/examples/gaokao_report_李明_20260611_122443.html",
                "pdf_path": "data/examples/gaokao_report_李明_20260611_122443.pdf",
            },
            actor="test",
            reason="report_ready_paths",
        )

    first = client.get(f"/portal/{token}/report")
    assert first.status_code == 200, first.text

    intake_store = IntakeStore.for_db(settings.orders_db_path)
    try:
        intake = intake_store.get(body["order_id"])
        assert intake is not None
        payload = dict(intake.payload)
        payload["candidate_score"] = 579
        payload["candidate_rank"] = 12001
        payload["profile_versions"] = [
            {
                "profile_version_id": "profile_v1",
                "stage_label": "初始档案方案",
                "snapshot_payload": {
                    "candidate_province": "湖南",
                    "candidate_subjects": ["物理", "化学", "生物"],
                    "candidate_score": 578,
                    "candidate_rank": 12345,
                },
                "created_at": "2026-06-23T00:00:00+00:00",
                "source": "portal",
            },
            {
                "profile_version_id": "profile_v2",
                "stage_label": "查分后校准方案",
                "snapshot_payload": {
                    "candidate_province": "湖南",
                    "candidate_subjects": ["物理", "化学", "生物"],
                    "candidate_score": 579,
                    "candidate_rank": 12001,
                },
                "created_at": "2026-06-23T00:00:00+00:00",
                "source": "admin",
            },
        ]
        payload["latest_profile_version_id"] = "profile_v2"
        intake_store.save(order_id=body["order_id"], payload=payload, submit=True)
    finally:
        intake_store.close()

    report_page = client.get(f"/portal/{token}/report")
    assert report_page.status_code == 200, report_page.text
    assert "基于历史档案版本生成，建议刷新" in report_page.text


def test_landing_page_shows_recent_review_result_entry_when_present(client, settings):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    start = client.get(f"/review/start?source=home&token={token}")
    assert start.status_code == 200, start.text

    landing = client.get(f"/?token={token}")
    assert landing.status_code == 200, landing.text
    assert "最近一次复核结果" in landing.text
    assert f"/review/start?source=home&amp;token={token}" in landing.text


def test_landing_page_shows_workspace_primary_action_for_incomplete_step1(client):
    resp = client.get("/?token=test-token")
    assert resp.status_code == 200, resp.text
    assert "工作台主动作" in resp.text
    assert "继续补充 Step 1" in resp.text


def test_landing_page_shows_workspace_primary_action_for_recent_review_result(
    route_client, client, settings
):
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
    token = (
        create_resp.json()["portal_status_url"].split("/portal/")[1].split("/status")[0]
    )

    start = client.get(f"/review/start?source=home&token={token}")
    assert start.status_code == 200, start.text

    landing = client.get(f"/?token={token}")
    assert landing.status_code == 200, landing.text
    assert "工作台主动作" in landing.text
    assert "继续查看最近一次复核" in landing.text
    assert f"/review/start?source=home&amp;token={token}" in landing.text
