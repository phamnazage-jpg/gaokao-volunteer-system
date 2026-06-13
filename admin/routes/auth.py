"""认证路由 (T6.1).

- POST /api/auth/login : 用户名 + 密码 → JWT
- GET  /api/auth/me    : 当前用户信息
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from admin.auth import encode_token, get_current_user
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser, AdminUserRepo, authenticate
from admin.errors import (
    AUTH_ACCOUNT_DISABLED,
    AUTH_INVALID_CREDENTIALS,
    BIZ_RATE_LIMITED,
    BusinessError,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])

_LOGIN_FAILURE_LOCK = threading.Lock()
_LOGIN_FAILURE_BUCKETS: dict[str, deque[float]] = {}
_LOGIN_FAILURE_LIMIT = 5
_LOGIN_FAILURE_WINDOW_SECONDS = 300.0


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class UserPublic(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: str
    last_login_at: Optional[str] = None


def _login_rate_limit_key(request: Request, username: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{username.lower()}@{client_host}"


def _prune_failures(bucket: deque[float], *, now: float) -> None:
    cutoff = now - _LOGIN_FAILURE_WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.popleft()


def _login_retry_after_seconds(key: str, *, now: float | None = None) -> int | None:
    if now is None:
        now = time.time()
    with _LOGIN_FAILURE_LOCK:
        bucket = _LOGIN_FAILURE_BUCKETS.get(key)
        if not bucket:
            return None
        _prune_failures(bucket, now=now)
        if len(bucket) < _LOGIN_FAILURE_LIMIT:
            if not bucket:
                _LOGIN_FAILURE_BUCKETS.pop(key, None)
            return None
        retry_after = int(_LOGIN_FAILURE_WINDOW_SECONDS - (now - bucket[0]))
        return max(1, retry_after)


def _record_login_failure(key: str, *, now: float | None = None) -> None:
    if now is None:
        now = time.time()
    with _LOGIN_FAILURE_LOCK:
        bucket = _LOGIN_FAILURE_BUCKETS.setdefault(key, deque())
        _prune_failures(bucket, now=now)
        bucket.append(now)


def _clear_login_failures(key: str) -> None:
    with _LOGIN_FAILURE_LOCK:
        _LOGIN_FAILURE_BUCKETS.pop(key, None)


def reset_login_rate_limit_for_tests() -> None:
    with _LOGIN_FAILURE_LOCK:
        _LOGIN_FAILURE_BUCKETS.clear()


@router.post("/login", response_model=LoginResponse, summary="登录")
def login(
    request: Request,
    body: LoginRequest,
    settings: Settings = Depends(get_settings_dep),
) -> LoginResponse:
    rate_limit_key = _login_rate_limit_key(request, body.username)
    retry_after = _login_retry_after_seconds(rate_limit_key)
    if retry_after is not None:
        raise BusinessError(
            BIZ_RATE_LIMITED,
            detail={"retry_after_seconds": retry_after},
            http_status=429,
        )
    repo = AdminUserRepo(settings.db_path)
    user = authenticate(repo, body.username, body.password)
    if user is None:
        _record_login_failure(rate_limit_key)
        retry_after = _login_retry_after_seconds(rate_limit_key)
        if retry_after is not None:
            raise BusinessError(
                BIZ_RATE_LIMITED,
                detail={"retry_after_seconds": retry_after},
                http_status=429,
            )
        # 401 不区分用户名/密码错误,避免账户枚举
        raise BusinessError(AUTH_INVALID_CREDENTIALS)
    if not user.is_active:
        raise BusinessError(AUTH_ACCOUNT_DISABLED, detail={"user_id": user.id})
    _clear_login_failures(rate_limit_key)
    token = encode_token(user, settings)
    return LoginResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=UserPublic, summary="当前用户")
def me(user: AdminUser = Depends(get_current_user)) -> UserPublic:
    return UserPublic(**user.to_public_dict())
