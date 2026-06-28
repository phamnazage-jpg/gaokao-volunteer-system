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
        self._timeout = settings.llm_timeout_seconds
        self._max_tokens = settings.llm_max_tokens

        # 构建供应商链：主供应商 + fallback 供应商列表
        self._providers: list[dict[str, str]] = []
        if settings.llm_provider != "none" and settings.llm_api_key:
            self._providers.append({
                "provider": settings.llm_provider,
                "api_key": settings.llm_api_key,
                "base_url": settings.llm_base_url.rstrip("/"),
                "model": settings.llm_model,
            })

        # 解析 fallback 配置
        fb_models = [
            s.strip()
            for s in (settings.llm_fallback_models or "").split(",")
            if s.strip()
        ]
        fb_providers = [
            s.strip()
            for s in (settings.llm_fallback_providers or "").split(",")
            if s.strip()
        ]
        fb_keys = [
            s.strip()
            for s in (settings.llm_fallback_api_keys or "").split(",")
            if s.strip()
        ]
        fb_urls = [
            s.strip()
            for s in (settings.llm_fallback_base_urls or "").split(",")
            if s.strip()
        ]

        for i, model in enumerate(fb_models):
            provider = (
                fb_providers[i]
                if i < len(fb_providers)
                else (self._providers[0]["provider"] if self._providers else "openai")
            )
            api_key = (
                fb_keys[i]
                if i < len(fb_keys)
                else (self._providers[0]["api_key"] if self._providers else "")
            )
            base_url = (
                fb_urls[i].rstrip("/")
                if i < len(fb_urls)
                else (
                    self._providers[0]["base_url"]
                    if self._providers
                    else "https://api.openai.com/v1"
                )
            )
            if api_key:
                self._providers.append({
                    "provider": provider,
                    "api_key": api_key,
                    "base_url": base_url,
                    "model": model,
                })

        # 兼容旧接口
        self._provider = self._providers[0]["provider"] if self._providers else "none"
        self._api_key = self._providers[0]["api_key"] if self._providers else ""
        self._base_url = self._providers[0]["base_url"] if self._providers else ""
        self._model = self._providers[0]["model"] if self._providers else ""

    @property
    def is_configured(self) -> bool:
        """LLM 是否已配置可用。"""
        return len(self._providers) > 0

    @property
    def provider_count(self) -> int:
        """已配置的供应商数量（含主+fallback）。"""
        return len(self._providers)

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """调用 chat completions API，支持多供应商 fallback。

        按供应商链顺序依次尝试，第一个成功即返回。
        全部失败时抛出最后一个错误。

        Args:
            messages: OpenAI 格式的消息列表。
            temperature: 采样温度。
            max_tokens: 最大生成 token 数，默认使用 Settings 配置。

        Returns:
            LLMResponse。

        Raises:
            LLMError: 全部供应商都失败。
        """
        if not self.is_configured:
            raise LLMError(
                f"LLM 未配置 (provider={self._provider})。"
                "请设置 GAOKAO_LLM_PROVIDER 和 GAOKAO_LLM_API_KEY。"
            )

        last_error: LLMError | None = None

        for idx, prov in enumerate(self._providers):
            try:
                return self._call_single_provider(
                    provider=prov,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens or self._max_tokens,
                )
            except LLMError as e:
                last_error = e
                prov_name = prov["provider"]
                model_name = prov["model"]
                # 如果还有下一个供应商，继续尝试
                if idx < len(self._providers) - 1:
                    continue
                # 最后一个也失败了
                raise LLMError(
                    f"全部 {len(self._providers)} 个 LLM 供应商均失败。"
                    f"最后错误 ({prov_name}/{model_name}): {e}"
                ) from e

        # 理论上不会到达这里
        raise last_error or LLMError("未知 LLM 错误")

    def _call_single_provider(
        self,
        *,
        provider: dict[str, str],
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """调用单个供应商的 API。"""
        payload: dict[str, Any] = {
            "model": provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = f"{provider['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['api_key']}",
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
        model = result.get("model", provider["model"])

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
