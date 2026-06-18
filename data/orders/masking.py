"""订单敏感字段展示脱敏工具 (T11.2).

职责：把明文 PII 转成"可展示但不完整"的形态，用于 API 响应、UI 列表、日志输出。

与 crypto.py 的关系：
- crypto.py 负责"落盘形态"（AES 密文 / SHA-256 hash），目的是不让磁盘/数据库泄露明文。
- masking.py 负责"展示形态"（部分遮罩），目的是最小特权展示，不让前端/日志/截图拿到完整 PII。
- 两者正交：脱敏展示不替代落盘加密，解密后仍然可以再脱敏展示。

设计原则：
1. 默认安全：None / 空串 / 非法输入 → 返回 None，绝不抛错给前端。
2. 不依赖具体加密密钥：纯字符串处理，可在 API 序列化层、模板、日志过滤器、CSV 导出器等任意层复用。
3. 不丢语义：保留可识别前缀（如手机前 3 位、身份证前 6 位行政区划），便于运营核对。
4. 不可逆：无法从展示形态恢复原文（mask 后字符是"原始位数"而非真实值）。
"""

from __future__ import annotations

import re
from typing import Any, Optional

# 11 位中国手机号（已剔除 +86 / 空格 / 横杠后）
_PHONE_11 = re.compile(r"^\d{11}$")
# 18 位身份证（含 17 位 + 末位校验位 X/x）
_ID_CARD_18 = re.compile(r"^\d{17}[\dXx]$")
# 15 位老版身份证
_ID_CARD_15 = re.compile(r"^\d{15}$")
# 86 / +86 国家码前缀(中国大陆手机号常见形态)
_PHONE_PREFIX_86 = re.compile(r"^(\+?86)[\s\-]?")


def mask_phone(value: Optional[str]) -> Optional[str]:
    """手机号脱敏：138****1234。

    接受：
    - 11 位纯数字 → "前3位****后4位"
    - 含 +86 / 86 / 空格 / 横杠 → 先剥离国家码与分隔再判定
    - None / 空串 / 长度不足 → 原样返回（None / ""）。
    - 非字符串 → 返回 None（不抛错给前端）。
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return ""
    # 显式剥离 +86 / 86 国家码(只剥一次,避免误处理纯数字 86 开头)
    s = _PHONE_PREFIX_86.sub("", s, count=1)
    # 去掉剩余的空格 / - / + 分隔符
    stripped = re.sub(r"[\s\-]", "", s)
    if _PHONE_11.match(stripped):
        return f"{stripped[:3]}****{stripped[-4:]}"
    # 非标准形态:长度 >= 7 时遮中段(至少遮 1 个 *),否则原样
    if len(stripped) >= 7:
        return stripped[:3] + "*" * max(1, len(stripped) - 7) + stripped[-4:]
    return s


def mask_id_card(value: Optional[str]) -> Optional[str]:
    """身份证脱敏：保留前 6 位行政区划 + 末 4 位。

    18 位：430102********1234
    15 位：430102******123（兼容老版）
    非标准长度（13-14 位）：按"前 6 后 4"遮中段，否则原样返回。
    < 13 位视为非身份证，原样返回以免误遮。
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return ""
    if _ID_CARD_18.match(s):
        return f"{s[:6]}********{s[-4:]}"
    if _ID_CARD_15.match(s):
        return f"{s[:6]}******{s[-3:]}"
    if len(s) >= 13:
        return s[:6] + "*" * max(2, len(s) - 10) + s[-4:]
    return s


def mask_name(value: Optional[str]) -> Optional[str]:
    """姓名脱敏：保留姓氏。

    规则：
    - 1 字姓名 → 原样返回（已是最低信息粒度）。
    - 2 字姓名 → 张*（姓 + 1 个 *）。
    - 3 字姓名 → 张*丰（姓 + 名首字 + 1 个 *）。
    - 4+ 字姓名 → 张**（姓 + 2 个 *，不暴露名长度）。
    - 非中文字符（英文/数字/混合） → 全遮 *（不暴露字符数）。
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return ""
    # 非中日韩文字：按"全遮"处理
    if not all("\u4e00" <= ch <= "\u9fff" for ch in s):
        return "*" * len(s)
    n = len(s)
    if n == 1:
        return s
    if n == 2:
        return s[0] + "*"
    if n == 3:
        return s[0] + "*" + s[2]
    # 4 字及以上：保留首字 + 2 个 *（不暴露名长度信息）
    return s[0] + "**"


def mask_wechat(value: Optional[str]) -> Optional[str]:
    """微信号脱敏：保留前 2 后 2，中段用 * 填充。"""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return ""
    if len(s) <= 2:
        return "*" * len(s)
    if len(s) <= 4:
        return s[0] + "*" * (len(s) - 2) + s[-1]
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


def mask_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return ""
    if "@" not in s:
        return "***"
    local, domain = s.split("@", 1)
    if not local:
        return f"***@{domain}"
    keep = local[0]
    return f"{keep}***@{domain}"


def mask_sensitive_dict(data: dict[str, Any]) -> dict[str, Any]:
    """对订单字典中已知的敏感字段统一脱敏。

    适配 Order.to_dict 输出：仅对明文 PII 字段做 mask，不修改 _enc / _hash 字段
    （那些字段本就不应出现在 API 响应里；如果出现了，说明上游泄露 — 本函数不动它，
    由调用方负责移除）。
    """
    if not isinstance(data, dict):
        return data
    masked = dict(data)
    if "customer_phone" in masked and masked["customer_phone"] is not None:
        masked["customer_phone"] = mask_phone(masked["customer_phone"])
    if "candidate_id_card" in masked and masked["candidate_id_card"] is not None:
        masked["candidate_id_card"] = mask_id_card(masked["candidate_id_card"])
    if "customer_name" in masked and masked["customer_name"] is not None:
        masked["customer_name"] = mask_name(masked["customer_name"])
    if "customer_wechat" in masked and masked["customer_wechat"] is not None:
        masked["customer_wechat"] = mask_wechat(masked["customer_wechat"])
    if "customer_email" in masked and masked["customer_email"] is not None:
        masked["customer_email"] = mask_email(masked["customer_email"])
    if "candidate_name" in masked and masked["candidate_name"] is not None:
        masked["candidate_name"] = mask_name(masked["candidate_name"])
    return masked


__all__ = [
    "mask_phone",
    "mask_id_card",
    "mask_name",
    "mask_wechat",
    "mask_email",
    "mask_sensitive_dict",
]
