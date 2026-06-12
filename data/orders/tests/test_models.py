"""models 模块集成测试（Order dataclass + 加解密串联）。"""

import os
import json


os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-unit-tests")

from data.orders.models import Order, generate_order_id, utc_now_iso
from data.orders.crypto import decrypt, hash_for_index


def setup_function(_):
    from data.orders import crypto

    crypto.get_fernet.cache_clear()


def test_generate_order_id_format():
    oid = generate_order_id()
    assert oid.startswith("GKO-")
    parts = oid.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 4


def test_order_auto_derives_phone_hash():
    order = Order(
        id="GKO-20260612-AAAA",
        source="web",
        service_version="basic",
        amount_cents=1000,
        customer_phone="13800001234",
    )
    assert order.customer_phone_hash == hash_for_index("13800001234")


def test_order_to_db_row_encrypts_phone():
    order = Order(
        id="GKO-20260612-AAAB",
        source="web",
        service_version="basic",
        amount_cents=1000,
        customer_phone="13800001234",
    )
    row = order.to_db_row()
    # 明文不出现在 DB 行
    assert "customer_phone" not in row or row.get("customer_phone") is None
    # 加密字段存在
    assert "customer_phone_enc" in row
    assert row["customer_phone_enc"] != "13800001234"
    # hash 字段保留
    assert row["customer_phone_hash"] == hash_for_index("13800001234")
    # 密文可解
    assert decrypt(row["customer_phone_enc"]) == "13800001234"


def test_order_to_db_row_encrypts_id_card():
    order = Order(
        id="GKO-20260612-AAAC",
        source="web",
        service_version="basic",
        amount_cents=1000,
        candidate_id_card="430102200501011234",
    )
    row = order.to_db_row()
    assert "candidate_id_card_enc" in row
    assert "candidate_id_card" not in row or row.get("candidate_id_card") is None
    assert decrypt(row["candidate_id_card_enc"]) == "430102200501011234"


def test_order_from_db_row_decrypts():
    """模拟数据库往返：to_db_row → 模拟 DB 读取 → from_db_row。"""
    order_in = Order(
        id="GKO-20260612-AAAD",
        source="xianyu",
        external_id="EXT-X",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张*",
        customer_phone="13800001234",
        candidate_name="张同学",
        candidate_province="湖南",
        candidate_score=578,
        candidate_subjects=["物理", "化学", "生物"],
        tags=["高优", "VIP"],
    )
    row = order_in.to_db_row()
    order_out = Order.from_db_row(row)
    assert order_out.customer_phone == "13800001234"
    assert order_out.customer_name == "张*"
    assert order_out.candidate_province == "湖南"
    assert order_out.candidate_subjects == ["物理", "化学", "生物"]
    assert order_out.tags == ["高优", "VIP"]


def test_order_to_dict_decrypt_sensitive_true():
    order = Order(
        id="GKO-20260612-AAAE",
        source="web",
        service_version="basic",
        customer_phone="13800001234",
        candidate_id_card="430102200501011234",
    )
    d = order.to_dict(decrypt_sensitive=True)
    assert d["customer_phone"] == "13800001234"
    assert d["candidate_id_card"] == "430102200501011234"


def test_order_to_dict_decrypt_sensitive_false():
    order = Order(
        id="GKO-20260612-AAAF",
        source="web",
        service_version="basic",
        customer_phone="13800001234",
        candidate_id_card="430102200501011234",
    )
    d = order.to_dict(decrypt_sensitive=False)
    assert "customer_phone" not in d
    assert "candidate_id_card" not in d
    assert "customer_phone_hash" in d


def test_order_default_timestamps():
    order = Order(
        id="GKO-20260612-AAAG",
        source="web",
        service_version="basic",
    )
    assert order.created_at is not None
    assert order.status_updated_at == order.created_at


def test_order_tags_json_serializable():
    """to_db_row 后 tags 为 JSON 字符串。"""
    order = Order(
        id="GKO-20260612-AAAH",
        source="web",
        service_version="basic",
        tags=["a", "b"],
    )
    row = order.to_db_row()
    # 重新解析应能还原
    parsed = json.loads(row["tags"])
    assert parsed == ["a", "b"]


def test_utc_now_iso_is_iso8601():
    ts = utc_now_iso()
    assert "T" in ts
    assert ts.endswith("+00:00") or ts.endswith("Z")
