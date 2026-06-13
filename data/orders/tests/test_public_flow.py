from __future__ import annotations

from data.orders.dao import OrdersDAO
from data.orders.public_flow import PublicOrderCreate, create_public_order


def test_create_public_order_defaults_to_web_pending(tmp_path, monkeypatch):
    monkeypatch.setenv("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-web-self-service")
    with OrdersDAO.connect(tmp_path / "orders.db") as dao:
        order = create_public_order(
            dao,
            PublicOrderCreate(
                service_version="standard",
                amount_cents=9900,
                customer_name="张家长",
                customer_phone="13800138000",
                candidate_name="张三",
                candidate_province="湖南",
            ),
        )

        assert order.source == "web"
        assert order.status == "pending"
        assert order.service_version == "standard"
        assert order.amount_cents == 9900
        assert order.customer_phone_hash is not None
        saved = dao.get(order.id)
        assert saved.customer_name == "张家长"
        assert saved.candidate_name == "张三"


def test_create_public_order_requires_contact_channel(tmp_path):
    with OrdersDAO.connect(tmp_path / "orders.db") as dao:
        try:
            create_public_order(
                dao,
                PublicOrderCreate(
                    service_version="audit",
                    amount_cents=4900,
                    customer_name="李家长",
                    candidate_province="广东",
                ),
            )
        except ValueError as exc:
            assert "customer_phone / customer_wechat 至少填写一个" in str(exc)
        else:
            raise AssertionError("expected ValueError for missing contact channel")
