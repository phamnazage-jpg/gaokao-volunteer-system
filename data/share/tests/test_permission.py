"""
分享权限策略单元测试 (T7.3)

覆盖:
- PermissionPolicy.for_permission() 对 read/comment/edit/admin/未知
- render_report_payload() 字段裁剪 + 姓名脱敏
- 兼容 PERM_ADMIN (alias -> edit)
- 路由层 route_short_link_with_report() 在 resolve 失败时不下发 payload

运行:
    python3 -m pytest data/share/tests/test_permission.py -v
    # 或 (无 pytest 时)
    python3 data/share/tests/test_permission.py
"""

import sys
import tempfile
import os
import uuid
from pathlib import Path

# 让 data.share 可被 import
PROJ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJ))

from data.share.permission import (  # noqa: E402
    POLICY_ADMIN_ALIAS,
    PermissionPolicy,
    is_known_permission,
    render_report_payload,
    supported_permissions,
)
from data.share.short_link import (  # noqa: E402
    PERM_COMMENT,
    PERM_EDIT,
    PERM_READ,
    STATUS_NOT_FOUND,
    STATUS_OK,
    STATUS_PASSWORD_REQUIRED,
    STATUS_REVOKED,
    ShortLinkService,
    route_short_link_with_report,
)


# ---------------------------------------------------------------------------
# 自定义 runner (兼容无 pytest 环境)
# ---------------------------------------------------------------------------

_TMP_DBS: list = []


def make_svc() -> ShortLinkService:
    fd, db = tempfile.mkstemp(prefix=f"perm_test_{uuid.uuid4().hex[:8]}_", suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    return ShortLinkService(db_path=db)


def cleanup_tmp_dbs():
    for db in _TMP_DBS:
        try:
            os.remove(db)
        except OSError:
            pass


_PASS = 0
_FAIL = 0
_ERRORS: list = []


def _eq(actual, expected, msg=""):
    global _PASS, _FAIL
    if actual == expected:
        _PASS += 1
    else:
        _FAIL += 1
        _ERRORS.append(f"FAIL: {msg or 'eq'}: {actual!r} != {expected!r}")


def _truthy(v, msg):
    global _PASS, _FAIL
    if v:
        _PASS += 1
    else:
        _FAIL += 1
        _ERRORS.append(f"FAIL: {msg}: {v!r}")


def _has(d, key, msg):
    _truthy(key in d, f"{msg}: {key!r} in dict")


# ---------------------------------------------------------------------------
# PermissionPolicy: 静态策略
# ---------------------------------------------------------------------------


def test_policy_supported_permissions():
    perms = set(supported_permissions())
    # 必须包含 3 级业务 + admin alias 兼容
    _eq(
        {"read", "comment", "edit", "admin"}.issubset(perms),
        True,
        "supported_permissions contains read/comment/edit/admin",
    )


def test_policy_admin_alias():
    _eq(POLICY_ADMIN_ALIAS, "edit", "admin aliases to edit")


def test_policy_read_caps():
    p = PermissionPolicy.for_permission("read")
    _eq(p.can_view, True, "read can_view")
    _eq(p.can_comment, False, "read cannot comment")
    _eq(p.can_edit, False, "read cannot edit")
    _eq(p.mask_name, True, "read masks name")
    _truthy(p.visible_fields is not None, "read has explicit visible_fields")


def test_policy_comment_caps():
    p = PermissionPolicy.for_permission("comment")
    _eq(p.can_view, True, "comment can_view")
    _eq(p.can_comment, True, "comment can comment")
    _eq(p.can_edit, False, "comment cannot edit")
    _eq(p.mask_name, True, "comment masks name")
    _truthy(p.visible_fields is not None, "comment has explicit visible_fields")


def test_policy_edit_caps():
    p = PermissionPolicy.for_permission("edit")
    _eq(p.can_view, True, "edit can_view")
    _eq(p.can_comment, True, "edit can comment")
    _eq(p.can_edit, True, "edit can edit")
    _eq(p.mask_name, False, "edit does NOT mask name")
    _eq(p.visible_fields, None, "edit visible_fields=None (default pass)")


def test_policy_admin_alias_to_edit():
    p = PermissionPolicy.for_permission("admin")
    _eq(p.permission, "edit", "admin permission normalized to edit")
    _eq(p.can_edit, True, "admin can edit (via alias)")
    _eq(p.mask_name, False, "admin does NOT mask name (via alias)")


def test_policy_unknown_permission_falls_back_to_read():
    """未知的 permission 必须落到最严格的 read 拒止策略, 不允许越权。"""
    p = PermissionPolicy.for_permission("superuser")
    _eq(p.permission, "read", "unknown perm stored as 'read'")
    _eq(p.can_view, True, "fallback: view OK (for nicer UX)")
    _eq(p.can_comment, False, "fallback: cannot comment")
    _eq(p.can_edit, False, "fallback: cannot edit")
    _eq(p.mask_name, True, "fallback: mask name")
    _truthy(p.is_restrictive_fallback, "is_restrictive_fallback=True")


def test_policy_empty_permission_falls_back():
    p = PermissionPolicy.for_permission("")
    _eq(p.is_restrictive_fallback, True, "empty perm triggers fallback")


def test_policy_case_insensitive():
    p1 = PermissionPolicy.for_permission("READ")
    p2 = PermissionPolicy.for_permission("read")
    _eq(p1.can_edit, p2.can_edit, "case insensitive read parity")
    _eq(p1.permission, "read", "uppercase normalized")


def test_is_known_permission():
    _eq(is_known_permission("read"), True, "read is known")
    _eq(is_known_permission("edit"), True, "edit is known")
    _eq(is_known_permission("admin"), True, "admin is known")
    _eq(is_known_permission("superuser"), False, "superuser unknown")
    _eq(is_known_permission(""), False, "empty unknown")


def test_allows_field_for_read():
    p = PermissionPolicy.for_permission("read")
    _eq(p.allows_field("recommendations"), False, "read hides recommendations")
    _eq(p.allows_field("report_id"), True, "read allows report_id")
    _eq(p.allows_field("score"), False, "read hides score")


def test_allows_field_for_edit():
    p = PermissionPolicy.for_permission("edit")
    _eq(p.allows_field("recommendations"), True, "edit allows recommendations")
    _eq(p.allows_field("candidate_phone"), True, "edit allows phone")
    _eq(
        p.allows_field("password_hash"),
        True,
        "edit: visible_fields=None -> pass (上层负责拦截 hash)",
    )


def test_allows_field_for_no_view():
    """can_view=False 时, 即便字段在 visible_fields 内也不应暴露。"""
    p = PermissionPolicy(
        permission="nop",
        can_view=False,
        can_comment=False,
        can_edit=False,
        mask_name=True,
        visible_fields=frozenset({"report_id"}),
    )
    _eq(p.allows_field("report_id"), False, "no view => no field")


def test_can_helper():
    p = PermissionPolicy.for_permission("edit")
    _eq(p.can("view"), True, "can('view')")
    _eq(p.can("comment"), True, "can('comment')")
    _eq(p.can("edit"), True, "can('edit')")
    _eq(p.can("admin"), False, "can('admin') unknown action -> False")


# ---------------------------------------------------------------------------
# render_report_payload: 字段裁剪 + 姓名脱敏
# ---------------------------------------------------------------------------


_SAMPLE_REPORT = {
    "report_id": "R-2026-001",
    "title": "578分 湖南 志愿方案",
    "summary": "冲稳保 45 志愿",
    "candidate_name": "李明",
    "customer_name": "李明",
    "score": 578,
    "rank": 12345,
    "year": 2026,
    "province": "湖南",
    "recommendations": [{"school": "江西财经大学", "major": "会计学", "prob": 0.35}],
    "volunteers": [{"group": 1, "school": "江西财经大学", "majors": ["会计学"]}],
    "candidate_phone": "13800001234",
    "candidate_id_card": "430102200801011234",
    "password_hash": "should-not-leak-via-policy",
    "internal_note": "should-not-leak-via-policy",
}


def test_render_read_payload():
    out = render_report_payload("read", _SAMPLE_REPORT)
    _eq(out["permission"], "read", "permission echoed")
    _eq(out["policy"]["can_view"], True, "policy.can_view")
    _eq(out["policy"]["can_comment"], False, "policy.can_comment")
    _eq(out["policy"]["mask_name"], True, "policy.mask_name")
    payload = out["payload"]
    # 可见
    _has(payload, "report_id", "read: report_id visible")
    # 不可见: title / recommendations / score / phone / hash
    _eq("title" in payload, False, "read: title hidden")
    _eq("recommendations" in payload, False, "read: recommendations hidden")
    _eq("score" in payload, False, "read: score hidden")
    _eq("candidate_phone" in payload, False, "read: phone hidden")
    _eq("password_hash" in payload, False, "read: hash hidden")
    # 姓名可见但必须脱敏
    _eq(payload.get("candidate_name"), "李*", "read: candidate_name masked")
    _eq(payload.get("customer_name"), "李*", "read: customer_name masked")
    _eq(
        sorted(out["masked_fields"]),
        ["candidate_name", "customer_name"],
        "read: masked_fields reports masked names",
    )


def test_render_comment_payload():
    out = render_report_payload("comment", _SAMPLE_REPORT)
    payload = out["payload"]
    # 可见: 报告正文类
    _has(payload, "title", "comment: title visible")
    _has(payload, "summary", "comment: summary visible")
    _has(payload, "score", "comment: score visible")
    _has(payload, "rank", "comment: rank visible")
    _has(payload, "recommendations", "comment: recommendations visible")
    _has(payload, "volunteers", "comment: volunteers visible")
    # 不可见: PII / 私密字段
    _eq("candidate_phone" in payload, False, "comment: phone hidden")
    _eq("candidate_id_card" in payload, False, "comment: id_card hidden")
    _eq("password_hash" in payload, False, "comment: hash hidden")
    _eq("internal_note" in payload, False, "comment: internal note hidden")
    # 姓名应被脱敏显示，满足分享页 UI 的“张**”效果
    _eq(payload.get("candidate_name"), "李*", "comment: candidate_name masked")
    _eq(payload.get("customer_name"), "李*", "comment: customer_name masked")
    _eq(
        sorted(out["masked_fields"]),
        ["candidate_name", "customer_name"],
        "comment: masked_fields reports masked names",
    )


def test_render_edit_payload():
    out = render_report_payload("edit", _SAMPLE_REPORT)
    payload = out["payload"]
    _eq(out["policy"]["mask_name"], False, "edit: no mask")
    # edit 默认通过业务字段，但内部敏感字段仍不可外暴
    _has(payload, "candidate_name", "edit: candidate_name visible")
    _has(payload, "candidate_phone", "edit: phone visible")
    _has(payload, "candidate_id_card", "edit: id_card visible")
    _eq("password_hash" in payload, False, "edit: password_hash hidden")
    _eq("internal_note" in payload, False, "edit: internal_note hidden")
    _eq(payload["candidate_name"], "李明", "edit: name intact")
    _eq(out["masked_fields"], [], "edit: no fields masked")


def test_render_edit_name_unmasked_in_payload():
    """编辑权限下, 报告里所有 *_name 字段应原样输出。"""
    report = {
        "candidate_name": "欧阳明月",
        "customer_name": "欧阳明月",
        "score": 600,
    }
    out = render_report_payload("edit", report)
    _eq(out["payload"]["candidate_name"], "欧阳明月", "edit: 4-char name intact")
    _eq(out["payload"]["customer_name"], "欧阳明月", "edit: customer_name intact")


def test_render_admin_aliases_to_edit():
    """admin 视为 edit, 姓名不脱敏, 字段全通过。"""
    out = render_report_payload("admin", _SAMPLE_REPORT)
    _eq(out["permission"], "edit", "admin perm normalized to edit in payload")
    _eq(out["payload"]["candidate_name"], "李明", "admin: name intact")
    _eq(out["policy"]["can_edit"], True, "admin: can edit")


def test_render_mask_name_when_name_field_in_visible():
    """分享页公开展示时, 3 字中文名应收敛为“姓 + **”。"""
    from data.share.permission import _POLICY_TABLE  # noqa

    original = _POLICY_TABLE["read"]["visible_fields"]
    try:
        _POLICY_TABLE["read"]["visible_fields"] = set(original) | {"candidate_name"}
        out = render_report_payload("read", {"candidate_name": "张三丰"})
        _eq(
            out["payload"]["candidate_name"],
            "张**",
            "share-name masking collapses 3-char CJK names to surname + **",
        )
        _eq(
            "candidate_name" in out["masked_fields"],
            True,
            "candidate_name reported in masked_fields",
        )
    finally:
        _POLICY_TABLE["read"]["visible_fields"] = original


def test_render_mask_name_non_cjk_collapses_to_constant():
    out = render_report_payload("read", {"candidate_name": "Alice"})
    _eq(
        out["payload"]["candidate_name"],
        "**",
        "non-cjk share name should not leak length",
    )
    _eq(
        "candidate_name" in out["masked_fields"],
        True,
        "non-cjk masked field still reported",
    )


def test_render_handles_none_report():
    out = render_report_payload("read", None)
    _eq(out["payload"], {}, "None report -> empty payload (still renders)")
    _eq(out["masked_fields"], [], "no fields masked on None report")
    _eq(out["policy"]["can_view"], True, "policy still echoed on None report")


def test_render_handles_non_dict_report():
    """非 dict 输入应被视作无报告, 不抛错。"""
    out = render_report_payload("edit", "not a dict")
    _eq(out["payload"], {}, "string report -> empty payload")


def test_render_share_url_injection():
    out = render_report_payload(
        "read", {"report_id": "R-1"}, share_url="https://x/s/ABC"
    )
    _eq(
        out["payload"].get("share_url"),
        "https://x/s/ABC",
        "share_url injected into payload when provided",
    )


def test_render_visible_fields_echo():
    out = render_report_payload("comment", _SAMPLE_REPORT)
    _truthy(out["visible_fields"] is not None, "comment: visible_fields list echoed")
    _eq("title" in out["visible_fields"], True, "title in visible_fields")


def test_render_edit_visible_fields_none():
    out = render_report_payload("edit", _SAMPLE_REPORT)
    _eq(out["visible_fields"], None, "edit: visible_fields=None means pass-through")


# ---------------------------------------------------------------------------
# route_short_link_with_report: 端到端
# ---------------------------------------------------------------------------


def test_route_with_report_read():
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", owner_id="alice", permission=PERM_READ)
        report = dict(_SAMPLE_REPORT, report_id="R-1")
        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report=report,
        )
        _eq(out["status"], STATUS_OK, "route ok")
        _has(out, "rendered", "rendered key present")
        _eq(out["rendered"]["permission"], "read", "rendered permission")
        _eq(out["url"], "https://gk.example.com/s/" + link.code, "url")
        _has(out["rendered"]["payload"], "report_id", "report_id in payload")
    finally:
        os.remove(db)


def test_route_with_report_loader_callback():
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-9", permission=PERM_COMMENT)
        loaded = {}

        def loader(report_id):
            loaded["report_id"] = report_id
            return {"report_id": report_id, "title": "from-loader"}

        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report_loader=loader,
        )
        _eq(loaded.get("report_id"), "R-9", "loader called with report_id")
        _eq(
            out["rendered"]["payload"]["title"], "from-loader", "loader result rendered"
        )
    finally:
        os.remove(db)


def test_route_with_report_loader_exception():
    """loader 抛错时, 路由不应整体崩溃, 仍下发的只是空 payload。"""
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", permission=PERM_EDIT)

        def boom(_):
            raise RuntimeError("storage down")

        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report_loader=boom,
        )
        _eq(out["status"], STATUS_OK, "still ok status")
        # loader 失败时: report_data=None, payload 走"无报告"分支;
        # 仍保留 share_url 方便前端"复制链接"按钮。
        _eq(
            "report_id" in out["rendered"]["payload"],
            False,
            "no report_id when loader fails",
        )
        _eq(
            "candidate_name" in out["rendered"]["payload"],
            False,
            "no name when loader fails",
        )
        _has(
            out["rendered"]["payload"],
            "share_url",
            "share_url still present when loader fails",
        )
    finally:
        os.remove(db)


def test_route_with_report_resolve_failure_no_payload():
    """resolve 失败时, 不应下发 rendered (避免泄露元数据)。"""
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        # 不创建 -> not_found
        out = route_short_link_with_report(
            "ZZZZZZ",
            base_url="https://gk.example.com",
            db_path=db,
            report={"report_id": "R-1"},
        )
        _eq(out["status"], STATUS_NOT_FOUND, "not_found")
        _eq("rendered" in out, False, "no rendered on failure")
    finally:
        os.remove(db)


def test_route_with_report_password_required_no_payload():
    """密码未提供 -> password_required, 不下发 rendered。"""
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", password="s3cr3t")
        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report={"report_id": "R-1"},
        )
        _eq(out["status"], STATUS_PASSWORD_REQUIRED, "password_required")
        _eq("rendered" in out, False, "no rendered when password required")
    finally:
        os.remove(db)


def test_route_with_report_revoked_no_payload():
    """revoked 时, 不应下发 rendered。"""
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", owner_id="alice")
        svc.revoke(link.code, owner_id="alice")
        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report={"report_id": "R-1"},
        )
        _eq(out["status"], STATUS_REVOKED, "revoked")
        _eq("rendered" in out, False, "no rendered when revoked")
    finally:
        os.remove(db)


def test_route_with_report_include_url_false():
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", permission=PERM_EDIT)
        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report={"report_id": "R-1"},
            include_url=False,
        )
        _eq(
            "share_url" in out["rendered"]["payload"],
            False,
            "share_url omitted when include_url=False",
        )
    finally:
        os.remove(db)


def test_route_with_report_report_arg_priority():
    """显式 report 参数优先级高于 loader。"""
    fd, db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _TMP_DBS.append(db)
    try:
        svc = ShortLinkService(db_path=db)
        link = svc.create(report_id="R-1", permission=PERM_EDIT)

        def loader(_):
            return {"title": "from-loader"}

        out = route_short_link_with_report(
            link.code,
            base_url="https://gk.example.com",
            db_path=db,
            report={"title": "from-arg"},
            report_loader=loader,
        )
        _eq(
            out["rendered"]["payload"]["title"],
            "from-arg",
            "explicit report arg wins over loader",
        )
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
        cleanup_tmp_dbs()
        sys.exit(1)
    print("ALL TESTS PASSED")
    cleanup_tmp_dbs()
    sys.exit(0)


if __name__ == "__main__":
    main()
