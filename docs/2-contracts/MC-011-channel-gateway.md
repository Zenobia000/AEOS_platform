---
id: MC-011
title: "Module Contract — Channel Gateway"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 90eaacb470567a3bf631af423e5dbf1ad8053a47
sync-source: doc
source-paths:
  - src/channels/
related: [SAD-v0.1, ADR-0005, API-002, MC-001, MC-009, MC-010, domain-model]
---

# Channel Gateway — One-Page Module Contract

> **Plane**: Data | **Priority**: #2 (LINE 是 Phase 1 唯一 channel，但介面設計須支援 Phase 2 多 channel) | **Phase 1 必做**

## Purpose

外部通訊平台（LINE、WhatsApp、Web Chat）與 AEOS 內部 Conversation Engine 之間的轉接層。負責接收 webhook、驗證簽章、將 channel-specific 訊息正規化為統一內部格式、並將 AI 回覆轉換回 channel 格式送出。Adapter Pattern 確保新增 channel 不需要改動核心邏輯。

## Responsibilities

| 做 | 不做 |
|---|---|
| 接收 webhook 並驗證簽章（LINE: HMAC-SHA256） | 處理對話邏輯（-> Conversation Engine MC-010） |
| 正規化 inbound 訊息為統一 InboundMessage 格式 | 生成 AI 回覆內容（-> Employee Runtime MC-009） |
| 將統一 OutboundReply 轉為 channel-specific 格式並發送 | 管理 Knowledge Cards（-> Knowledge MC-008） |
| Webhook idempotency（dedup by webhookEventId） | 對話狀態管理（-> Conversation Engine MC-010） |
| Per-channel rate limiting（inbound + outbound） | PII pseudonymization（-> API 邊界層） |
| Channel health monitoring（token validity, webhook status） | Channel 帳號申請或設定（客戶自行操作） |
| 每個 inbound/outbound event 發 audit log | 費用統計（-> Cost Tracker，Phase 2） |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | Adapter Pattern：ChannelAdapter interface + per-channel implementation | :green_circle: | Phase 1 只有 LINE，但設計上 Phase 2 加 WhatsApp 只需新增一個 class | 超過 5 個 channel -> :yellow_circle: plugin registry |
| D2 | Webhook handler 只做驗簽 + 正規化 + enqueue，不同步呼叫 LLM | :green_circle: | LINE 要求 webhook <= 1s 回應；LLM 呼叫 2-15s 不可能同步 | 無（架構原則，不變） |
| D3 | Outbound 用 LINE Push API（非 Reply API） | :green_circle: | Reply token 只有 30 秒有效；Worker 處理時間通常 > 30s（ADR-0002 pipeline） | 需要 < 5s 回覆 -> 評估 Reply API + async 加速 |
| D4 | Phase 1 只處理 text message；其他類型回 fallback | :green_circle: | 最小可行；Phase 1 客服場景 90%+ 是文字 | 客戶要求圖片/語音 -> :yellow_circle: 多媒體 adapter |
| D5 | LINE channel config（access token, secret）加密存 channel_binding table | :green_circle: | 安全需求；per-employee channel binding 支援多 OA 場景 | 需要 dynamic token rotation -> :yellow_circle: vault integration |
| D6 | End user identity: LINE userId hash 為 end_user_pseudo_id | :green_circle: | ADR-0005 PII 最小化；tenant-specific salt 防跨租戶關聯 | 需要跨 channel 統一 identity -> :yellow_circle: identity resolution service |

## Data Model

```sql
-- channel_binding 已在 db-schema.md 定義（employee <-> channel mapping）

CREATE TABLE channel_binding (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL CHECK (channel IN ('line', 'web_chat', 'whatsapp')),
    config          JSONB NOT NULL DEFAULT '{}',           -- encrypted channel credentials
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, channel)
);

-- config JSONB structure (LINE):
-- {
--   "channel_id": "17xxxxxxx",
--   "channel_secret": "<<encrypted>>",
--   "channel_access_token": "<<encrypted>>",
--   "webhook_url": "https://{slug}.aeos.app/api/v1/webhooks/line/{channel_id}"
-- }

-- Webhook event dedup table (prevent reprocessing)
CREATE TABLE webhook_event (
    id              TEXT NOT NULL,                          -- LINE: webhookEventId
    tenant_id       UUID NOT NULL REFERENCES tenant(id),   -- resolved from channel_binding
    channel         TEXT NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, channel)
);
-- Auto-purge events older than 7 days (dedup window)
CREATE INDEX idx_webhook_event_purge ON webhook_event(received_at);

-- Outbound message tracking (for retry + audit)
CREATE TABLE outbound_message (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    conversation_id UUID NOT NULL,
    message_id      UUID NOT NULL,                         -- internal message that triggered this
    channel         TEXT NOT NULL,
    channel_user_id TEXT NOT NULL,                          -- target user (hashed LINE userId)
    status          TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'retrying')),
    retry_count     INT NOT NULL DEFAULT 0,
    error_message   TEXT,
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_outbound_pending ON outbound_message(status, created_at)
    WHERE status IN ('pending', 'retrying');
```

## Interface

### Internal Python API — Channel Adapter Pattern

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class InboundMessage:
    """Normalized inbound message from any channel."""
    channel: str                    # 'line' | 'web_chat' | 'whatsapp'
    channel_user_id: str            # raw channel user ID (will be hashed downstream)
    channel_message_id: str         # channel-specific message ID
    webhook_event_id: str           # for dedup
    message_type: str               # 'text' | 'image' | 'sticker' | 'location' | ...
    text: str | None                # message text (None for non-text)
    raw_payload: dict               # original channel payload (for debugging)
    timestamp: int                  # epoch ms from channel
    is_redelivery: bool             # channel retry flag

@dataclass(frozen=True)
class OutboundReply:
    """Normalized outbound reply to be sent via channel."""
    conversation_id: str
    message_id: str                 # internal message ID
    channel: str
    channel_user_id: str            # target user
    text: str                       # response text
    channel_config: dict            # { channel_access_token, ... }

class ChannelAdapter(ABC):
    """Interface for channel-specific implementations."""

    @abstractmethod
    async def verify_webhook(self, body: bytes, headers: dict, config: dict) -> bool:
        """Verify webhook signature. Return False -> 403."""
        ...

    @abstractmethod
    async def parse_inbound(self, body: dict) -> list[InboundMessage]:
        """Parse channel webhook body into normalized InboundMessages."""
        ...

    @abstractmethod
    async def send_reply(self, reply: OutboundReply) -> bool:
        """Send outbound reply via channel API. Return success."""
        ...

    @abstractmethod
    async def send_fallback(self, channel_user_id: str, config: dict) -> bool:
        """Send a generic 'please wait' or 'I can only read text' fallback."""
        ...

class LineAdapter(ChannelAdapter):
    """LINE Messaging API implementation. See API-002 for full spec."""

    async def verify_webhook(self, body: bytes, headers: dict, config: dict) -> bool:
        """HMAC-SHA256(channel_secret, body) == X-Line-Signature"""
        ...

    async def parse_inbound(self, body: dict) -> list[InboundMessage]:
        """Parse LINE webhook events -> InboundMessages. One webhook may contain multiple events."""
        ...

    async def send_reply(self, reply: OutboundReply) -> bool:
        """POST https://api.line.me/v2/bot/message/push"""
        ...

    async def send_fallback(self, channel_user_id: str, config: dict) -> bool:
        """Send text: 'I currently only understand text messages.'"""
        ...

# Future adapters (Phase 2+):
# class WhatsAppAdapter(ChannelAdapter): ...
# class WebChatAdapter(ChannelAdapter): ...
```

### Internal Python API — ChannelGateway

```python
class ChannelGateway:
    """Orchestrates inbound webhook processing and outbound reply delivery."""

    def __init__(self, adapters: dict[str, ChannelAdapter]):
        self._adapters = adapters  # {'line': LineAdapter(), ...}

    # -- Inbound (called by FastAPI webhook route) --
    async def handle_webhook(
        self,
        channel: str,
        channel_id: str,
        body: bytes,
        headers: dict,
    ) -> None:
        """
        1. Look up channel_binding by channel + channel_id -> get config
        2. Verify webhook signature via adapter
        3. Parse inbound messages
        4. For each message:
           a. Dedup check (webhook_event_id)
           b. Hash channel_user_id -> end_user_pseudo_id
           c. Get or create conversation (via ConversationService)
           d. Append user message (via ConversationService)
           e. Enqueue processing job to Redis (-> Employee Runtime)
           f. Audit: channel.message_received
        5. Return (caller sends 200 OK)
        """
        ...

    # -- Outbound (called by Worker after Employee Runtime produces reply) --
    async def send_reply(
        self,
        tenant_id: str,
        conversation_id: str,
        message_id: str,
        channel: str,
        channel_user_id: str,
        text: str,
    ) -> bool:
        """
        1. Look up channel config for this conversation's employee
        2. Build OutboundReply
        3. Call adapter.send_reply()
        4. If success: update outbound_message status='sent'
        5. If failure: retry with exponential backoff (2, 4, 8s), max 3 retries
        6. If all retries fail: DLQ + audit channel.send_failed
        7. Audit: channel.message_sent or channel.send_failed
        """
        ...
```

### REST API (Webhook Endpoints)

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/webhooks/line/{channel_id}` | POST | LINE webhook 入口（see API-002） |
| `/api/v1/webhooks/whatsapp/{channel_id}` | POST | WhatsApp webhook（Phase 2） |
| `/api/v1/webhooks/webchat/{channel_id}` | POST | Web Chat webhook（Phase 2） |

### REST API (Admin)

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/channels/health` | GET | Channel 健康狀態（token validity, last webhook, error rate） |
| `/api/v1/channels/outbound/failed` | GET | 查詢失敗的 outbound messages（DLQ inspection） |
| `/api/v1/channels/outbound/{id}/retry` | POST | 手動重試失敗的 outbound message |
| `/api/v1/channels/stats` | GET | Channel 統計（messages in/out per day, error rate） |

### Worker Job — SendReply

```
Redis queue: channel:send
Payload: { tenant_id, conversation_id, message_id, channel, channel_user_id, text }

Pipeline:
  1. Dequeue job
  2. Call ChannelGateway.send_reply()
  3. If retry needed: re-enqueue with delay + incremented retry_count
  4. If max retries exceeded: insert to outbound_message(status='failed') + alert
  5. ACK job
```

### Inbound Processing Pipeline (Detail)

```
LINE Platform
     │
     │ POST /api/v1/webhooks/line/{channel_id}
     ▼
┌─────────────────────────────────────────┐
│ FastAPI Route Handler (< 1s total)      │
│                                         │
│  1. channel_binding = lookup(channel_id)│
│  2. adapter.verify_webhook(body, sig)   │
│     └─ FAIL -> 403 + audit SIG_INVALID │
│  3. messages = adapter.parse_inbound()  │
│  4. for msg in messages:                │
│     a. dedup(msg.webhook_event_id)      │
│        └─ DUPLICATE -> skip (return 200)│
│     b. pseudo_id = hash(msg.user_id)    │
│     c. conv_id = get_or_create_conv()   │
│     d. msg_id = append_message(user)    │
│     e. enqueue(conversation:process)    │
│     f. audit(channel.message_received)  │
│  5. return 200 OK                       │
└─────────────────────────────────────────┘
     │
     │ Redis queue: conversation:process
     ▼
  Worker -> Employee Runtime (MC-009)
     │
     │ Redis queue: channel:send
     ▼
  Worker -> ChannelGateway.send_reply()
     │
     │ POST https://api.line.me/v2/bot/message/push
     ▼
LINE Platform -> End User
```

## Event Types

| Event | Trigger | Payload (key fields) |
|---|---|---|
| `channel.webhook_received` | Valid webhook received and parsed | `{ channel, channel_id, tenant_id, event_count }` |
| `channel.webhook_invalid_signature` | Webhook signature verification failed | `{ channel, channel_id, source_ip }` |
| `channel.message_received` | Inbound message normalized and enqueued | `{ channel, tenant_id, conversation_id, message_type }` |
| `channel.message_sent` | Outbound reply delivered successfully | `{ channel, tenant_id, conversation_id, message_id }` |
| `channel.send_failed` | Outbound reply failed after all retries | `{ channel, tenant_id, conversation_id, message_id, error_message }` |
| `channel.send_retried` | Outbound reply retry attempted | `{ channel, tenant_id, message_id, retry_count }` |

## Dependencies

```
 External                          Internal
 ┌────────────────┐              ┌────────────────┐
 │ LINE Platform  │──webhook──►  │ Channel Gateway│
 │                │◄──push────── │ (MC-011)       │
 └────────────────┘              └────────┬───────┘
                                          │
 ┌────────────────┐              ┌────────┼───────────────┐
 │ WhatsApp (P2)  │              │        │               │
 │ Web Chat (P2)  │              ▼        ▼               ▼
 └────────────────┘       ┌──────────┐ ┌──────────┐ ┌──────────┐
                          │ Convers. │ │ Employee │ │ Audit    │
                          │ Engine   │ │ Runtime  │ │ Service  │
                          │ (MC-010) │ │ (MC-009) │ │ (MC-001) │
                          └──────────┘ └──────────┘ └──────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| LINE adapter（text message 收發） | WhatsApp / Web Chat adapter |
| Webhook 簽章驗證（HMAC-SHA256） | OAuth token auto-refresh |
| Push API 送訊息（不用 Reply API） | Reply API（< 30s 快速回覆） |
| Text-only inbound；非文字回 fallback | 圖片 / 語音 / 影片處理 |
| Webhook dedup（webhookEventId） | Exactly-once delivery guarantee |
| Exponential backoff retry（3 次） | Circuit breaker pattern |
| outbound_message 追蹤（sent/failed） | 送達確認（delivery receipt） |
| LINE push 配額監控（daily cron） | Real-time quota dashboard |
| Per-IP rate limit（1000 req/min） | Per-user adaptive rate limit |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
LINE only                LINE + WhatsApp             LINE + WhatsApp + Web + Voice
──────────────────────────────────────────────────────────────────
1 adapter class         -> adapter registry          -> plugin system + hot-reload
text only               -> text + image + template   -> multi-modal (voice, video)
Push API only           -> Push + Reply (< 30s)      -> streaming response
retry 3x backoff        -> circuit breaker           -> per-channel health routing
channel_binding table   -> dynamic config (vault)    -> self-service channel setup
dedup table             -> Redis-based dedup (TTL)   -> distributed dedup (idempotency key)
per-IP rate limit       -> per-user + per-tenant     -> adaptive rate limit + WAF
single VM               -> regional edge endpoints   -> CDN + edge functions
```
