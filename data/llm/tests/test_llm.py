"""LLM 模块测试。"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

from data.llm.client import LLMClient, LLMResponse, LLMError
from data.llm.prompts import (
    build_audit_prompt,
    build_cwb_prompt,
    build_full_plan_prompt,
)


@dataclass
class MockSettings:
    llm_provider: str = "none"
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    llm_timeout_seconds: int = 60
    llm_max_tokens: int = 4096


class TestLLMClient:
    def test_not_configured_when_provider_none(self):
        client = LLMClient(MockSettings(llm_provider="none"))
        assert not client.is_configured

    def test_not_configured_when_no_api_key(self):
        client = LLMClient(MockSettings(llm_provider="openai", llm_api_key=""))
        assert not client.is_configured

    def test_configured_when_provider_and_key_set(self):
        client = LLMClient(MockSettings(llm_provider="openai", llm_api_key="sk-test"))
        assert client.is_configured

    def test_chat_raises_when_not_configured(self):
        client = LLMClient(MockSettings(llm_provider="none"))
        with pytest.raises(LLMError, match="LLM 未配置"):
            client.chat([{"role": "user", "content": "test"}])

    @patch("data.llm.client.urllib.request.urlopen")
    def test_chat_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"choices":[{"message":{"content":"test response"}}],"usage":{"total_tokens":10},"model":"qwen-plus"}'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = LLMClient(
            MockSettings(llm_provider="dashscope", llm_api_key="sk-test")
        )
        result = client.chat([{"role": "user", "content": "hello"}])

        assert isinstance(result, LLMResponse)
        assert result.content == "test response"
        assert result.model == "qwen-plus"
        assert result.usage["total_tokens"] == 10

    @patch("data.llm.client.urllib.request.urlopen")
    def test_chat_http_error(self, mock_urlopen):
        import urllib.error
        import io

        error_fp = io.BytesIO(b'{"error":"bad key"}')
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://test", 401, "Unauthorized", {}, error_fp
        )
        client = LLMClient(MockSettings(llm_provider="openai", llm_api_key="bad"))
        with pytest.raises(LLMError, match="HTTP 401"):
            client.chat([{"role": "user", "content": "test"}])

    def test_chat_with_system(self):
        """chat_with_system 构建正确的消息结构。"""
        with patch.object(LLMClient, "chat") as mock_chat:
            mock_chat.return_value = LLMResponse(content="ok")
            client = LLMClient(
                MockSettings(llm_provider="openai", llm_api_key="sk-test")
            )
            client.chat_with_system("you are helpful", "hello")

            call_args = mock_chat.call_args
            messages = call_args[0][0]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "you are helpful"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "hello"


class TestPrompts:
    def test_audit_prompt_structure(self):
        system, user = build_audit_prompt(
            province="湖南",
            score=578,
            rank=12000,
            subjects=["物理", "化学", "生物"],
            existing_plan="已有一版方案",
        )
        assert "志愿填报顾问" in system
        assert "湖南" in user
        assert "578" in user
        assert "物理" in user
        assert "JSON" in user
        assert "risk_level" in user

    def test_audit_prompt_with_crowd_db(self):
        recs = [
            {"name": "湖南大学", "major": "计算机"},
            {"name": "中南大学", "major": "软件工程"},
        ]
        system, user = build_audit_prompt(
            province="湖南",
            score=578,
            rank=12000,
            subjects=["物理"],
            existing_plan="test",
            crowd_db_recs=recs,
        )
        assert "湖南大学" in user
        assert "中南大学" in user

    def test_audit_prompt_minimal(self):
        system, user = build_audit_prompt(
            province="广东",
            score=None,
            rank=None,
            subjects=[],
            existing_plan="",
        )
        assert "未提供" in user

    def test_cwb_prompt_structure(self):
        system, user = build_cwb_prompt(
            province="湖南",
            score=578,
            rank=12000,
            subjects=["物理", "化学", "生物"],
            target_cities=["长沙", "深圳"],
        )
        assert "冲稳保" in system
        assert "长沙" in user
        assert "598" in user  # score + 20
        assert "558" in user  # score - 20

    def test_full_plan_prompt_structure(self):
        system, user = build_full_plan_prompt(
            province="湖南",
            score=578,
            rank=12000,
            subjects=["物理", "化学", "生物"],
            target_majors=["计算机科学", "人工智能"],
            family_background="家长希望省内优先",
        )
        assert "完整" in system
        assert "计算机科学" in user
        assert "家长希望省内优先" in user
        assert "volunteers" in user
        assert "至少 8 条" in user
