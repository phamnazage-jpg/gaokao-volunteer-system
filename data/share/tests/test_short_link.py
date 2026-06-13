"""
短链接服务单元测试 (T7.1)

运行:
    python3 -m pytest data/share/tests/test_short_link.py -v
    # 或 (无 pytest 时)
    python3 data/share/tests/test_short_link.py
"""

import hashlib
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Callable

# 让 data.share 可被 import
PROJ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJ))

import data.share.short_link as short_link_module  # noqa: E402
from data.share.short_link import (  # noqa: E402
    BASE62_ALPHABET,
    DEFAULT_CODE_LEN,
    PERM_COMMENT,
    PERM_EDIT,
    PERM_READ,
    STATUS_EXPIRED,
    STATUS_NOT_FOUND,
    STATUS_OK,
    STATUS_PASSWORD_REQUIRED,
    STATUS_PASSWORD_WRONG,
    STATUS_REVOKED,
    ShortLinkService,
    base62_decode,
    base62_encode,
    build_url,
    generate_code,
    route_short_link,
)

# in-memory DB 共享 cache 会跨实例泄漏, 测试中用临时文件更安全
_TMP_DBS: list = []


def make_svc() -> ShortLinkService:
    """为每个测试创建独立的临时 SQLite 文件 (避免 in-memory 共享)"""
    fd, db = tempfile.mkstemp(
        prefix=f"shortlink_test_{uuid.uuid4().hex[:8]}_", suffix=".db"
    )
    os.close(fd)
    _TMP_DBS.append(db)
    return ShortLinkService(db_path=db)


def cleanup_tmp_dbs():
    for db in _TMP_DBS:
        try:
            os.remove(db)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# 简易测试运行器 (兼容无 pytest 环境)
# ---------------------------------------------------------------------------

_PASS = 0
_FAIL = 0
_ERRORS: list = []


def _eq(a, b, msg=""):
    global _PASS, _FAIL
    if a == b:
        _PASS += 1
    else:
        _FAIL += 1
        _ERRORS.append(f"FAIL: {msg or 'equality'}: {a!r} != {b!r}")


def _truthy(v, msg):
    global _PASS, _FAIL
    if v:
        _PASS += 1
    else:
        _FAIL += 1
        _ERRORS.append(f"FAIL: {msg}: {v!r}")


def _raises(fn, exc_type, msg):
    global _PASS, _FAIL
    try:
        fn()
    except exc_type:
        _PASS += 1
        return
    except Exception as e:
        _FAIL += 1
        _ERRORS.append(f"FAIL: {msg}: expected {exc_type}, got {type(e).__name__}: {e}")
        return
    _FAIL += 1
    _ERRORS.append(f"FAIL: {msg}: no exception raised")


# ---------------------------------------------------------------------------
# base62 codec
# ---------------------------------------------------------------------------


def test_base62_codec_basic():
    _eq(base62_encode(0), "0", "0 -> '0'")
    # 字母表 = digits + ascii_uppercase + ascii_lowercase
    # index 0-9 = '0'-'9', 10-35 = 'A'-'Z', 36-61 = 'a'-'z'
    _eq(base62_encode(9), "9", "9 -> '9'")
    _eq(base62_encode(10), "A", "10 -> 'A'")
    _eq(base62_encode(35), "Z", "35 -> 'Z'")
    _eq(base62_encode(36), "a", "36 -> 'a'")
    _eq(base62_encode(61), "z", "61 -> 'z'")
    _eq(base62_encode(62), "10", "62 -> '10'")
    _eq(base62_encode(62 * 62), "100", "62^2 -> '100'")
    _truthy(len(base62_encode(62**6 - 1)) == 6, "62^6-1 fits in 6 chars")


def test_base62_codec_roundtrip():
    for n in [
        0,
        1,
        9,
        35,
        36,
        61,
        62,
        62**2,
        62**3,
        62**4,
        62**5,
        62**6,
        62**6 + 12345,
    ]:
        s = base62_encode(n)
        _eq(base62_decode(s), n, f"roundtrip {n}")


def test_base62_invalid_char():
    _raises(lambda: base62_decode("abc!"), ValueError, "invalid char raises")
    _raises(lambda: base62_decode(""), ValueError, "empty raises")
    _raises(lambda: base62_encode(-1), ValueError, "negative raises")


def test_generate_code():
    for length in [4, 6, 8, 16]:
        c = generate_code(length)
        _eq(len(c), length, f"code length {length}")
        _truthy(
            all(ch in BASE62_ALPHABET for ch in c),
            f"code chars in alphabet (len={length})",
        )
    _raises(lambda: generate_code(3), ValueError, "len=3 rejected")
    _raises(lambda: generate_code(17), ValueError, "len=17 rejected")


# ---------------------------------------------------------------------------
# 服务: 创建 / 解析
# ---------------------------------------------------------------------------


def test_create_basic():
    svc = make_svc()
    link = svc.create(report_id="R-1", owner_id="alice")
    _eq(len(link.code), DEFAULT_CODE_LEN, "default code length")
    _eq(link.report_id, "R-1", "report_id")
    _eq(link.owner_id, "alice", "owner_id")
    _eq(link.permission, PERM_COMMENT, "default permission")
    _eq(link.revoked, 0, "not revoked")
    _eq(link.access_count, 0, "no access yet")


def test_create_collision_retry():
    """验证 create() 在碰撞时会重试 (此处不模拟碰撞, 只验证正常路径)"""
    svc = make_svc()
    codes = set()
    for i in range(50):
        link = svc.create(report_id=f"R-{i}")
        _truthy(link.code not in codes, f"code {link.code} unique")
        codes.add(link.code)


def test_get_missing():
    svc = make_svc()
    _eq(svc.get(""), None, "empty code returns None")
    _eq(svc.get("NOTHERE"), None, "missing code returns None")


def test_resolve_ok():
    svc = make_svc()
    link = svc.create(report_id="R-1", owner_id="alice", permission=PERM_READ)
    res = svc.resolve(link.code)
    _eq(res.status, STATUS_OK, "resolve ok")
    _eq(res.link.report_id, "R-1", "resolve report_id")
    _eq(res.link.access_count, 1, "resolve bumps access_count to 1")
    _eq(res.link.last_access_at is not None, True, "last_access_at set")


def test_resolve_dry_run():
    svc = make_svc()
    link = svc.create(report_id="R-1")
    res = svc.resolve(link.code, record_access=False)
    _eq(res.status, STATUS_OK, "dry-run ok")
    _eq(res.link.access_count, 0, "dry-run keeps access_count 0")


def test_resolve_not_found():
    svc = make_svc()
    res = svc.resolve("ZZZZZZ")
    _eq(res.status, STATUS_NOT_FOUND, "not_found")
    _eq(res.link, None, "no link object")


def test_resolve_password_required():
    svc = make_svc()
    link = svc.create(report_id="R-1", password="s3cr3t")
    res = svc.resolve(link.code)
    _eq(res.status, STATUS_PASSWORD_REQUIRED, "password_required")
    res = svc.resolve(link.code, password="wrong")
    _eq(res.status, STATUS_PASSWORD_WRONG, "password_wrong")
    res = svc.resolve(link.code, password="s3cr3t")
    _eq(res.status, STATUS_OK, "correct pwd ok")


def test_create_password_uses_pbkdf2_storage_format():
    svc = make_svc()
    link = svc.create(report_id="R-1", password="s3cr3t")
    _truthy(link.password_hash is not None, "password hash stored")
    assert link.password_hash is not None
    _truthy("$" in link.password_hash, "pbkdf2 format contains separator")
    salt_hex, digest_hex = link.password_hash.split("$", 1)
    _eq(len(salt_hex), 32, "salt is 16 bytes hex")
    _eq(len(digest_hex), 64, "digest is 32 bytes hex")


def test_resolve_legacy_sha256_hash_migrates_to_pbkdf2():
    svc = make_svc()
    link = svc.create(report_id="R-1", password="s3cr3t")
    legacy_hash = hashlib.sha256("s3cr3t".encode("utf-8")).hexdigest()
    with svc._connect() as conn:
        conn.execute(
            "UPDATE share_links SET password_hash = ? WHERE code = ?",
            (legacy_hash, link.code),
        )

    res = svc.resolve(link.code, password="s3cr3t")
    _eq(res.status, STATUS_OK, "legacy sha256 password still resolves")
    migrated = svc.get(link.code)
    _truthy(migrated is not None, "link still exists after migration")
    assert migrated is not None
    _truthy(migrated.password_hash is not None, "migrated hash stored")
    assert migrated.password_hash is not None
    _truthy("$" in migrated.password_hash, "legacy hash upgraded to pbkdf2")
    _truthy(
        migrated.password_hash != legacy_hash,
        "migrated hash no longer equals raw sha256 hex",
    )


def test_wrong_password_does_not_migrate_legacy_hash():
    svc = make_svc()
    link = svc.create(report_id="R-1", password="s3cr3t")
    legacy_hash = hashlib.sha256("s3cr3t".encode("utf-8")).hexdigest()
    with svc._connect() as conn:
        conn.execute(
            "UPDATE share_links SET password_hash = ? WHERE code = ?",
            (legacy_hash, link.code),
        )

    res = svc.resolve(link.code, password="wrong")
    _eq(res.status, STATUS_PASSWORD_WRONG, "wrong legacy password rejected")
    unchanged = svc.get(link.code)
    _truthy(unchanged is not None, "link still exists after wrong password")
    assert unchanged is not None
    _eq(
        unchanged.password_hash,
        legacy_hash,
        "wrong password keeps legacy hash unchanged",
    )


def test_resolve_expired():
    svc = make_svc()
    link = svc.create(report_id="R-1", ttl_seconds=1)
    res = svc.resolve(link.code)
    _eq(res.status, STATUS_OK, "fresh ok")
    time.sleep(1.2)
    res = svc.resolve(link.code)
    _eq(res.status, STATUS_EXPIRED, "expired after ttl")


def test_resolve_revoked():
    svc = make_svc()
    link = svc.create(report_id="R-1", owner_id="alice")
    _truthy(svc.revoke(link.code, owner_id="alice"), "revoke returns True")
    res = svc.resolve(link.code)
    _eq(res.status, STATUS_REVOKED, "revoked")
    # 重复 revoke
    _truthy(not svc.revoke(link.code, owner_id="alice"), "double revoke returns False")


def test_revoke_owner_check():
    svc = make_svc()
    link = svc.create(report_id="R-1", owner_id="alice")
    _truthy(not svc.revoke(link.code, owner_id="bob"), "wrong owner rejected")
    res = svc.resolve(link.code)
    _eq(res.status, STATUS_OK, "wrong-owner revoke doesn't actually revoke")


def test_ttl_days():
    svc = make_svc()
    link = svc.create(report_id="R-1", ttl_days=1)
    _truthy(link.expires_at is not None, "ttl_days sets expires_at")
    _truthy(link.expires_at > link.created_at, "expires_at > created_at")


def test_ttl_exclusive():
    svc = make_svc()
    _raises(
        lambda: svc.create(report_id="R-1", ttl_seconds=60, ttl_days=1),
        ValueError,
        "ttl_seconds & ttl_days exclusive",
    )
    _raises(
        lambda: svc.create(report_id="R-1", ttl_seconds=0),
        ValueError,
        "ttl_seconds > 0",
    )


def test_invalid_permission():
    svc = make_svc()
    _raises(
        lambda: svc.create(report_id="R-1", permission="superuser"),
        ValueError,
        "invalid permission rejected",
    )


def test_required_report_id():
    svc = make_svc()
    _raises(
        lambda: svc.create(report_id=""),
        ValueError,
        "empty report_id rejected",
    )


# ---------------------------------------------------------------------------
# 列表 / 统计 / 维护
# ---------------------------------------------------------------------------


def test_list_by_report():
    svc = make_svc()
    svc.create(report_id="R-1")
    svc.create(report_id="R-1", permission=PERM_EDIT)
    svc.create(report_id="R-2")
    links = svc.list_by_report("R-1")
    _eq(len(links), 2, "list_by_report filters correctly")
    _truthy(
        all(link.report_id == "R-1" for link in links),
        "all links belong to R-1",
    )


def test_list_by_owner():
    svc = make_svc()
    svc.create(report_id="R-1", owner_id="alice")
    svc.create(report_id="R-2", owner_id="alice")
    svc.create(report_id="R-3", owner_id="bob")
    links = svc.list_by_owner("alice")
    _eq(len(links), 2, "alice has 2 links")
    links = svc.list_by_owner("bob")
    _eq(len(links), 1, "bob has 1 link")


def test_stats():
    svc = make_svc()
    link = svc.create(report_id="R-1")
    svc.resolve(link.code)
    svc.resolve(link.code)
    stats = svc.get_stats(link.code)
    _truthy(stats is not None, "stats exists")
    _eq(stats["access_count"], 2, "access_count=2")
    _eq(stats["code"], link.code, "stats code matches")
    _eq(svc.get_stats("NOTHERE"), None, "missing stats -> None")


def test_revoke_by_report():
    svc = make_svc()
    a = svc.create(report_id="R-1", owner_id="alice")
    b = svc.create(report_id="R-1", owner_id="alice")
    c = svc.create(report_id="R-1", owner_id="bob")
    d = svc.create(report_id="R-2", owner_id="alice")

    _eq(svc.revoke_by_report("R-1", owner_id="alice"), 2, "revoke 2 alice links")
    _eq(svc.resolve(a.code).status, STATUS_REVOKED, "alice link A revoked")
    _eq(svc.resolve(b.code).status, STATUS_REVOKED, "alice link B revoked")
    _eq(svc.resolve(c.code).status, STATUS_OK, "bob link untouched")
    _eq(svc.resolve(d.code).status, STATUS_OK, "other report untouched")
    _eq(svc.revoke_by_report("R-1", owner_id="alice"), 0, "idempotent second revoke")


def test_stats_include_daily_accesses_and_unique_visitors():
    svc = make_svc()
    link = svc.create(report_id="R-1")
    original_now = short_link_module._now
    try:
        timestamps = [
            1718064000.0,  # 2024-06-11 UTC
            1718067600.0,  # 2024-06-11 UTC
            1718150400.0,  # 2024-06-12 UTC
        ]
        visitors = ["wechat-openid-1", "wechat-openid-1", "wechat-openid-2"]

        def _fixed_now(ts: float) -> Callable[[], float]:
            return lambda: ts

        for ts, visitor in zip(timestamps, visitors):
            short_link_module._now = _fixed_now(ts)
            svc._bump_access(link.code, visitor_token=visitor)
    finally:
        short_link_module._now = original_now

    stats = svc.get_stats(link.code, days=2)
    _eq(stats["access_count"], 3, "access_count aggregates event log")
    _eq(stats["unique_visitors"], 2, "unique visitors dedup by visitor_token")
    _eq(
        stats["daily_accesses"],
        [
            {"date": "2024-06-11", "access_count": 2, "unique_visitors": 1},
            {"date": "2024-06-12", "access_count": 1, "unique_visitors": 1},
        ],
        "daily stats grouped by UTC day",
    )

    report_stats = svc.get_report_stats("R-1", days=2)
    _eq(report_stats["total_links"], 1, "report tracks link count")
    _eq(report_stats["total_access_count"], 3, "report total accesses sums links")
    _eq(report_stats["unique_visitors"], 2, "report unique visitors deduped")
    _eq(
        report_stats["daily_accesses"],
        stats["daily_accesses"],
        "report reuses daily aggregation",
    )


def test_purge_expired():
    svc = make_svc()
    svc.create(report_id="R-1", ttl_seconds=1)
    svc.create(report_id="R-2")  # permanent
    time.sleep(1.2)
    n = svc.purge_expired()
    _eq(n, 1, "purged 1 expired")
    _eq(svc.count(), 1, "permanent link remains")


def test_count():
    svc = make_svc()
    _eq(svc.count(), 0, "empty db count=0")
    svc.create(report_id="R-1", owner_id="alice")
    svc.create(report_id="R-2", owner_id="alice")
    svc.create(report_id="R-3", owner_id="bob")
    _eq(svc.count(), 3, "total 3")
    _eq(svc.count(owner_id="alice"), 2, "alice 2")


# ---------------------------------------------------------------------------
# 路由辅助
# ---------------------------------------------------------------------------


def test_build_url():
    _eq(
        build_url("ABC123"),
        "http://localhost:8000/s/ABC123",
        "build_url default base",
    )
    _eq(
        build_url("ABC123", base="https://gk.example.com/"),
        "https://gk.example.com/s/ABC123",
        "build_url custom base (trailing slash stripped)",
    )


def test_route_short_link():
    """route_short_link 走指定 db; 用 temp file 隔离"""
    import tempfile
    import os

    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", password="s3cr3t")
        # OK
        out = route_short_link(
            link.code,
            password="s3cr3t",
            base_url="https://gk.example.com",
            db_path=db,
        )
        _eq(out["status"], STATUS_OK, "route ok")
        _eq(out["report_id"], "R-1", "route returns report_id")
        _eq(out["url"], "https://gk.example.com/s/" + link.code, "route url")
        # password_required
        out = route_short_link(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
        )
        _eq(out["status"], STATUS_PASSWORD_REQUIRED, "route pwd_required")
        # not_found
        out = route_short_link(
            "ZZZZZZ",
            base_url="https://gk.example.com",
            db_path=db,
        )
        _eq(out["status"], STATUS_NOT_FOUND, "route not_found")
    finally:
        os.remove(db)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    test_funcs = [
        v for k, v in globals().items() if k.startswith("test_") and callable(v)
    ]
    for fn in test_funcs:
        try:
            fn()
        except Exception as e:
            global _FAIL
            _FAIL += 1
            _ERRORS.append(f"ERROR in {fn.__name__}: {type(e).__name__}: {e}")

    print()
    print(f"PASS: {_PASS}")
    print(f"FAIL: {_FAIL}")
    if _ERRORS:
        print()
        for err in _ERRORS:
            print(f"  {err}")
        sys.exit(1)
    print("ALL TESTS PASSED")
    cleanup_tmp_dbs()
    sys.exit(0)


if __name__ == "__main__":
    main()
