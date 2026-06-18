"""JWT 鉴权测试 (T6.1).

覆盖:
- encode/decode roundtrip
- 过期 / 签名错 / sub 格式错 → TokenError
- get_current_user 通过/拒绝路径
"""

from __future__ import annotations

import time

import jwt
import pytest

from admin.auth import TokenError, decode_token, encode_token
from admin.db import AdminUser
from admin.errors import BusinessError


def _make_user() -> AdminUser:
    return AdminUser(
        id=7,
        username="alice",
        role="admin",
        is_active=True,
        created_at="2026-06-12T00:00:00+00:00",
    )


def test_encode_decode_roundtrip(settings):
    user = _make_user()
    token = encode_token(user, settings)
    claims = decode_token(token, settings)
    assert claims["sub"] == "admin:7"
    assert claims["username"] == "alice"
    assert claims["role"] == "admin"
    assert claims["exp"] > claims["iat"]
    assert claims["exp"] - claims["iat"] == settings.jwt_expire_minutes * 60


def test_decode_expired_raises(settings):
    """手工签发已过期 token → TokenError。"""
    user = _make_user()
    now = int(time.time())
    payload = {
        "sub": f"admin:{user.id}",
        "username": user.username,
        "role": user.role,
        "iat": now - 3600,
        "exp": now - 1,
    }
    bad = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenError, match="expired"):
        decode_token(bad, settings)


def test_decode_bad_signature_raises(settings):
    user = _make_user()
    token = encode_token(user, settings)
    forged = jwt.encode(
        jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]),
        "wrong-secret-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenError, match="invalid"):
        decode_token(forged, settings)


def test_decode_malformed_sub_raises():
    """sub 不是 'admin:N' 格式 → _parse_user_id_from_subject 抛 TokenError。"""
    from admin.auth import _parse_user_id_from_subject

    # wrong prefix
    with pytest.raises(TokenError, match="prefix"):
        _parse_user_id_from_subject("user:7")
    # malformed
    with pytest.raises(TokenError, match="malformed"):
        _parse_user_id_from_subject("no-colon")
    # non-int id
    with pytest.raises(TokenError, match="non-integer"):
        _parse_user_id_from_subject("admin:abc")


def test_get_current_user_rejects_missing_token(client):
    """/api/auth/me 无 token → 401 + WWW-Authenticate。"""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate", "").lower() == "bearer"


def test_get_current_user_rejects_bogus_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_get_current_user_accepts_valid_token(client, auth_token):
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"
    assert body["is_active"] is True


def test_get_current_user_rejects_inactive(settings):
    """直接构造 inactive 用户 token → 403。"""
    from admin.db import AdminUser, AdminUserRepo, ensure_schema
    from admin.auth import encode_token
    from fastapi.testclient import TestClient
    from admin.app import create_app

    ensure_schema(settings.db_path)
    repo = AdminUserRepo(settings.db_path)
    user = repo.create(username="inactive_test", password="p@ss123")
    # 手动停用
    import sqlite3 as _sq

    with _sq.connect(settings.db_path) as conn:
        conn.execute("UPDATE admin_users SET is_active = 0 WHERE id = ?", (user.id,))

    inactive_user = AdminUser(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=False,
        created_at=user.created_at,
    )
    token = encode_token(inactive_user, settings)

    app = create_app(settings)
    with TestClient(app) as c:
        resp = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


def test_require_role_rejects_non_admin_user(settings):
    from admin.auth import require_role
    from admin.db import AdminUserRepo, ensure_schema

    ensure_schema(settings.db_path)
    repo = AdminUserRepo(settings.db_path)
    viewer = repo.create(username="viewer-role-test", password="p@ss123", role="viewer")

    dep = require_role("admin")

    with pytest.raises(BusinessError) as exc_info:
        dep(viewer)

    assert str(exc_info.value.code) == "E01301"
