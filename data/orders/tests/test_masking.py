"""masking 模块单元测试 (T11.2).

覆盖：
- 各 mask 函数的正常路径与边界（None / 空串 / 非字符串 / 非标准长度）
- Order.to_dict 的 mask 模式串联通路
- 默认安全：未知 decrypt_sensitive 值回退 mask 而非明文
"""

from __future__ import annotations

import os

os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-unit-tests")

from data.orders.models import Order
from data.orders.masking import (
    mask_id_card,
    mask_name,
    mask_phone,
    mask_sensitive_dict,
    mask_wechat,
)


# ---------------------- mask_phone ----------------------


def test_mask_phone_standard_11_digits():
    assert mask_phone("13800001234") == "138****1234"


def test_mask_phone_strip_prefix_and_separator():
    assert mask_phone("+86 138-0000-1234") == "138****1234"
    assert mask_phone(" 13800001234 ") == "138****1234"


def test_mask_phone_none_returns_none():
    assert mask_phone(None) is None


def test_mask_phone_empty_returns_empty():
    assert mask_phone("") == ""
    assert mask_phone("   ") == ""


def test_mask_phone_non_string_returns_none():
    assert mask_phone(13800001234) is None  # type: ignore[arg-type]
    assert mask_phone(["13800001234"]) is None  # type: ignore[arg-type]


def test_mask_phone_short_falls_back_to_partial_mask():
    """7 位临界值:走遮罩(至少 1 个 *),8-10 位类似。"""
    out7: str = mask_phone("1234567") or ""  # type: ignore[assignment]
    assert out7.startswith("123")
    assert out7.endswith("4567")
    assert "*" in out7
    # 6 位及以下 — 长度不足,原样返回
    assert mask_phone("123456") == "123456"


def test_mask_phone_keeps_non_standard_length_prefix_suffix():
    """长度 >= 7 但不是 11 位（如带分机 12 位）也走遮罩 — 至少遮 1 个 *。"""
    # 12 位带分机号 — 至少 1 个 *，前 3 后 4 保留
    out: str = mask_phone("138000012345") or ""  # type: ignore[assignment]
    assert out.startswith("138*")
    assert out.endswith("2345")
    assert "*" in out


# ---------------------- mask_id_card ----------------------


def test_mask_id_card_18_digits_keeps_district_and_tail():
    assert mask_id_card("430102200501011234") == "430102********1234"


def test_mask_id_card_18_with_x_checksum_lowercased_ok():
    """末位 X/x 视为合法的身份证校验位 — 遮罩保留末 4 位（含 X）。"""
    assert mask_id_card("43010220050101123X") == "430102********123X"


def test_mask_id_card_15_legacy_format():
    assert mask_id_card("430102050101123") == "430102******123"


def test_mask_id_card_none_returns_none():
    assert mask_id_card(None) is None


def test_mask_id_card_empty_returns_empty():
    assert mask_id_card("") == ""
    assert mask_id_card("   ") == ""


def test_mask_id_card_non_string_returns_none():
    assert mask_id_card(123) is None  # type: ignore[arg-type]


def test_mask_id_card_short_below_threshold_unchanged():
    """< 13 位视为非身份证 — 原样返回,避免误遮短串。"""
    assert mask_id_card("4301021234") == "4301021234"
    assert mask_id_card("12345") == "12345"


def test_mask_id_card_non_standard_length_partial_mask():
    """13-14 位非标准长度:前 6 后 4 保留,中段至少 2 个 *。"""
    out: str = mask_id_card("4301022005011") or ""  # type: ignore[assignment]  # 13 位
    assert out.startswith("430102")
    assert out.endswith("5011")  # 末 4 位
    assert "*" in out


# ---------------------- mask_name ----------------------


def test_mask_name_one_char_unchanged():
    assert mask_name("张") == "张"


def test_mask_name_two_chars_surname_plus_star():
    assert mask_name("张三") == "张*"


def test_mask_name_three_chars_surname_given_name_partial():
    """3 字姓名 → 姓 + 1 个 * + 名末字（如"张三丰" → "张*丰"）。"""
    assert mask_name("张三丰") == "张*丰"


def test_mask_name_four_chars_collapsed_to_surname_two_stars():
    """4+ 字姓名 → 姓 + 2 个 *（不暴露名长度信息）。"""
    assert mask_name("欧阳明月") == "欧**"
    assert mask_name("上官婉儿") == "上**"


def test_mask_name_none_returns_none():
    assert mask_name(None) is None


def test_mask_name_empty_returns_empty():
    assert mask_name("") == ""
    assert mask_name("   ") == ""


def test_mask_name_english_fully_masked():
    assert mask_name("Alice") == "*****"
    assert mask_name("Bo") == "**"


def test_mask_name_mixed_chinese_and_digits_treats_as_non_cjk():
    """含非中日韩字符 → 全遮，不暴露字符数。"""
    assert mask_name("张3") == "**"
    assert mask_name("John 张") == "******"  # 6 字符全遮


# ---------------------- mask_sensitive_dict ----------------------


def test_mask_wechat_keeps_prefix_suffix():
    assert mask_wechat("wx-li") == "wx*li"
    assert mask_wechat("wechat_user") == "we*******er"


def test_mask_wechat_none_and_empty_are_safe():
    assert mask_wechat(None) is None
    assert mask_wechat("") == ""
    assert mask_wechat("ab") == "**"


def test_mask_sensitive_dict_handles_all_known_fields():
    data = {
        "customer_phone": "13800001234",
        "candidate_id_card": "430102200501011234",
        "customer_name": "张三",
        "customer_wechat": "wx-li",
        "candidate_name": "李四光",
        "customer_phone_hash": "abc",
        "amount_cents": 1000,
    }
    out = mask_sensitive_dict(data)
    assert out["customer_phone"] == "138****1234"
    assert out["candidate_id_card"] == "430102********1234"
    assert out["customer_name"] == "张*"
    assert out["customer_wechat"] == "wx*li"
    assert out["candidate_name"] == "李*光"  # 3 字姓名 → 姓 + * + 名末字
    assert out["customer_phone_hash"] == "abc"
    assert out["amount_cents"] == 1000


def test_mask_sensitive_dict_keeps_none_fields_none():
    data = {"customer_phone": None, "candidate_id_card": None}
    out = mask_sensitive_dict(data)
    assert out["customer_phone"] is None
    assert out["candidate_id_card"] is None


def test_mask_sensitive_dict_does_not_mutate_input():
    data = {"customer_phone": "13800001234"}
    out = mask_sensitive_dict(data)
    assert data["customer_phone"] == "13800001234"  # 原字典未变
    assert out["customer_phone"] == "138****1234"


def test_mask_sensitive_dict_non_dict_passthrough():
    assert mask_sensitive_dict("not a dict") == "not a dict"  # type: ignore[arg-type]
    assert mask_sensitive_dict(None) is None  # type: ignore[arg-type]


# ---------------------- Order.to_dict mask 集成 ----------------------


def _make_order() -> Order:
    return Order(
        id="GKO-20260612-MASK",
        source="web",
        service_version="basic",
        customer_name="张三",
        customer_phone="13800001234",
        candidate_name="李四光",
        candidate_id_card="430102200501011234",
    )


def test_order_to_dict_default_is_mask():
    """不传参 = mask 模式 — 默认安全。"""
    order = _make_order()
    d = order.to_dict()
    assert d["customer_phone"] == "138****1234"
    assert d["candidate_id_card"] == "430102********1234"
    assert d["customer_name"] == "张*"
    assert d["candidate_name"] == "李*光"  # 3 字姓名规则
    # hash 字段保留
    assert "customer_phone_hash" in d


def test_order_to_dict_mask_explicit_string():
    order = _make_order()
    d = order.to_dict(decrypt_sensitive="mask")
    assert d["customer_phone"] == "138****1234"


def test_order_to_dict_unknown_string_falls_back_to_mask():
    """默认安全:未知策略值回退 mask,而非明文。"""
    order = _make_order()
    d = order.to_dict(decrypt_sensitive="plaintext-oops")  # type: ignore[arg-type]
    assert d["customer_phone"] == "138****1234"


def test_order_to_dict_true_returns_plaintext():
    order = _make_order()
    d = order.to_dict(decrypt_sensitive=True)
    assert d["customer_phone"] == "13800001234"
    assert d["candidate_id_card"] == "430102200501011234"


def test_order_to_dict_false_strips_sensitive():
    order = _make_order()
    d = order.to_dict(decrypt_sensitive=False)
    assert "customer_phone" not in d
    assert "candidate_id_card" not in d
    assert "customer_phone_hash" in d
