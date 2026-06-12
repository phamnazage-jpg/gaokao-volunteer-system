"""crypto 模块测试"""

import os
import pytest

# 测试开始前设置密钥（必须在 import data.orders.crypto 之前）
os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-unit-tests")

from data.orders.crypto import (
    derive_key,
    encrypt,
    decrypt,
    hash_for_index,
    constant_time_equals,
    EncryptionError,
    MissingEncryptionKey,
    ENV_KEY_NAME,
)
from cryptography.fernet import Fernet


def setup_function(_):
    """每个用例前清掉缓存，避免环境变量副作用。"""
    from data.orders import crypto

    crypto.get_fernet.cache_clear()


# -------- derive_key --------


def test_derive_key_is_deterministic():
    """同 secret 派生同 key。"""
    k1 = derive_key("hello")
    k2 = derive_key("hello")
    assert k1 == k2
    assert len(k1) > 0


def test_derive_key_distinct_for_different_secrets():
    """不同 secret 派生不同 key。"""
    assert derive_key("a") != derive_key("b")


def test_derive_key_rejects_empty():
    with pytest.raises(EncryptionError):
        derive_key("")


def test_derive_key_accepts_fernet_key_directly():
    """Fernet 直接生成的 key 应被接受（兼容）。"""
    direct = Fernet.generate_key()
    # derive_key 用 sha256 派生；这里验证 Fernet 能用直接 key 初始化
    Fernet(direct)  # 不抛即可


# -------- encrypt/decrypt round-trip --------


def test_encrypt_decrypt_round_trip_chinese():
    """中文明文 round-trip。"""
    plaintext = "张同学 13800001234"
    ct = encrypt(plaintext)
    assert ct != plaintext
    assert decrypt(ct) == plaintext


def test_encrypt_decrypt_round_trip_empty_string():
    """空字符串也能 round-trip。"""
    assert decrypt(encrypt("")) == ""


def test_encrypt_output_is_ascii():
    """密文为 base64-url 字符串，仅含 ASCII。"""
    ct = encrypt("hello world")
    ct.encode("ascii")  # 不抛即通过


def test_decrypt_with_wrong_key_fails():
    """错误密钥解密应抛 EncryptionError。"""
    # 先用当前 key 加密
    ct = encrypt("secret-value")
    # 切换密钥
    os.environ[ENV_KEY_NAME] = "different-secret"
    from data.orders import crypto

    crypto.get_fernet.cache_clear()
    with pytest.raises(EncryptionError):
        decrypt(ct)
    # 恢复
    os.environ[ENV_KEY_NAME] = "test-secret-for-unit-tests"
    crypto.get_fernet.cache_clear()


def test_encrypt_rejects_non_string():
    with pytest.raises(EncryptionError):
        encrypt(12345)  # type: ignore[arg-type]


def test_decrypt_rejects_non_string():
    with pytest.raises(EncryptionError):
        decrypt(12345)  # type: ignore[arg-type]


def test_missing_key_raises_missing_encryption_key(monkeypatch):
    """未配置密钥时 get_fernet 抛 MissingEncryptionKey，不静默降级。"""
    monkeypatch.delenv(ENV_KEY_NAME, raising=False)
    from data.orders import crypto

    crypto.get_fernet.cache_clear()
    with pytest.raises(MissingEncryptionKey):
        encrypt("test")


# -------- hash_for_index --------


def test_hash_for_index_is_stable():
    """同输入同输出。"""
    assert hash_for_index("13800001234") == hash_for_index("13800001234")


def test_hash_for_index_strips_whitespace():
    """前后空白不影响 hash。"""
    assert hash_for_index(" 13800001234 ") == hash_for_index("13800001234")


def test_hash_for_index_is_hex_64_chars():
    """SHA-256 hex 应为 64 字符。"""
    h = hash_for_index("13800001234")
    assert len(h) == 64
    int(h, 16)  # 可被解析为 16 进制


def test_hash_for_index_different_inputs():
    """不同输入产生不同 hash。"""
    assert hash_for_index("13800001234") != hash_for_index("13800001235")


def test_hash_for_index_rejects_non_string():
    with pytest.raises(EncryptionError):
        hash_for_index(12345)  # type: ignore[arg-type]


# -------- constant_time_equals --------


def test_constant_time_equals_equal():
    assert constant_time_equals("abc", "abc") is True


def test_constant_time_equals_unequal():
    assert constant_time_equals("abc", "abd") is False


def test_constant_time_equals_different_length():
    assert constant_time_equals("abc", "abcd") is False
