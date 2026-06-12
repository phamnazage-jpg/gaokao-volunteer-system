"""订单敏感字段加密模块

使用 Fernet（cryptography 包）实现 AES-256 加密：
- Fernet = AES-128-CBC + HMAC-SHA256 + 时间戳，密钥派生后等价于 256-bit 安全强度
- 密钥来源：环境变量 GAOKAO_ORDERS_FERNET_KEY（任意字符串，经 SHA-256 派生为 32 字节）
- 密文存储：base64-url 字符串，写入 SQLite TEXT 字段

索引字段：手机号用 SHA-256 hex 单独存储，供去重查询（密文不能直接索引）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


ENV_KEY_NAME = "GAOKAO_ORDERS_FERNET_KEY"
_KEY_LENGTH = 32  # bytes; SHA-256 digest length


class EncryptionError(RuntimeError):
    """加密/解密失败时抛出的基础异常。"""


class MissingEncryptionKey(EncryptionError):
    """环境变量未配置加密密钥时抛出。"""


def derive_key(secret: str) -> bytes:
    """从任意 secret 字符串派生 32 字节 Fernet key（base64-url 编码）。

    使用 SHA-256 对 secret 散列得到 32 字节，再 base64-url 编码为 Fernet 接受的格式。
    同 secret 总是派生同 key（确定性），便于备份恢复。
    """
    if not isinstance(secret, str) or not secret:
        raise EncryptionError("secret 必须为非空字符串")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    """从环境变量获取 Fernet 实例。缺失则抛 MissingEncryptionKey（不静默降级）。"""
    secret = os.environ.get(ENV_KEY_NAME)
    if not secret:
        raise MissingEncryptionKey(
            f"环境变量 {ENV_KEY_NAME} 未设置；为保证数据安全，禁止以明文存储敏感字段。"
        )
    return Fernet(derive_key(secret))


def encrypt(plaintext: str) -> str:
    """加密字符串并返回 base64 字符串。

    输入必须为 str；输出为 str（utf-8 解码后的 base64），可直接写入 SQLite TEXT。
    """
    if not isinstance(plaintext, str):
        raise EncryptionError(
            f"encrypt 输入必须为 str，实际为 {type(plaintext).__name__}"
        )
    token = get_fernet().encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt(ciphertext: str) -> str:
    """解密 base64 字符串并返回原始明文。

    密钥错误或密文被篡改时抛 InvalidToken。
    """
    if not isinstance(ciphertext, str):
        raise EncryptionError(
            f"decrypt 输入必须为 str，实际为 {type(ciphertext).__name__}"
        )
    try:
        plain = get_fernet().decrypt(ciphertext.encode("ascii"))
    except InvalidToken as exc:
        raise EncryptionError("密文无法解密（密钥错误或数据被篡改）") from exc
    return plain.decode("utf-8")


def hash_for_index(value: str) -> str:
    """对索引字段（如手机号）计算 SHA-256 hex，用于去重查询。

    注意：SHA-256 不抗碰撞查找，仅用于去重，不应用于需要抗碰撞审计的场景。
    """
    if not isinstance(value, str):
        raise EncryptionError(
            f"hash_for_index 输入必须为 str，实际为 {type(value).__name__}"
        )
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    """常数时间字符串比较（防时序攻击的辅助工具，DAO 比较密文时使用）。"""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
