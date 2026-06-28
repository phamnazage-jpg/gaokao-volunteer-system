"""LLM 集成模块。

支持 openai/dashscope/anthropic 三种供应商，通过统一的 OpenAI-compatible API 调用。
"""

from .client import LLMClient, LLMResponse, LLMError
from .prompts import (
    build_audit_prompt,
    build_cwb_prompt,
    build_full_plan_prompt,
)

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMError",
    "build_audit_prompt",
    "build_cwb_prompt",
    "build_full_plan_prompt",
]
