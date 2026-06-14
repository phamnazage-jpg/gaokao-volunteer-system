"""用户端 Web 自助入口页面测试（T12.2/T12.3）。"""

from __future__ import annotations


def test_public_landing_page_served(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "高考志愿填报智能系统" in body
    assert "用户端 Web 自助服务" in body
    assert 'href="/pricing"' in body
    assert "49元 AI方案审核" in body


def test_public_pricing_page_served(client):
    resp = client.get("/pricing")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "服务套餐" in body
    assert "49元 AI方案审核" in body
    assert "99元 完整志愿方案" in body
    assert "199元 深度辅导版" in body
    assert 'data-package="audit"' in body
    assert 'data-package="standard"' in body
    assert 'data-package="premium"' in body
    assert "支付接入建设中" in body


def test_public_create_order_endpoint(client):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_name": "张三",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["order_id"].startswith("GKO-")
    assert body["source"] == "web"
    assert body["status"] == "pending"
    assert body["service_version"] == "standard"
    assert body["amount_cents"] == 9900
    assert body["next_step"] == "payment"
    assert body["checkout_url"].startswith("/pay/mock/")
    assert "/portal/" in body["portal_status_url"]


def test_public_create_order_rejects_missing_contact(client):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "audit",
            "amount_cents": 4900,
            "customer_name": "李家长",
            "candidate_province": "广东",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert (
        body["detail"]["fields"][0]["reason"]
        == "Value error, customer_phone / customer_wechat 至少填写一个"
    )


def test_public_create_order_rejects_price_tampering(client):
    resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 1,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_province": "湖南",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "请求数据未通过校验"
    assert (
        body["detail"]["fields"][0]["reason"]
        == "Value error, amount_cents 与套餐价格不一致"
    )


def test_mock_payment_complete_rejects_wrong_portal_token(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    payment_id = body["checkout_url"].split("/pay/mock/")[1].split("?")[0]

    resp = client.post(f"/pay/mock/{payment_id}/complete?token=wrong-token")
    assert resp.status_code == 401 or resp.status_code == 403


def test_payment_return_redirects_to_portal_status(client):
    create_resp = client.post(
        "/api/public/orders",
        json={
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_name": "张家长",
            "customer_phone": "13800138000",
            "candidate_province": "湖南",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    token = body["portal_status_url"].split("/portal/")[1].split("/status")[0]

    resp = client.get(f"/portal/payment-return?token={token}", follow_redirects=False)
    assert resp.status_code == 303, resp.text
    assert resp.headers["location"] == f"/portal/{token}/status"
