"""LLM client interface (ADR-0001).

設計原則（ADR-0012 借鑑 nanobot/providers/base.py）：
- 統一 DTO（LLMMessage / LLMToolDefinition / LLMResponse / LLMUsage），
  讓 application 層不直接依賴 provider SDK 型別
- 抽象介面只有 `complete()` 一個方法；streaming 等 S4 開工再擴
- usage / cost tracking 直接放進 LLMResponse，供 QuotaHook 消費
- 結構化錯誤分類（transient vs permanent）— Phase 1 簡化為 retry-friendly
  vs not，AnthropicClient 在內部處理 retry

非目標（Phase 1）：
- 多 provider routing — 唯一實作 Anthropic（ADR-0001）
- prompt caching SDK 細節 — 由 AnthropicClient 內部處理
- streaming — S4 LINE Draft Mode 時擴接口
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

LLMRole = Literal["user", "assistant", "system"]


@dataclass(frozen=True)
class LLMMessage:
    """單則 chat message。"""

    role: LLMRole
    content: str


@dataclass(frozen=True)
class LLMToolDefinition:
    """提供給 LLM 的 tool schema（function calling）。"""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class LLMToolUse:
    """LLM 決定呼叫的 tool（從 response 解析出來）。"""

    tool_use_id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True)
class LLMUsage:
    """單次呼叫的 token usage（供 QuotaHook / cost tracking）。"""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class LLMResponse:
    """`complete()` 回傳值。"""

    text: str
    tool_uses: Sequence[LLMToolUse] = field(default_factory=list)
    stop_reason: str = "end_turn"
    model: str = ""
    usage: LLMUsage = field(default_factory=lambda: LLMUsage(0, 0))


class LLMClient(ABC):
    """Abstract LLM client. Phase 1 唯一實作為 AnthropicClient。"""

    @abstractmethod
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
        """一次性 completion（含可選 tool use）.

        Args:
            messages: 對話歷史
            system: 系統 prompt
            tools: 給 LLM 的工具 schemas（function calling）
            max_tokens: 輸出上限
            temperature: 採樣溫度
            model: 模型名稱（None = 用 client 預設）

        Returns:
            LLMResponse — 含 text、tool_uses、usage
        """
        raise NotImplementedError
