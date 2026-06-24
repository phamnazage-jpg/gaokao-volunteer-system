from __future__ import annotations

from fastapi.testclient import TestClient


def test_alipay_sim_public_user_e2e_flow(tmp_path, monkeypatch):
    admin_db = tmp_path / "admin.db"
    orders_db = tmp_path / "orders.db"
    share_db = tmp_path / "share.db"
    share_reports = tmp_path / "share_reports"
    share_reports.mkdir()

    monkeypatch.setenv("GAOKAO_ENV", "dev")
    monkeypatch.setenv("GAOKAO_DB_PATH", str(admin_db))
    monkeypatch.setenv("GAOKAO_ORDERS_DB_PATH", str(orders_db))
    monkeypatch.setenv("GAOKAO_SHARE_DB_PATH", str(share_db))
    monkeypatch.setenv("GAOKAO_SHARE_REPORT_DIR", str(share_reports))
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_JWT_EXP_MIN", "5")
    monkeypatch.setenv("GAOKAO_ADMIN_USER", "admin")
    monkeypatch.setenv("GAOKAO_ADMIN_PASS", "test-pass-123")
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "alipay_sim")
    monkeypatch.setenv("GAOKAO_PAYMENT_BASE_URL", "http://testserver")
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "alipay-sim-secret")

    from admin.app import create_app
    from admin.config import load_settings
    from data.orders.dao import OrdersDAO
    from data.orders.intake_store import IntakeStore

    settings = load_settings()
    app = create_app(settings)

    with TestClient(app) as client:
        create_resp = client.post(
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
        assert create_resp.status_code == 201, create_resp.text
        created = create_resp.json()
        assert created["checkout_url"].startswith("/pay/alipay-sim/")

        payment_id = created["checkout_url"].split("/pay/alipay-sim/")[1].split("?")[0]
        portal_status_url = created["portal_status_url"]
        portal_info_url = created["portal_info_url"]
        token = portal_status_url.split("/portal/")[1].split("/status")[0]

        checkout_page = client.get(created["checkout_url"])
        assert checkout_page.status_code == 200, checkout_page.text
        assert "支付宝模拟收银台" in checkout_page.text

        before_pay_status = client.get(portal_status_url)
        assert before_pay_status.status_code == 200, before_pay_status.text
        assert "待支付" in before_pay_status.text

        pay_resp = client.post(
            f"/pay/alipay-sim/{payment_id}/complete",
            follow_redirects=False,
        )
        assert pay_resp.status_code == 303, pay_resp.text
        # After successful payment, the gateway now lands users on an
        # intermediate "payment-success" page that explains next steps
        # before they continue to the live status view. Redirect token
        # may be freshly signed, so only assert the route shape and then
        # follow the concrete redirected location.
        success_path = pay_resp.headers["location"]
        assert success_path.startswith("/portal/")
        assert success_path.endswith("/payment-success")
        success_page = client.get(success_path)
        assert success_page.status_code == 200, success_page.text
        assert "支付成功" in success_page.text

        after_pay_status = client.get(portal_status_url)
        assert after_pay_status.status_code == 200, after_pay_status.text
        assert "待填写资料" in after_pay_status.text

        info_page = client.get(portal_info_url)
        assert info_page.status_code == 200, info_page.text
        assert "考生资料填写" in info_page.text

        submit_info = client.post(
            portal_info_url,
            json={
                "mode": "submit",
                "candidate_province": "湖南",
                "candidate_score": 578,
                "candidate_rank": 12034,
                "candidate_subjects": ["物理", "化学", "生物"],
                "candidate_interests": "计算机",
                "guardian_notes": "更看重省内城市",
                "consent_version": "t12-web-mvp-v1",
                "consent_scope": "web-self-service-order-intake",
                "privacy_accepted": True,
                "service_terms_accepted": True,
                "guardian_confirmed": True,
            },
        )
        assert submit_info.status_code == 200, submit_info.text
        assert submit_info.json()["stage"] == "processing"

        with OrdersDAO.connect(settings.orders_db_path) as dao:
            order = dao.get(created["order_id"])
            report_path = share_reports / "report.html"
            pdf_path = share_reports / "report.pdf"
            report_path.write_text(
                "<h1>志愿方案报告</h1><p>已生成。</p>", encoding="utf-8"
            )
            pdf_path.write_bytes(b"%PDF-1.4\nalipay-sim-report\n")
            dao.update(
                order.id,
                {"audit_report": str(report_path), "pdf_path": str(pdf_path)},
                actor="test",
                reason="attach_report",
            )
            dao.transition_status(
                order.id, "delivered", actor="test", reason="report_ready"
            )

        report_status = client.get(portal_status_url)
        assert report_status.status_code == 200, report_status.text
        assert "报告已就绪" in report_status.text

        report_view = client.get(f"/portal/{token}/report")
        assert report_view.status_code == 200, report_view.text
        assert "志愿方案报告" in report_view.text

        report_pdf = client.get(f"/portal/{token}/report.pdf")
        assert report_pdf.status_code == 200, report_pdf.text
        assert report_pdf.headers["content-type"].startswith("application/pdf")

        intake = IntakeStore.for_db(settings.orders_db_path)
        try:
            record = intake.get(created["order_id"])
        finally:
            intake.close()
        assert record is not None
        assert record.status == "submitted"
