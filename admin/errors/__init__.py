"""统一错误处理模块 (T9.2 — 用户友好提示).

设计目标:
- 业务码与 HTTP 状态码解耦 (T9.1)
- 错误码 → 中文消息 + 解决建议 (本任务)
- 单源注册表, 避免散落字符串

公开 API:
- BusinessError              : 业务异常基类
- catch(...)                 : 统一异常捕获装饰器 (T9.4)
- ErrorCode / ErrorSegment / ErrorSubdomain : 码点 dataclass 与枚举
- <NAME> 常量 (AUTH_*, BIZ_*, DATA_*, THIRD_PARTY_*, SYS_*, FALLBACK_CODE)
- get_message(code, locale='zh-CN') -> Message
- register_exception_handler(app)   : FastAPI 全局 handler

后续 T9.3 / T9.4 将分别接入结构化日志与 @catch 装饰器.
"""

from admin.errors import codes as _codes
from admin.errors.codes import (
    FALLBACK_CODE,
    ErrorCode,
    ErrorSegment,
    ErrorSubdomain,
)
from admin.errors.exceptions import (
    BusinessError,
    catch,
    error_response,
    register_exception_handler,
)
from admin.errors.registry import (
    MESSAGES_ZH_CN,
    Message,
    MessageNotFoundError,
    get_message,
    is_registered,
    registered_codes,
)

# 集中 re-export 所有声明的 ErrorCode 常量, 调用方只需 `from admin.errors import AUTH_*`
# 这样新码点不需要改 __init__.py (但需要在 codes.py 里声明并用 is_registered 校验注册)
_ERROR_CODE_NAMES = tuple(
    sorted(
        name
        for name, value in vars(_codes).items()
        if isinstance(value, ErrorCode) and not name.startswith("_")
    )
)


def __getattr__(name: str):
    """PEP 562 lazy attribute: 让 from admin.errors import AUTH_INVALID_CREDENTIALS 也能拿到."""
    if name in _ERROR_CODE_NAMES:
        return getattr(_codes, name)
    raise AttributeError(f"module 'admin.errors' has no attribute {name!r}")


# 显式列出, 方便 IDE 自动补全与 lint
__all__ = [
    "BusinessError",
    "catch",
    "ErrorCode",
    "ErrorSegment",
    "ErrorSubdomain",
    "FALLBACK_CODE",
    "MESSAGES_ZH_CN",
    "Message",
    "MessageNotFoundError",
    "error_response",
    "get_message",
    "is_registered",
    "register_exception_handler",
    "registered_codes",
    *_ERROR_CODE_NAMES,
]
