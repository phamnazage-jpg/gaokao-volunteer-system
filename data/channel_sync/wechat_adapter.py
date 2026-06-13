"""微信 SDK 最小集成层（T8.2）

目标：不依赖第三方微信 SDK，仅用标准库封装两类常用能力：
- 订阅消息推送（/cgi-bin/message/subscribe/send）
- 客服文本消息（/cgi-bin/message/custom/send）

设计取向：
- access_token 自动缓存与过期刷新
- 纯标准库 HTTP 传输，便于单测注入 fake transport
- 上游 errcode / HTTP 状态统一包装为结构化异常
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional, Protocol
from urllib import error, parse, request


DEFAULT_API_BASE = "https://api.weixin.qq.com"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_TOKEN_REFRESH_SKEW_SECONDS = 60.0


class WeChatConfigError(ValueError):
    """微信配置缺失或非法。"""


class WeChatAPIError(RuntimeError):
    """微信接口返回错误。"""

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
class WeChatConfig:
    app_id: str
    app_secret: str
    api_base: str = DEFAULT_API_BASE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    token_refresh_skew_seconds: float = DEFAULT_TOKEN_REFRESH_SKEW_SECONDS

    def __post_init__(self) -> None:
        if not self.app_id:
            raise WeChatConfigError("GAOKAO_WECHAT_APP_ID 未设置")
        if not self.app_secret:
            raise WeChatConfigError("GAOKAO_WECHAT_APP_SECRET 未设置")
        if self.timeout_seconds <= 0:
            raise WeChatConfigError("timeout_seconds 必须大于 0")
        if self.token_refresh_skew_seconds < 0:
            raise WeChatConfigError("token_refresh_skew_seconds 不能为负")


@dataclass
class AccessToken:
    token: str
    expires_at: float

    def valid(self, now: float, skew_seconds: float) -> bool:
        return bool(self.token) and now < (self.expires_at - skew_seconds)


class Transport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> tuple[int, bytes]: ...


class UrllibTransport:
    """基于 urllib 的标准库 HTTP 传输实现。"""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> tuple[int, bytes]:
        req = request.Request(url=url, method=method.upper(), data=body)
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                return int(resp.status), resp.read()
        except error.HTTPError as e:
            return int(e.code), e.read()


class WeChatClient:
    """微信开放接口最小客户端。"""

    def __init__(
        self,
        *,
        config: WeChatConfig,
        transport: Optional[Transport] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._config = config
        self._transport = transport or UrllibTransport()
        self._clock = clock or time.time
        self._access_token: Optional[AccessToken] = None

    @classmethod
    def from_env(
        cls,
        *,
        transport: Optional[Transport] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> "WeChatClient":
        return cls(
            config=WeChatConfig(
                app_id=os.environ.get("GAOKAO_WECHAT_APP_ID", ""),
                app_secret=os.environ.get("GAOKAO_WECHAT_APP_SECRET", ""),
                api_base=os.environ.get("GAOKAO_WECHAT_API_BASE", DEFAULT_API_BASE),
                timeout_seconds=float(
                    os.environ.get(
                        "GAOKAO_WECHAT_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
                    )
                ),
                token_refresh_skew_seconds=float(
                    os.environ.get(
                        "GAOKAO_WECHAT_TOKEN_REFRESH_SKEW_SECONDS",
                        DEFAULT_TOKEN_REFRESH_SKEW_SECONDS,
                    )
                ),
            ),
            transport=transport,
            clock=clock,
        )

    def _now(self) -> float:
        return float(self._clock())

    def _api_url(self, path: str) -> str:
        base = self._config.api_base.rstrip("/")
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
                timeout=self._config.timeout_seconds,
            )
        except Exception as e:
            raise WeChatAPIError(
                f"微信接口 transport_error: {type(e).__name__}: {e}",
                endpoint=path,
            ) from e
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:  # pragma: no cover - defensive
            raise WeChatAPIError(
                f"微信接口返回非 JSON: {e}", http_status=status, endpoint=path
            ) from e
        if status >= 400:
            raise WeChatAPIError(
                f"微信接口 HTTP {status}",
                http_status=status,
                endpoint=path,
                errmsg=data.get("errmsg") if isinstance(data, dict) else None,
                errcode=data.get("errcode") if isinstance(data, dict) else None,
            )
        if not isinstance(data, dict):
            raise WeChatAPIError(
                "微信接口返回结构非法",
                http_status=status,
                endpoint=path,
            )
        errcode = data.get("errcode", 0)
        if errcode not in (0, None):
            raise WeChatAPIError(
                f"微信接口错误: {errcode} {data.get('errmsg', '')}".strip(),
                errcode=int(errcode),
                errmsg=str(data.get("errmsg", "")),
                http_status=status,
                endpoint=path,
            )
        return data

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
            "/cgi-bin/token",
            query={
                "grant_type": "client_credential",
                "appid": self._config.app_id,
                "secret": self._config.app_secret,
            },
        )
        token = str(data.get("access_token", ""))
        if not token:
            raise WeChatAPIError(
                "微信接口未返回 access_token",
                http_status=200,
                endpoint="/cgi-bin/token",
            )
        expires_in = float(data.get("expires_in", 7200))
        self._access_token = AccessToken(token=token, expires_at=now + expires_in)
        return token

    @staticmethod
    def _normalize_msg_data(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        for key, value in data.items():
            if isinstance(value, dict) and "value" in value:
                normalized[key] = {"value": value["value"]}
            else:
                normalized[key] = {"value": value}
        return normalized

    def send_subscribe_message(
        self,
        *,
        openid: str,
        template_id: str,
        data: dict[str, Any],
        page: Optional[str] = None,
        miniprogram_state: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> dict[str, Any]:
        token = self._get_access_token()
        payload: dict[str, Any] = {
            "touser": openid,
            "template_id": template_id,
            "data": self._normalize_msg_data(data),
        }
        if page:
            payload["page"] = page
        if miniprogram_state:
            payload["miniprogram_state"] = miniprogram_state
        if lang:
            payload["lang"] = lang
        return self._request_json(
            "POST",
            "/cgi-bin/message/subscribe/send",
            query={"access_token": token},
            payload=payload,
        )

    def send_custom_message(
        self,
        *,
        openid: str,
        msgtype: str,
        payload: dict[str, Any],
        kf_account: Optional[str] = None,
    ) -> dict[str, Any]:
        token = self._get_access_token()
        body: dict[str, Any] = {"touser": openid, "msgtype": msgtype, msgtype: payload}
        if kf_account:
            body["customservice"] = {"kf_account": kf_account}
        return self._request_json(
            "POST",
            "/cgi-bin/message/custom/send",
            query={"access_token": token},
            payload=body,
        )

    def send_custom_text(
        self,
        *,
        openid: str,
        content: str,
        kf_account: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.send_custom_message(
            openid=openid,
            msgtype="text",
            payload={"content": content},
            kf_account=kf_account,
        )


__all__ = [
    "AccessToken",
    "DEFAULT_API_BASE",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_TOKEN_REFRESH_SKEW_SECONDS",
    "Transport",
    "UrllibTransport",
    "WeChatAPIError",
    "WeChatClient",
    "WeChatConfig",
    "WeChatConfigError",
]
