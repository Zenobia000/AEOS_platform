---
id: MC-009
title: "Module Contract — Employee Runtime"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 90eaacb470567a3bf631af423e5dbf1ad8053a47
sync-source: doc
source-paths:
  - src/runtime/
related: [SAD-v0.1, ADR-0001, ADR-0002, MC-001, MC-005, MC-006, MC-008, MC-010, MC-011, domain-model]
---

# Employee Runtime — One-Page Module Contract

> **Plane**: Data | **Priority**: #1 (核心執行引擎 -- AI 員工在此"工作") | **Phase 1 必做**

## Purpose

AI 員工的核心執行引擎。接收使用者訊息後，組裝 Frozen Runtime 快照（Skill + Knowledge + Tools），驅動 LLM 生成回覆，驗證輸出品質，並在必要時呼叫工具。這是 AEOS 的心臟 -- 治理、凍結、可審計的 AI 行為全在這裡實現。

## Responsibilities

| 做 | 不做 |
|---|---|
| 載入 Employee 的 Frozen Snapshot（Skill 版本 + persona + 工具清單） | 管理 Skill 版本生命週期（-> Skill Registry MC-005） |
| 組裝 LLM prompt（system prompt + skill prompt + knowledge context + conversation history） | 儲存對話歷史（-> Conversation Engine MC-010） |
| 呼叫 LLM 生成回覆（透過 LLMClient 抽象） | 處理 channel 訊息格式轉換（-> Channel Gateway MC-011） |
| 執行 output validation（格式、禁止語、PII 檢查） | 管理知識卡片 CRUD（-> Knowledge MC-008） |
| 代理 tool calls（透過 Tool Registry MC-006） | 訓練或改進 Skill（-> Training Room，Phase 2） |
| 每步驟發 audit event（message_received -> llm_called -> tool_invoked -> message_sent） | 即時監控告警（-> Evaluation Service，Phase 2） |
| Frozen Runtime 強制：prod Employee 的行為完全由 snapshot 決定 | 自我修改行為或 prompt（違反 Frozen Runtime） |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | Worker process 執行（非 API process），透過 Redis queue 接收任務 | :green_circle: | LLM call 耗時 2-15s，不能阻塞 webhook response | 併發 > 50 req/s -> :yellow_circle: 多 worker + autoscale |
| D2 | Employee config 是 snapshot（建立時複製，非 live reference） | :green_circle: | Frozen Runtime 核心：prod Employee 的行為不隨 Skill Registry 變更而變 | 需要 canary 發布時 -> :yellow_circle: 加 traffic splitting |
| D3 | 包裝 nanobot 作為內部 runtime（ADR-0002） | :green_circle: | 已驗證的 runtime，90 天可上線 | nanobot tool-calling 穩定性 < 95% -> 評估替換 |
| D4 | Output validation 在 LLM response 後、送出前執行 | :green_circle: | 治理紅線：禁止未經驗證的回覆直接發給使用者 | 需要多層 validation -> :yellow_circle: validation pipeline |
| D5 | Prompt 組裝順序：system -> persona -> skill -> knowledge -> history -> user message | :green_circle: | 優先序符合 Claude best practice；knowledge 在 history 前避免被截斷 | Token budget > 100K -> :yellow_circle: 動態截斷策略 |
| D6 | 單一 LLM call per turn（不做 multi-step reasoning chain） | :yellow_circle: | Phase 1 客服場景夠用；複雜推理交給 tool call 分步 | 需要 ReAct / multi-step -> :yellow_circle: 加 agent loop |
| D7 | Expert handoff：confidence < threshold 或 risk_tier=restricted tool -> 轉人 | :green_circle: | 安全閥；Phase 1 閾值可調（預設 0.6） | 需要更精細的 routing -> :yellow_circle: 多級 escalation |

## Data Model

```sql
-- employee 已在 db-schema.md 定義，此處補充 runtime 需要的欄位

CREATE TABLE employee (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,                         -- 'customer_service' (Phase 1)
    status          TEXT NOT NULL CHECK (status IN ('draft', 'live', 'paused', 'retired')),
    version         TEXT NOT NULL,                         -- semver snapshot
    persona_config  JSONB NOT NULL DEFAULT '{}',           -- { tone, style, language, greeting }
    runtime_snapshot JSONB NOT NULL DEFAULT '{}',          -- frozen config (see below)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- runtime_snapshot JSONB structure:
-- {
--   "skill_bindings": [
--     { "skill_id": "uuid", "skill_slug": "customer-service/faq-respond",
--       "version": "1.2.0", "prompt_template_ref": "skills/cs/faq/v1.2.0/prompt.md" }
--   ],
--   "tool_bindings": [
--     { "tool_id": "uuid", "tool_name": "search_knowledge", "risk_tier": "safe" }
--   ],
--   "knowledge_config": {
--     "retrieval_top_k": 5,
--     "score_threshold": 0.7,
--     "card_types": ["faq", "policy", "product", "procedure", "risk"]
--   },
--   "llm_config": {
--     "primary_model": "claude-sonnet-4-6-20250514",
--     "temperature": 0.3,
--     "max_output_tokens": 2048
--   },
--   "validation_rules": {
--     "max_response_length": 2000,
--     "forbidden_patterns": ["competitor_name", ...],
--     "require_citation": true
--   },
--   "handoff_config": {
--     "confidence_threshold": 0.6,
--     "max_consecutive_uncertain": 3
--   },
--   "frozen_at": "2026-05-15T10:00:00Z"
-- }

-- Employee status transition tracking (for audit)
-- draft -> live: requires all skill_bindings status=production
-- live -> paused: admin action (kill switch)
-- paused -> live: admin action (resume)
-- live -> retired: permanent decommission

CREATE INDEX idx_employee_tenant ON employee(tenant_id);
CREATE INDEX idx_employee_status ON employee(tenant_id, status);
```

## Interface

### Internal Python API — EmployeeRuntime

```python
from dataclasses import dataclass
from enum import Enum

class ProcessingOutcome(Enum):
    REPLIED = "replied"              # Normal AI response sent
    HANDOFF_HUMAN = "handoff_human"  # Escalated to Expert
    TOOL_ERROR = "tool_error"        # Tool call failed, fallback sent
    VALIDATION_FAILED = "validation_failed"  # Output validation blocked response
    LLM_ERROR = "llm_error"          # LLM call failed

@dataclass(frozen=True)
class ProcessedMessage:
    conversation_id: str
    response_text: str
    outcome: ProcessingOutcome
    tool_invocations: list[dict]     # tool calls made during this turn
    knowledge_cards_used: list[str]  # card IDs retrieved
    token_usage: dict                # { prompt_tokens, completion_tokens, total_cost }
    latency_ms: int

class EmployeeRuntime:
    """Core execution engine for AI Employees."""

    async def process_message(
        self,
        tenant_id: str,
        employee_id: str,
        conversation_id: str,
        user_message: str,
    ) -> ProcessedMessage:
        """
        Main entry point. Called by Worker when dequeuing a message job.

        Pipeline:
        1. Load Employee frozen snapshot
        2. Load conversation history (from Conversation Engine)
        3. Retrieve relevant knowledge (from Knowledge Service)
        4. Assemble LLM prompt
        5. Call LLM (via LLMClient)
        6. Parse LLM response (text + tool_calls)
        7. If tool_calls: execute via Tool Registry, append results, re-call LLM
        8. Validate output (forbidden patterns, length, PII check)
        9. If validation fails: return fallback message
        10. If confidence < threshold: trigger Expert handoff
        11. Save assistant message (via Conversation Engine)
        12. Audit all steps
        13. Return ProcessedMessage
        """
        ...

    async def load_snapshot(self, employee_id: str) -> dict:
        """Load the frozen runtime_snapshot. Cached in Redis for hot employees."""
        ...

    async def assemble_prompt(
        self,
        snapshot: dict,
        conversation_history: list[dict],
        knowledge_results: list[dict],
        user_message: str,
    ) -> list[dict]:
        """
        Build LLM messages array:

        [
          { role: "system", content: <system_prompt + persona + skill_prompt> },
          { role: "system", content: <knowledge_context> },   # retrieved cards
          ...conversation_history[-N:],                        # recent messages
          { role: "user", content: <user_message> }
        ]

        Token budget management:
        - System prompt + persona + skill: ~2000 tokens (fixed)
        - Knowledge context: ~3000 tokens (top-K cards, truncated)
        - Conversation history: ~3000 tokens (most recent first, trim oldest)
        - User message: ~500 tokens
        - Reserved for output: ~2000 tokens
        - Total budget: ~10000-12000 tokens (Sonnet 4.6 context)
        """
        ...

    async def validate_output(self, response: str, snapshot: dict) -> tuple[bool, str | None]:
        """
        Check response against validation_rules in snapshot:
        - Length within max_response_length
        - No forbidden_patterns matched
        - No raw PII leaked (regex check)
        - If require_citation: verify knowledge source reference

        Returns (is_valid, rejection_reason).
        """
        ...
```

### Worker Job — ProcessMessage

```
Redis queue: conversation:process
Payload: { tenant_id, employee_id, conversation_id, message_id }

Pipeline:
  1. Dequeue job
  2. Load Employee snapshot (Redis cache -> DB fallback)
  3. Verify Employee status == 'live' (if not -> audit + skip)
  4. Call EmployeeRuntime.process_message()
  5. Enqueue outbound reply to channel (-> Channel Gateway)
  6. Audit: conversation.message_sent { outcome, latency, tokens }
  7. If handoff: create Expert notification (Phase 1: email/LINE Notify)
  8. ACK job
```

### REST API (Admin Console)

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/employees` | GET | 列出所有 AI 員工（filter: tenant_id, status） |
| `/api/v1/employees` | POST | 建立 AI 員工（body: name, role, persona_config, skill_bindings, tool_bindings） |
| `/api/v1/employees/{id}` | GET | 員工詳情 + runtime_snapshot |
| `/api/v1/employees/{id}` | PATCH | 更新 draft 員工設定（live 員工不可改） |
| `/api/v1/employees/{id}/deploy` | POST | draft -> live（快照凍結，驗證所有 skill=production） |
| `/api/v1/employees/{id}/pause` | POST | live -> paused（kill switch） |
| `/api/v1/employees/{id}/resume` | POST | paused -> live |
| `/api/v1/employees/{id}/retire` | POST | -> retired（永久停用） |
| `/api/v1/employees/{id}/snapshot` | GET | 查看當前 frozen snapshot 詳情 |

### Frozen Runtime 機制

```
Deploy 流程（draft -> live）:

1. 驗證前置條件：
   - 所有 skill_bindings 指向 status='production' 的 SkillVersion
   - 所有 tool_bindings 指向 enabled=true 的 Tool
   - persona_config 已填寫

2. 建立 Snapshot：
   - 複製當前 skill prompt_template_ref 的內容（非 reference）
   - 複製 tool 清單 + risk_tier
   - 複製 knowledge retrieval config
   - 複製 LLM model config
   - 記錄 frozen_at timestamp

3. 寫入 runtime_snapshot JSONB

4. 設定 status = 'live'

5. Audit: employee.deployed { version, snapshot_hash }

結果：即使之後 Skill Registry 的 prompt 被修改，
      live Employee 的行為不會改變 -- 它讀的是 snapshot。
      要更新行為 = 建立新版本 Employee + 重新 deploy。
```

## Event Types

| Event | Trigger | Payload (key fields) |
|---|---|---|
| `employee.created` | New Employee record inserted | `{ employee_id, tenant_id, role }` |
| `employee.deployed` | Employee status draft -> live (snapshot frozen) | `{ employee_id, tenant_id, version, snapshot_hash }` |
| `employee.paused` | Employee status live -> paused (kill switch) | `{ employee_id, tenant_id }` |
| `employee.resumed` | Employee status paused -> live | `{ employee_id, tenant_id }` |
| `employee.retired` | Employee permanently decommissioned | `{ employee_id, tenant_id }` |
| `employee.snapshot_loaded` | Frozen snapshot loaded for processing | `{ employee_id, tenant_id, cache_hit }` |
| `employee.message_processed` | Message processing pipeline completed | `{ employee_id, conversation_id, outcome, latency_ms, token_usage }` |
| `employee.message_failed` | Message processing pipeline failed | `{ employee_id, conversation_id, error_type, error_message }` |
| `employee.handoff_requested` | Confidence below threshold, escalating to Expert | `{ employee_id, conversation_id, reason }` |

## Cross-Module Interface Notes

- **Knowledge Service (MC-008)** is called during `process_message` pipeline step 3:
  ```python
  # In process_message pipeline, step 3:
  knowledge_results = await knowledge_service.retrieve(
      tenant_id=tenant_id,
      query=message_text,
      top_k=5
  )
  ```

## Dependencies

```
                    ┌──────────────────┐
                    │  Channel Gateway │
                    │  (MC-011)        │
                    └────────┬─────────┘
                             │ normalized message
                             ▼
 ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
 │ Conversation │◄──│ Employee Runtime │──►│ Knowledge    │
 │ Engine       │   │ (MC-009)         │   │ (RAG)        │
 │ (MC-010)     │   │                  │   │ (MC-008)     │
 └──────────────┘   └────────┬─────────┘   └──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────┐ ┌──────────────┐
     │ LLM Client   │ │ Tool     │ │ Audit Service│
     │ (Anthropic)  │ │ Registry │ │ (MC-001)     │
     │ ADR-0001     │ │ (MC-006) │ └──────────────┘
     └──────────────┘ └──────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| 單一 LLM call per turn（text in -> text out） | Multi-step reasoning chain / ReAct loop |
| Frozen snapshot deploy 機制 | Canary 發布 / A-B test |
| Output validation（length, forbidden patterns, PII） | ML-based hallucination detection |
| Expert handoff（confidence threshold） | Multi-tier escalation routing |
| 1 Employee per tenant（Phase 1 pilot） | 多 Employee 併行 + routing |
| Prompt assembly with token budget | Dynamic context window optimization |
| Tool calling（single round） | Multi-round tool orchestration |
| Redis cache for hot snapshot | Distributed cache / edge cache |
| Kill switch（pause/resume） | Graceful drain + connection handoff |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
1 employee/tenant        multi-employee + routing     100+ employees
──────────────────────────────────────────────────────────────────
single LLM call         -> ReAct loop (max 5 steps) -> autonomous agent chains
manual deploy           -> canary (10/50/100%)       -> blue-green + rollback
regex validation        -> LLM-as-judge              -> fine-tuned safety model
single Worker           -> Worker pool + autoscale   -> K8s job scheduler
snapshot in JSONB       -> versioned config store    -> GitOps + config server
hardcoded token budget  -> dynamic by model          -> adaptive context window
email handoff           -> in-app queue + SLA        -> multi-channel escalation
```
