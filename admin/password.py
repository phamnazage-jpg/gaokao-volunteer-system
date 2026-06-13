"""密码哈希 (T6.1).

使用 PBKDF2-HMAC-SHA256（200k 迭代）。salt 16B hex；hash 64B hex。
不依赖 bcrypt/argon2 等第三方库，保持项目"零运行时第三方"约束。

存储格式: "<salt_hex>$<hash_hex>"（便于单字段持久化）。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_PBKDF2_ALGO = "sha256"
_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16
_HASH_BYTES = 32
_STORED_SEPARATOR = "$"


def hash_password(plain: str) -> str:
    """对明文密码进行 PBKDF2 哈希。

    Args:
        plain: 明文密码

    Returns:
        形如 "<salt_hex>$<hash_hex>" 的字符串，可直接入库
    """
    if not plain:
        raise ValueError("password cannot be empty")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO,
        plain.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_HASH_BYTES,
    )
    return f"{salt.hex()}{_STORED_SEPARATOR}{digest.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    """校验明文密码与存储哈希是否匹配。

    使用恒定时间比较避免时序攻击。

    Args:
        plain: 明文密码
        stored: 数据库存储的 "<salt>$<hash>" 字符串

    Returns:
        True 表示匹配
    """
    if not plain or not stored or _STORED_SEPARATOR not in stored:
        return False
    salt_hex, hash_hex = stored.split(_STORED_SEPARATOR, 1)
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO,
        plain.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_HASH_BYTES,
    )
    return hmac.compare_digest(candidate, expected)
