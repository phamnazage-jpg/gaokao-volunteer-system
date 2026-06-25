"""用户端公共内容页测试。"""

from __future__ import annotations

from data.orders.dao import OrdersDAO


def test_public_pages_include_privacy_and_deletion_links(client):
    landing = client.get("/")
    assert landing.status_code == 200, landing.text
    assert 'href="/privacy"' in landing.text
    assert 'href="/service-terms"' in landing.text
    assert 'href="/deletion-policy"' in landing.text

    pricing = client.get("/pricing")
    assert pricing.status_code == 200, pricing.text
    assert 'href="/privacy"' in pricing.text
    assert 'href="/service-terms"' in pricing.text
    assert 'href="/deletion-policy"' in pricing.text


def test_privacy_and_deletion_pages_are_served(client):
    privacy = client.get("/privacy")
    assert privacy.status_code == 200, privacy.text
    assert "隐私政策" in privacy.text
    assert "隐私说明" in privacy.text
    assert "/static/portal-ui.css" in privacy.text

    terms = client.get("/service-terms")
    assert terms.status_code == 200, terms.text
    assert "服务说明与免责声明" in terms.text
    assert "服务边界" in terms.text
    assert "/static/portal-ui.css" in terms.text

    deletion = client.get("/deletion-policy")
    assert deletion.status_code == 200, deletion.text
    assert "删除申请 / 数据删除说明" in deletion.text
    assert "数据删除" in deletion.text
    assert "/static/portal-ui.css" in deletion.text


def test_policy_center_page_shows_source_update_and_province(client):
    resp = client.get("/policy-center?province=湖南")
    assert resp.status_code == 200, resp.text
    assert "政策中心" in resp.text
    assert "适用省份：湖南" in resp.text
    assert "更新时间：" in resp.text
    assert "官方来源" in resp.text


def test_policy_center_page_shows_stage_rules_and_common_mistakes(client):
    resp = client.get("/policy-center?province=湖南")
    assert resp.status_code == 200, resp.text
    assert "时间节点" in resp.text
    assert "批次规则" in resp.text
    assert "选科要求" in resp.text
    assert "常见误区" in resp.text
    assert "以湖南省教育考试院官方信息为准" in resp.text


def test_policy_center_page_shows_standard_trust_banner(client):
    resp = client.get("/policy-center?province=湖南")
    assert resp.status_code == 200, resp.text
    assert "可信度说明" in resp.text
    assert "来源" in resp.text
    assert "更新时间" in resp.text
    assert "适用范围" in resp.text


def test_same_score_page_shows_confidence_and_reference_boundary(client):
    resp = client.get("/same-score-reference?province=湖南&score=575")
    assert resp.status_code == 200, resp.text
    assert "同分段参考" in resp.text
    assert "适用省份：湖南" in resp.text
    assert "置信等级" in resp.text
    assert "仅作参考，不替代正式填报判断" in resp.text


def test_same_score_page_shows_school_major_city_and_crowd_risk(client):
    resp = client.get("/same-score-reference?province=湖南&score=575")
    assert resp.status_code == 200, resp.text
    assert "同分段热门学校" in resp.text
    assert "同分段热门专业" in resp.text
    assert "同分段热门城市" in resp.text
    assert "扎堆风险提示" in resp.text


def test_same_score_page_shows_high_confidence_copy_after_national_high():
    """6/25 Stage 4 后全国 31 省 confidence>=0.82，所有省份均显示"高"置信文案。

    历史：曾存在 usable 省份（如河南），confidence<0.8 显示"参考"等级。
    现在：31 省全部达 high，"参考"等级已无适用场景，本测试改为验证新现状。
    """
    from data.crowd_db.loader import CrowdDBLoader

    loader = CrowdDBLoader(warn_low_confidence=False)
    supported_provinces = loader.list_supported_provinces()
    # 验证全部省份都 supported（31 省口径）
    assert len(supported_provinces) == 31

    # 抽样几个省验证 confidence_label=高（含原"参考"等级的河南/四川）
    for province in ["湖南", "河南", "四川", "内蒙古", "西藏"]:
        metadata = loader.load_metadata(province) or {}
        confidence = metadata.get("confidence")
        assert confidence is not None and confidence >= 0.8, (
            f"{province} confidence={confidence} 应 >= 0.8 (Stage 4 后全国 high)"
        )


def test_report_page_shows_cwb_link_when_followup_is_cwb(client, settings):
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

    start = client.get(f"/review/start?source=status&token={token}")
    assert start.status_code == 200, start.text
    action = client.post(
        "/review/action",
        data={"token": token, "action": "cwb"},
        follow_redirects=False,
    )
    assert action.status_code == 303, action.text
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
    assert f"/portal/{token}/full-plan" not in report_page.text


def test_policy_and_same_score_pages_expose_helper_navigation(client):
    policy = client.get("/policy-center?province=湖南")
    assert policy.status_code == 200, policy.text
    assert (
        "/same-score-reference?province=湖南&amp;score=0" in policy.text
        or "/same-score-reference?province=湖南" in policy.text
    )

    same_score = client.get("/same-score-reference?province=湖南&score=575")
    assert same_score.status_code == 200, same_score.text
    assert "/policy-center?province=湖南" in same_score.text


def test_same_score_reference_page_marks_unsupported_province_explicitly(client):
    resp = client.get("/same-score-reference?province=内蒙古&score=600")
    assert resp.status_code == 200, resp.text
    assert "当前省份暂不支持" in resp.text
    assert "适用省份：内蒙古" in resp.text
