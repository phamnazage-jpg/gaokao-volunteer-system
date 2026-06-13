"""
高考志愿填报系统 - 分享权限策略 (T7.3)

职责: 把 ShortLinkService.permission 字段 (read/comment/edit) 翻译成
"前端可不可以点编辑/可不可以提交评论/可见哪些字段" 的策略对象。

设计目标:
- 单测友好: 纯函数 + dataclass, 不依赖 DB / Web 框架。
- 关注点分离: 短链接服务只管"短码 → 报告元数据"；策略层只管"权限 → UI 能力"。
- 默认安全: 未知 permission 一律按最严格的"只读 + 全脱敏"处理, 不允许越权。

与 masking 的关系:
- data.orders.masking.mask_name 提供基础姓名脱敏能力。
- 本模块负责 "在哪个 permission 等级下要不要遮" 的策略决策。
- 分享页是公开场景，因此在基础脱敏之上再做更保守的收敛，保证输出符合
  T7.3/T7.5 的 "张**" 风格约束。

层级 (T7.3 范围, 与 docs/plans/T7-sharing-mvp.md 对齐):

    级别       字段值     可查看       可评论        可编辑       姓名展示
    --------   ---------  ----------   ------------  -----------  ------------
    只读       read       ✔            ✘             ✘            张**  (全遮)
    评论       comment    ✔            ✔             ✘            张**  (全遮)
    编辑       edit       ✔            ✔             ✔            张明  (全显)

    # 兼容 T7.1 留下的 PERM_ADMIN 等级: 视为 edit, 仍走策略表。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# 兼容 PERM_ADMIN: 把它当 edit 处理, 防止历史数据遗留 admin 等级时崩溃。
# 改 POLICY_ADMIN_ALIAS 可调整。
POLICY_ADMIN_ALIAS = "edit"

# ---------------------------------------------------------------------------
# 字段可见性策略表
# ---------------------------------------------------------------------------
# key: permission 等级
# value: dict(可见字段集合, 允许能力集合, 是否脱敏姓名)
#
# 字段集合 None = "全部可见 (除内部字段外默认通过)";
#      iterable = "只允许 iterable 列出的字段被前端渲染"。
# 这样未来加新 PII (电话 / 身份证) 时, 只要在 read/comment 行内把它们
# 排除即可, 不必改 ShareLinkService。

_POLICY_TABLE: dict[str, dict[str, Any]] = {
    "read": {
        "can_view": True,
        "can_comment": False,
        "can_edit": False,
        "mask_name": True,
        # read 默认只暴露"通用展示"字段 + 脱敏姓名;
        # 报告正文 / 推荐表 / 联系方式 全部隐藏
        "visible_fields": {
            "report_id",
            "permission",
            "owner_id",
            "share_url",
            "created_at_iso",
            "expires_at_iso",
            "candidate_name",
            "customer_name",
            "student_name",
            "name",
        },
    },
    "comment": {
        "can_view": True,
        "can_comment": True,
        "can_edit": False,
        "mask_name": True,
        # comment 可看报告正文 + 脱敏姓名, 但联系方式 / 身份证 / 电话仍不暴露
        "visible_fields": {
            "report_id",
            "permission",
            "owner_id",
            "share_url",
            "created_at_iso",
            "expires_at_iso",
            "candidate_name",
            "customer_name",
            "student_name",
            "name",
            "title",
            "summary",
            "recommendations",
            "volunteers",
            "score",
            "rank",
            "year",
            "province",
        },
    },
    "edit": {
        "can_view": True,
        "can_comment": True,
        "can_edit": True,
        "mask_name": False,
        # edit 允许业务字段透传，但内部敏感字段仍由 _ALWAYS_HIDDEN_FIELDS 拦截。
        "visible_fields": None,
    },
    "admin": {
        # alias -> edit
        "can_view": True,
        "can_comment": True,
        "can_edit": True,
        "mask_name": False,
        "visible_fields": None,
    },
}


# 默认拒止策略: 任何未知 permission 一律当 read 处理 (最严)
_RESTRICTIVE_FALLBACK = _POLICY_TABLE["read"].copy()
_RESTRICTIVE_FALLBACK["visible_fields"] = set(_POLICY_TABLE["read"]["visible_fields"])


# 显式 PII 字段: 永远走 mask_name 决策, 与 visible_fields 正交
_PII_NAME_FIELDS = ("candidate_name", "customer_name", "student_name", "name")

# 无论 permission 等级如何都不应进入公开分享 payload 的内部字段。
# 这些字段要么属于安全敏感信息，要么只服务存储/运营侧，不应由 T7.3 透传。
_ALWAYS_HIDDEN_FIELDS = frozenset(
    {
        "password_hash",
        "internal_note",
        "note",
        "debug_info",
        "raw_payload",
    }
)


# ---------------------------------------------------------------------------
# Policy 数据类
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PermissionPolicy:
    """分享页的权限策略对象。"""

    permission: str
    can_view: bool
    can_comment: bool
    can_edit: bool
    mask_name: bool
    # None = "默认通过 (除显式内部字段外全部可见)"
    visible_fields: Optional[frozenset[str]]
    # 内部使用: True 表示输入 permission 不在策略表内, 已落 fallback。
    _is_fallback: bool = False

    @property
    def is_restrictive_fallback(self) -> bool:
        """True 表示 permission 未知/为空, 已落到 read 默认拒止策略上。"""
        return self._is_fallback

    def allows_field(self, field_name: str) -> bool:
        """判断某个字段对当前策略是否应该被前端渲染。"""
        if not self.can_view:
            return False
        if self.visible_fields is None:
            return True
        return field_name in self.visible_fields

    def can(self, action: str) -> bool:
        """通用能力判断: can("view") / can("comment") / can("edit")"""
        return bool(getattr(self, f"can_{action}", False))

    @classmethod
    def for_permission(cls, permission: str) -> "PermissionPolicy":
        """根据 permission 字段值返回策略对象；未知值走严格 fallback。"""
        perm_raw = (permission or "").strip().lower()
        perm = POLICY_ADMIN_ALIAS if perm_raw == "admin" else perm_raw
        if perm not in _POLICY_TABLE:
            cfg = _RESTRICTIVE_FALLBACK
            stored_perm = "read"
            is_fallback = True
        else:
            cfg = _POLICY_TABLE[perm]
            stored_perm = perm
            is_fallback = False
        vf = cfg.get("visible_fields")
        vf_fs = frozenset(vf) if vf is not None else None
        return cls(
            permission=stored_perm,
            can_view=bool(cfg.get("can_view", False)),
            can_comment=bool(cfg.get("can_comment", False)),
            can_edit=bool(cfg.get("can_edit", False)),
            mask_name=bool(cfg.get("mask_name", True)),
            visible_fields=vf_fs,
            _is_fallback=is_fallback,
        )


# ---------------------------------------------------------------------------
# 报告 payload 渲染
# ---------------------------------------------------------------------------


def _mask_name_safe(value: Any) -> Any:
    """分享页姓名脱敏包装。

    复用 data.orders.masking.mask_name 的基础能力，但分享页采用更保守的公开展示策略：
    - 中文 3 字及以上统一收敛为“姓 + **”（如 张三丰 -> 张**）
    - 非中文姓名统一收敛为 "**"，不泄露原始长度
    - 2 字中文沿用基础规则（张三 -> 张*）
    """
    from data.orders.masking import mask_name

    if not isinstance(value, str):
        return mask_name(value)

    s = value.strip()
    if not s:
        return ""

    base_masked = mask_name(s)
    is_cjk = all("\u4e00" <= ch <= "\u9fff" for ch in s)
    if not is_cjk:
        return "**"
    if len(s) >= 3:
        return s[0] + "**"
    return base_masked


def render_report_payload(
    permission: str,
    report: Optional[dict[str, Any]],
    *,
    share_url: Optional[str] = None,
) -> dict[str, Any]:
    """根据权限等级, 渲染前端可见的报告 payload。"""
    policy = PermissionPolicy.for_permission(permission)
    raw = report if isinstance(report, dict) else {}

    payload: dict[str, Any] = {}
    masked: list[str] = []

    if share_url:
        payload["share_url"] = share_url

    for key, value in raw.items():
        if key in _ALWAYS_HIDDEN_FIELDS:
            continue
        if not policy.allows_field(key):
            continue
        if key in _PII_NAME_FIELDS and policy.mask_name:
            payload[key] = _mask_name_safe(value)
            masked.append(key)
        else:
            payload[key] = value

    return {
        "permission": policy.permission,
        "policy": {
            "can_view": policy.can_view,
            "can_comment": policy.can_comment,
            "can_edit": policy.can_edit,
            "mask_name": policy.mask_name,
        },
        "visible_fields": sorted(policy.visible_fields)
        if policy.visible_fields is not None
        else None,
        "payload": payload,
        "masked_fields": masked,
    }


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def supported_permissions() -> list[str]:
    """返回策略表支持的全部 permission 等级 (含 admin alias)。"""
    return list(_POLICY_TABLE.keys())


def is_known_permission(permission: str) -> bool:
    """判断 permission 是否在策略表中 (admin 视为合法)。"""
    perm = (permission or "").strip().lower()
    return perm in _POLICY_TABLE


__all__ = [
    "POLICY_ADMIN_ALIAS",
    "PermissionPolicy",
    "is_known_permission",
    "render_report_payload",
    "supported_permissions",
]
