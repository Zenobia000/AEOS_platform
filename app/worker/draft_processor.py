"""DraftProcessor — 對話一回合的 LLM draft 生成 (Tier 4 整合層).

整合 Tier 0~3 全部元件 + Tier 4 channel：
- 載入 conversation 歷史 (MC-010)
- 載入 skill_version → LoadedSkill (MC-005 + skills/ git tree via SkillLoader)
- 構造 AgentContext (MC-009 Frozen Runtime snapshot)
- 構造 EmployeeRuntime + LLMClient + CompositeHook(Audit/Policy/Quota) + ToolExecutor
- run_turn() → 寫 assistant message + outbound_message (status=pending)
- 返回 DraftResult 給呼叫端（worker 主迴圈或 webhook 同步路徑）

設計選擇（Phase 1）：
- 不負責出站 LINE Push API call（由 LINE Push worker 撿 pending outbound_message 跑）
- 不負責 LLM message 形態的 PII pseudonymize — caller 已在 webhook 階段處理
- skill_version_id 透過 conversation.employee.runtime_snapshot 解析（無 binding lookup
  的話 fallback Phase 1 預設）

對應 PRD-001 §5.4 Draft Mode：F-DFT-01 LINE 收訊 → AI draft 不直發 → expert 通知 →
F-DFT-02 1-click approve/edit/reject → F-DFT-03 全進 audit。本 commit 落地 F-DFT-01
的「AI 產出 draft 進 DB」這一段。
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import (
    AgentContext,
    AgentHook,
    EmployeeRuntime,
    InternalToolRegistry,
    ToolExecutionContext,
    ToolExecutor,
)
from app.agent.runtime import TurnResult
from app.db.models.conversation import Conversation
from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.llm.client import LLMClient, LLMMessage, LLMToolDefinition
from app.observability import e2e_latency_seconds, llm_tokens_total
from app.services import audit as audit_service
from app.services import kill_switch
from app.skill import LoadedSkill, SkillLoader


@dataclass(frozen=True)
class DraftResult:
    """`process_message()` 回傳值."""

    conversation_id: uuid.UUID
    assistant_text: str
    outbound_message_id: uuid.UUID | None  # None 若沒產 outbound（e.g. handoff-only turn）
    turn_result: TurnResult


class DraftProcessor:
    """跑單一 turn 的 draft 生成。

    Args:
        llm: 已建好的 LLMClient（AnthropicClient or fake）
        skill_loader: 讀 skills/ git tree
        registry: tool 註冊表（Phase 1 預設 register_builtins 後傳入）
        hook: 可選 CompositeHook（governance）；None 用 no-op
        max_history: 取最近 N 則 message 進 LLM context（避免 token 爆）
    """

    def __init__(
        self,
        *,
        llm: LLMClient,
        skill_loader: SkillLoader,
        registry: InternalToolRegistry,
        hook: AgentHook | None = None,
        max_history: int = 20,
        outbound_initial_status: str = "pending",
    ) -> None:
        """outbound_initial_status:
        - 'pending' (預設 / Canary mode): OutboundProcessor 立即撿並 Push
        - 'awaiting_review' (Draft Mode, PRD §5.4): 等 expert 審後才轉 pending
        """
        self._llm = llm
        self._skill_loader = skill_loader
        self._registry = registry
        self._hook = hook or AgentHook()
        self._max_history = max_history
        self._outbound_initial_status = outbound_initial_status

    async def process_message(
        self,
        *,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        skill_slug: str,
        skill_version: str,
    ) -> DraftResult:
        """對指定 conversation 的最新 user message 跑一次 LLM turn.

        Args:
            session: async DB session
            conversation_id: 對話 UUID
            skill_slug: 'customer-service/faq-respond'
            skill_version: 'v1.0.0'

        Returns:
            DraftResult — 含 assistant_text + outbound_message_id + turn detail
        """
        conv = (
            await session.execute(select(Conversation).where(Conversation.id == conversation_id))
        ).scalar_one()
        employee = (
            await session.execute(select(Employee).where(Employee.id == conv.employee_id))
        ).scalar_one()

        # Kill switch — 每 turn 查 DB（< 1ms），30 秒內生效（UF-004）
        if not await kill_switch.is_ai_enabled(session, conv.tenant_id):
            return await self._handle_kill_switch(session, conv)

        skill = self._skill_loader.load(skill_slug, skill_version)

        ctx = AgentContext(
            tenant_id=conv.tenant_id,
            conversation_id=conv.id,
            employee_id=conv.employee_id,
            employee_version=conv.employee_version,
            skill_version_id=None,  # Phase 1：DB skill_version_id 之後接 skill_binding lookup
            runtime_snapshot=employee.runtime_snapshot or {},
            session=session,
            metadata={"channel": conv.channel},
        )

        messages = await self._load_history(session, conv.id)
        tools = _build_tool_definitions(skill)
        _llm_start = time.perf_counter()

        # ToolExecutor 用同一個 session 跑（共享 transaction → audit/policy hook 看得到 seed）
        tool_exec = ToolExecutor(
            registry=self._registry,
            record_invocations=True,
        )

        async def _dispatch(name: str, args: dict[str, object]) -> object:
            tool_ctx = ToolExecutionContext(
                tenant_id=ctx.tenant_id,
                conversation_id=ctx.conversation_id,
                employee_id=ctx.employee_id,
                skill_version_id=ctx.skill_version_id,
                session=session,
            )
            result = await tool_exec.dispatch(name, args, ctx=tool_ctx)
            return result.output

        runtime = EmployeeRuntime(
            llm=self._llm,
            hook=self._hook,
            tool_executor=_dispatch,
        )

        turn = await runtime.run_turn(
            ctx=ctx,
            messages=messages,
            system=skill.system_prompt,
            tools=tools,
            max_tokens=1024,
            temperature=0.3,
        )

        # Prometheus：LLM 延遲 + token usage
        e2e_latency_seconds.labels(step="llm").observe(time.perf_counter() - _llm_start)
        _model = turn.response.model or "unknown"
        _tenant = str(ctx.tenant_id)
        llm_tokens_total.labels(tenant_id=_tenant, model=_model, type="prompt").inc(
            turn.response.usage.input_tokens
        )
        llm_tokens_total.labels(tenant_id=_tenant, model=_model, type="completion").inc(
            turn.response.usage.output_tokens
        )

        assistant_text = turn.response.text

        # 寫 assistant message 進 message 表
        # 用 MAX(seq) 而非 denormalized counter，避免 race + stale 問題
        max_seq_row = (
            await session.execute(
                text("SELECT COALESCE(MAX(seq), 0) FROM message WHERE conversation_id = :cid"),
                {"cid": str(conv.id)},
            )
        ).scalar()
        next_seq = int(max_seq_row or 0) + 1
        # RETURNING id 拿回剛寫進去的 message UUID，給 outbound_message.message_id 用
        new_message_row = (
            await session.execute(
                text(
                    "INSERT INTO message "
                    "(id, conversation_id, seq, role, content, token_count, created_at) "
                    "VALUES (gen_random_uuid(), :cid, :seq, 'assistant', :c, :tk, NOW()) "
                    "RETURNING id"
                ),
                {
                    "cid": str(conv.id),
                    "seq": next_seq,
                    "c": assistant_text,
                    "tk": turn.response.usage.output_tokens,
                },
            )
        ).first()
        new_message_id: uuid.UUID = uuid.UUID(str(new_message_row[0]))  # type: ignore[index]
        await session.execute(
            text(
                "UPDATE conversation "
                "SET message_count = message_count + 1, last_message_at = NOW() "
                "WHERE id = :cid"
            ),
            {"cid": str(conv.id)},
        )

        # 寫 outbound_message (status=pending) — LINE Push worker 撿
        outbound_id: uuid.UUID | None = None
        if assistant_text:
            outbound = OutboundMessage(
                tenant_id=ctx.tenant_id,
                conversation_id=conv.id,
                message_id=new_message_id,
                channel=conv.channel,
                channel_user_id=conv.channel_user_id,
                status=self._outbound_initial_status,
            )
            session.add(outbound)
            await session.flush()
            outbound_id = outbound.id

        return DraftResult(
            conversation_id=conv.id,
            assistant_text=assistant_text,
            outbound_message_id=outbound_id,
            turn_result=turn,
        )

    async def _handle_kill_switch(
        self,
        session: AsyncSession,
        conv: Conversation,
    ) -> DraftResult:
        """Kill switch active：跳過 LLM，建 handoff + audit。不寫 outbound。"""
        handoff = ConversationHandoff(
            from_conversation_id=conv.id,
            reason="policy_deny",
            handoff_message="AI disabled by kill switch — escalate to human",
            expert_id=None,
        )
        session.add(handoff)
        await session.flush()

        await audit_service.emit(
            session,
            event_type="kill_switch.intercepted",
            tenant_id=conv.tenant_id,
            actor_id="draft_processor",
            resource_type="conversation",
            resource_id=str(conv.id),
            payload={"handoff_id": str(handoff.id)},
        )
        # 回傳空 turn 給 caller；外層 worker loop 看 outbound_message_id None
        # 知道不要再嘗試 push
        from app.agent.runtime import TurnResult
        from app.llm.client import LLMResponse, LLMUsage

        empty_response = LLMResponse(
            text="",
            tool_uses=[],
            stop_reason="kill_switch",
            usage=LLMUsage(input_tokens=0, output_tokens=0),
        )
        return DraftResult(
            conversation_id=conv.id,
            assistant_text="",
            outbound_message_id=None,
            turn_result=TurnResult(response=empty_response, tool_calls=[]),
        )

    async def _load_history(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> Sequence[LLMMessage]:
        """從 message 表撈最近 N 則訊息（依 seq asc）."""
        rows = (
            await session.execute(
                text(
                    "SELECT role, content FROM message "
                    "WHERE conversation_id = :cid "
                    "ORDER BY seq DESC "
                    "LIMIT :lim"
                ),
                {"cid": str(conversation_id), "lim": self._max_history},
            )
        ).all()
        # rows 是 desc 排，reverse 回 chronological 順序給 LLM
        items: list[LLMMessage] = []
        for role, content in reversed(rows):
            if role in ("user", "assistant"):
                items.append(LLMMessage(role=role, content=content))
        return items


def _build_tool_definitions(skill: LoadedSkill) -> list[LLMToolDefinition]:
    """從 LoadedSkill.tool_bindings 構造給 LLM 的 tool schemas.

    Phase 1 簡化：用 hardcoded schema for builtin tools（search_knowledge /
    request_human_handoff）。完整 schema 應從 skills/<v>/tools.yaml 讀，
    S3 Skill loader 強化時補。
    """
    schemas: dict[str, LLMToolDefinition] = {
        "search_knowledge": LLMToolDefinition(
            name="search_knowledge",
            description="在 KB 中搜尋與 query 最相關的 top-K 張 KnowledgeCard",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "min_score": {"type": "number", "default": 0.7},
                },
                "required": ["query"],
            },
        ),
        "request_human_handoff": LLMToolDefinition(
            name="request_human_handoff",
            description="將對話轉給 expert（人工客服）",
            input_schema={
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "enum": [
                            "low_confidence",
                            "restricted_tool",
                            "user_request",
                            "policy_deny",
                        ],
                    },
                    "handoff_message": {"type": "string"},
                },
                "required": ["reason"],
            },
        ),
    }
    return [schemas[s] for s in skill.tool_bindings if s in schemas]
