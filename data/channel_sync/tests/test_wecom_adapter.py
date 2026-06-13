"""T8.3 企业微信集成测试

覆盖:
- 机器人 webhook 文本通知 payload
- 应用消息 access_token 获取/缓存与文本消息 payload
- 上游 errcode / transport 异常统一包装
- 环境变量缺失 fail-fast
"""

from __future__ import annotations

import json
import os
import unittest
from dataclasses import dataclass
from typing import Optional

from data.channel_sync.wecom_adapter import (
    WeComAPIError,
    WeComAppClient,
    WeComAppConfig,
    WeComBotClient,
    WeComBotConfig,
    WeComConfigError,
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


class WeComBotClientTests(unittest.TestCase):
    def test_send_text_posts_robot_webhook_payload(self) -> None:
        transport = _FakeTransport([_FakeResponse(200, {"errcode": 0, "errmsg": "ok"})])
        client = WeComBotClient(
            config=WeComBotConfig(webhook_key="robot-key", timeout_seconds=3.0),
            transport=transport,
        )

        result = client.send_text(
            content="新订单已支付，请及时跟进",
            mentioned_list=["@all"],
            mentioned_mobile_list=["13800138000"],
        )

        self.assertEqual(result["errmsg"], "ok")
        self.assertEqual(len(transport.calls), 1)
        self.assertIn("/cgi-bin/webhook/send?key=robot-key", transport.calls[0]["url"])
        payload = json.loads(transport.calls[0]["body"].decode("utf-8"))
        self.assertEqual(payload["msgtype"], "text")
        self.assertEqual(payload["text"]["content"], "新订单已支付，请及时跟进")
        self.assertEqual(payload["text"]["mentioned_list"], ["@all"])
        self.assertEqual(payload["text"]["mentioned_mobile_list"], ["13800138000"])

    def test_transport_error_wrapped_as_wecom_api_error(self) -> None:
        client = WeComBotClient(
            config=WeComBotConfig(webhook_key="robot-key"),
            transport=_ExplodingTransport(),
        )

        with self.assertRaises(WeComAPIError) as cm:
            client.send_text(content="hello")
        self.assertEqual(cm.exception.endpoint, "/cgi-bin/webhook/send")
        self.assertIn("transport_error", str(cm.exception))

    def test_from_env_missing_webhook_key_fails_fast(self) -> None:
        old = os.environ.get("GAOKAO_WECOM_BOT_KEY")
        try:
            os.environ.pop("GAOKAO_WECOM_BOT_KEY", None)
            with self.assertRaises(WeComConfigError):
                WeComBotClient.from_env()
        finally:
            if old is None:
                os.environ.pop("GAOKAO_WECOM_BOT_KEY", None)
            else:
                os.environ["GAOKAO_WECOM_BOT_KEY"] = old


class WeComAppClientTests(unittest.TestCase):
    def test_access_token_cached_until_expiry(self) -> None:
        now = [1000.0]
        transport = _FakeTransport(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "invaliduser": ""}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "invaliduser": ""}),
            ]
        )
        client = WeComAppClient(
            config=WeComAppConfig(
                corp_id="corp-id",
                corp_secret="corp-secret",
                agent_id=1000002,
                timeout_seconds=3.0,
                token_refresh_skew_seconds=60.0,
            ),
            transport=transport,
            clock=lambda: now[0],
        )

        client.send_text(to_user="zhangsan", content="第一条")
        now[0] += 300
        client.send_text(to_party="party-1", content="第二条")

        token_fetches = [
            call for call in transport.calls if "/cgi-bin/gettoken?" in call["url"]
        ]
        self.assertEqual(len(token_fetches), 1)
        payload = json.loads(transport.calls[-1]["body"].decode("utf-8"))
        self.assertEqual(payload["msgtype"], "text")
        self.assertEqual(payload["agentid"], 1000002)
        self.assertEqual(payload["toparty"], "party-1")
        self.assertEqual(payload["text"]["content"], "第二条")

    def test_send_text_supports_duplicate_check_and_safe(self) -> None:
        transport = _FakeTransport(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(200, {"errcode": 0, "errmsg": "ok", "invaliduser": ""}),
            ]
        )
        client = WeComAppClient(
            config=WeComAppConfig(
                corp_id="corp-id", corp_secret="corp-secret", agent_id=42
            ),
            transport=transport,
        )

        result = client.send_text(
            to_user="lisi",
            content="请尽快联系家长",
            safe=1,
            enable_duplicate_check=1,
            duplicate_check_interval=600,
        )

        self.assertEqual(result["errmsg"], "ok")
        payload = json.loads(transport.calls[-1]["body"].decode("utf-8"))
        self.assertEqual(payload["touser"], "lisi")
        self.assertEqual(payload["safe"], 1)
        self.assertEqual(payload["enable_duplicate_check"], 1)
        self.assertEqual(payload["duplicate_check_interval"], 600)

    def test_upstream_errcode_raises_structured_error(self) -> None:
        transport = _FakeTransport(
            [
                _FakeResponse(200, {"access_token": "token-1", "expires_in": 7200}),
                _FakeResponse(200, {"errcode": 81013, "errmsg": "invalid userid"}),
            ]
        )
        client = WeComAppClient(
            config=WeComAppConfig(
                corp_id="corp-id", corp_secret="corp-secret", agent_id=42
            ),
            transport=transport,
        )

        with self.assertRaises(WeComAPIError) as cm:
            client.send_text(to_user="bad-user", content="hello")
        self.assertEqual(cm.exception.errcode, 81013)
        self.assertIn("invalid userid", str(cm.exception))

    def test_from_env_missing_secret_fails_fast(self) -> None:
        old_id = os.environ.get("GAOKAO_WECOM_CORP_ID")
        old_secret = os.environ.get("GAOKAO_WECOM_CORP_SECRET")
        old_agent = os.environ.get("GAOKAO_WECOM_AGENT_ID")
        try:
            os.environ["GAOKAO_WECOM_CORP_ID"] = "corp-id"
            os.environ.pop("GAOKAO_WECOM_CORP_SECRET", None)
            os.environ["GAOKAO_WECOM_AGENT_ID"] = "42"
            with self.assertRaises(WeComConfigError):
                WeComAppClient.from_env()
        finally:
            if old_id is None:
                os.environ.pop("GAOKAO_WECOM_CORP_ID", None)
            else:
                os.environ["GAOKAO_WECOM_CORP_ID"] = old_id
            if old_secret is None:
                os.environ.pop("GAOKAO_WECOM_CORP_SECRET", None)
            else:
                os.environ["GAOKAO_WECOM_CORP_SECRET"] = old_secret
            if old_agent is None:
                os.environ.pop("GAOKAO_WECOM_AGENT_ID", None)
            else:
                os.environ["GAOKAO_WECOM_AGENT_ID"] = old_agent
