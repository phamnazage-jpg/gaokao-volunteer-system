"""password.py 单元测试 (T6.1)."""

from __future__ import annotations

import pytest

from admin.password import hash_password, verify_password


def test_hash_then_verify_roundtrip():
    h = hash_password("hunter2")
    assert h != "hunter2"
    assert verify_password("hunter2", h) is True


def test_verify_wrong_password_fails():
    h = hash_password("hunter2")
    assert verify_password("hunter2-wrong", h) is False


def test_hash_is_salted_different_each_time():
    h1 = hash_password("hunter2")
    h2 = hash_password("hunter2")
    assert h1 != h2  # 不同的 salt → 不同的 hash
    # 但都能校验同一个密码
    assert verify_password("hunter2", h1)
    assert verify_password("hunter2", h2)


def test_hash_empty_password_raises():
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_handles_malformed_stored():
    assert verify_password("hunter2", "no-separator") is False
    assert verify_password("hunter2", "") is False
    assert verify_password("hunter2", "garbage$garbage") is False  # bad hex
