---
id: MC-010
title: "Module Contract — Conversation Engine"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
sync-source: doc
source-paths:
  - src/conversation/
related: [SAD-v0.1, ADR-0005, ADR-0010, MC-001, MC-009, MC-011, domain-model]
---

# Conversation Engine — One-Page Module Contract

> **Plane**: Data | **Priority**: #1 (Employee Runtime + Channel Gateway 雙向依賴) | **Phase 1 必做**

## Purpose

管理 AI 員工與終端使用者之間的對話狀態、訊息歷史、和 context window 組裝。Conversation Engine 是 AEOS 的記憶體 -- 它決定 AI 員工「記得什麼」和「忘記什麼」，同時確保所有對話記錄可追溯、90 天後 PII 脫敏。

## Responsibilities

| 做 | 不做 |
|---|---|
| 管理 Conversation 生命週期（open -> active -> resolved -> closed -> archived） | 生成 AI 回覆（-> Employee Runtime MC-009） |
| 儲存所有 Message（user + assistant + tool + system），append-only | 決定使用哪些 Knowledge Cards（-> Knowledge MC-008） |
| 維護 Redis session cache（hot conversation 的最近 N 條訊息） | Channel 訊息格式轉換（-> Channel Gateway MC-011） |
| 組裝 context window（recent messages within token budget） | Tool 執行（-> Tool Registry MC-006） |
| Conversation 結束時觸發 summary 生成（L2.5 Session Summary，ADR-0010） | 評估對話品質（-> Evaluation Service，Phase 2） |
| 90 天後執行 PII 脫敏（cron job，ADR-0005） | 全文搜尋對話內容（Phase 2） |
| Expert handoff 狀態管理（AI -> human -> AI transfer） | Expert 排程或 routing（Phase 2） |
| 每個 state transition 發 audit event | 跨租戶對話聚合 |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | Conversation + Message 存 PostgreSQL；hot session cache 在 Redis | :green_circle: | PG 是持久化 source of truth；Redis 加速 active conversation 讀取 | 併發 active conversations > 1000 -> :yellow_circle: Redis Cluster |
| D2 | Message table partition by month（append-only） | :green_circle: | 對話量大但查詢通常在時間範圍內；partition 便於 retention purge | 月對話 > 100 萬筆 -> :yellow_circle: 更細粒度 partition |
| D3 | Context window 固定 token budget：~8000 tokens for history | :yellow_circle: | Phase 1 簡單預設；pilot 期間調參 | 需要動態 budget -> :yellow_circle: 根據 knowledge + skill 消耗動態分配 |
| D4 | 對話 idle > 30 分鐘自動 resolve | :green_circle: | 防止 zombie conversations；30 分鐘符合客服場景 | 不同場景需要不同 timeout -> 加 per-employee config |
| D5 | Expert handoff 實作為 conversation status 切換 + notification | :green_circle: | Phase 1 最小實現；Expert 透過 Web UI 接管 | 需要即時 handoff -> :yellow_circle: WebSocket + queue |
| D6 | L2.5 Summary 在 conversation 結束時由 Haiku 4.5 生成 | :green_circle: | 低成本摘要；用於跨 session 記憶（ADR-0010） | 摘要品質不足 -> 升級為 Sonnet |
| D7 | PII 脫敏 cron 每日執行，處理 > 90 天的 message.content | :green_circle: | ADR-0005 要求；cron 簡單可靠 | 需要即時脫敏 -> :red_circle: stream processing |

## Data Model

```sql
-- conversation 和 message 已在 db-schema.md 定義，此處補充 conversation engine 需要的欄位

CREATE TABLE conversation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenant(id),
    employee_id         UUID NOT NULL REFERENCES employee(id),
    employee_version    TEXT NOT NULL,                     -- snapshot version at start
    end_user_pseudo_id  TEXT NOT NULL,                     -- pseudonymized (ADR-0005)
    channel             TEXT NOT NULL,                     -- 'line' | 'web_chat' | 'whatsapp'
    channel_user_id     TEXT NOT NULL,                     -- channel-specific user ID (hashed)
    status              TEXT NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'active', 'waiting_human', 'resolved', 'closed', 'archived')),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at     TIMESTAMPTZ,                      -- for idle timeout detection
    ended_at            TIMESTAMPTZ,
    outcome             TEXT CHECK (outcome IN ('resolved', 'handoff_human', 'abandoned', 'error')),
    summary             TEXT,                              -- L2.5 session summary (generated on close)
    message_count       INT NOT NULL DEFAULT 0,           -- denormalized counter
    metadata            JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_conv_tenant_started ON conversation(tenant_id, started_at DESC);
CREATE INDEX idx_conv_employee ON conversation(employee_id);
CREATE INDEX idx_conv_status ON conversation(tenant_id, status);
CREATE INDEX idx_conv_end_user ON conversation(tenant_id, end_user_pseudo_id);
CREATE INDEX idx_conv_idle ON conversation(status, last_message_at)
    WHERE status IN ('open', 'active', 'waiting_human');

-- message (partitioned by month, defined in db-schema.md)
CREATE TABLE message (
    id                  UUID NOT NULL DEFAULT gen_random_uuid(),
    conversation_id     UUID NOT NULL,
    seq                 INT NOT NULL,
    role                TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    status              TEXT NOT NULL DEFAULT 'sent'
                        CHECK (status IN ('sent', 'draft_pending', 'approved', 'rejected')),
    content             TEXT NOT NULL,                     -- pseudonymized
    content_raw_ref     UUID,                              -- FK encrypted_pii.id
    skill_invocation_id UUID,
    tool_invocations    JSONB NOT NULL DEFAULT '[]',
    token_count         INT,                               -- for context window budget tracking
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at),
    UNIQUE (conversation_id, seq, created_at)
) PARTITION BY RANGE (created_at);

-- Conversation-to-conversation linking (for handoff tracking)
CREATE TABLE conversation_handoff (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_conversation_id UUID NOT NULL,
    to_conversation_id  UUID,                              -- NULL until Expert picks up
    reason              TEXT NOT NULL,                      -- 'low_confidence' | 'restricted_tool' | 'user_request' | 'policy_deny'
    handoff_message     TEXT,                               -- context for Expert
    expert_id           TEXT,                               -- who picked up
    picked_up_at        TIMESTAMPTZ,
    resolved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_handoff_pending ON conversation_handoff(created_at)
    WHERE to_conversation_id IS NULL;
```

## Interface

### Internal Python API — ConversationService

```python
from dataclasses import dataclass
from enum import Enum

class ConversationStatus(Enum):
    OPEN = "open"                  # Just created, first message pending
    ACTIVE = "active"              # At least one exchange completed
    WAITING_HUMAN = "waiting_human" # Expert handoff in progress
    RESOLVED = "resolved"          # Issue resolved (by AI or human)
    CLOSED = "closed"              # Finalized, summary generated
    ARCHIVED = "archived"          # PII redacted (post-90-day)

@dataclass(frozen=True)
class ConversationContext:
    conversation_id: str
    employee_id: str
    messages: list[dict]           # recent messages within token budget
    total_messages: int
    status: ConversationStatus
    summary_of_prior_sessions: str | None  # L2.5 from previous conversations

class ConversationService:
    """Conversation lifecycle + message storage + context assembly."""

    # -- Conversation lifecycle --
    async def get_or_create_conversation(
        self,
        tenant_id: str,
        employee_id: str,
        channel: str,
        channel_user_id: str,
        end_user_pseudo_id: str,
    ) -> str:
        """
        Find active conversation for this end_user + employee pair.
        If none exists (or last one is resolved/closed), create new.
        Returns conversation_id.
        """
        ...

    async def get_conversation(self, conversation_id: str) -> dict:
        """Get conversation metadata."""
        ...

    # -- Message operations --
    async def append_message(
        self,
        conversation_id: str,
        role: str,                  # 'user' | 'assistant' | 'tool' | 'system'
        content: str,               # already pseudonymized
        content_raw_ref: str | None = None,
        tool_invocations: list[dict] | None = None,
    ) -> str:
        """
        Append message with auto-incremented seq.
        Also updates Redis session cache + conversation.last_message_at.
        Returns message_id.
        """
        ...

    # -- Context window assembly (for Employee Runtime) --
    async def get_context(
        self,
        conversation_id: str,
        token_budget: int = 8000,
    ) -> ConversationContext:
        """
        Build context window for LLM prompt:
        1. Read from Redis cache (hot path) or DB (cold path)
        2. Include most recent messages that fit within token_budget
        3. Oldest messages trimmed first
        4. Always include first message (user's initial question)
        5. If prior sessions exist for same end_user, include L2.5 summary
        Returns ConversationContext.
        """
        ...

    # -- Status transitions --
    async def mark_active(self, conversation_id: str) -> None:
        """open -> active (after first AI response)."""
        ...

    async def request_handoff(
        self,
        conversation_id: str,
        reason: str,
        handoff_message: str,
    ) -> str:
        """
        active -> waiting_human.
        Creates conversation_handoff record.
        Returns handoff_id.
        """
        ...

    async def resolve(self, conversation_id: str, outcome: str) -> None:
        """
        -> resolved. Triggers summary generation job.
        outcome: 'resolved' | 'handoff_human' | 'abandoned' | 'error'
        """
        ...

    async def close(self, conversation_id: str) -> None:
        """
        resolved -> closed.
        Summary must exist. Clears Redis session cache.
        """
        ...

    # -- Summary (L2.5) --
    async def generate_summary(self, conversation_id: str) -> str:
        """
        Use Haiku 4.5 to generate structured summary:
        - Customer intent
        - Key facts discussed
        - Resolution status
        - Any commitments made
        Stores in conversation.summary. <= 200 tokens, PII-free.
        """
        ...

    # -- Retention --
    async def run_retention_purge(self, tenant_id: str) -> int:
        """
        Cron job: find messages older than tenant.data_retention_days.
        Replace message.content with '<<REDACTED>>' where PII was present.
        Delete corresponding encrypted_pii records.
        Returns count of redacted messages.
        """
        ...

    # -- Cross-session memory --
    async def get_prior_summaries(
        self,
        tenant_id: str,
        end_user_pseudo_id: str,
        limit: int = 3,
    ) -> list[dict]:
        """
        Retrieve L2.5 summaries from previous closed conversations
        for the same end_user. Used in context assembly.
        Returns [{conversation_id, summary, ended_at}].
        """
        ...
```

### Redis Session Cache Schema

```
Key:    conv:{conversation_id}:messages
Type:   LIST (append-only, trim to last 50)
TTL:    30 minutes after last write (auto-expire idle conversations)
Value:  JSON-encoded message objects

Key:    conv:{conversation_id}:meta
Type:   HASH { status, employee_id, last_message_at, message_count }
TTL:    same as messages

Operations:
  - RPUSH on new message
  - LTRIM to keep last 50
  - LRANGE for context window assembly
  - EXPIRE reset on every write
```

### REST API (Admin Console / Expert UI)

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/conversations` | GET | 分頁查詢（filter: tenant_id, status, employee_id, date range） |
| `/api/v1/conversations/{id}` | GET | 對話詳情 + 訊息列表 |
| `/api/v1/conversations/{id}/messages` | GET | 訊息分頁（支援 before/after cursor） |
| `/api/v1/conversations/{id}/resolve` | POST | Expert 手動 resolve |
| `/api/v1/conversations/{id}/handoff` | GET | 查看 handoff 詳情 |
| `/api/v1/conversations/handoffs/pending` | GET | Expert 待處理的 handoff queue |
| `/api/v1/conversations/handoffs/{id}/pickup` | POST | Expert 接單 |
| `/api/v1/conversations/messages?status=draft_pending` | GET | Draft Inbox: 列出待審核的 draft 訊息 |
| `/api/v1/conversations/messages/{id}/approve` | POST | Draft Inbox: 核准 draft 訊息（送出給使用者） |
| `/api/v1/conversations/messages/{id}/reject` | POST | Draft Inbox: 駁回 draft 訊息 |
| `/api/v1/conversations/stats` | GET | 統計（active count, avg duration, handoff rate） |

> **Draft Inbox**: 用於高風險回覆場景 -- 當 AI 員工信心度低於門檻時，Employee Runtime 將訊息 `status` 設為 `draft_pending`，由 Expert 人工審核後 approve（送出）或 reject（丟棄）。

### Worker Jobs

```
Job 1: conversation:idle-timeout (cron, every 5 min)
  - Find conversations WHERE status IN ('open','active') AND last_message_at < NOW() - 30min
  - For each: mark resolved(outcome='abandoned'), generate summary
  - Audit: conversation.timeout { conversation_id }

Job 2: conversation:retention-purge (cron, daily 03:00)
  - For each tenant: run_retention_purge()
  - Audit: system.retention_purge { tenant_id, redacted_count }

Job 3: conversation:generate-summary (on-demand, triggered by resolve)
  - Call generate_summary()
  - Update conversation.summary
  - Audit: conversation.summary_generated { conversation_id }
```

### Conversation State Machine

```
                    first message
        open ──────────────────────► active
                                       │
                              ┌────────┼────────┐
                              │        │        │
                      handoff │  resolved  user stops
                              ▼        │   responding
                      waiting_human    │        │
                         │    │        │        │
                   Expert │    │ timeout│   idle timeout
                  resolves│    │(30min) │   (30 min)
                         │    │        │        │
                         └────┤        ▼        ▼
                              └──► resolved ◄───┘
                                       │
                              summary generated
                                       │
                                       ▼
                                    closed
                                       │
                              90-day PII purge
                                       │
                                       ▼
                                   archived
```

## Event Types

| Event | Trigger | Payload (key fields) |
|---|---|---|
| `conversation.created` | New conversation record inserted | `{ conversation_id, tenant_id, employee_id, channel }` |
| `conversation.activated` | First AI response sent (open -> active) | `{ conversation_id, tenant_id }` |
| `conversation.handoff_requested` | Escalation to Expert triggered | `{ conversation_id, tenant_id, reason, handoff_id }` |
| `conversation.handoff_completed` | Expert resolved the handoff | `{ conversation_id, tenant_id, expert_id }` |
| `conversation.resolved` | Conversation marked resolved | `{ conversation_id, tenant_id, outcome }` |
| `conversation.closed` | Summary generated, conversation finalized | `{ conversation_id, tenant_id }` |
| `conversation.archived` | PII redacted (post-90-day) | `{ conversation_id, tenant_id }` |
| `conversation.summary_generated` | L2.5 summary created | `{ conversation_id, tenant_id, summary_tokens }` |
| `message.created` | New message appended | `{ message_id, conversation_id, role }` |
| `message.draft_pending` | Message saved as draft awaiting approval | `{ message_id, conversation_id, tenant_id }` |
| `message.approved` | Draft message approved by Expert | `{ message_id, conversation_id, approved_by }` |
| `message.rejected` | Draft message rejected by Expert | `{ message_id, conversation_id, rejected_by }` |
| `system.retention_purge` | PII retention purge executed | `{ tenant_id, redacted_count }` |

## Dependencies

```
 寫入方                                讀取方
 ┌────────────────┐                  ┌────────────────┐
 │ Channel Gateway│──┐               │ Employee Runtime│
 │ (MC-011)       │  │  append_msg   │ (MC-009)       │
 └────────────────┘  │  + get/create │ get_context()  │
                     ▼               └───────┬────────┘
              ┌──────────────────┐           │
              │ Conversation     │◄──────────┘
              │ Engine           │
              │ (MC-010)         │──→ Audit Service (MC-001)
              │ PG + Redis cache │──→ LLM Client (Haiku for summary)
              └──────────────────┘
                     ↑
              ┌──────────────┐
              │ Admin Console│  query / resolve / handoff pickup
              │ Expert UI    │
              └──────────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| Conversation CRUD + status machine | Conversation search (full-text) |
| Message append-only + Redis cache | Message editing or deletion (by design) |
| Context window assembly (fixed budget 8K tokens) | Dynamic token budget per model |
| L2.5 Summary generation (Haiku) | L4 Operational Memory (cross-session patterns) |
| Expert handoff (notification + Web UI pickup) | Real-time handoff (WebSocket) |
| Idle timeout auto-resolve (30 min) | Configurable per-employee timeout |
| 90-day PII retention purge (cron) | Real-time PII stream masking |
| Prior session summary retrieval (last 3) | Full cross-session conversation graph |
| Basic stats (active count, handoff rate) | Analytics dashboard |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
< 100 concurrent convs   100-1K concurrent            10K+ concurrent
──────────────────────────────────────────────────────────────────
PG + Redis LIST         -> Redis Streams             -> Kafka + PG (CQRS)
fixed 8K token budget   -> dynamic per model/skill   -> adaptive context compression
cron idle timeout       -> Redis keyspace notify     -> distributed scheduler
Haiku summary           -> Sonnet summary + extract  -> fine-tuned summarizer
email handoff notify    -> WebSocket live queue      -> multi-channel + SLA routing
monthly partitions      -> weekly partitions         -> sharded by tenant
single PG for read/write-> read replica for queries  -> separate OLAP for analytics
```
