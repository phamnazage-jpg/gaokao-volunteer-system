"""
高考志愿填报系统 - 短链接生成服务 (T7.1)

提供:
- 短码生成 (base62, 默认 6 位)
- SQLite 映射表 (短码 → 报告元数据)
- 访问控制 (有效期 / 密码 / 权限)
- 访问统计 (次数 / 时间)

URL 模式:
    /s/{code}      → 分享短链接 (由 Web 路由 /s/<code> 调用 resolve())
    /s/ABC123      → 短码示例

依赖:
    仅 Python 3.8+ 标准库 (sqlite3, hashlib, secrets)
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import string
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# base62 字母表 (0-9, A-Z, a-z) — URL-safe, 无需 urlencode
BASE62_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase
BASE62_LEN = len(BASE62_ALPHABET)  # 62

# 短码默认长度 (6 位 = 56B 空间, 实际使用远小于该值, 碰撞概率极低)
DEFAULT_CODE_LEN = 6

PBKDF2_SALT_BYTES = 16
PBKDF2_ITERATIONS = 100_000

# 默认数据库路径
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "short_links.db"

# 权限级别
PERM_READ = "read"
PERM_COMMENT = "comment"
PERM_EDIT = "edit"
PERM_ADMIN = "admin"
VALID_PERMISSIONS = {PERM_READ, PERM_COMMENT, PERM_EDIT, PERM_ADMIN}

# 状态常量
STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_REVOKED = "revoked"
STATUS_EXPIRED = "expired"
STATUS_PASSWORD_REQUIRED = "password_required"
STATUS_PASSWORD_WRONG = "password_wrong"
STATUS_PASSWORD_WRONG = "password_wrong"


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------


@dataclass
class ShareLink:
    """分享链接记录"""

    code: str
    report_id: str
    owner_id: str = "anonymous"
    permission: str = PERM_COMMENT
    password_hash: Optional[str] = (
        None  # pbkdf2: salt_hex$digest_hex；兼容历史 sha256 hex
    )
    expires_at: Optional[float] = None  # unix timestamp
    revoked: int = 0
    access_count: int = 0
    last_access_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    note: Optional[str] = None

    def is_expired(self, now: Optional[float] = None) -> bool:
        if self.expires_at is None:
            return False
        return (now or time.time()) >= self.expires_at

    def is_active(self) -> bool:
        return self.revoked == 0 and not self.is_expired()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["created_at_iso"] = _iso(self.created_at)
        if self.expires_at is not None:
            d["expires_at_iso"] = _iso(self.expires_at)
        else:
            d["expires_at_iso"] = None
        if self.last_access_at is not None:
            d["last_access_at_iso"] = _iso(self.last_access_at)
        else:
            d["last_access_at_iso"] = None
        return d


@dataclass
class ResolveResult:
    """resolve() 的返回结果"""

    status: str
    code: str
    link: Optional[ShareLink] = None
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "status": self.status,
            "code": self.code,
            "reason": self.reason,
        }
        if self.link is not None:
            d["link"] = self.link.to_dict()
        return d


# ---------------------------------------------------------------------------
# base62 编解码
# ---------------------------------------------------------------------------


def base62_encode(num: int) -> str:
    """
    把非负整数编码为 base62 字符串
    例: 0 -> "0", 61 -> "Z", 62 -> "10", 1234567 -> "3Gtv"
    """
    if num < 0:
        raise ValueError("num must be >= 0")
    if num == 0:
        return BASE62_ALPHABET[0]
    parts = []
    while num > 0:
        num, rem = divmod(num, BASE62_LEN)
        parts.append(BASE62_ALPHABET[rem])
    return "".join(reversed(parts))


def base62_decode(s: str) -> int:
    """把 base62 字符串解码为整数"""
    if not s:
        raise ValueError("empty string")
    n = 0
    for ch in s:
        idx = BASE62_ALPHABET.find(ch)
        if idx < 0:
            raise ValueError(f"invalid base62 char: {ch!r}")
        n = n * BASE62_LEN + idx
    return n


def generate_code(length: int = DEFAULT_CODE_LEN) -> str:
    """
    用加密安全的随机数生成短码
    注: 大批量时实际碰撞概率可用生日悖论估算
         (N=10M, length=6, p≈4e-7), 失败后由调用方重试
    """
    if length < 4 or length > 16:
        raise ValueError("length must be in [4, 16]")
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _iso(ts: float) -> str:
    """unix timestamp -> ISO8601 (UTC)"""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _now() -> float:
    return time.time()


def _hash_password(password: str) -> str:
    """密码哈希: pbkdf2_hmac(sha256) + 16-byte salt，格式为 salt_hex$digest_hex。"""
    if not password:
        raise ValueError("password must be non-empty")
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"{salt.hex()}${digest.hex()}"


def _is_legacy_sha256_hash(password_hash: str) -> bool:
    return len(password_hash) == 64 and "$" not in password_hash


def _verify_password(password: str, password_hash: str) -> bool:
    if not password:
        return False
    if _is_legacy_sha256_hash(password_hash):
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, password_hash)

    salt_hex, _, digest_hex = password_hash.partition("$")
    if not salt_hex or not digest_hex:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(candidate, expected)


def _row_to_link(row: sqlite3.Row) -> ShareLink:
    return ShareLink(
        code=row["code"],
        report_id=row["report_id"],
        owner_id=row["owner_id"],
        permission=row["permission"],
        password_hash=row["password_hash"],
        expires_at=row["expires_at"],
        revoked=row["revoked"],
        access_count=row["access_count"],
        last_access_at=row["last_access_at"],
        created_at=row["created_at"],
        note=row["note"],
    )


# ---------------------------------------------------------------------------
# 短链接服务
# ---------------------------------------------------------------------------


class ShortLinkService:
    """
    短链接服务, 对应 /s/{code} 路由

    用法:
        svc = ShortLinkService()                       # 默认 DB 路径
        link = svc.create(report_id="R-2026-001",
                           permission="read",
                           ttl_days=7)
        print(link.code)                                # "aB3xY7"
        print(svc.url(link.code, base="https://gk.example.com"))
        # -> "https://gk.example.com/s/aB3xY7"

        result = svc.resolve(link.code)
        assert result.ok
        assert result.link.report_id == "R-2026-001"
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS share_links (
        code            TEXT PRIMARY KEY,
        report_id       TEXT NOT NULL,
        owner_id        TEXT NOT NULL DEFAULT 'anonymous',
        permission      TEXT NOT NULL DEFAULT 'comment',
        password_hash   TEXT,
        expires_at      REAL,
        revoked         INTEGER NOT NULL DEFAULT 0,
        access_count    INTEGER NOT NULL DEFAULT 0,
        last_access_at  REAL,
        created_at      REAL NOT NULL,
        note            TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_share_links_report
        ON share_links(report_id);
    CREATE INDEX IF NOT EXISTS idx_share_links_owner
        ON share_links(owner_id);
    CREATE INDEX IF NOT EXISTS idx_share_links_expires
        ON share_links(expires_at);

    CREATE TABLE IF NOT EXISTS share_link_access_events (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        code            TEXT NOT NULL,
        accessed_at     REAL NOT NULL,
        visitor_token   TEXT,
        ip              TEXT,
        user_agent      TEXT,
        FOREIGN KEY(code) REFERENCES share_links(code) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_share_link_access_events_code_time
        ON share_link_access_events(code, accessed_at);
    CREATE INDEX IF NOT EXISTS idx_share_link_access_events_visitor
        ON share_link_access_events(visitor_token);
    """

    def __init__(self, db_path: str | os.PathLike[str] | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # 第一次实例化即建表 (亦可显式调用 init_schema)
        self.init_schema()

    # ---- 生命周期 ----

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        # in-memory DB 需要 shared cache 才能在多次 connect 中共享
        if str(self.db_path) == ":memory:":
            conn = sqlite3.connect(
                "file::memory:?cache=shared",
                timeout=10.0,
                isolation_level=None,
                uri=True,
            )
        else:
            conn = sqlite3.connect(
                str(self.db_path), timeout=10.0, isolation_level=None
            )
        conn.row_factory = sqlite3.Row
        if str(self.db_path) != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # ---- 创建 ----

    def create(
        self,
        report_id: str,
        owner_id: str = "anonymous",
        permission: str = PERM_COMMENT,
        password: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        ttl_days: Optional[int] = None,
        code_length: int = DEFAULT_CODE_LEN,
        max_retries: int = 8,
        note: Optional[str] = None,
    ) -> ShareLink:
        """
        创建一条分享链接

        参数:
            report_id   关联的报告 ID (T1 / T2 / T3 报告)
            owner_id    创建者 ID
            permission  read / comment / edit / admin
            password    可选访问密码
            ttl_seconds / ttl_days  二选一, None 表示永不过期
            code_length 短码长度 (4-16)
            max_retries 碰撞重试次数
            note        备注
        """
        if not report_id:
            raise ValueError("report_id is required")
        if permission not in VALID_PERMISSIONS:
            raise ValueError(f"permission must be one of {sorted(VALID_PERMISSIONS)}")
        if ttl_seconds is not None and ttl_days is not None:
            raise ValueError("ttl_seconds 与 ttl_days 不能同时指定")
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        if ttl_days is not None and ttl_days <= 0:
            raise ValueError("ttl_days must be > 0")

        expires_at = None
        if ttl_seconds is not None:
            expires_at = _now() + ttl_seconds
        elif ttl_days is not None:
            expires_at = _now() + ttl_days * 86400

        password_hash = _hash_password(password) if password else None

        last_err: Optional[Exception] = None
        for _ in range(max_retries):
            code = generate_code(code_length)
            try:
                with self._connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO share_links(
                            code, report_id, owner_id, permission,
                            password_hash, expires_at, revoked,
                            access_count, last_access_at, created_at, note
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, NULL, ?, ?)
                        """,
                        (
                            code,
                            report_id,
                            owner_id,
                            permission,
                            password_hash,
                            expires_at,
                            _now(),
                            note,
                        ),
                    )
                created = self.get(code)
                if created is None:
                    raise RuntimeError(f"short link created but lookup failed: {code}")
                return created
            except sqlite3.IntegrityError as e:
                # 唯一冲突: 碰撞, 重试
                last_err = e
                continue
        raise RuntimeError(
            f"无法生成唯一短码 (length={code_length}, retries={max_retries}): {last_err}"
        )

    # ---- 查询 ----

    def get(self, code: str) -> Optional[ShareLink]:
        if not code:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM share_links WHERE code = ?", (code,)
            ).fetchone()
        return _row_to_link(row) if row else None

    def resolve(
        self,
        code: str,
        password: Optional[str] = None,
        record_access: bool = True,
        visitor_token: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ResolveResult:
        """
        解析短码 -> (status, link, reason)

        状态:
            ok / not_found / revoked / expired /
            password_required / password_wrong

        校验顺序 (按 HTTP 语义):
            1. 存在?
            2. 已撤销?
            3. 已过期?
            4. 需要密码?
            5. 密码正确?
        """
        link = self.get(code)
        if link is None:
            return ResolveResult(
                status=STATUS_NOT_FOUND, code=code, reason="code not found"
            )
        if link.revoked != 0:
            return ResolveResult(
                status=STATUS_REVOKED, code=code, link=link, reason="revoked"
            )
        if link.is_expired():
            return ResolveResult(
                status=STATUS_EXPIRED, code=code, link=link, reason="expired"
            )
        if link.password_hash is not None:
            if not password:
                return ResolveResult(
                    status=STATUS_PASSWORD_REQUIRED,
                    code=code,
                    link=link,
                    reason="password required",
                )
            if not _verify_password(password, link.password_hash):
                return ResolveResult(
                    status=STATUS_PASSWORD_WRONG,
                    code=code,
                    link=link,
                    reason="wrong password",
                )
            if _is_legacy_sha256_hash(link.password_hash):
                upgraded_hash = _hash_password(password)
                with self._connect() as conn:
                    conn.execute(
                        "UPDATE share_links SET password_hash = ? WHERE code = ?",
                        (upgraded_hash, link.code),
                    )
                link.password_hash = upgraded_hash

        if record_access:
            self._bump_access(
                link.code,
                visitor_token=visitor_token,
                ip=ip,
                user_agent=user_agent,
            )
            link.access_count += 1
            link.last_access_at = _now()
        return ResolveResult(status=STATUS_OK, code=code, link=link, reason="ok")

    def _bump_access(
        self,
        code: str,
        *,
        visitor_token: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        accessed_at = _now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE share_links
                SET access_count = access_count + 1,
                    last_access_at = ?
                WHERE code = ?
                """,
                (accessed_at, code),
            )
            conn.execute(
                """
                INSERT INTO share_link_access_events(
                    code, accessed_at, visitor_token, ip, user_agent
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (code, accessed_at, visitor_token, ip, user_agent),
            )

    # ---- 撤销 ----

    def revoke(self, code: str, owner_id: Optional[str] = None) -> bool:
        """
        撤销一条链接
        如果指定 owner_id, 只有 owner 匹配时才能撤销 (防止越权)
        返回: 是否从「未撤销」变为「已撤销」(True/False),
              重复撤销 / 不存在的 code 均返回 False
        """
        with self._connect() as conn:
            if owner_id is not None:
                cur = conn.execute(
                    "UPDATE share_links SET revoked = 1 "
                    "WHERE code = ? AND owner_id = ? AND revoked = 0",
                    (code, owner_id),
                )
            else:
                cur = conn.execute(
                    "UPDATE share_links SET revoked = 1 WHERE code = ? AND revoked = 0",
                    (code,),
                )
            return cur.rowcount > 0

    def revoke_by_report(self, report_id: str, owner_id: Optional[str] = None) -> int:
        """按 report 批量撤销分享链接；可选 owner 约束避免越权。"""
        if not report_id:
            return 0
        with self._connect() as conn:
            if owner_id is not None:
                cur = conn.execute(
                    "UPDATE share_links SET revoked = 1 "
                    "WHERE report_id = ? AND owner_id = ? AND revoked = 0",
                    (report_id, owner_id),
                )
            else:
                cur = conn.execute(
                    "UPDATE share_links SET revoked = 1 "
                    "WHERE report_id = ? AND revoked = 0",
                    (report_id,),
                )
            return cur.rowcount

    # ---- 列表 / 统计 ----

    def list_by_report(self, report_id: str) -> List[ShareLink]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM share_links WHERE report_id = ? ORDER BY created_at DESC",
                (report_id,),
            ).fetchall()
        return [_row_to_link(r) for r in rows]

    def list_by_owner(self, owner_id: str, limit: int = 100) -> List[ShareLink]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM share_links WHERE owner_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (owner_id, limit),
            ).fetchall()
        return [_row_to_link(r) for r in rows]

    def get_stats(self, code: str, days: int = 7) -> Optional[dict]:
        link = self.get(code)
        if link is None:
            return None
        return {
            "code": link.code,
            "report_id": link.report_id,
            "access_count": link.access_count,
            "last_access_at": link.last_access_at,
            "last_access_at_iso": _iso(link.last_access_at)
            if link.last_access_at
            else None,
            "revoked": bool(link.revoked),
            "expired": link.is_expired(),
            "created_at_iso": _iso(link.created_at),
            "expires_at_iso": _iso(link.expires_at) if link.expires_at else None,
            "unique_visitors": self._count_unique_visitors(code=link.code),
            "daily_accesses": self._daily_access_stats(code=link.code, days=days),
        }

    def _count_unique_visitors(
        self,
        *,
        code: Optional[str] = None,
        report_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> int:
        clauses = ["e.visitor_token IS NOT NULL", "e.visitor_token != ''"]
        params: list = []
        join = ""
        if code is not None:
            clauses.append("e.code = ?")
            params.append(code)
        else:
            join = " JOIN share_links l ON l.code = e.code"
            if report_id is not None:
                clauses.append("l.report_id = ?")
                params.append(report_id)
            if owner_id is not None:
                clauses.append("l.owner_id = ?")
                params.append(owner_id)
        query = (
            "SELECT COUNT(DISTINCT e.visitor_token) AS n "
            "FROM share_link_access_events e"
            f"{join} WHERE {' AND '.join(clauses)}"
        )
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row["n"] if row else 0)

    def _daily_access_stats(
        self,
        *,
        code: Optional[str] = None,
        report_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        days: int = 7,
    ) -> List[dict]:
        if days <= 0:
            raise ValueError("days must be > 0")

        params: list = []
        if code is not None:
            query = """
                SELECT
                    DATE(accessed_at, 'unixepoch') AS date,
                    COUNT(*) AS access_count,
                    COUNT(DISTINCT CASE
                        WHEN visitor_token IS NOT NULL AND visitor_token != ''
                        THEN visitor_token
                    END) AS unique_visitors
                FROM share_link_access_events
                WHERE code = ?
                GROUP BY DATE(accessed_at, 'unixepoch')
                ORDER BY DATE(accessed_at, 'unixepoch') ASC
            """
            params.append(code)
        else:
            query = """
                SELECT
                    DATE(e.accessed_at, 'unixepoch') AS date,
                    COUNT(*) AS access_count,
                    COUNT(DISTINCT CASE
                        WHEN e.visitor_token IS NOT NULL AND e.visitor_token != ''
                        THEN e.visitor_token
                    END) AS unique_visitors
                FROM share_link_access_events e
                JOIN share_links l ON l.code = e.code
                WHERE l.report_id = ?
            """
            params.append(report_id)
            if owner_id is not None:
                query += " AND l.owner_id = ?"
                params.append(owner_id)
            query += (
                " GROUP BY DATE(e.accessed_at, 'unixepoch')"
                " ORDER BY DATE(e.accessed_at, 'unixepoch') ASC"
            )

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        daily = [
            {
                "date": row["date"],
                "access_count": int(row["access_count"]),
                "unique_visitors": int(row["unique_visitors"]),
            }
            for row in rows
        ]
        return daily[-days:]

    def get_report_stats(
        self,
        report_id: str,
        owner_id: Optional[str] = None,
        days: int = 7,
    ) -> dict:
        if not report_id:
            raise ValueError("report_id is required")

        if owner_id is None:
            links = self.list_by_report(report_id)
        else:
            links = [
                link
                for link in self.list_by_report(report_id)
                if link.owner_id == owner_id
            ]

        last_access_at = max(
            (link.last_access_at for link in links if link.last_access_at is not None),
            default=None,
        )
        return {
            "report_id": report_id,
            "owner_id": owner_id,
            "total_links": len(links),
            "active_links": sum(1 for link in links if link.is_active()),
            "revoked_links": sum(1 for link in links if link.revoked != 0),
            "expired_links": sum(1 for link in links if link.is_expired()),
            "total_access_count": sum(link.access_count for link in links),
            "unique_visitors": self._count_unique_visitors(
                report_id=report_id,
                owner_id=owner_id,
            ),
            "last_access_at": last_access_at,
            "last_access_at_iso": _iso(last_access_at) if last_access_at else None,
            "daily_accesses": self._daily_access_stats(
                report_id=report_id,
                owner_id=owner_id,
                days=days,
            ),
        }

    # ---- 维护 ----

    def purge_expired(self) -> int:
        """清理过期记录 (T7.1 不强制, 仅供维护)"""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM share_links WHERE expires_at IS NOT NULL AND expires_at < ?",
                (_now(),),
            )
            return cur.rowcount

    def count(self, owner_id: Optional[str] = None) -> int:
        with self._connect() as conn:
            if owner_id is None:
                row = conn.execute("SELECT COUNT(*) AS n FROM share_links").fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) AS n FROM share_links WHERE owner_id = ?",
                    (owner_id,),
                ).fetchone()
        return int(row["n"])


# ---------------------------------------------------------------------------
# 路由辅助 (供 Web 框架 / T7.5 分享页接入)
# ---------------------------------------------------------------------------


def _route_with_svc(
    svc: ShortLinkService,
    code: str,
    password: Optional[str] = None,
    base_url: str = "http://localhost:8000",
) -> dict:
    """route_short_link 的核心逻辑, 接受外部 svc (用于 in-memory 测试)"""
    res = svc.resolve(code, password=password, record_access=True)
    out: dict = {
        "code": code,
        "status": res.status,
        "reason": res.reason,
        "url": f"{base_url.rstrip('/')}/s/{code}",
    }
    if res.ok and res.link is not None:
        out["report_id"] = res.link.report_id
        out["permission"] = res.link.permission
        out["owner_id"] = res.link.owner_id
        out["access_count"] = res.link.access_count
    return out


def route_short_link(
    code: str,
    password: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    db_path: Optional[os.PathLike] = None,
) -> dict:
    """
    模拟 /s/{code} 路由的入口
    返回 JSON-friendly dict, 包含 redirect URL 或错误信息

    用法 (Flask 示意):
        @app.route("/s/<code>")
        def short_link(code):
            return jsonify(route_short_link(code, request.args.get("pwd")))

    参数:
        code       短码 (URL 路径变量)
        password   访问密码 (query/body)
        base_url   用于构造 /s/{code} 完整 URL
        db_path    数据库路径, 默认 DEFAULT_DB_PATH; 测试可覆盖
    """
    svc = ShortLinkService(db_path=db_path)
    return _route_with_svc(svc, code, password=password, base_url=base_url)


def build_url(code: str, base: str = "http://localhost:8000") -> str:
    """生成 /s/{code} 完整 URL"""
    return f"{base.rstrip('/')}/s/{code}"


# ---------------------------------------------------------------------------
# T7.3 权限感知路由: 在 resolve() 之上叠加 report payload 渲染
# ---------------------------------------------------------------------------
# 之所以不放进 route_short_link, 是为了:
#   1. 不破坏 T7.1 / T7.2 已落地的 CLI 脚本与单测签名;
#   2. 报告获取通常需要读盘 / 调 T2/T3 服务, 不在短链接服务职责内,
#      通过 report_loader 回调注入, 让本层保持零业务耦合。
# ---------------------------------------------------------------------------


def route_short_link_with_report(
    code: str,
    password: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    db_path: Optional[os.PathLike] = None,
    *,
    report_loader=None,
    report: Optional[dict] = None,
    include_url: bool = True,
) -> dict:
    """
    在 route_short_link 之上叠加 T7.3 权限感知渲染。

    用法 (Web 路由示意):
        @app.route("/s/<code>")
        def short_link(code):
            def loader(report_id):
                return load_report_from_storage(report_id)
            return jsonify(route_short_link_with_report(
                code,
                password=request.args.get("pwd"),
                base_url=request.host_url.rstrip("/"),
                report_loader=loader,
            ))

    参数:
        code         短码
        password     访问密码 (query/body)
        base_url     构造 /s/{code} 完整 URL
        db_path      SQLite 路径, 默认 DEFAULT_DB_PATH
        report_loader  可选 callable(report_id) -> dict | None
                      用于按 report_id 拉取原始报告数据
        report       可选直接传入报告 dict (优先级高于 report_loader)
        include_url  是否在 payload 中附 share_url

    返回 dict (兼容 T7.1 shape + 扩展字段):
        {
          ...route_short_link() 原样字段 (status, code, reason, url, ...)...
          "rendered": {                    # T7.3 新增
              "permission": "read",
              "policy": {...},
              "visible_fields": [...] | None,
              "payload": {...},            # 字段裁剪 + 姓名脱敏后
              "masked_fields": [...]
          }
        }

    当 resolve() 失败 (not_found / revoked / expired / password_*) 时,
    rendered 不会被计算 — 让 Web 层直接根据 status 返回 401/403/404/410。
    """
    # 延迟 import 避免循环 (permission 模块会 import orders.masking)
    from data.share.permission import render_report_payload

    base = route_short_link(
        code,
        password=password,
        base_url=base_url,
        db_path=db_path,
    )

    # resolve 失败 -> 不渲染 payload, 行为对齐"未授权禁止"原则
    if base.get("status") != STATUS_OK:
        return base

    report_id = base.get("report_id")
    perm = base.get("permission", "read")
    if report is not None:
        report_data = report
    elif report_loader is not None and report_id is not None:
        try:
            report_data = report_loader(report_id)
        except Exception:
            report_data = None
    else:
        report_data = None

    share_url = base.get("url") if include_url else None
    base["rendered"] = render_report_payload(perm, report_data, share_url=share_url)
    return base


# ---------------------------------------------------------------------------
# CLI 直接调用 (python -m data.share.short_link ...) 用作冒烟
# ---------------------------------------------------------------------------


def _self_test() -> None:  # pragma: no cover - 仅 CLI 触发
    svc = ShortLinkService(db_path=":memory:")
    print("=== short_link self test ===")

    # 1. create
    link = svc.create(
        report_id="R-2026-001",
        owner_id="alice",
        permission="read",
        ttl_days=7,
    )
    print(f"created: code={link.code} report_id={link.report_id}")
    assert len(link.code) == DEFAULT_CODE_LEN
    assert all(c in BASE62_ALPHABET for c in link.code)

    # 2. resolve (ok)
    res = svc.resolve(link.code)
    assert res.ok, f"unexpected status: {res.status}"
    assert res.link is not None
    print(f"resolve ok: access_count={res.link.access_count}")

    # 3. revoke
    assert svc.revoke(link.code, owner_id="alice") is True
    res = svc.resolve(link.code)
    assert res.status == STATUS_REVOKED
    print("revoke works")

    # 4. password
    link2 = svc.create(
        report_id="R-2026-002",
        owner_id="bob",
        permission="edit",
        password="s3cr3t",
    )
    res = svc.resolve(link2.code, password=None)
    assert res.status == STATUS_PASSWORD_REQUIRED, res.status
    res = svc.resolve(link2.code, password="wrong")
    assert res.status == STATUS_PASSWORD_WRONG
    res = svc.resolve(link2.code, password="s3cr3t")
    assert res.ok
    print("password works")

    # 5. expire
    link3 = svc.create(
        report_id="R-2026-003",
        owner_id="carol",
        permission="read",
        ttl_seconds=1,
    )
    time.sleep(1.2)
    res = svc.resolve(link3.code)
    assert res.status == STATUS_EXPIRED
    print("expire works")

    # 6. base62 codec sanity
    for n in [0, 1, 61, 62, 62**6 - 1, 62**6]:
        s = base62_encode(n)
        assert base62_decode(s) == n, (n, s)
    print("base62 codec works")

    # 7. route helper (复用同一 in-memory svc, 避免创建新连接)
    out = _route_with_svc(
        svc, link2.code, password="s3cr3t", base_url="https://gk.example.com"
    )
    assert out["status"] == "ok", out
    assert out["url"] == "https://gk.example.com/s/" + link2.code
    print(f"route helper works: {out['url']}")

    print("=== all self tests passed ===")


if __name__ == "__main__":  # pragma: no cover
    _self_test()
