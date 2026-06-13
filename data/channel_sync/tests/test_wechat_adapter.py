"""T8.2 微信 SDK 集成测试

覆盖:
- access token 获取/缓存/过期刷新
- 订阅消息 payload 规范化与发送
- 客服文本消息 payload 与可选客服账号字段
- 上游 errcode / HTTP 异常透传为结构化错误
- 环境变量缺失 fail-fast
"""

from __future__ import annotations

import json
import os
import unittest
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

from data.channel_sync.wechat_adapter import (
    WeChatAPIError,
    WeChatClient,
    WeChatConfig,
    WeChatConfigError,
)


@dataclass
class _FakeResponse:
    status: int
    payload: dict


class _FakeTransport:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: float = 0,
    ) -> tuple[int, bytes]:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "body": body,
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("no fake response left")
        response = self._responses.pop(0)
        return response.status, json.dumps(response.payload).encode("utf-8")


class _ExplodingTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: float = 0,
    ) -> tuple[int, bytes]:
        raise TimeoutError("network down")


class WeChatClientTests(unittest.TestCase):
    def make_client(
        self,
        responses: list[_FakeResponse],
        *,
        clock: Callable[[], float] | None = None,
    ) -> tuple[WeChatClient, _FakeTransport]:
        transport = _FakeTransport(responses)
        client = WeChatClient(
            config=WeChatConfig(
                app_id="wx-test-appid",
                app_secret="wx-test-secret",
                api_base="https://api.weixin.qq.com",
                timeout_seconds=3.0,
                token_refresh_skew_seconds=60,
            ),
            transport=transport,
            clock=clock,
        )
        return client, transport

    def test_access_token_cached_until_expiry(self) -> None:
        now = [1000.0]
        client, transport = self.make_client(
            [
                _FakeResponse(
                    200,
                    {
                        "access_token": "token-1",
                        "expires_in": 7200,
                    },
                ),
                _FakeResponse(
                    200,
                    {
                        "errcode": 0,
                        "errmsg": "ok",
                        "msgid": 123,
                    },
                ),
                _FakeResponse(
                    200,
                    {
                        "errcode": 0,
                        "errmsg": "ok",
                        "msgid": 124,
                    },
                ),
            ],
            clock=lambda: now[0],
        )

        client.send_subscribe_message(
            openid="openid-1",
            template_id="tmpl-1",
            data={"thing1": "待付款提醒"},
        )
        now[0] += 300
        client.send_custom_text(openid="openid-1", content="您好，这里是客服")

        self.assertEqual(len(transport.calls), 3)
        self.assertIn("/cgi-bin/token?", transport.calls[0]["url"])
        self.assertIn(
            "access_token=token-1",
            transport.calls[1]["url"] + transport.calls[2]["url"],
        )
        token_fetches = [
            call for call in transport.calls if "/cgi-bin/token?" in call["url"]
        ]
        self.assertEqual(len(token_fetches), 1)

    def test_access_token_refreshes_after_expiry(self) -> None:
        now = [1000.0]
        client, transport = self.make_client(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 120}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "msgid": 1}),
                _FakeResponse(200, {"access_token": "token-2", "expires_in": 120}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "msgid": 2}),
            ],
            clock=lambda: now[0],
        )

        client.send_custom_text(openid="openid-1", content="first")
        now[0] += 70
        client.send_custom_text(openid="openid-1", content="second")

        token_fetches = [
            call for call in transport.calls if "/cgi-bin/token?" in call["url"]
        ]
        self.assertEqual(len(token_fetches), 2)
        self.assertIn("access_token=token-2", transport.calls[-1]["url"])

    def test_send_subscribe_message_normalizes_payload(self) -> None:
        client, transport = self.make_client(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "msgid": 9001}),
            ]
        )

        result = client.send_subscribe_message(
            openid="openid-1",
            template_id="tmpl-1",
            data={
                "thing1": "支付成功",
                "date2": {"value": "2026-06-12 18:00"},
            },
            page="pages/orders/detail?id=GKO-1",
            miniprogram_state="formal",
            lang="zh_CN",
        )

        self.assertEqual(result["msgid"], 9001)
        send_call = transport.calls[-1]
        payload = json.loads(send_call["body"].decode("utf-8"))
        self.assertEqual(payload["touser"], "openid-1")
        self.assertEqual(payload["template_id"], "tmpl-1")
        self.assertEqual(payload["data"]["thing1"], {"value": "支付成功"})
        self.assertEqual(payload["data"]["date2"], {"value": "2026-06-12 18:00"})
        self.assertEqual(payload["page"], "pages/orders/detail?id=GKO-1")
        self.assertEqual(payload["miniprogram_state"], "formal")
        self.assertEqual(payload["lang"], "zh_CN")

    def test_send_custom_text_with_kf_account(self) -> None:
        client, transport = self.make_client(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "msgid": 7001}),
            ]
        )

        result = client.send_custom_text(
            openid="openid-2",
            content="请补充考生分数和位次",
            kf_account="advisor@test",
        )

        self.assertEqual(result["msgid"], 7001)
        payload = json.loads(transport.calls[-1]["body"].decode("utf-8"))
        self.assertEqual(payload["msgtype"], "text")
        self.assertEqual(payload["text"]["content"], "请补充考生分数和位次")
        self.assertEqual(payload["customservice"], {"kf_account": "advisor@test"})

    def test_upstream_errcode_raises_structured_error(self) -> None:
        client, _ = self.make_client(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(200, {"errcode": 40003, "errmsg": "invalid openid"}),
            ]
        )

        with self.assertRaises(WeChatAPIError) as cm:
            client.send_custom_text(openid="bad-openid", content="hello")
        self.assertEqual(cm.exception.errcode, 40003)
        self.assertIn("invalid openid", str(cm.exception))

    def test_http_error_raises_structured_error(self) -> None:
        client, _ = self.make_client(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(500, {"errcode": 0, "errmsg": "server busy"}),
            ]
        )

        with self.assertRaises(WeChatAPIError) as cm:
            client.send_custom_text(openid="openid-1", content="hello")
        self.assertEqual(cm.exception.http_status, 500)

    def test_transport_error_wrapped_as_wechat_api_error(self) -> None:
        client = WeChatClient(
            config=WeChatConfig(
                app_id="wx-test-appid",
                app_secret="wx-test-secret",
            ),
            transport=_ExplodingTransport(),
        )

        with self.assertRaises(WeChatAPIError) as cm:
            client.send_custom_text(openid="openid-1", content="hello")
        self.assertIn("transport_error", str(cm.exception))

    def test_config_from_env_missing_secret_fails_fast(self) -> None:
        old_id = os.environ.get("GAOKAO_WECHAT_APP_ID")
        old_secret = os.environ.get("GAOKAO_WECHAT_APP_SECRET")
        try:
            os.environ["GAOKAO_WECHAT_APP_ID"] = "wx-appid"
            os.environ.pop("GAOKAO_WECHAT_APP_SECRET", None)
            with self.assertRaises(WeChatConfigError):
                WeChatClient.from_env()
        finally:
            if old_id is None:
                os.environ.pop("GAOKAO_WECHAT_APP_ID", None)
            else:
                os.environ["GAOKAO_WECHAT_APP_ID"] = old_id
            if old_secret is None:
                os.environ.pop("GAOKAO_WECHAT_APP_SECRET", None)
            else:
                os.environ["GAOKAO_WECHAT_APP_SECRET"] = old_secret
