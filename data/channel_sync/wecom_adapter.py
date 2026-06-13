"""企业微信最小集成层（T8.3）

目标：不依赖第三方企业微信 SDK，仅用标准库封装两类常用能力：
- 通知机器人 webhook 文本消息（/cgi-bin/webhook/send）
- 应用消息文本推送（/cgi-bin/message/send）

设计取向：
- 机器人与应用消息分离建模，避免混淆不同鉴权方式
- 应用 access_token 自动缓存与过期刷新
- 纯标准库 HTTP 传输，便于单测注入 fake transport
- 上游 errcode / HTTP 状态 / transport 异常统一包装为结构化异常
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional
from urllib import parse

from .wechat_adapter import AccessToken, Transport, UrllibTransport

DEFAULT_API_BASE = "https://qyapi.weixin.qq.com"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_TOKEN_REFRESH_SKEW_SECONDS = 60.0


class WeComConfigError(ValueError):
    """企业微信配置缺失或非法。"""


class WeComAPIError(RuntimeError):
    """企业微信接口返回错误。"""

    def __init__(
        self,
        message: str,
        *,
        errcode: Optional[int] = None,
        errmsg: Optional[str] = None,
        http_status: Optional[int] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.errcode = errcode
        self.errmsg = errmsg
        self.http_status = http_status
        self.endpoint = endpoint


@dataclass(frozen=True)
class WeComBotConfig:
    webhook_key: str
    api_base: str = DEFAULT_API_BASE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if not self.webhook_key:
            raise WeComConfigError("GAOKAO_WECOM_BOT_KEY 未设置")
        if self.timeout_seconds <= 0:
            raise WeComConfigError("timeout_seconds 必须大于 0")


@dataclass(frozen=True)
class WeComAppConfig:
    corp_id: str
    corp_secret: str
    agent_id: int
    api_base: str = DEFAULT_API_BASE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    token_refresh_skew_seconds: float = DEFAULT_TOKEN_REFRESH_SKEW_SECONDS

    def __post_init__(self) -> None:
        if not self.corp_id:
            raise WeComConfigError("GAOKAO_WECOM_CORP_ID 未设置")
        if not self.corp_secret:
            raise WeComConfigError("GAOKAO_WECOM_CORP_SECRET 未设置")
        if self.agent_id <= 0:
            raise WeComConfigError("GAOKAO_WECOM_AGENT_ID 必须为正整数")
        if self.timeout_seconds <= 0:
            raise WeComConfigError("timeout_seconds 必须大于 0")
        if self.token_refresh_skew_seconds < 0:
            raise WeComConfigError("token_refresh_skew_seconds 不能为负")


class _WeComBaseClient:
    def __init__(
        self,
        *,
        api_base: str,
        timeout_seconds: float,
        transport: Optional[Transport] = None,
    ) -> None:
        self._api_base = api_base
        self._timeout_seconds = timeout_seconds
        self._transport = transport or UrllibTransport()

    def _api_url(self, path: str) -> str:
        base = self._api_base.rstrip("/")
        return f"{base}/{path.lstrip('/')}"

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        query: Optional[dict[str, Any]] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = self._api_url(path)
        if query:
            url = f"{url}?{parse.urlencode(query)}"
        body = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        try:
            status, raw = self._transport.request(
                method.upper(),
                url,
                headers=headers,
                body=body,
                timeout=self._timeout_seconds,
            )
        except Exception as e:
            raise WeComAPIError(
                f"企业微信接口 transport_error: {e}",
                endpoint=path,
            ) from e
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:  # pragma: no cover - defensive
            raise WeComAPIError(
                f"企业微信接口返回非 JSON: {e}", http_status=status, endpoint=path
            ) from e
        if status >= 400:
            raise WeComAPIError(
                f"企业微信接口 HTTP {status}",
                http_status=status,
                endpoint=path,
                errmsg=data.get("errmsg") if isinstance(data, dict) else None,
                errcode=data.get("errcode") if isinstance(data, dict) else None,
            )
        if not isinstance(data, dict):
            raise WeComAPIError(
                "企业微信接口返回结构非法",
                http_status=status,
                endpoint=path,
            )
        errcode = data.get("errcode", 0)
        if errcode not in (0, None):
            raise WeComAPIError(
                f"企业微信接口错误: {errcode} {data.get('errmsg', '')}".strip(),
                errcode=int(errcode),
                errmsg=str(data.get("errmsg", "")),
                http_status=status,
                endpoint=path,
            )
        return data


class WeComBotClient(_WeComBaseClient):
    def __init__(
        self, *, config: WeComBotConfig, transport: Optional[Transport] = None
    ) -> None:
        super().__init__(
            api_base=config.api_base,
            timeout_seconds=config.timeout_seconds,
            transport=transport,
        )
        self._config = config

    @classmethod
    def from_env(cls, *, transport: Optional[Transport] = None) -> "WeComBotClient":
        return cls(
            config=WeComBotConfig(
                webhook_key=os.environ.get("GAOKAO_WECOM_BOT_KEY", ""),
                api_base=os.environ.get("GAOKAO_WECOM_API_BASE", DEFAULT_API_BASE),
                timeout_seconds=float(
                    os.environ.get(
                        "GAOKAO_WECOM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
                    )
                ),
            ),
            transport=transport,
        )

    def send_text(
        self,
        *,
        content: str,
        mentioned_list: Optional[list[str]] = None,
        mentioned_mobile_list: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "msgtype": "text",
            "text": {"content": content},
        }
        if mentioned_list:
            payload["text"]["mentioned_list"] = list(mentioned_list)
        if mentioned_mobile_list:
            payload["text"]["mentioned_mobile_list"] = list(mentioned_mobile_list)
        return self._request_json(
            "POST",
            "/cgi-bin/webhook/send",
            query={"key": self._config.webhook_key},
            payload=payload,
        )


class WeComAppClient(_WeComBaseClient):
    def __init__(
        self,
        *,
        config: WeComAppConfig,
        transport: Optional[Transport] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        super().__init__(
            api_base=config.api_base,
            timeout_seconds=config.timeout_seconds,
            transport=transport,
        )
        self._config = config
        self._clock = clock or time.time
        self._access_token: Optional[AccessToken] = None

    @classmethod
    def from_env(
        cls,
        *,
        transport: Optional[Transport] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> "WeComAppClient":
        return cls(
            config=WeComAppConfig(
                corp_id=os.environ.get("GAOKAO_WECOM_CORP_ID", ""),
                corp_secret=os.environ.get("GAOKAO_WECOM_CORP_SECRET", ""),
                agent_id=int(os.environ.get("GAOKAO_WECOM_AGENT_ID", "0")),
                api_base=os.environ.get("GAOKAO_WECOM_API_BASE", DEFAULT_API_BASE),
                timeout_seconds=float(
                    os.environ.get(
                        "GAOKAO_WECOM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
                    )
                ),
                token_refresh_skew_seconds=float(
                    os.environ.get(
                        "GAOKAO_WECOM_TOKEN_REFRESH_SKEW_SECONDS",
                        DEFAULT_TOKEN_REFRESH_SKEW_SECONDS,
                    )
                ),
            ),
            transport=transport,
            clock=clock,
        )

    def _now(self) -> float:
        return float(self._clock())

    def _get_access_token(self, *, force_refresh: bool = False) -> str:
        now = self._now()
        if (
            not force_refresh
            and self._access_token is not None
            and self._access_token.valid(now, self._config.token_refresh_skew_seconds)
        ):
            return self._access_token.token

        data = self._request_json(
            "GET",
            "/cgi-bin/gettoken",
            query={
                "corpid": self._config.corp_id,
                "corpsecret": self._config.corp_secret,
            },
        )
        token = str(data.get("access_token", ""))
        if not token:
            raise WeComAPIError(
                "企业微信接口未返回 access_token",
                http_status=200,
                endpoint="/cgi-bin/gettoken",
            )
        expires_in = float(data.get("expires_in", 7200))
        self._access_token = AccessToken(token=token, expires_at=now + expires_in)
        return token

    def send_text(
        self,
        *,
        content: str,
        to_user: Optional[str] = None,
        to_party: Optional[str] = None,
        to_tag: Optional[str] = None,
        safe: int = 0,
        enable_duplicate_check: int = 0,
        duplicate_check_interval: int = 1800,
    ) -> dict[str, Any]:
        token = self._get_access_token()
        payload: dict[str, Any] = {
            "msgtype": "text",
            "agentid": self._config.agent_id,
            "text": {"content": content},
            "safe": safe,
            "enable_duplicate_check": enable_duplicate_check,
            "duplicate_check_interval": duplicate_check_interval,
        }
        if to_user:
            payload["touser"] = to_user
        if to_party:
            payload["toparty"] = to_party
        if to_tag:
            payload["totag"] = to_tag
        if not any((to_user, to_party, to_tag)):
            payload["touser"] = "@all"
        return self._request_json(
            "POST",
            "/cgi-bin/message/send",
            query={"access_token": token},
            payload=payload,
        )


__all__ = [
    "DEFAULT_API_BASE",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_TOKEN_REFRESH_SKEW_SECONDS",
    "WeComAPIError",
    "WeComAppClient",
    "WeComAppConfig",
    "WeComBotClient",
    "WeComBotConfig",
    "WeComConfigError",
]
