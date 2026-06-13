"""渠道 SDK 集成层 (T8)

子模块:

- :mod:`data.channel_sync.signature` — HMAC-SHA256 签名 / 校验
- :mod:`data.channel_sync.audit` — Webhook 审计日志
- :mod:`data.channel_sync.xianyu_adapter` — 闲鱼事件 → Order 映射
- :mod:`data.channel_sync.wechat_adapter` — 微信消息推送 / 客服消息
- :mod:`data.channel_sync.wecom_adapter` — 企业微信机器人 / 应用消息
- :mod:`data.channel_sync.dao_extension` — 配套订单 DAO 扩展
- :mod:`data.channel_sync.poller` — 兜底轮询
- :mod:`data.channel_sync.monitor` — 兜底巡检 / 人工兜底提示
- :mod:`data.channel_sync.webhook_server` — 接收端 (stdlib http.server)

公开 API 由各子模块 re-export。
"""

from . import audit, dao_extension, monitor, poller, signature, webhook_server
from . import wechat_adapter, wecom_adapter, xianyu_adapter

__all__ = [
    "audit",
    "dao_extension",
    "monitor",
    "poller",
    "signature",
    "webhook_server",
    "wechat_adapter",
    "wecom_adapter",
    "xianyu_adapter",
]
