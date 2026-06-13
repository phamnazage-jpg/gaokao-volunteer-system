"""SQLite 连接管理 (T6.1).

提供:
- get_connection(db_path) : 打开 SQLite（启用外键 + WAL）
- ensure_schema(db_path)  : 幂等创建 admin_users 表
- bootstrap_admin(...)    : 启动时若无账户则自动创建默认管理员
- AdminUser / AdminUserRepo : dataclass + 简单 DAO
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from admin.config import Settings
from admin.password import hash_password, verify_password


def utc_now_iso() -> str:
    """当前 UTC 时间（ISO8601 秒精度）。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_connection(db_path: str) -> sqlite3.Connection:
    """打开 SQLite 连接。

    启用外键约束；row_factory = Row（便于列名访问）。
    默认路径会创建父目录。
    """
    path = Path(db_path)
    if path != Path(":memory:") and str(db_path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL 仅对真实文件有效（:memory: 会忽略）
    if str(db_path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


ADMIN_USERS_DDL = """
CREATE TABLE IF NOT EXISTS admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'admin',
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    last_login_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
"""


def ensure_schema(db_path: str) -> None:
    """幂等创建 admin_users 表。"""
    with get_connection(db_path) as conn:
        conn.executescript(ADMIN_USERS_DDL)


@dataclass(frozen=True)
class AdminUser:
    """管理员用户（不可变视图）。"""

    id: int
    username: str
    role: str
    is_active: bool
    created_at: str
    last_login_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AdminUser":
        return cls(
            id=row["id"],
            username=row["username"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            last_login_at=row["last_login_at"],
        )

    def to_public_dict(self) -> dict:
        """公开字段（不含密码）。"""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at,
        }


class AdminUserRepo:
    """AdminUser 仓库（基于 sqlite3）。"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def get_by_username(self, username: str) -> Optional[tuple[AdminUser, str]]:
        """按用户名查找，返回 (AdminUser, password_hash) 或 None。"""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, role, is_active, "
                "created_at, last_login_at FROM admin_users WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return None
        return AdminUser.from_row(row), row["password_hash"]

    def get_by_id(self, user_id: int) -> Optional[AdminUser]:
        """按 ID 查找（不含密码）。"""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, username, role, is_active, created_at, last_login_at "
                "FROM admin_users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return AdminUser.from_row(row) if row else None

    def create(self, username: str, password: str, role: str = "admin") -> AdminUser:
        """创建管理员。重复 username 抛 sqlite3.IntegrityError。"""
        now = utc_now_iso()
        password_hash = hash_password(password)
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO admin_users(username, password_hash, role, "
                "is_active, created_at) VALUES(?, ?, ?, 1, ?)",
                (username, password_hash, role, now),
            )
            user_id = cur.lastrowid or 0
        if user_id <= 0:  # pragma: no cover - 数据库异常兜底
            raise RuntimeError("failed to obtain lastrowid for new admin user")
        return AdminUser(
            id=user_id,
            username=username,
            role=role,
            is_active=True,
            created_at=now,
        )

    def count(self) -> int:
        """当前账户总数。"""
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM admin_users").fetchone()
        return int(row["n"])

    def update_last_login(self, user_id: int) -> None:
        """更新最后登录时间。"""
        with self._conn() as conn:
            conn.execute(
                "UPDATE admin_users SET last_login_at = ? WHERE id = ?",
                (utc_now_iso(), user_id),
            )


def bootstrap_admin(settings: Settings) -> tuple[bool, str]:
    """若 admin_users 为空,自动创建默认管理员。

    Returns:
        (created, message): created=True 表示已创建, message 为提示文本
    """
    ensure_schema(settings.db_path)
    repo = AdminUserRepo(settings.db_path)
    if repo.count() > 0:
        return False, "已存在管理员账户,跳过 bootstrap"
    user = repo.create(
        username=settings.default_admin_username,
        password=settings.default_admin_password,
    )
    return True, (
        f"已创建默认管理员: username={user.username} id={user.id} "
        f"(请尽快通过 GAOKAO_ADMIN_PASS 覆盖默认密码!)"
    )


def authenticate(
    repo: AdminUserRepo, username: str, password: str
) -> Optional[AdminUser]:
    """校验用户名+密码,成功返回 AdminUser 并更新 last_login_at。"""
    result = repo.get_by_username(username)
    if result is None:
        return None
    user, password_hash = result
    if not user.is_active:
        return None
    if not verify_password(password, password_hash):
        return None
    repo.update_last_login(user.id)
    return user
