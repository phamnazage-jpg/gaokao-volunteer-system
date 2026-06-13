"""HMAC-SHA256 签名 / 校验与时间戳防重放 (T8.1)

闲鱼 Webhook 头约定（与设计文档 CHANNEL_INTEGRATION.md §3.1 / §5.2 一致）:

- ``X-Signature``: 形如 ``hmac-sha256=<hex>``
- ``X-Timestamp``: unix 秒级时间戳
- ``X-Nonce``:    一次性随机串（防同秒内重放）

签名原文: ``f"{ts}.{nonce}.{raw_body}"``，密钥来自
``GAOKAO_XIANYU_WEBHOOK_SECRET`` 环境变量。

防重放: 时间戳与本地时间偏差超过 ``XIANYU_WEBHOOK_TS_TOLERANCE``（默认 300s）
视为过期；同时已使用过的 ``(timestamp, nonce)`` 组合在 10 分钟内
不能再次通过。
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections import OrderedDict
from threading import Lock
from typing import Tuple

# 默认时间戳容差 300s (5 分钟)
DEFAULT_TS_TOLERANCE_SECONDS: int = 300

# nonce 缓存 10 分钟
NONCE_CACHE_TTL_SECONDS: int = 600

# nonce 缓存最大条目 (避免内存爆)
NONCE_CACHE_MAX_SIZE: int = 4096


class SignatureError(ValueError):
    """签名校验失败（格式错误 / 签名不匹配 / 时间戳过期 / nonce 重复）。"""


def get_webhook_secret() -> str:
    """读取 Webhook 签名密钥。

    环境变量 ``GAOKAO_XIANYU_WEBHOOK_SECRET`` 必须设置；缺失时抛 ``SignatureError``。
    测试场景应通过 ``monkeypatch.setenv`` 或 ``os.environ`` 注入。
    """
    secret = os.environ.get("GAOKAO_XIANYU_WEBHOOK_SECRET", "")
    if not secret:
        raise SignatureError(
            "GAOKAO_XIANYU_WEBHOOK_SECRET 未设置；"
            "生产环境必须配置签名密钥，测试环境通过 os.environ 注入"
        )
    return secret


def sign(
    body: bytes,
    *,
    secret: str | None = None,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> Tuple[str, int, str]:
    """生成 Webhook 签名（测试用）。返回 (signature_header, ts, nonce)。

    形参全为 None 时使用 ``get_webhook_secret()`` + ``time.time()`` + 16 字节 hex nonce。
    """
    if secret is None:
        secret = get_webhook_secret()
    if timestamp is None:
        timestamp = int(time.time())
    if nonce is None:
        nonce = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    payload = f"{timestamp}.{nonce}.".encode("utf-8") + body
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"hmac-sha256={digest}", timestamp, nonce


class _NonceCache:
    """线程安全的 LRU nonce 缓存，按 (timestamp, nonce) 记录首次出现时间。

    容量超限自动淘汰最旧条目。``now`` 参数可注入以方便单测。
    """

    def __init__(
        self,
        *,
        ttl_seconds: int = NONCE_CACHE_TTL_SECONDS,
        max_size: int = NONCE_CACHE_MAX_SIZE,
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max_size
        self._lock = Lock()
        self._store: "OrderedDict[Tuple[int, str], float]" = OrderedDict()

    def remember(self, ts: int, nonce: str, now: float | None = None) -> bool:
        """记录 nonce；若 (ts, nonce) 已在 TTL 内则返回 False（重放）。

        否则写入并返回 True。
        """
        if now is None:
            now = time.time()
        with self._lock:
            self._purge_locked(now)
            key = (ts, nonce)
            if key in self._store:
                # 重新插入到队尾表示最近使用
                self._store.move_to_end(key)
                return False
            self._store[key] = now
            if len(self._store) > self._max:
                self._store.popitem(last=False)
            return True

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def _purge_locked(self, now: float) -> None:
        cutoff = now - self._ttl
        # 队首是最旧的，顺序弹出过期项
        while self._store:
            oldest_key, first_seen = next(iter(self._store.items()))
            if first_seen < cutoff:
                self._store.popitem(last=False)
            else:
                break


# 模块级默认实例
_NONCE_CACHE = _NonceCache()


def _get_nonce_cache() -> _NonceCache:
    return _NONCE_CACHE


def reset_nonce_cache_for_tests() -> None:
    """清空 nonce 缓存（仅用于单测）。"""
    _NONCE_CACHE.clear()


def verify(
    body: bytes,
    signature_header: str,
    timestamp_header: str | int,
    nonce_header: str,
    *,
    secret: str | None = None,
    tolerance_seconds: int = DEFAULT_TS_TOLERANCE_SECONDS,
    nonce_cache: _NonceCache | None = None,
    now: float | None = None,
) -> None:
    """校验 Webhook 签名；失败抛 :class:`SignatureError`。

    参数:
        body: 原始请求体（bytes，不参与解码/排序）
        signature_header: ``X-Signature`` 头的完整值
        timestamp_header: ``X-Timestamp`` 头（字符串或整数）
        nonce_header: ``X-Nonce`` 头
        secret: 显式密钥；None 时从环境变量读取
        tolerance_seconds: 时间戳容差，默认 300s
        nonce_cache: 注入的 nonce 缓存（用于单测隔离）
        now: 注入的"当前时间"（用于单测）

    异常: :class:`SignatureError` 包含具体的 reject_reason
    """
    if secret is None:
        secret = get_webhook_secret()
    if nonce_cache is None:
        nonce_cache = _get_nonce_cache()
    if now is None:
        now = time.time()

    # 1) 解析签名
    if not signature_header or not signature_header.startswith("hmac-sha256="):
        raise SignatureError("malformed_signature: missing hmac-sha256= prefix")
    provided = signature_header.split("=", 1)[1].strip()
    if not provided:
        raise SignatureError("malformed_signature: empty signature")

    # 2) 解析时间戳
    try:
        ts = int(timestamp_header)
    except (TypeError, ValueError):
        raise SignatureError("malformed_timestamp: not an integer")

    if abs(now - ts) > tolerance_seconds:
        raise SignatureError(f"timestamp_out_of_range: |now-ts|>{tolerance_seconds}s")

    # 3) nonce 必填
    if not nonce_header:
        raise SignatureError("missing_nonce")

    # 4) 重新计算签名
    payload = f"{ts}.{nonce_header}.".encode("utf-8") + body
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, provided):
        raise SignatureError("signature_mismatch")

    # 5) 防重放
    if not nonce_cache.remember(ts, nonce_header, now=now):
        raise SignatureError("nonce_replay")


def sha256_hex(data: bytes) -> str:
    """计算 body 的 SHA-256 hex 摘要（用于审计 raw_body_hash）。"""
    return hashlib.sha256(data).hexdigest()
