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
# Portal token 独立 dev 占位密钥。**与后台 JWT 密钥不同**,P2-4 验收要求。
# 生产环境必须显式设置 GAOKAO_PORTAL_TOKEN_SECRET。
_DEV_PORTAL_TOKEN_SECRET = "dev-only-portal-token-secret-do-not-use-in-prod"
# Payment webhook dev 默认密钥。生产环境必须显式设置,否则 fail-closed (P2-5)。
_DEV_PAYMENT_WEBHOOK_SECRET = "dev-mock-payment-secret"
_DEFAULT_ADMIN_PASSWORD = "admin123"
_MIN_ADMIN_PASSWORD_LENGTH = 10
# Webhook secret 最低长度门槛 (生产环境)
_MIN_PROD_WEBHOOK_SECRET_LEN = 16
# Portal token secret 最低长度门槛 (生产环境)
_MIN_PORTAL_TOKEN_SECRET_LEN = 32
_SUPPORTED_PAYMENT_PROVIDERS = {"mock", "alipay_sim", "alipay"}
_PROD_ALLOWED_PAYMENT_PROVIDERS = {"alipay"}


@dataclass(frozen=True)
class Settings:
    """运行时配置（不可变）。"""

    env: str
    db_path: str
    orders_db_path: str  # T6.2 — 订单数据 (data.orders.* 写入位置)
    share_db_path: str  # T7.5 — 短链接 SQLite
    share_report_dir: str  # T7.5 — report_id -> JSON 报告目录
    portal_upload_dir: str  # T12 — 用户前台资料/附件上传目录
    portal_upload_max_bytes: int  # T12 — 单文件上传大小上限
    portal_upload_max_files: int  # T12 — 单订单最大附件数
    payment_provider: str  # mock|alipay
    payment_base_url: str
    payment_webhook_secret: str
    payment_notify_url: str
    payment_return_url: str
    payment_app_id: str
    payment_merchant_id: str
    payment_private_key_path: str
    payment_alipay_public_key_path: str
    smtp_host: str
    smtp_port: int
    smtp_sender: str
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    alert_recipients: list[str]
    alert_webhook_urls: list[str]
    ops_alert_log_path: str
    deletion_request_log_path: str
    retention_days: int  # 2026-06-19: 删除/匿名化保留期 (天)
    jwt_secret: str
    portal_token_secret: str  # P2-4: 与后台 jwt_secret 分离
    jwt_algorithm: str
    jwt_expire_minutes: int
    default_admin_username: str
    default_admin_password: str
    consent_version: str  # 当前同意协议版本号，与 docs/PRIVACY_POLICY_DRAFT.md 版本对齐
    consent_scope_portal: str  # portal 资料提交默认 scope
    consent_scope_channel_prefix: str  # 后台代录 scope 前缀


def _resolve_payment_webhook_secret(env: str) -> str:
    """解析支付 webhook secret,根据环境返回实际值。

    dev/test 保留 dev 默认值 ``_DEV_PAYMENT_WEBHOOK_SECRET``,便于本地开发/测试;
    生产环境不读取默认值,强制要求显式设置环境变量。
    """
    raw = os.getenv("GAOKAO_PAYMENT_WEBHOOK_SECRET")
    if raw is None or raw == "":
        if env == "prod":
            # 生产环境未设置环境变量 → 抛错,防止 Settings 实例化成功后再次绕过校验
            raise RuntimeError(
                "GAOKAO_PAYMENT_WEBHOOK_SECRET 必须在生产环境显式设置 "
                "(当前缺失或为空),已拒绝启动 (P2-5 fail-closed)"
            )
        return _DEV_PAYMENT_WEBHOOK_SECRET
    return raw


def _enforce_payment_webhook_secret_policy(settings: Settings) -> None:
    """生产环境 webhook secret fail-closed 校验 (P2-5)。

    不接受:
    - 缺失/空字符串 (由 ``_resolve_payment_webhook_secret`` 处理,但为防御性双重检查)
    - dev 占位 secret (``_DEV_PAYMENT_WEBHOOK_SECRET``)
    - 长度 < ``_MIN_PROD_WEBHOOK_SECRET_LEN`` 字符
    """
    if settings.env != "prod":
        return
    secret = settings.payment_webhook_secret
    if not secret:
        raise RuntimeError(
            "GAOKAO_PAYMENT_WEBHOOK_SECRET 缺失,生产环境必须显式设置 (P2-5 fail-closed)"
        )
    if secret == _DEV_PAYMENT_WEBHOOK_SECRET:
        raise RuntimeError(
            "GAOKAO_PAYMENT_WEBHOOK_SECRET 仍使用 dev 默认值,生产环境禁止 "
            "(P2-5 fail-closed)"
        )
    if len(secret) < _MIN_PROD_WEBHOOK_SECRET_LEN:
        raise RuntimeError(
            "GAOKAO_PAYMENT_WEBHOOK_SECRET 长度 {} 小于生产环境最低要求 {} "
            "(P2-5 fail-closed)".format(len(secret), _MIN_PROD_WEBHOOK_SECRET_LEN)
        )


def _resolve_portal_token_secret(env: str) -> str:
    raw = os.getenv("GAOKAO_PORTAL_TOKEN_SECRET")
    if raw is None or raw == "":
        if env == "prod":
            raise RuntimeError(
                "GAOKAO_PORTAL_TOKEN_SECRET 必须在生产环境显式设置 "
                "(当前缺失或为空),已拒绝启动 (P2-4 fail-closed)"
            )
        return _DEV_PORTAL_TOKEN_SECRET
    return raw


def is_portal_token_secret_secure(settings: Settings) -> tuple[bool, str]:
    secret = settings.portal_token_secret
    if settings.env == "prod":
        if secret == _DEV_PORTAL_TOKEN_SECRET:
            return False, "生产环境禁止使用默认 portal token secret"
        if len(secret) < _MIN_PORTAL_TOKEN_SECRET_LEN:
            return False, "portal token secret 长度必须 >= 32"
        if secret == settings.jwt_secret:
            return False, "portal token secret 必须与 JWT secret 分离"
    if settings.env == "dev" and secret == _DEV_PORTAL_TOKEN_SECRET:
        return False, "dev 环境使用占位 portal token secret（仅本地开发可接受）"
    if len(secret) < _MIN_PORTAL_TOKEN_SECRET_LEN:
        return False, "portal token secret 长度必须 >= 32"
    if secret == settings.jwt_secret:
        return False, "portal token secret 必须与 JWT secret 分离"
    return True, "ok"


def _enforce_portal_token_secret_policy(settings: Settings) -> None:
    secure, reason = is_portal_token_secret_secure(settings)
    if not secure and settings.env == "prod":
        raise RuntimeError(f"GAOKAO_PORTAL_TOKEN_SECRET invalid in prod: {reason}")


def _enforce_jwt_secret_policy(settings: Settings) -> None:
    """6/20 加固: 生产环境 JWT secret 必须满足强度门槛, 否则 fail-closed。"""
    secure, reason = is_jwt_secret_secure(settings)
    if not secure and settings.env == "prod":
        raise RuntimeError(f"GAOKAO_JWT_SECRET invalid in prod: {reason}")


def _enforce_default_admin_password_policy(settings: Settings) -> None:
    """6/20 加固: 生产环境默认管理员密码必须满足强度门槛, 否则 fail-closed。"""
    secure, reason = is_default_admin_password_secure(settings)
    if not secure and settings.env == "prod":
        raise RuntimeError(f"GAOKAO_ADMIN_PASS invalid in prod: {reason}")


def _enforce_payment_provider_policy(settings: Settings) -> None:
    provider = (settings.payment_provider or "mock").strip().lower()
    if settings.env != "prod":
        return
    if provider not in _SUPPORTED_PAYMENT_PROVIDERS:
        raise RuntimeError(
            "GAOKAO_PAYMENT_PROVIDER={} 在生产环境被禁止，"
            "仅允许受支持且可上线的 provider {} (P0-2 fail-closed)".format(
                provider, sorted(_PROD_ALLOWED_PAYMENT_PROVIDERS)
            )
        )
    if provider not in _PROD_ALLOWED_PAYMENT_PROVIDERS:
        raise RuntimeError(
            "GAOKAO_PAYMENT_PROVIDER={} 在生产环境被禁止，"
            "仅允许受支持且可上线的 provider {} (P0-2 fail-closed)".format(
                provider, sorted(_PROD_ALLOWED_PAYMENT_PROVIDERS)
            )
        )


def load_settings() -> Settings:
    """从环境变量加载配置。

    - GAOKAO_ENV              : dev|prod，默认 dev
    - GAOKAO_DB_PATH          : 管理后台 SQLite 文件路径，默认 data/orders/admin.db
    - GAOKAO_ORDERS_DB_PATH   : 订单 DB 路径 (与 data.orders.* 共享),默认 data/orders.db
    - GAOKAO_SHARE_DB_PATH    : 分享短链接 DB 路径，默认 data/share/short_links.db
    - GAOKAO_SHARE_REPORT_DIR : 分享报告 JSON 目录，默认 data/share/reports
    - GAOKAO_PAYMENT_PROVIDER : 支付 provider，默认 mock
    - GAOKAO_PAYMENT_BASE_URL : 支付相关回跳基础 URL，默认 http://testserver
    - GAOKAO_PAYMENT_WEBHOOK_SECRET : 支付 webhook 独立签名密钥。生产环境 (GAOKAO_ENV=prod)
                                       必须显式设置强密钥,否则启动 fail-closed (P2-5)。
                                       dev 保留 ``dev-mock-payment-secret`` 默认值。
    - GAOKAO_PAYMENT_NOTIFY_URL : 真实 provider 异步通知地址，默认空
    - GAOKAO_PAYMENT_RETURN_URL : 真实 provider 浏览器返回地址，默认空
    - GAOKAO_PAYMENT_APP_ID : 真实 provider 应用 ID，默认空
    - GAOKAO_PAYMENT_MERCHANT_ID : 真实 provider 商户/卖家 ID，默认空
    - GAOKAO_PAYMENT_PRIVATE_KEY_PATH : 真实 provider 私钥路径，默认空
    - GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH : 支付宝公钥路径，默认空
    - GAOKAO_SMTP_HOST : SMTP 主机，默认空
    - GAOKAO_SMTP_PORT : SMTP 端口，默认 25
    - GAOKAO_SMTP_SENDER : 发件邮箱，默认空
    - GAOKAO_SMTP_USER : SMTP 用户名，默认空
    - GAOKAO_SMTP_PASS : SMTP 密码，默认空
    - GAOKAO_SMTP_USE_TLS : 是否启用 STARTTLS，默认 false
    - GAOKAO_SMTP_USE_SSL : 是否启用 SMTPS，默认 false
    - GAOKAO_JWT_SECRET       : HS256 密钥，默认 dev 占位（启动日志 WARN）
    - GAOKAO_PORTAL_TOKEN_SECRET : Portal token 独立签名密钥 (P2-4)。
                                    与 ``GAOKAO_JWT_SECRET`` **分离**:默认 dev 占位,
                                    生产环境必须显式设置且与 JWT secret 不同。
    - GAOKAO_JWT_EXP_MIN      : JWT 过期时间（分钟），默认 60
    - GAOKAO_ADMIN_USER       : 默认管理员用户名，默认 admin
    - GAOKAO_ADMIN_PASS       : 默认管理员密码，默认 admin123（仅本地开发占位）

    Raises:
        RuntimeError: 生产环境下 GAOKAO_PAYMENT_WEBHOOK_SECRET 缺失/默认值/长度不足
                     时 fail-closed。
    """
    settings = Settings(
        env=os.getenv("GAOKAO_ENV", "dev"),
        db_path=os.getenv("GAOKAO_DB_PATH", "data/orders/admin.db"),
        orders_db_path=os.getenv("GAOKAO_ORDERS_DB_PATH", "data/orders.db"),
        share_db_path=os.getenv("GAOKAO_SHARE_DB_PATH", "data/share/short_links.db"),
        share_report_dir=os.getenv("GAOKAO_SHARE_REPORT_DIR", "data/share/reports"),
        portal_upload_dir=os.getenv("GAOKAO_PORTAL_UPLOAD_DIR", "data/portal_uploads"),
        portal_upload_max_bytes=int(
            os.getenv("GAOKAO_PORTAL_UPLOAD_MAX_BYTES", "5242880")
        ),
        portal_upload_max_files=int(os.getenv("GAOKAO_PORTAL_UPLOAD_MAX_FILES", "5")),
        payment_provider=os.getenv("GAOKAO_PAYMENT_PROVIDER", "mock").strip().lower(),
        payment_base_url=os.getenv("GAOKAO_PAYMENT_BASE_URL", "http://testserver"),
        payment_webhook_secret=_resolve_payment_webhook_secret(
            os.getenv("GAOKAO_ENV", "dev")
        ),
        payment_notify_url=os.getenv("GAOKAO_PAYMENT_NOTIFY_URL", ""),
        payment_return_url=os.getenv("GAOKAO_PAYMENT_RETURN_URL", ""),
        payment_app_id=os.getenv("GAOKAO_PAYMENT_APP_ID", ""),
        payment_merchant_id=os.getenv("GAOKAO_PAYMENT_MERCHANT_ID", ""),
        payment_private_key_path=os.getenv("GAOKAO_PAYMENT_PRIVATE_KEY_PATH", ""),
        payment_alipay_public_key_path=os.getenv(
            "GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH", ""
        ),
        smtp_host=os.getenv("GAOKAO_SMTP_HOST", ""),
        smtp_port=int(os.getenv("GAOKAO_SMTP_PORT", "25")),
        smtp_sender=os.getenv("GAOKAO_SMTP_SENDER", ""),
        smtp_username=os.getenv("GAOKAO_SMTP_USER", ""),
        smtp_password=os.getenv("GAOKAO_SMTP_PASS", ""),
        smtp_use_tls=os.getenv("GAOKAO_SMTP_USE_TLS", "false").lower() == "true",
        smtp_use_ssl=os.getenv("GAOKAO_SMTP_USE_SSL", "false").lower() == "true",
        alert_recipients=[
            s.strip()
            for s in os.getenv("GAOKAO_ALERT_RECIPIENTS", "").split(",")
            if s.strip()
        ],
        alert_webhook_urls=[
            s.strip()
            for s in os.getenv("GAOKAO_ALERT_WEBHOOK_URLS", "").split(",")
            if s.strip()
        ],
        ops_alert_log_path=os.getenv(
            "GAOKAO_OPS_ALERT_LOG", "data/alerts/ops-alerts.jsonl"
        ),
        deletion_request_log_path=os.getenv(
            "GAOKAO_DELETION_REQUEST_LOG", "data/alerts/deletion-requests.jsonl"
        ),
        retention_days=int(os.getenv("GAOKAO_RETENTION_DAYS", "180")),
        jwt_secret=os.getenv("GAOKAO_JWT_SECRET", _DEV_JWT_SECRET),
        portal_token_secret=_resolve_portal_token_secret(
            os.getenv("GAOKAO_ENV", "dev")
        ),
        jwt_algorithm=os.getenv("GAOKAO_JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.getenv("GAOKAO_JWT_EXP_MIN", "60")),
        default_admin_username=os.getenv("GAOKAO_ADMIN_USER", "admin"),
        default_admin_password=os.getenv("GAOKAO_ADMIN_PASS", _DEFAULT_ADMIN_PASSWORD),
        consent_version=os.getenv(
            "GAOKAO_CONSENT_VERSION", "privacy-policy-v2026.06.25"
        ),
        consent_scope_portal=os.getenv(
            "GAOKAO_CONSENT_SCOPE_PORTAL", "web-self-service-order-intake"
        ),
        consent_scope_channel_prefix=os.getenv(
            "GAOKAO_CONSENT_SCOPE_CHANNEL_PREFIX", "channel-intake"
        ),
    )
    # 生产环境 post-load 校验:webhook / portal token / JWT / admin password
    # / payment provider 必须满足强度门槛, 任一不满足 fail-closed (P0-2/P2-4/P2-5/6/20)。
    _enforce_payment_webhook_secret_policy(settings)
    _enforce_portal_token_secret_policy(settings)
    _enforce_jwt_secret_policy(settings)
    _enforce_default_admin_password_policy(settings)
    _enforce_payment_provider_policy(settings)
    return settings


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
        classes = sum(
            (
                any(ch.islower() for ch in password),
                any(ch.isupper() for ch in password),
                any(ch.isdigit() for ch in password),
                any(ch in string.punctuation for ch in password),
            )
        )
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
