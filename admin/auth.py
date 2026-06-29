"""JWT 鉴权 (T6.1).

- encode_token / decode_token: HS256 签发与校验
- get_current_user: FastAPI 依赖,从 Authorization 头提取 Bearer token
- require_user / require_role: 路由级保护
"""

from __future__ import annotations

import time
from typing import Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from admin.config import Settings
from admin.db import AdminUser, AdminUserRepo
from admin.errors import (
    AUTH_ACCOUNT_DISABLED,
    AUTH_INSUFFICIENT_PERMISSION,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    BusinessError,
)


_BEARER_SCHEME = HTTPBearer(auto_error=False)


def encode_token(
    user: AdminUser,
    settings: Settings,
    *,
    extra_claims: Optional[dict] = None,
) -> str:
    """签发 JWT。

    Args:
        user: 当前登录用户
        settings: 配置
        extra_claims: 可选附加 claims（如自定义角色扩展）

    Returns:
        JWT 字符串
    """
    now = int(time.time())
    payload = {
        "sub": f"admin:{user.id}",
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class TokenError(ValueError):
    """Token 解析失败（签名错/过期/格式错）。"""


def decode_token(token: str, settings: Settings) -> dict:
    """解析 JWT 校验签名与有效期。

    Raises:
        TokenError: 任何解析失败
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenError("token expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenError(f"invalid token: {e}") from e


def _parse_user_id_from_subject(sub: str) -> int:
    """'admin:42' → 42"""
    if not isinstance(sub, str) or ":" not in sub:
        raise TokenError("malformed sub")
    prefix, _, sid = sub.partition(":")
    if prefix != "admin":
        raise TokenError("unexpected sub prefix")
    try:
        return int(sid)
    except ValueError as e:
        raise TokenError("non-integer sub id") from e


def get_settings(request: Request) -> Settings:
    """从 app.state 取 Settings（避免每次都重新加载）。"""
    settings = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover - 兜底
        from admin.config import load_settings

        settings = load_settings()
    return settings


def _raise_token_error(exc: TokenError) -> None:
    """把 TokenError 翻译成业务错误 (区分过期 vs 无效)."""
    msg = str(exc).lower()
    if "expired" in msg:
        raise BusinessError(AUTH_TOKEN_EXPIRED, detail={"reason": str(exc)}) from exc
    raise BusinessError(AUTH_TOKEN_INVALID, detail={"reason": str(exc)}) from exc


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER_SCHEME),
    settings: Settings = Depends(get_settings),
) -> AdminUser:
    """FastAPI 依赖:从 Authorization: Bearer *** JWT,返回 AdminUser。

    缺失/无效/过期一律 401 (走业务错误码 E012xx 系列).
    支持从 URL query 参数 ``t`` 获取 token（仅用于管理后台 Web 页面场景）。
    """
    raw_token: str | None = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        raw_token = credentials.credentials
    # fallback: URL query 参数 t（管理后台 Web 登录页跳转场景）
    if raw_token is None:
        query_token = request.query_params.get("t")
        if query_token:
            raw_token = query_token
    if raw_token is None:
        raise BusinessError(
            AUTH_TOKEN_INVALID, detail={"reason": "missing bearer token"}
        )
    try:
        claims = decode_token(raw_token, settings)
    except TokenError as e:
        _raise_token_error(e)
        raise AssertionError("unreachable")
    try:
        user_id = _parse_user_id_from_subject(claims.get("sub", ""))
    except TokenError as e:
        _raise_token_error(e)
        raise AssertionError("unreachable")
    repo = AdminUserRepo(settings.db_path)
    user = repo.get_by_id(user_id)
    if user is None:
        raise BusinessError(AUTH_TOKEN_INVALID, detail={"reason": "user not found"})
    if not user.is_active:
        raise BusinessError(AUTH_ACCOUNT_DISABLED, detail={"user_id": user.id})
    return user


def require_role(*allowed_roles: str):
    def _dep(user: AdminUser = Depends(get_current_user)) -> AdminUser:
        if user.role not in allowed_roles:
            raise BusinessError(
                AUTH_INSUFFICIENT_PERMISSION,
                detail={
                    "required_roles": list(allowed_roles),
                    "actual_role": user.role,
                    "user_id": user.id,
                },
            )
        return user

    return _dep
