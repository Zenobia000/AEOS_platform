"""AnthropicClient 單元測試 — 用 fake anthropic SDK，不打真實 API.

S4 開工後加 integration test (with real API key + smoke against sonnet)。
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.llm.anthropic_client import AnthropicClient
from app.llm.client import (
    LLMMessage,
    LLMResponse,
    LLMToolDefinition,
)


def _fake_text_block(text: str) -> Any:
    from anthropic.types import TextBlock

    return TextBlock(type="text", text=text, citations=None)


def _fake_tool_use_block(tool_id: str, name: str, input_dict: dict[str, Any]) -> Any:
    from anthropic.types import ToolUseBlock

    return ToolUseBlock(type="tool_use", id=tool_id, name=name, input=input_dict)


def _fake_message(
    *,
    content_blocks: list[Any],
    input_tokens: int = 100,
    output_tokens: int = 50,
    stop_reason: str = "end_turn",
    model: str = "claude-sonnet-4-6",
    cache_creation: int = 0,
    cache_read: int = 0,
) -> MagicMock:
    msg = MagicMock()
    msg.content = content_blocks
    msg.stop_reason = stop_reason
    msg.model = model
    msg.usage = MagicMock(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=cache_creation,
        cache_read_input_tokens=cache_read,
    )
    return msg


@pytest.fixture
def fake_sdk_client() -> MagicMock:
    """A fake AsyncAnthropic with .messages.create coroutine."""
    sdk = MagicMock()
    sdk.messages = MagicMock()
    sdk.messages.create = AsyncMock()
    return sdk


async def test_complete_text_only(fake_sdk_client: MagicMock) -> None:
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("您好，有什麼可以幫您？")],
        input_tokens=120,
        output_tokens=30,
    )

    client = AnthropicClient(client=fake_sdk_client)
    resp: LLMResponse = await client.complete(
        messages=[LLMMessage(role="user", content="hi")],
        system="你是 AI 客服",
        max_tokens=200,
        temperature=0.2,
    )

    assert resp.text == "您好，有什麼可以幫您？"
    assert resp.tool_uses == []
    assert resp.usage.input_tokens == 120
    assert resp.usage.output_tokens == 30
    assert resp.usage.total_tokens == 150
    assert resp.model == "claude-sonnet-4-6"
    assert resp.stop_reason == "end_turn"


async def test_complete_with_tool_use(fake_sdk_client: MagicMock) -> None:
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[
            _fake_text_block("讓我查一下訂單。"),
            _fake_tool_use_block(
                tool_id="toolu_abc",
                name="lookup_order",
                input_dict={"order_id": "12345"},
            ),
        ],
        stop_reason="tool_use",
    )

    client = AnthropicClient(client=fake_sdk_client)
    resp = await client.complete(
        messages=[LLMMessage(role="user", content="查訂單 12345")],
        tools=[
            LLMToolDefinition(
                name="lookup_order",
                description="依訂單編號查訂單詳情",
                input_schema={
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                },
            )
        ],
    )

    assert resp.text == "讓我查一下訂單。"
    assert len(resp.tool_uses) == 1
    assert resp.tool_uses[0].name == "lookup_order"
    assert resp.tool_uses[0].input == {"order_id": "12345"}
    assert resp.tool_uses[0].tool_use_id == "toolu_abc"
    assert resp.stop_reason == "tool_use"


async def test_default_model_used(fake_sdk_client: MagicMock) -> None:
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("ok")],
    )

    client = AnthropicClient(client=fake_sdk_client, default_model="claude-haiku-4-5")
    await client.complete(messages=[LLMMessage(role="user", content="hi")])

    call_kwargs = fake_sdk_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-4-5"


async def test_model_override(fake_sdk_client: MagicMock) -> None:
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("ok")],
    )

    client = AnthropicClient(client=fake_sdk_client)
    await client.complete(
        messages=[LLMMessage(role="user", content="hi")],
        model="claude-opus-4-7",
    )

    call_kwargs = fake_sdk_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-7"


async def test_system_prompt_passed(fake_sdk_client: MagicMock) -> None:
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("ok")],
    )

    client = AnthropicClient(client=fake_sdk_client)
    await client.complete(
        messages=[LLMMessage(role="user", content="hi")],
        system="你是 AI 客服，回答簡短",
    )

    call_kwargs = fake_sdk_client.messages.create.call_args.kwargs
    assert call_kwargs["system"] == "你是 AI 客服，回答簡短"


async def test_no_system_when_none(fake_sdk_client: MagicMock) -> None:
    """system=None 時不傳給 SDK（Anthropic 接受沒有 system）."""
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("ok")],
    )

    client = AnthropicClient(client=fake_sdk_client)
    await client.complete(messages=[LLMMessage(role="user", content="hi")])

    call_kwargs = fake_sdk_client.messages.create.call_args.kwargs
    assert "system" not in call_kwargs


async def test_tools_formatted_for_sdk(fake_sdk_client: MagicMock) -> None:
    """tools 轉成 anthropic SDK 期望格式（name/description/input_schema dict）."""
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("ok")],
    )

    client = AnthropicClient(client=fake_sdk_client)
    tools = [
        LLMToolDefinition(
            name="search_knowledge",
            description="搜尋 KB",
            input_schema={"type": "object"},
        ),
    ]
    await client.complete(
        messages=[LLMMessage(role="user", content="hi")],
        tools=tools,
    )

    call_kwargs = fake_sdk_client.messages.create.call_args.kwargs
    assert call_kwargs["tools"] == [
        {
            "name": "search_knowledge",
            "description": "搜尋 KB",
            "input_schema": {"type": "object"},
        }
    ]


async def test_usage_with_cache(fake_sdk_client: MagicMock) -> None:
    """prompt caching 的 cache_creation / cache_read tokens 也要收進 LLMUsage."""
    fake_sdk_client.messages.create.return_value = _fake_message(
        content_blocks=[_fake_text_block("ok")],
        cache_creation=200,
        cache_read=500,
    )

    client = AnthropicClient(client=fake_sdk_client)
    resp = await client.complete(messages=[LLMMessage(role="user", content="hi")])

    assert resp.usage.cache_creation_input_tokens == 200
    assert resp.usage.cache_read_input_tokens == 500
