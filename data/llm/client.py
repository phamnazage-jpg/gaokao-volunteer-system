"""LLM 客户端：统一 OpenAI-compatible 接口调用。"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any

from admin.config import Settings


class LLMError(Exception):
    """LLM 调用失败。"""


@dataclass(frozen=True)
class LLMResponse:
    """LLM 响应。"""

    content: str
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class LLMClient:
    """统一 LLM 客户端，通过 OpenAI-compatible API 调用。

    支持:
    - openai: https://api.openai.com/v1
    - dashscope: https://dashscope.aliyuncs.com/compatible-mode/v1
    - anthropic: 通过兼容层或直接 API
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider = settings.llm_provider
        self._api_key = settings.llm_api_key
        self._base_url = settings.llm_base_url.rstrip("/")
        self._model = settings.llm_model
        self._timeout = settings.llm_timeout_seconds
        self._max_tokens = settings.llm_max_tokens

    @property
    def is_configured(self) -> bool:
        """LLM 是否已配置可用。"""
        return self._provider != "none" and bool(self._api_key)

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """调用 chat completions API。

        Args:
            messages: OpenAI 格式的消息列表。
            temperature: 采样温度。
            max_tokens: 最大生成 token 数，默认使用 Settings 配置。

        Returns:
            LLMResponse。

        Raises:
            LLMError: 调用失败。
        """
        if not self.is_configured:
            raise LLMError(
                f"LLM 未配置 (provider={self._provider})。"
                "请设置 GAOKAO_LLM_PROVIDER 和 GAOKAO_LLM_API_KEY。"
            )

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
        except urllib.error.HTTPError as e:
            raw_body = e.read()
            error_body = (
                raw_body.decode("utf-8", "replace")
                if isinstance(raw_body, bytes)
                else str(raw_body)
            )
            raise LLMError(f"LLM API HTTP {e.code}: {error_body[:500]}") from e
        except urllib.error.URLError as e:
            raise LLMError(f"LLM API 连接失败: {e}") from e
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM API 响应解析失败: {e}") from e

        choices = result.get("choices", [])
        if not choices:
            raise LLMError(f"LLM API 返回空 choices: {result}")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise LLMError(f"LLM API 返回空 content: {result}")

        usage = result.get("usage", {})
        model = result.get("model", self._model)

        return LLMResponse(
            content=content,
            usage=usage,
            model=model,
            raw=result,
        )

    def chat_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """便捷方法：system + user 两条消息。"""
        return self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
