---
id: MC-001
title: "Module Contract — Audit Service"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
sync-source: doc
source-paths:
  - src/governance/audit/
related: [SAD-v0.1, ADR-0005, ADR-0007, OBS-001]
---

# Audit Service — One-Page Module Contract

> **Plane**: Governance | **Priority**: #1 (所有模組依賴它) | **Phase 1 必做**
>
> **Note**: MC-001 is the canonical audit event schema. db-schema.md and API-001 will be regenerated to match.

## Purpose

記錄 AEOS 平台上所有有意義的操作事件（AI 員工行為、管理員操作、系統事件），提供不可竄改的追溯軌跡。這是「治理」護城河的技術基礎 — 沒有 audit trail，合規和問責都是空話。

## Responsibilities

| 做 | 不做 |
|---|---|
| 接收所有模組的事件，寫入 append-only log | 即時告警（→ Evaluation Service） |
| 記錄 who / what / when / why / outcome | 資料分析或報表（→ Admin Console） |
| 保證 log 不可竄改（DB trigger 擋 UPDATE/DELETE） | PII 偵測（→ API 邊界層，各模組呼叫前處理） |
| 提供按 tenant + 時間 + 事件類型的查詢 API | 全文搜尋（Phase 1 不做） |
| 90 天後對 payload 中 PII 欄位脫敏 | 複雜的分層 retention 策略 |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | PostgreSQL append-only table（不用 ES/ClickHouse） | :green_circle: | 1-3 客戶日均數千筆，PG 綽綽有餘 | Log > 5000 萬筆且查詢 > 2s → :yellow_circle: partitioning by month |
| D2 | 固定欄位 + JSONB payload（Schema-on-Read） | :green_circle: | 事件類型差異大，Phase 1 靈活性 > 查詢效能 | 需要跨事件類型 JOIN 分析 → :yellow_circle: 拆專用 table |
| D3 | 各模組主動呼叫 `audit.log()`（非 middleware 攔截） | :green_circle: | 業務語義比 HTTP 層資訊有用；非 HTTP 操作也需記錄 | 模組數 > 15 且漏記頻繁 → :yellow_circle: event bus |
| D4 | Payload 記完整對話內容，90 天後脫敏 | :yellow_circle: | 完整追溯能力，但依賴脫敏 cron 不出錯 | 客戶要求即時脫敏 → 升級為寫入時即 mask |
| D5 | Audit log 永久保留，PII 欄位 90 天後 REDACTED | :green_circle: | 合規要求（ADR-0005）；事件骨架永遠可查 | 儲存成本 > 閾值 → :yellow_circle: 冷熱分層（PG + S3 archive） |

## Data Model

```sql
CREATE TABLE audit_log (
    id            BIGSERIAL    PRIMARY KEY,
    tenant_id     UUID         NOT NULL,                -- ADR-0007 租戶隔離
    actor_type    TEXT         NOT NULL CHECK (actor_type IN ('ai_employee', 'admin', 'system', 'policy_engine')),
    actor_id      TEXT         NOT NULL,                 -- 操作者 ID
    event_type    TEXT         NOT NULL,                 -- 'conversation.message_sent' | 'skill.deployed' | ...
    resource_type TEXT,                                  -- 'conversation' | 'skill' | 'tool' | ...
    resource_id   TEXT,                                  -- 被操作對象 ID
    action        TEXT         NOT NULL,                 -- 'create' | 'invoke' | 'deploy' | ...
    outcome       TEXT         NOT NULL,                 -- 'success' | 'failure' | 'denied'
    payload       JSONB,                                 -- 事件特有資料（含完整對話內容）
    ip_address    INET,                                  -- 來源 IP
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Append-only 保護
CREATE OR REPLACE FUNCTION reject_audit_mutation() RETURNS TRIGGER AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation();

-- Phase 1 索引（最小集）
CREATE INDEX idx_audit_tenant_time  ON audit_log (tenant_id, created_at DESC);
CREATE INDEX idx_audit_event_type   ON audit_log (event_type, created_at DESC);
CREATE INDEX idx_audit_resource     ON audit_log (resource_type, resource_id);
```

## Interface

### 寫入（所有模組呼叫）

```python
# Internal Python API — AuditClient
class AuditClient:
    async def log(
        self,
        event_type: str,           # "conversation.message_sent"
        actor: Actor,              # (type='ai_employee', id='emp-001')
        resource: tuple[str, str], # ('conversation', 'conv-abc')
        action: str,               # 'create'
        outcome: str,              # 'success'
        payload: dict | None = None
    ) -> None: ...
```

### 查詢（Admin Console / Evaluation Service）

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/audit` | GET | 分頁查詢（filter: tenant_id, start, end, event_type, actor_id） |
| `/api/v1/audit/{id}` | GET | 單筆詳情 |
| `/api/v1/audit/stats` | GET | 事件類型統計（Phase 1 簡版，供 dashboard） |

### Event Type 命名規範

```
{module}.{action}

範例：
  conversation.message_sent      — AI 員工發送訊息
  conversation.message_received  — 收到使用者訊息
  skill.deployed                 — Skill 版本上線
  skill.rolled_back              — Skill 回滾
  tool.invoked                   — AI 員工呼叫外部工具
  tool.denied                    — Policy Engine 拒絕工具呼叫
  employee.created               — 新 AI 員工建立
  employee.frozen                — AI 員工進入 frozen 狀態
  training.test_run              — 訓練室測試執行
  training.approved              — 專家審核通過
  admin.config_changed           — 管理員修改設定
  system.retention_purge         — 系統執行 PII 脫敏
```

## Dependencies

```
 寫入方（所有模組）              讀取方
 ┌────────────────┐            ┌────────────────┐
 │ Employee Runtime│──┐        │ Admin Console  │
 │ Conversation   │──┤  log() │ (查詢 + 報表)   │
 │ Skill Registry │──┤──────→ ┌──────────────┐  │
 │ Tool Registry  │──┤        │ Audit Service│──→│
 │ Training Room  │──┤        │ (audit_log)  │  │
 │ Channel Gateway│──┤        └──────────────┘  │
 │ Tenant Manager │──┤              ↓           │
 │ Knowledge (RAG)│──┘        │ Evaluation Svc │
 └────────────────┘           │ (品質分析)      │
                              └────────────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| `audit_log` table + append-only trigger | Event bus / async queue |
| `AuditClient` class 供所有模組 import | 全文搜尋 (Elasticsearch) |
| REST 查詢 API（分頁 + 篩選） | 即時串流 dashboard |
| 3 個索引（tenant+time, event_type, resource） | OLAP 分析型查詢 |
| 90 天 PII 脫敏 cron job | 冷熱分層儲存 |
| Event type 命名規範文件 | 跨租戶聚合分析 |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
1-3 tenants              5-15 tenants                 50+ tenants
──────────────────────────────────────────────────────────────────
單 table                → partition by month        → ClickHouse / TimescaleDB
同步 log()              → async event bus           → Kafka + consumer
REST 查詢               → Grafana dashboard         → 自建 audit analytics
PG 索引                 → 部分欄位 GIN index        → 專用搜尋引擎
cron 脫敏               → 即時 PII stream mask      → 合規自動化平台
```
