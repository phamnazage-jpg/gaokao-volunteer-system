"""错误码常量定义 (T9.1 + T9.2 落地)。

码点结构 (固定 6 字符):
    E  AA  BBB
    |  |   +-- 段内顺序号 (001-999, 零填充 3 位)
    |  +----- 段号 (2 位)
    +-------- 字面量 'E' 固定前缀

段号分配 (T9.1):
    01 用户    (E01001-E01199, 199 码点)
    02 业务    (E02001-E02199, 199 码点)
    03 数据    (E03001-E03199, 199 码点)
    04 第三方  (E04001-E04199, 199 码点)
    05 系统    (E05001-E05099, 99 码点)
    90-99 保留 (不分配给业务)

每段内 xx0xx-xx5xx 是子域位 (xx0 通用 / xx1 凭证 / xx2 会话 / ...).

注意:
- 字面量前缀 'E' 用于日志链路快速定位业务错误.
- 与 HTTP 状态码解耦 — 同一 HTTP 状态可对应不同业务码.
- 5xx 系统级错误严禁落到非 05 段 (防兜底掩盖).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


# ---------------- 段与子域枚举 ----------------


class ErrorSegment(str, Enum):
    """业务段号 (2 位数字字符串)."""

    USER = "01"
    BUSINESS = "02"
    DATA = "03"
    THIRD_PARTY = "04"
    SYSTEM = "05"

    @classmethod
    def values(cls) -> FrozenSet[str]:
        return frozenset(s.value for s in cls)


class ErrorSubdomain(str, Enum):
    """段内子域位 (按段独立计数).

    取值对应码点第 2 位 (xx?xx 中的 ?):
      0 通用
      1 凭证
      2 会话/速率
      3 权限/状态机
      4 设备/并发
      5 配额/迁移
    """

    GENERAL = "0"
    CREDENTIAL = "1"
    SESSION = "2"
    PERMISSION = "3"
    DEVICE = "4"
    QUOTA = "5"


# ---------------- 错误码 dataclass ----------------


@dataclass(frozen=True)
class ErrorCode:
    """业务错误码.

    形如 E01A01: E 前缀 + 段号 01 + 子域位 A (0-5) + 段内子码 01.
    """

    segment: ErrorSegment
    subdomain: ErrorSubdomain
    sequence: int  # 1-99 (保留首位给 1-9 用于通用, 10-99 子桶内分配)

    def __post_init__(self) -> None:
        if not (1 <= self.sequence <= 99):
            raise ValueError(f"sequence 必须在 1-99, 得到 {self.sequence}")

    def __str__(self) -> str:
        # E + 段号 + 子域位 + 2 位顺序号
        return f"E{self.segment.value}{self.subdomain.value}{self.sequence:02d}"

    @classmethod
    def of(cls, code: str) -> "ErrorCode":
        """从码点字符串反解 (用于日志/测试断言).

        Raises:
            ValueError: 码点格式不合法
        """
        if len(code) != 6 or not code.startswith("E"):
            raise ValueError(f"无效码点: {code!r} (期望 E + 5 位数字)")
        try:
            seg = ErrorSegment(code[1:3])
            sub = ErrorSubdomain(code[3])
        except ValueError as exc:
            raise ValueError(f"无效码点: {code!r} ({exc})") from exc
        try:
            seq = int(code[4:])
        except ValueError as exc:
            raise ValueError(f"无效码点: {code!r} ({exc})") from exc
        if not (1 <= seq <= 99):
            raise ValueError(f"无效码点: {code!r} (sequence 越界)")
        return cls(segment=seg, subdomain=sub, sequence=seq)


# ---------------- 内置错误码常量 ----------------
#
# 在这里集中声明项目实际使用的业务错误码, 避免散落字符串.
# 命名约定: <SEG>_<DOMAIN>_<INTENT>  (全大写, 下划线)
# 新增错误码时:
#   1) 在此处声明常量
#   2) 在 registry.py 的 MESSAGES_ZH_CN 中注册中文文案


# 01 段 — 用户域
AUTH_INVALID_CREDENTIALS = ErrorCode(
    segment=ErrorSegment.USER, subdomain=ErrorSubdomain.CREDENTIAL, sequence=1
)  # E01101
AUTH_TOKEN_EXPIRED = ErrorCode(
    segment=ErrorSegment.USER, subdomain=ErrorSubdomain.SESSION, sequence=1
)  # E01201
AUTH_TOKEN_INVALID = ErrorCode(
    segment=ErrorSegment.USER, subdomain=ErrorSubdomain.SESSION, sequence=2
)  # E01202
AUTH_INSUFFICIENT_PERMISSION = ErrorCode(
    segment=ErrorSegment.USER, subdomain=ErrorSubdomain.PERMISSION, sequence=1
)  # E01301
AUTH_ACCOUNT_DISABLED = ErrorCode(
    segment=ErrorSegment.USER, subdomain=ErrorSubdomain.CREDENTIAL, sequence=2
)  # E01102

# 02 段 — 业务域
BIZ_ORDER_NOT_FOUND = ErrorCode(
    segment=ErrorSegment.BUSINESS, subdomain=ErrorSubdomain.GENERAL, sequence=1
)  # E02001
BIZ_ORDER_RETENTION_NOT_EXPIRED = ErrorCode(
    segment=ErrorSegment.BUSINESS, subdomain=ErrorSubdomain.GENERAL, sequence=2
)  # E02002
BIZ_ORDER_INVALID_STATUS = ErrorCode(
    segment=ErrorSegment.BUSINESS, subdomain=ErrorSubdomain.PERMISSION, sequence=1
)  # E02301
BIZ_RATE_LIMITED = ErrorCode(
    segment=ErrorSegment.BUSINESS, subdomain=ErrorSubdomain.QUOTA, sequence=1
)  # E02501

# 03 段 — 数据域
DATA_VALIDATION_FAILED = ErrorCode(
    segment=ErrorSegment.DATA, subdomain=ErrorSubdomain.GENERAL, sequence=1
)  # E03001
DATA_NOT_FOUND = ErrorCode(
    segment=ErrorSegment.DATA, subdomain=ErrorSubdomain.GENERAL, sequence=2
)  # E03002
DATA_PERSIST_FAILED = ErrorCode(
    segment=ErrorSegment.DATA, subdomain=ErrorSubdomain.GENERAL, sequence=3
)  # E03003

# 04 段 — 第三方域
THIRD_PARTY_UPSTREAM_ERROR = ErrorCode(
    segment=ErrorSegment.THIRD_PARTY, subdomain=ErrorSubdomain.GENERAL, sequence=1
)  # E04001
THIRD_PARTY_TIMEOUT = ErrorCode(
    segment=ErrorSegment.THIRD_PARTY, subdomain=ErrorSubdomain.GENERAL, sequence=2
)  # E04002

# 05 段 — 系统域
SYS_INTERNAL_ERROR = ErrorCode(
    segment=ErrorSegment.SYSTEM, subdomain=ErrorSubdomain.GENERAL, sequence=1
)  # E05001
SYS_CONFIG_MISSING = ErrorCode(
    segment=ErrorSegment.SYSTEM, subdomain=ErrorSubdomain.GENERAL, sequence=2
)  # E05002
SYS_RESOURCE_EXHAUSTED = ErrorCode(
    segment=ErrorSegment.SYSTEM, subdomain=ErrorSubdomain.GENERAL, sequence=3
)  # E05003

# 兜底码 (用于未注册码点时使用,确保任何错误都能渲染)
FALLBACK_CODE = ErrorCode(
    segment=ErrorSegment.SYSTEM, subdomain=ErrorSubdomain.GENERAL, sequence=99
)  # E05099
