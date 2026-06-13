"""配置加载 (T6.1).

所有运行时配置通过环境变量读取。提供默认值用于开发环境，但启动时
必须输出 WARN 提示生产环境必须显式覆盖。
"""

from __future__ import annotations

import os
import secrets
import string
from dataclasses import dataclass

from fastapi import Request


# 安全占位密钥（仅 dev 环境）。生产必须显式设置 GAOKAO_JWT_SECRET。
_DEV_JWT_SECRET = "dev-only-do-not-use-in-prod-please-override-via-env"
_DEFAULT_ADMIN_PASSWORD = "admin123"
_MIN_ADMIN_PASSWORD_LENGTH = 10


@dataclass(frozen=True)
class Settings:
    """运行时配置（不可变）。"""

    env: str
    db_path: str
    orders_db_path: str  # T6.2 — 订单数据 (data.orders.* 写入位置)
    share_db_path: str  # T7.5 — 短链接 SQLite
    share_report_dir: str  # T7.5 — report_id -> JSON 报告目录
    payment_provider: str  # mock|alipay
    payment_base_url: str
    payment_webhook_secret: str
    payment_notify_url: str
    payment_return_url: str
    payment_app_id: str
    payment_private_key_path: str
    payment_alipay_public_key_path: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    default_admin_username: str
    default_admin_password: str


def load_settings() -> Settings:
    """从环境变量加载配置。

    - GAOKAO_ENV              : dev|prod，默认 dev
    - GAOKAO_DB_PATH          : 管理后台 SQLite 文件路径，默认 data/orders/admin.db
    - GAOKAO_ORDERS_DB_PATH   : 订单 DB 路径 (与 data.orders.* 共享),默认 data/orders.db
    - GAOKAO_SHARE_DB_PATH    : 分享短链接 DB 路径，默认 data/share/short_links.db
    - GAOKAO_SHARE_REPORT_DIR : 分享报告 JSON 目录，默认 data/share/reports
    - GAOKAO_PAYMENT_PROVIDER : 支付 provider，默认 mock
    - GAOKAO_PAYMENT_BASE_URL : 支付相关回跳基础 URL，默认 http://testserver
    - GAOKAO_PAYMENT_WEBHOOK_SECRET : 支付 webhook 独立签名密钥，默认 dev mock secret
    - GAOKAO_PAYMENT_NOTIFY_URL : 真实 provider 异步通知地址，默认空
    - GAOKAO_PAYMENT_RETURN_URL : 真实 provider 浏览器返回地址，默认空
    - GAOKAO_PAYMENT_APP_ID : 真实 provider 应用 ID，默认空
    - GAOKAO_PAYMENT_PRIVATE_KEY_PATH : 真实 provider 私钥路径，默认空
    - GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH : 支付宝公钥路径，默认空
    - GAOKAO_JWT_SECRET       : HS256 密钥，默认 dev 占位（启动日志 WARN）
    - GAOKAO_JWT_EXP_MIN      : JWT 过期时间（分钟），默认 60
    - GAOKAO_ADMIN_USER       : 默认管理员用户名，默认 admin
    - GAOKAO_ADMIN_PASS       : 默认管理员密码，默认 admin123（仅本地开发占位）

    Returns:
        Settings: 不可变配置实例
    """
    return Settings(
        env=os.getenv("GAOKAO_ENV", "dev"),
        db_path=os.getenv("GAOKAO_DB_PATH", "data/orders/admin.db"),
        orders_db_path=os.getenv("GAOKAO_ORDERS_DB_PATH", "data/orders.db"),
        share_db_path=os.getenv("GAOKAO_SHARE_DB_PATH", "data/share/short_links.db"),
        share_report_dir=os.getenv("GAOKAO_SHARE_REPORT_DIR", "data/share/reports"),
        payment_provider=os.getenv("GAOKAO_PAYMENT_PROVIDER", "mock"),
        payment_base_url=os.getenv("GAOKAO_PAYMENT_BASE_URL", "http://testserver"),
        payment_webhook_secret=os.getenv(
            "GAOKAO_PAYMENT_WEBHOOK_SECRET", "dev-mock-payment-secret"
        ),
        payment_notify_url=os.getenv("GAOKAO_PAYMENT_NOTIFY_URL", ""),
        payment_return_url=os.getenv("GAOKAO_PAYMENT_RETURN_URL", ""),
        payment_app_id=os.getenv("GAOKAO_PAYMENT_APP_ID", ""),
        payment_private_key_path=os.getenv("GAOKAO_PAYMENT_PRIVATE_KEY_PATH", ""),
        payment_alipay_public_key_path=os.getenv(
            "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH", ""
        ),
        jwt_secret=os.getenv("GAOKAO_JWT_SECRET", _DEV_JWT_SECRET),
        jwt_algorithm=os.getenv("GAOKAO_JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.getenv("GAOKAO_JWT_EXP_MIN", "60")),
        default_admin_username=os.getenv("GAOKAO_ADMIN_USER", "admin"),
        default_admin_password=os.getenv("GAOKAO_ADMIN_PASS", _DEFAULT_ADMIN_PASSWORD),
    )


def is_jwt_secret_secure(settings: Settings) -> tuple:
    """判断 JWT 密钥是否满足最低安全门槛。

    Returns:
        (is_secure, reason) : 不满足时给出原因字符串
    """
    secret = settings.jwt_secret
    if settings.env == "prod":
        if secret == _DEV_JWT_SECRET:
            return False, "生产环境禁止使用 dev 占位密钥"
        if len(secret) < 32:
            return False, "生产环境 JWT 密钥长度必须 >= 32 (当前 {})".format(
                len(secret)
            )
    if secret == _DEV_JWT_SECRET and settings.env == "dev":
        return False, "dev 环境使用占位密钥（仅本地开发可接受）"
    if len(secret) < 32:
        return False, "JWT 密钥长度必须 >= 32 (当前 {})".format(len(secret))
    return True, "ok"


def is_default_admin_password_secure(settings: Settings) -> tuple[bool, str]:
    """判断默认管理员密码是否满足最低安全门槛。"""
    password = settings.default_admin_password
    if len(password) < _MIN_ADMIN_PASSWORD_LENGTH:
        return False, (
            f"默认管理员密码长度必须 >= {_MIN_ADMIN_PASSWORD_LENGTH} (当前 {len(password)})"
        )
    if settings.env == "prod" and password == _DEFAULT_ADMIN_PASSWORD:
        return False, "生产环境禁止使用默认管理员密码 admin123"
    if settings.env == "prod":
        classes = sum((
            any(ch.islower() for ch in password),
            any(ch.isupper() for ch in password),
            any(ch.isdigit() for ch in password),
            any(ch in string.punctuation for ch in password),
        ))
        if classes < 3:
            return False, "生产环境默认管理员密码至少覆盖 3 类字符（大小写/数字/符号）"
    if settings.env == "dev" and password == _DEFAULT_ADMIN_PASSWORD:
        return False, "dev 环境仍在使用默认管理员密码（仅本地临时开发可接受）"
    return True, "ok"


def generate_secure_secret() -> str:
    """生成 32-byte 十六进制密钥（用于初始化文档示例）。"""
    return secrets.token_hex(32)


def get_settings_dep(request: Request) -> Settings:
    """FastAPI 依赖:从 app.state 取已加载的 Settings。

    与 admin.auth.get_settings 重复,但放在 config 里便于其他路由直接引用。
    """
    settings = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover - 兜底
        settings = load_settings()
    return settings
