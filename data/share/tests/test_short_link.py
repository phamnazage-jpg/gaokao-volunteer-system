"""
短链接服务单元测试 (T7.1)

运行:
    python3 -m pytest data/share/tests/test_short_link.py -v
    # 或 (无 pytest 时)
    python3 data/share/tests/test_short_link.py
"""

import sys
import time
from pathlib import Path

# 让 data.share 可被 import
PROJ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJ))

import tempfile
import os
import uuid

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
        all(l.report_id == "R-1" for l in links),
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
        for e in _ERRORS:
            print(f"  {e}")
        sys.exit(1)
    print("ALL TESTS PASSED")
    cleanup_tmp_dbs()
    sys.exit(0)


if __name__ == "__main__":
    main()
