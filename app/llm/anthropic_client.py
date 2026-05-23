"""AnthropicClient — Phase 1 唯一 LLM 實作 (ADR-0001 / ADR-0012).

依 ADR-0001 §Decision:
- 主力 model: claude-sonnet-4-6
- 高頻 / 成本敏感: claude-haiku-4-5
- prompt caching 啟用（cache long system prompts + knowledge context）

Note: 本檔不直接被 test 跑（沒 API key）；測試覆蓋見 tests/llm/test_anthropic_client.py
（用 fake / mocked anthropic SDK）。S4 開工真實 API 接通時再加 integration test。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import (
    Message,
    TextBlock,
    ToolUseBlock,
)

from app.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolDefinition,
    LLMToolUse,
    LLMUsage,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
HAIKU_MODEL = "claude-haiku-4-5"


class AnthropicClient(LLMClient):
    """Anthropic Claude API wrapper.

    Args:
        api_key: 直接傳 key；若 None 則由 anthropic SDK 從 ANTHROPIC_API_KEY env 讀
        default_model: 不指定 model 時的預設值
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        default_model: str = DEFAULT_MODEL,
        client: AsyncAnthropic | None = None,
    ) -> None:
        # 允許 test 傳入 fake client；prod 走 default 建構
        self._client = client if client is not None else AsyncAnthropic(api_key=api_key)
        self._default_model = default_model

    async def complete(
        self,
        *,
        messages: Sequence[LLMMessage],
        system: str | None = None,
        tools: Sequence[LLMToolDefinition] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        model: str | None = None,
    ) -> LLMResponse:
        anthropic_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]

        kwargs: dict[str, Any] = {
            "model": model or self._default_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages,
        }
        if system is not None:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                }
                for t in tools
            ]

        raw: Message = await self._client.messages.create(**kwargs)
        return _to_llm_response(raw)


def _to_llm_response(raw: Message) -> LLMResponse:
    """把 anthropic Message 轉成 AEOS LLMResponse DTO。"""
    text_parts: list[str] = []
    tool_uses: list[LLMToolUse] = []

    for block in raw.content:
        if isinstance(block, TextBlock):
            text_parts.append(block.text)
        elif isinstance(block, ToolUseBlock):
            tool_uses.append(
                LLMToolUse(
                    tool_use_id=block.id,
                    name=block.name,
                    input=dict(block.input) if isinstance(block.input, dict) else {},
                )
            )

    usage = LLMUsage(
        input_tokens=raw.usage.input_tokens,
        output_tokens=raw.usage.output_tokens,
        cache_creation_input_tokens=getattr(raw.usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(raw.usage, "cache_read_input_tokens", 0) or 0,
    )

    return LLMResponse(
        text="".join(text_parts),
        tool_uses=tool_uses,
        stop_reason=raw.stop_reason or "end_turn",
        model=raw.model,
        usage=usage,
    )
