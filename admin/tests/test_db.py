"""db.py 单元测试 (T6.1).

覆盖:
- get_connection / ensure_schema 幂等
- AdminUserRepo CRUD
- authenticate 正确密码 / 错密码 / 不存在用户 / inactive 用户
- bootstrap_admin 首次创建 + 二次跳过
"""

from __future__ import annotations

import pytest

from admin.db import (
    AdminUserRepo,
    authenticate,
    bootstrap_admin,
    ensure_schema,
    get_connection,
)


def test_ensure_schema_idempotent(tmp_path):
    """多次 ensure_schema 不报错。"""
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    ensure_schema(db)
    ensure_schema(db)
    with get_connection(db) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='admin_users'"
        ).fetchone()
        assert row is not None


def test_repo_create_and_lookup(tmp_path):
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)

    u = repo.create("alice", "p@ss123")
    assert u.id > 0
    assert u.username == "alice"
    assert u.is_active is True

    found = repo.get_by_username("alice")
    assert found is not None
    user, password_hash = found
    assert user.id == u.id
    # 密码 hash 应被 PBKDF2 序列化(salt$hash)
    assert "$" in password_hash
    assert len(password_hash.split("$")) == 2


def test_repo_duplicate_username_raises(tmp_path):
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)
    repo.create("bob", "x")

    import sqlite3 as _sq

    with pytest.raises(_sq.IntegrityError):
        repo.create("bob", "y")


def test_repo_count_and_get_by_id(tmp_path):
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)
    assert repo.count() == 0
    u = repo.create("c1", "p")
    assert repo.count() == 1
    assert repo.get_by_id(u.id) is not None
    assert repo.get_by_id(99999) is None


def test_authenticate_correct_password(tmp_path):
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)
    repo.create("dave", "correct-horse")
    user = authenticate(repo, "dave", "correct-horse")
    assert user is not None
    assert user.username == "dave"
    # last_login_at 应已更新
    fresh = repo.get_by_id(user.id)
    assert fresh is not None
    assert fresh.last_login_at is not None


def test_authenticate_wrong_password(tmp_path):
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)
    repo.create("erin", "right")
    assert authenticate(repo, "erin", "wrong") is None


def test_authenticate_unknown_user(tmp_path):
    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)
    assert authenticate(repo, "ghost", "anything") is None


def test_authenticate_inactive_user(tmp_path):
    """is_active=0 → authenticate 返回 None。"""
    import sqlite3 as _sq

    db = str(tmp_path / "t.db")
    ensure_schema(db)
    repo = AdminUserRepo(db)
    u = repo.create("frank", "p")
    with _sq.connect(db) as conn:
        conn.execute("UPDATE admin_users SET is_active = 0 WHERE id = ?", (u.id,))
    assert authenticate(repo, "frank", "p") is None


def test_bootstrap_admin_creates_then_skips(settings):
    """bootstrap_admin 第一次创建,第二次跳过。"""
    created1, msg1 = bootstrap_admin(settings)
    assert created1 is True
    assert "已创建默认管理员" in msg1
    assert "请尽快" in msg1  # 安全提示

    created2, msg2 = bootstrap_admin(settings)
    assert created2 is False
    assert "已存在" in msg2

    repo = AdminUserRepo(settings.db_path)
    assert repo.count() == 1
