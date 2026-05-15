---
id: MC-004
title: "Module Contract — Tenant Manager"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
sync-source: doc
source-paths:
  - src/control/tenant/
related: [SAD-v0.1, ADR-0004, ADR-0006, ADR-0007, MC-001, MC-007]
---

# Tenant Manager — One-Page Module Contract

> **Plane**: Control | **Priority**: #2 (所有業務模組需要 tenant context) | **Phase 1 必做**

## Purpose

管理 AEOS 平台上的租戶生命週期 — 從建立、設定、暫停到終止。每個 tenant 代表一個付費客戶企業，Tenant Manager 是多租戶隔離（ADR-0007）的管理入口，也是 API Key 認證（ADR-0006）的發行端。Phase 1 每 tenant 一台 VM（ADR-0004），但所有 code 透過 `tenant_id` filter 操作，為 Phase 2 multi-tenant 預留。

## Responsibilities

| 做 | 不做 |
|---|---|
| Tenant CRUD（create, read, update, suspend, terminate） | 計費 / 帳單（→ 外部系統 or Phase 2） |
| API Key 生成、輪換、撤銷（bcrypt hash 儲存） | 使用者身份認證（→ Auth Service / ADR-0006） |
| 租戶層級設定（LLM model、channel config、branding） | Channel webhook 管理（→ Channel Gateway） |
| 提供 `tenant_context` middleware（從 API Key → tenant_id） | 資料隔離 RLS 策略維護（→ DB migration / ADR-0007） |
| Tenant 狀態機執行（active → suspended → terminated → purged） | 跨租戶聚合分析（→ Admin Console / Phase 2） |
| 租戶資料匯出（GDPR / 客戶要求） | VM 部署 / 基礎設施管理（→ DevOps scripts） |

> **Scope enforcement**: Tenant Manager provides `resolve_api_key()` middleware. Each module's router applies scope checks via dependency injection.

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | 單一 `tenant` table + JSONB config（不拆 config 子表） | :green_circle: | Phase 1 < 5 tenants，schema 靈活性 > 查詢最佳化 | Tenant > 50 且需 config 欄位級查詢 → :yellow_circle: 拆專用 config table |
| D2 | API Key 用 bcrypt hash 儲存（不存明文） | :green_circle: | 安全基線；Key 只在生成時顯示一次 | 需 Key 前綴查詢 → 另存 key prefix (前 8 字元) 做查詢 |
| D3 | 每 tenant 最多 5 個 active API Key | :green_circle: | 防止 Key 濫發；足夠應付 admin + CI + 外部整合 | 客戶要求 > 5 → 調高上限，評估 Key 分組管理 |
| D4 | Tenant config 用 JSONB 存（LLM model、channel、branding） | :green_circle: | 不同 tenant 需要不同 config 欄位；JSONB 靈活 | Config 項超過 20 且需驗證 → :yellow_circle: JSON Schema 驗證 + 拆 typed table |
| D5 | Tenant 狀態機 4 態（active/suspended/terminated/purged） | :green_circle: | 對應 ADR-0007 §7 生命週期；夠用且可審計 | 需 trial / grace period → :yellow_circle: 加 provisioning / grace 態 |

## Data Model

```sql
CREATE TABLE tenant (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL,                      -- 顯示名稱
    slug            TEXT         NOT NULL UNIQUE,               -- URL-safe 識別符
    status          TEXT         NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended', 'terminated', 'purged')),
    plan            TEXT         NOT NULL DEFAULT 'pilot'
                    CHECK (plan IN ('pilot', 'standard', 'premium')),
    config          JSONB        NOT NULL DEFAULT '{}',         -- LLM model, branding, channel 設定
    contact_email   TEXT         NOT NULL,                      -- 主要聯繫 email
    contract_start  DATE         NOT NULL,
    contract_end    DATE,                                       -- null = 無期限
    data_retention_days INT      NOT NULL DEFAULT 90,           -- ADR-0005
    suspended_at    TIMESTAMPTZ,
    terminated_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- tenant_id RLS（ADR-0007）
ALTER TABLE tenant ENABLE ROW LEVEL SECURITY;

CREATE UNIQUE INDEX idx_tenant_slug ON tenant (slug);

CREATE TABLE api_key (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL REFERENCES tenant(id),
    name            TEXT         NOT NULL,                      -- 'admin-key', 'ci-deploy', etc.
    key_prefix      TEXT         NOT NULL,                      -- 前 8 字元，用於識別（不是秘密）
    key_hash        TEXT         NOT NULL,                      -- bcrypt hash of full key
    scopes          TEXT[]       NOT NULL DEFAULT '{}',         -- 'admin', 'read', 'deploy', 'webhook'
    status          TEXT         NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'revoked')),
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,                                -- null = 不過期（手動輪換）
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);

-- 索引
CREATE INDEX idx_api_key_tenant   ON api_key (tenant_id, status);
CREATE INDEX idx_api_key_prefix   ON api_key (key_prefix) WHERE status = 'active';
```

### Tenant Config JSONB Schema（Phase 1 範圍）

```json
{
  "llm": {
    "primary_model": "claude-sonnet-4-20250514",
    "fallback_model": "claude-haiku-4-20250514",
    "max_tokens_per_turn": 1024,
    "temperature": 0.3
  },
  "branding": {
    "display_name": "XX 公司 AI 客服",
    "greeting_message": "您好！我是 XX 公司的 AI 客服，請問有什麼可以幫您的？",
    "farewell_message": "感謝您的來訊，祝您有美好的一天！"
  },
  "channels": {
    "line": {
      "channel_id": "...",
      "channel_name": "..."
    }
  },
  "limits": {
    "max_conversations_per_day": 1000,
    "max_api_keys": 5
  }
}
```

## Interface

### Internal Python API — TenantService

```python
class TenantService:
    async def create_tenant(
        self,
        name: str,
        slug: str,
        contact_email: str,
        plan: str = "pilot",
        config: dict | None = None
    ) -> Tenant: ...

    async def get_tenant(self, tenant_id: str) -> Tenant: ...

    async def update_config(self, tenant_id: str, config_patch: dict) -> Tenant: ...

    async def suspend_tenant(self, tenant_id: str, reason: str) -> Tenant: ...

    async def terminate_tenant(self, tenant_id: str, reason: str) -> Tenant: ...

    async def generate_api_key(
        self,
        tenant_id: str,
        name: str,
        scopes: list[str]
    ) -> tuple[ApiKey, str]: ...  # returns (record, plaintext_key)

    async def rotate_api_key(self, key_id: str) -> tuple[ApiKey, str]: ...

    async def revoke_api_key(self, key_id: str) -> None: ...

    async def resolve_api_key(self, raw_key: str) -> tuple[str, list[str]] | None: ...
    # returns (tenant_id, scopes) or None if invalid
```

### REST Endpoints（Admin Console 呼叫）

| Endpoint | Method | 用途 | Scope |
|---|---|---|---|
| `/api/v1/tenants` | POST | 建立新 tenant（僅 AEOS 內部） | `aeos_admin` |
| `/api/v1/tenants/{id}` | GET | 取得 tenant 詳情 | `admin` |
| `/api/v1/tenants/{id}` | PATCH | 更新 tenant 設定 | `admin` |
| `/api/v1/tenants/{id}/suspend` | POST | 暫停 tenant | `aeos_admin` |
| `/api/v1/tenants/{id}/terminate` | POST | 終止 tenant（30 天 soft delete） | `aeos_admin` |
| `/api/v1/tenants/{id}/api-keys` | GET | 列出 API keys（不含 hash） | `admin` |
| `/api/v1/tenants/{id}/api-keys` | POST | 產生新 API Key | `admin` |
| `/api/v1/tenants/{id}/api-keys/{key_id}/rotate` | POST | 輪換 Key（舊 Key 立即失效） | `admin` |
| `/api/v1/tenants/{id}/api-keys/{key_id}/revoke` | POST | 撤銷 Key | `admin` |

### Tenant 狀態機

```
              create
                │
                ▼
           ┌─────────┐
           │  active  │◄──── re-activate (Phase 2)
           └────┬─────┘
                │ suspend(reason)
                ▼
           ┌───────────┐
           │ suspended  │
           └────┬───────┘
                │ terminate(reason)
                ▼
           ┌────────────┐
           │ terminated  │ ← 30 天 soft delete 觀察期
           └────┬────────┘
                │ purge (RUNBOOK-003 §5.5)
                ▼
           ┌─────────┐
           │  purged  │ ← 全資料刪除 + 證明
           └──────────┘
```

### Event Types

```
tenant.created
tenant.updated
tenant.suspended
tenant.terminated
tenant.config_changed
api_key.generated
api_key.rotated
api_key.revoked
```

## Dependencies

```
 建立方                        消費方
 ┌────────────────┐           ┌────────────────┐
 │ Admin Console  │──create──→│                │
 │ (MC-007)       │           │ Tenant Manager │
 │                │──config──→│ (tenant +      │
 └────────────────┘           │  api_key)      │
                              └───────┬────────┘
                                      │
            ┌─────────────────────────┼──────────────────────┐
            │ tenant_context()        │ resolve_api_key()    │
            ▼                         ▼                      ▼
 ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
 │ All Modules    │    │ Auth Middleware │    │ Audit Service  │
 │ (需 tenant_id) │    │ (API Key 驗證)  │    │ (MC-001)       │
 └────────────────┘    └────────────────┘    └────────────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| `tenant` + `api_key` table | 計費 / 訂閱管理 |
| TenantService（CRUD + 狀態機） | 自助 tenant 註冊（CTO 手動建） |
| API Key 生成 / 輪換 / 撤銷 | API Key 自動過期提醒 |
| JSONB config（LLM + branding + channel） | Config 版本歷史 / diff |
| `resolve_api_key()` middleware | OAuth2 / SSO 整合（→ Phase 2 ADR-0006） |
| REST CRUD endpoints | 多 plan 定價邏輯 |
| 每個操作 → `audit.log()` | Tenant 資料匯出 API（手動 pg_dump） |
| 狀態機（active/suspended/terminated/purged） | 自動化 purge 流程（Phase 1 手動執行） |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
1-3 tenants              5-15 tenants                 50+ tenants
──────────────────────────────────────────────────────────────────
手動建 tenant           → self-service signup        → 自動化 provisioning pipeline
JSONB config            → JSON Schema validation     → typed config table + versioning
手動 purge              → scheduled purge cron       → 自動化 data lifecycle
單 plan (pilot)         → multi-plan + billing       → usage-based pricing
手動 API Key 輪換       → auto-expire + 提醒 email   → Key vault + rotation policy
pg_dump 匯出            → tenant data export API     → compliance export + audit cert
```
