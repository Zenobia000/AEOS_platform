"""QuotaHook — token-based 簡易 quota enforcement.

依 QUOTA-001 §6 降級三級：soft / hard / emergency。Phase 1 簡化版只
做「累加」：超過 tenant 的 monthly_token_cap 直接 raise QuotaError；
完整 5 層 rate limit + 3 級降級留 Phase 2 接 Redis token bucket。

設計：QuotaHook 在 after_llm_call 累加 tenant 該月 token 使用量；
before_llm_call 檢查是否已超 cap。

Phase 1 token cap 配置：在 ctx.runtime_snapshot["quota"] 或 default 寫死。
"""

from __future__ import annotations

import uuid

from app.agent.context import AgentContext
from app.agent.hook import AgentHook
from app.llm.client import LLMResponse


class QuotaError(Exception):
    """超出該 tenant token quota."""

    def __init__(self, tenant_id: uuid.UUID, used: int, cap: int) -> None:
        super().__init__(f"tenant {tenant_id} exceeded monthly token quota: {used}/{cap}")
        self.tenant_id = tenant_id
        self.used = used
        self.cap = cap


# Phase 1 預設 cap（QUOTA-001 §1 例：月費 US$500 = US$150 LLM = ~312,500 對話）
# 以 token 為計，simplified to ~5M tokens/month
_DEFAULT_MONTHLY_TOKEN_CAP = 5_000_000


class QuotaHook(AgentHook):
    """In-memory token counter per tenant.

    Note: Phase 1 simplification — 進程內計數，重啟歸零；Phase 2 改 Redis。
    """

    def __init__(self, monthly_cap: int = _DEFAULT_MONTHLY_TOKEN_CAP) -> None:
        self._monthly_cap = monthly_cap
        self._used: dict[uuid.UUID, int] = {}

    def usage(self, tenant_id: uuid.UUID) -> int:
        return self._used.get(tenant_id, 0)

    def reset(self, tenant_id: uuid.UUID | None = None) -> None:
        if tenant_id is None:
            self._used.clear()
        else:
            self._used.pop(tenant_id, None)

    async def before_llm_call(self, ctx: AgentContext) -> None:
        used = self._used.get(ctx.tenant_id, 0)
        if used >= self._monthly_cap:
            raise QuotaError(ctx.tenant_id, used, self._monthly_cap)

    async def after_llm_call(
        self,
        ctx: AgentContext,
        response: LLMResponse,
    ) -> None:
        prev = self._used.get(ctx.tenant_id, 0)
        self._used[ctx.tenant_id] = prev + response.usage.total_tokens
