---
id: ADR-0007
title: Tenant Isolation Strategy
status: accepted
date: 2026-05-15
deciders: CTO
tier: 1
---

# ADR-0007 — 多租戶隔離策略

## Context

AEOS 是 multi-tenant SaaS：Phase 1 預計 3~5 個 tenant；Phase 2 目標 50+；Phase 3 期望 500+。

關鍵衝突：
- **資料隔離**（避免 tenant A 看到 tenant B 的資料）
- **運維簡潔**（單人團隊不可能管 500 個 DB）
- **成本效率**（每 tenant 獨立 stack = 燒錢）
- **客戶要求**（部分客戶可能要求「資料絕對不混在一起」）

業界 3 種主流隔離：

| 模式 | 隔離度 | 成本 | 運維複雜度 |
|---|---|---|---|
| **A. Shared DB, shared schema, row-level**（每 row 帶 tenant_id） | 低 | 低 | 低 |
| **B. Shared DB, schema-per-tenant** | 中 | 中 | 中 |
| **C. DB-per-tenant**（含獨立 schema、獨立連線） | 高 | 高 | 高 |

## Decision

**Phase 1：方案 A（shared DB, row-level isolation with PostgreSQL RLS）**
**為「Phase 2+ 客戶要求專屬 DB」預留 escape hatch：Premium tenant 可升級到方案 C。**

### 1. Row-Level Isolation（方案 A）細節

- 所有業務表必有 `tenant_id UUID NOT NULL` column
- 啟用 PostgreSQL Row Level Security (RLS)：

```sql
CREATE POLICY tenant_isolation ON conversations
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;
```

- 每個 request 進來，app 在開 transaction 前 `SET LOCAL app.current_tenant_id = ...`
- DB user 用 `tenant_app` role，**強制套用 RLS**（不能 bypass）
- Migration / 維護用 `tenant_admin` role，**繞過 RLS**，但需 audit

### 2. 應用層雙重防護

不依賴 RLS 單一機制 — application 層也檢查：

```python
# 每個 query / repository 函式必帶 tenant_id 參數
def list_conversations(session, tenant_id: UUID, ...) -> list[Conversation]:
    return session.query(Conversation).filter_by(tenant_id=tenant_id).all()
    # RLS 是第二道保險，不是唯一保險
```

PR review 規則：缺 tenant_id filter → block merge。

### 3. 認證綁定

- JWT claim 含 `tenant_id`
- 每個 API endpoint middleware 自動 inject `tenant_id` 到 SQL session context
- Cross-tenant API（如平台管理員）需顯式 `aeos_admin` role + 額外 audit

### 4. 非結構化資料隔離

| 資產類型 | 隔離方式 |
|---|---|
| Postgres tables | RLS + tenant_id column |
| Object Storage（KB 檔案） | S3 key prefix: `tenants/<tenant_id>/...` + IAM policy by prefix |
| Vector DB（embeddings） | Namespace per tenant（如 Qdrant `collection_name=tenant_<id>`）|
| Cache（Redis） | Key prefix `t:<tenant_id>:...` |
| Logs | tenant_id label on every log line（OBS-001 §4.1）|
| Audit log | tenant_id 索引；客戶可下載自己 tenant 的部分 |

### 5. 計算資源隔離

Phase 1：**共享**（同一 app process 服務所有 tenant）
- 用 QUOTA-001 §3 per-tenant rate limit 防止 noisy neighbor
- 慢 query 限制：statement_timeout = 5s per query
- LLM 呼叫 per tenant queue 防止單 tenant 阻塞他人

Phase 2：**Premium tier 可選 isolated compute**（dedicated worker pod）

### 6. Premium Tenant Escape Hatch（方案 C）

未來客戶若要求「絕對隔離」：

- 提供 `tier = premium_isolated` 配置
- 為該 tenant 開：
  - 獨立 Postgres database（仍在同 server，Phase 2 升級為獨立 server）
  - 獨立 S3 bucket
  - 獨立 Vector DB collection（或獨立 instance）
  - 獨立 LLM API key（成本與 audit 完全獨立）
- 連線層：tenant_id → connection string 路由表
- 定價：基礎價 × 3

Phase 1 不實作，但**程式設計時保留路由抽象層**（avoid hardcoding shared DB assumption）。

### 7. Tenant 生命週期管理

| 階段 | 動作 |
|---|---|
| **Provisioning** | 新增 row in `tenants` table；建立 admin user；S3 prefix 自動產生 |
| **Active** | 正常運作 |
| **Suspended** | quota-guard suspend；保留資料；不可登入 |
| **Termination request** | 30 天 soft delete 觀察期 |
| **Purge** | RUNBOOK-003 §5.5 全資料刪除 + 證明 |

## Consequences

### 正向

- 單一 DB / 單一 stack：運維極簡（Pilot 期關鍵）
- 成本低（500 tenant 一個 Postgres 撐得住）
- Migration 一次套用所有 tenant
- 跨 tenant 分析（aggregate metrics）容易

### 負向

- RLS 一旦設定錯誤 = 全 tenant 資料外洩風險
- 單 tenant 異常負載可能影響他人（用 QUOTA-001 緩解）
- 升級 / 降級 Premium tenant 需資料搬遷（Phase 2 流程設計）

### 風險與緩解

| 風險 | 緩解 |
|---|---|
| RLS policy 寫錯 → 跨 tenant 洩漏 | 應用層 double-check（§2）；CI 加 cross-tenant query 測試 |
| Migration 忘加 RLS | CI 檢查：新增表必須啟用 RLS（PR template 提醒） |
| `tenant_admin` role 誤用 | 限制使用 + 強制 audit + 雙人核可 |
| Premium 客戶想要 isolated 但成本不願多付 | 提前在 SOW 標明價格 |
| Noisy neighbor | QUOTA-001 §3 rate limit + per-tenant queue |
| Tenant ID forgery（JWT 偽造） | ADR-0006 §5 JWT 簽章驗證 + tenant_id 必驗 |

## Alternatives Considered

| 方案 | 為何不選（Phase 1） |
|---|---|
| **B. Schema-per-tenant** | 5 tenant 已有 5 個 schema；100 tenant migration 變地獄；無顯著安全收益 |
| **C. DB-per-tenant**（全套） | Pilot 期運維成本爆表；單人無法管 |
| **微服務 per tenant** | 完全 overkill；Phase 4+ 才考慮 |
| **僅應用層隔離（無 RLS）** | 單點失誤即洩漏；不可接受 |

## Implementation Notes

- DB schema 變更：所有 tier-2 db-schema.md 中的業務表加 `tenant_id` + RLS policy
- Repository pattern（patterns.md）強制接 tenant_id 參數
- 主程式碼：`shared/tenant_context.py`（middleware 從 JWT 取出 tenant_id 並 SET LOCAL）
- 測試：`tests/integration/test_tenant_isolation.py` 必含 cross-tenant access denial 測試

## Related

- ADR-0006 — Auth & identity（tenant_id 進 JWT）
- ADR-0005 — PII（tenant 資料分離是 PII 保護的基礎）
- ADR-0009 — Prompt versioning（prompt 也是 per-tenant 隔離）
- QUOTA-001 — Per-tenant quota
- SEC-001 — Threat model（cross-tenant 攻擊面）
- LEGAL-001 §4.4 — 對客戶承諾
- db-schema.md — RLS policy 實際定義位置
