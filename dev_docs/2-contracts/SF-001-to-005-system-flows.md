---
id: SF-001..SF-005
title: System Flows — Sequence Diagrams for UF-001 to UF-005
status: active
type: system-flow
created: 2026-05-14
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 2
related: [UF-001, UF-002, UF-003, UF-004, UF-005, API-001, API-002]
---

# System Flows v0 — SF-001 到 SF-005

> 每個 SF 對應一個 UF；用 Mermaid sequenceDiagram 表示系統 module 間的呼叫順序。
> Module 名與 SAD（`docs/2-contracts/SAD-v0.1.md`）的 container 一致。

## Naming Convention

- `Expert` / `EndUser` — actor
- `LINE` — LINE Platform
- `Web` — AEOS 後台 SPA
- `API` — AEOS API gateway / FastAPI app
- `Worker` — async job processor
- `LLM` — Anthropic Claude API
- `Embed` — embedding service（Phase 1 用 Anthropic 或 sentence-transformers）
- `PG` — PostgreSQL（含 pgvector）
- `Redis` — Redis（queue + cache）
- `Audit` — Audit logger（thin wrapper, writes to PG audit_event）

---

## SF-001 — KB Upload → KC Draft → Approve

```mermaid
sequenceDiagram
    autonumber
    actor Expert
    participant Web
    participant API
    participant Worker
    participant LLM
    participant Embed
    participant PG
    participant Audit

    Expert->>Web: 上傳檔案 (PDF/MD/URL)
    Web->>API: POST /v1/knowledge/ingest (multipart)
    API->>PG: INSERT ingest_job(status=queued)
    API->>Redis: enqueue ingest_job_id
    API-->>Web: 202 Accepted + job_id
    Web-->>Expert: 顯示 "Ingest 中..."

    Worker->>Redis: dequeue
    Worker->>PG: SELECT ingest_job
    Worker->>Worker: parse + chunk (Day 1 fixed-size, Phase 2 semantic)
    loop 每個 chunk
        Worker->>LLM: summarize + extract title/tags
        LLM-->>Worker: KC draft fields
        Worker->>Embed: embed(text)
        Embed-->>Worker: vector(1024)
        Worker->>PG: INSERT knowledge_card(status=draft, embedding)
        Worker->>Audit: emit KC_DRAFTED
    end
    Worker->>PG: UPDATE ingest_job(status=done)
    Worker->>Redis: publish job_done event

    Web->>API: poll GET /v1/ingest-jobs/{id} (or SSE)
    API->>PG: SELECT
    API-->>Web: status=done + KC list

    Expert->>Web: review + edit
    Web->>API: PATCH /v1/knowledge-cards/{id}
    API->>PG: UPDATE knowledge_card
    API->>Audit: emit KC_EDITED

    Expert->>Web: Approve
    Web->>API: POST /v1/knowledge-cards/{id}/approve
    API->>PG: UPDATE status=approved, approved_by, approved_at
    API->>Audit: emit KC_APPROVED
    API-->>Web: 200 OK
```

---

## SF-002 — Test Set Run

```mermaid
sequenceDiagram
    autonumber
    actor Expert
    participant Web
    participant API
    participant Worker
    participant LLM
    participant PG
    participant Audit

    Expert->>Web: 填 50 題 test set
    Web->>API: PUT /v1/test-sets/{id} (整批 50 題)
    API->>PG: UPSERT test_set + test_cases
    API->>Audit: emit TEST_SET_SAVED
    API-->>Web: 200 OK

    Expert->>Web: 按 "Run Test"
    Web->>API: POST /v1/test-sets/{id}/runs (employee_id, employee_version)
    API->>PG: INSERT test_run(status=running)
    API->>Redis: enqueue test_run_id
    API-->>Web: 202 + run_id

    Worker->>Redis: dequeue
    loop 每個 test_case
        Worker->>PG: SELECT employee, skill_version, knowledge_cards
        Worker->>LLM: 模擬一次 conversation (system + user_question + retrieved_KCs)
        LLM-->>Worker: AI response
        Worker->>Worker: 判定 pass/fail (keyword + optional LLM judge)
        Worker->>PG: INSERT test_result(test_case_id, run_id, pass, actual_response)
        Worker->>Audit: emit TEST_CASE_RUN
    end
    Worker->>PG: UPDATE test_run(status=done, pass_rate)
    Worker->>Redis: publish run_done

    Web->>API: GET /v1/test-runs/{id}
    API->>PG: SELECT run + results
    API-->>Web: 200 OK + pass_rate + per-case detail
    Web-->>Expert: 顯示結果頁
```

---

## SF-003 — LINE Inbound → Draft Mode → Expert Approve

```mermaid
sequenceDiagram
    autonumber
    actor EndUser
    participant LINE
    participant API
    participant Worker
    participant LLM
    participant Embed
    participant PG
    participant Audit
    actor Expert
    participant Web

    EndUser->>LINE: 傳訊息
    LINE->>API: POST /webhooks/line/{channel_id} (X-Line-Signature)
    API->>API: 驗 signature
    API->>PG: UPSERT conversation, INSERT message(role=user)
    API->>Audit: emit MESSAGE_RECEIVED
    API->>Redis: enqueue process_message(msg_id)
    API-->>LINE: 200 OK (< 1s)

    Worker->>Redis: dequeue
    Worker->>PG: SELECT employee + skill_version + recent messages
    Worker->>Embed: embed(user_message)
    Worker->>PG: SELECT top_k knowledge_card by cosine similarity
    Worker->>LLM: complete(system_prompt + KCs + history + user_msg, tools)
    LLM-->>Worker: draft_text + confidence + tool_calls
    Worker->>PG: INSERT message(role=assistant, status=draft_pending, content=draft_text)
    Worker->>Audit: emit DRAFT_GENERATED

    Worker->>LINE: (via LINE Notify) 推送 Expert "有 N 則待審"
    Note over Worker,LINE: Web push 也同步發

    Expert->>Web: 開 Draft Inbox
    Web->>API: GET /v1/messages?status=draft_pending
    API->>PG: SELECT
    API-->>Web: 列表

    Expert->>Web: 開一則 → 看 user/draft/KC sources
    Expert->>Web: 按 Approve (or Edit and Send)
    Web->>API: POST /v1/messages/{id}/approve (optional edited_content)
    API->>PG: UPDATE message(status=sent or sent_edited)
    API->>Audit: emit EXPERT_APPROVED (含 diff if edited)
    API->>LINE: POST /v2/bot/message/push (reply to user)
    LINE-->>API: 200
    API-->>Web: 200 OK
    LINE->>EndUser: 訊息送達
```

---

## SF-004 — Canary Auto Reply with Confidence Threshold

```mermaid
sequenceDiagram
    autonumber
    actor EndUser
    participant LINE
    participant API
    participant Worker
    participant LLM
    participant PG
    participant Audit

    EndUser->>LINE: 傳訊息
    LINE->>API: POST /webhooks/line/{channel_id}
    API->>PG: UPSERT conversation, INSERT message(user)
    API->>Audit: emit MESSAGE_RECEIVED
    API->>Redis: enqueue
    API-->>LINE: 200 OK

    Worker->>PG: SELECT employee.auto_reply_pct, conversation
    Worker->>Worker: in_auto_bucket = hash(conv_id) % 100 < auto_reply_pct?
    Worker->>LLM: complete(...)
    LLM-->>Worker: draft + confidence

    alt confidence >= 0.75 AND in_auto_bucket AND no_anomaly_flag
        Worker->>PG: INSERT message(status=sent, auto=true)
        Worker->>LINE: push reply (auto)
        Worker->>Audit: emit AUTO_SENT (含 confidence)
        LINE->>EndUser: 訊息送達
    else
        Worker->>PG: INSERT message(status=draft_pending)
        Worker->>Audit: emit DRAFT_GENERATED (含 fallback_reason)
        Note over Worker: 走 SF-003 後半 (Expert approve flow)
    end

    Worker->>PG: 1h moving window: count P0 incidents
    alt P0 >= 1 in last 1h
        Worker->>PG: SET employee.anomaly_flag=true
        Worker->>Audit: emit ANOMALY_DETECTED
        Note over Worker: 後續訊息全走 Draft Mode
    end
```

---

## SF-005 — Emergency Kill Switch

```mermaid
sequenceDiagram
    autonumber
    actor CTO
    participant Web
    participant API
    participant PG
    participant Audit
    participant Notify
    participant Worker

    CTO->>Web: 進 "Emergency Controls" → 點 DISABLE AI
    Web->>Web: 二次確認 modal (要求填原因)
    CTO->>Web: 填原因 + Confirm
    Web->>API: POST /v1/admin/employees/{id}/emergency-disable {reason}
    API->>API: 驗 actor 權限
    API->>PG: UPDATE employee SET status='paused', paused_at, paused_reason
    API->>Audit: emit EMERGENCY_DISABLE (含 actor, reason, ts)
    API->>Notify: dispatch alerts (CEO + CTO via Slack/Email/SMS)
    Notify-->>CTO: ack
    API-->>Web: 200 OK
    Web-->>CTO: 顯示 "AI 已停"

    Note over Worker,PG: 新訊息進來
    Worker->>PG: SELECT employee
    Worker->>Worker: status==paused → 不跑 LLM
    Worker->>PG: INSERT message(status=expert_takeover, auto=false)
    Worker->>Audit: emit EXPERT_TAKEOVER (reason=emergency_paused)

    Note over CTO: 處理完之後
    CTO->>Web: Re-enable AI (二次確認)
    Web->>API: POST /v1/admin/employees/{id}/re-enable
    API->>PG: UPDATE status='live', resumed_at
    API->>Audit: emit EMERGENCY_REENABLED
```

---

## SF 共通模式

| 模式 | 適用 SF |
|---|---|
| **Async 處理**：API 收到後立即 ACK + enqueue，Worker 背景處理 | SF-001, SF-002, SF-003, SF-004 |
| **Audit 強制 emit**：任何 state transition 必發 AuditEvent | 全部 |
| **Idempotency**：所有 POST 帶 `Idempotency-Key` header，Worker dedupe | 全部 |
| **Retry / Dead-letter**：Worker 失敗 → retry 3 次（exp backoff）→ DLQ | SF-001, SF-002, SF-003, SF-004 |
| **PII pseudonymize at boundary**：API gateway 入口層做（見 ADR-0005） | SF-003, SF-004 |

## 連結

- 對應 User Flows：`UF-001` ~ `UF-005`
- 後端 API spec：`API-001-internal.md`
- LINE webhook spec：`API-002-line-webhook.md`
- Architecture：`SAD-v0.1.md`
- Data model：`domain-model.md`
