"""i18n 消息注册表 (T9.2 — 用户友好提示).

每个错误码对应:
- message    : 给用户看的中文短句 (≤ 30 字, 一句话讲清楚发生了什么)
- suggestion : 给用户的可执行建议 (≤ 50 字, 具体到下一步动作)
- severity   : 'info' / 'warn' / 'error' (驱动前端图标与重试策略, T9.3 接入)
- retryable  : True 表示前端/SDK 可安全重试 (T9.4 装饰器用)

未来扩展:
- 引入 en-US 资源包时, 把 MESSAGES 改为按 locale 索引的 dict:
    MESSAGES = {"zh-CN": {...}, "en-US": {...}}
- CI 校验脚本应扫描 codes.py 的常量是否都已注册, 防止散落字符串
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Mapping

from admin.errors.codes import (
    AUTH_ACCOUNT_DISABLED,
    AUTH_INSUFFICIENT_PERMISSION,
    AUTH_INVALID_CREDENTIALS,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    BIZ_ORDER_INVALID_STATUS,
    BIZ_ORDER_NOT_FOUND,
    BIZ_RATE_LIMITED,
    DATA_NOT_FOUND,
    DATA_PERSIST_FAILED,
    DATA_VALIDATION_FAILED,
    FALLBACK_CODE,
    SYS_CONFIG_MISSING,
    SYS_INTERNAL_ERROR,
    SYS_RESOURCE_EXHAUSTED,
    THIRD_PARTY_TIMEOUT,
    THIRD_PARTY_UPSTREAM_ERROR,
)


Severity = Literal["info", "warn", "error"]


@dataclass(frozen=True)
class Message:
    """用户可见的错误消息 (i18n 资源包的最小单元)."""

    code: str
    message: str
    suggestion: str
    severity: Severity
    retryable: bool

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
            "severity": self.severity,
            "retryable": self.retryable,
        }


class MessageNotFoundError(KeyError):
    """注册表中找不到对应码点 (本应被兜底拦截,仅测试用)."""


# ---------------- zh-CN 资源包 ----------------
#
# 编写准则:
# - message: 陈述句, 不带感叹号; 第二人称避免 ('您'/'请' 可用)
# - suggestion: 祈使句开头, 给出 1-2 步可执行动作; 不承诺能解决
# - 不暴露内部实现细节 (DB 名/字段名/IP), 但允许给文件路径/链接
# - 同一段号内的码点, 文案语气保持一致

MESSAGES_ZH_CN: Mapping[str, Message] = {
    # 01 段 — 用户域
    str(AUTH_INVALID_CREDENTIALS): Message(
        code=str(AUTH_INVALID_CREDENTIALS),
        message="用户名或密码不正确",
        suggestion="请检查大小写和输入法,确认无误后重新登录。忘记密码请联系管理员重置。",
        severity="warn",
        retryable=False,
    ),
    str(AUTH_TOKEN_EXPIRED): Message(
        code=str(AUTH_TOKEN_EXPIRED),
        message="登录状态已过期",
        suggestion="请重新登录后再继续操作。系统默认会话有效期 5 分钟。",
        severity="warn",
        retryable=False,
    ),
    str(AUTH_TOKEN_INVALID): Message(
        code=str(AUTH_TOKEN_INVALID),
        message="登录凭证无效",
        suggestion="请重新登录。如反复出现,请清除浏览器 Cookie 后重试。",
        severity="warn",
        retryable=False,
    ),
    str(AUTH_INSUFFICIENT_PERMISSION): Message(
        code=str(AUTH_INSUFFICIENT_PERMISSION),
        message="当前账号无访问权限",
        suggestion="请使用具备相应权限的账号登录,或联系管理员开通权限。",
        severity="warn",
        retryable=False,
    ),
    str(AUTH_ACCOUNT_DISABLED): Message(
        code=str(AUTH_ACCOUNT_DISABLED),
        message="账号已被停用",
        suggestion="请联系管理员确认账号状态,启用后再登录。",
        severity="warn",
        retryable=False,
    ),
    # 02 段 — 业务域
    str(BIZ_ORDER_NOT_FOUND): Message(
        code=str(BIZ_ORDER_NOT_FOUND),
        message="未找到该订单",
        suggestion="请检查订单号是否正确,或在订单列表中通过筛选条件重新查询。",
        severity="warn",
        retryable=False,
    ),
    str(BIZ_ORDER_INVALID_STATUS): Message(
        code=str(BIZ_ORDER_INVALID_STATUS),
        message="订单当前状态不支持该操作",
        suggestion="请刷新订单详情查看最新状态,或前往订单列表查看状态流转。",
        severity="warn",
        retryable=False,
    ),
    str(BIZ_RATE_LIMITED): Message(
        code=str(BIZ_RATE_LIMITED),
        message="请求过于频繁",
        suggestion="请稍候 30 秒后再试。如持续触发,可联系管理员调整配额。",
        severity="warn",
        retryable=True,
    ),
    # 03 段 — 数据域
    str(DATA_VALIDATION_FAILED): Message(
        code=str(DATA_VALIDATION_FAILED),
        message="请求数据未通过校验",
        suggestion="请检查必填字段和格式。鼠标悬停字段标签可查看填写要求。",
        severity="warn",
        retryable=False,
    ),
    str(DATA_NOT_FOUND): Message(
        code=str(DATA_NOT_FOUND),
        message="未找到对应的数据",
        suggestion="该记录可能已被删除或尚未创建,请刷新页面或返回列表确认。",
        severity="warn",
        retryable=False,
    ),
    str(DATA_PERSIST_FAILED): Message(
        code=str(DATA_PERSIST_FAILED),
        message="数据保存失败",
        suggestion="请稍后重试。如反复失败,请联系技术支持并保留错误码。",
        severity="error",
        retryable=True,
    ),
    # 04 段 — 第三方域
    str(THIRD_PARTY_UPSTREAM_ERROR): Message(
        code=str(THIRD_PARTY_UPSTREAM_ERROR),
        message="外部服务暂时不可用",
        suggestion="我们正在同步上游状态,请稍后重试;如紧急可联系客服。",
        severity="error",
        retryable=True,
    ),
    str(THIRD_PARTY_TIMEOUT): Message(
        code=str(THIRD_PARTY_TIMEOUT),
        message="外部服务响应超时",
        suggestion="请稍后重试,或在网络稳定的环境下再次尝试。",
        severity="error",
        retryable=True,
    ),
    # 05 段 — 系统域
    str(SYS_INTERNAL_ERROR): Message(
        code=str(SYS_INTERNAL_ERROR),
        message="系统内部异常",
        suggestion="请稍后重试。如反复出现,请联系技术支持并提供错误码。",
        severity="error",
        retryable=True,
    ),
    str(SYS_CONFIG_MISSING): Message(
        code=str(SYS_CONFIG_MISSING),
        message="系统配置缺失",
        suggestion="请联系运维人员检查服务配置,确认环境变量已正确注入。",
        severity="error",
        retryable=False,
    ),
    str(SYS_RESOURCE_EXHAUSTED): Message(
        code=str(SYS_RESOURCE_EXHAUSTED),
        message="系统资源不足",
        suggestion="当前访问量过高,请稍后再试;如紧急可联系运维扩容。",
        severity="error",
        retryable=True,
    ),
}


# 兜底文案 (任何未注册码点都返回这一份, 永远不会让用户看到空白)
_FALLBACK_MESSAGE = Message(
    code=str(FALLBACK_CODE),
    message="服务暂时无法处理请求",
    suggestion="请稍后重试,或联系技术支持并提供错误码以便排查。",
    severity="error",
    retryable=True,
)


def get_message(code: str, locale: str = "zh-CN") -> Message:
    """根据业务码查找本地化消息.

    行为契约:
    - 已注册码点 → 返回 MESSAGES_ZH_CN 中的 Message
    - 未注册但格式合法的码点 → 返回 _FALLBACK_MESSAGE (但 code 字段被替换为入参,
      便于排查是哪类未注册)
    - 格式非法码点 → 返回 _FALLBACK_MESSAGE (code 字段保留原值以保留上下文)

    当前实现只支持 zh-CN; 后续多 locale 时改为 MESSAGES[locale].get(code, fallback).
    """
    if locale != "zh-CN":
        # 当前仅支持 zh-CN, 其他 locale 走兜底
        return _FALLBACK_MESSAGE
    msg = MESSAGES_ZH_CN.get(code)
    if msg is not None:
        return msg
    # 未注册: 保留原 code 用于排查, 文案用兜底
    return Message(
        code=code,
        message=_FALLBACK_MESSAGE.message,
        suggestion=_FALLBACK_MESSAGE.suggestion,
        severity=_FALLBACK_MESSAGE.severity,
        retryable=_FALLBACK_MESSAGE.retryable,
    )


def is_registered(code: str) -> bool:
    """检查码点是否已注册 (CI 校验脚本与单元测试用)."""
    return code in MESSAGES_ZH_CN


def registered_codes() -> Dict[str, Message]:
    """返回当前已注册的所有码点 (测试与文档生成用)."""
    return dict(MESSAGES_ZH_CN)
