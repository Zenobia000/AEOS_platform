---
id: MC-006
title: "Module Contract — Tool Registry"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
sync-source: doc
source-paths:
  - src/control/tool_registry/
related: [SAD-v0.1, MC-001, MC-005, MC-007, domain-model]
---

# Tool Registry — One-Page Module Contract

> **Plane**: Control | **Priority**: #4 (Employee Runtime 需要它才能呼叫外部能力) | **Phase 1 必做（最小版）**

## Purpose

管理 AI 員工可呼叫的外部工具（API、function、knowledge search），並透過 Tool Gateway 作為所有工具呼叫的唯一出口 -- 每次呼叫都經過 Policy check -> Audit log -> PII mask -> Execute -> Log result。Tool Registry 是「Governance-first」原則在工具層的執行點：AI 員工不能繞過 Gateway 直接呼叫任何外部資源。

## Responsibilities

| 做 | 不做 |
|---|---|
| Tool CRUD（註冊、啟用、停用、設定） | 實作具體 tool 的業務邏輯（→ 各 tool adapter） |
| Tool Gateway：policy check -> audit -> PII mask -> execute -> log | LLM 決定何時呼叫 tool（→ Employee Runtime） |
| Policy Engine v0：YAML 規則判斷 tool 是否允許呼叫 | 複雜 policy 推理（→ Phase 2 Policy Engine） |
| 記錄每次 ToolInvocation（input, output, latency, cost） | Tool 的 auth credential 管理（→ Secret Manager / env） |
| Rate limiting per tool per tenant | Tool 結果的業務解讀（→ Employee Runtime / Skill） |
| 提供 tool schema 給 LLM function calling | 監控 tool 健康度（→ Phase 2 Observability） |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | Tool Gateway = 同步 Python function call（不是 HTTP proxy） | :green_circle: | Phase 1 tools 都在同一 process；避免 network hop | Tool 需獨立部署 / 多語言 → :yellow_circle: HTTP sidecar proxy |
| D2 | Policy Engine v0 = YAML 靜態規則（不是 OPA/Rego） | :green_circle: | Phase 1 < 10 tools，規則簡單（allow/deny by skill + risk_tier） | 規則超 50 條或需動態判斷 → :yellow_circle: OPA / Cedar |
| D3 | 3 級 risk_tier：safe / caution / restricted | :green_circle: | 簡單分級；restricted 需額外 policy approval | 需更細粒度 → :yellow_circle: 加 custom risk score |
| D4 | ToolInvocation 寫入專用 table（不只是 audit_log） | :green_circle: | 需 latency/cost 聚合查詢；audit_log 是 JSONB 不好做 GROUP BY | Invocation > 100 萬/月 → :yellow_circle: partition by month |
| D5 | Tool auth config 存 DB（encrypted JSONB），runtime 解密 | :yellow_circle: | 需要 per-tool 不同 auth；但加密 key 管理需嚴謹 | 客戶要求外部 KMS → :red_circle: 接 Vault / AWS KMS |

## Data Model

```sql
-- Tool = AI 員工可呼叫的外部能力
CREATE TABLE tool (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         REFERENCES tenant(id),    -- null = 系統內建 tool
    slug            TEXT         NOT NULL,                   -- 'search_knowledge', 'lookup_order'
    name            TEXT         NOT NULL,                   -- 人類可讀名稱
    description     TEXT         NOT NULL,                   -- LLM 看的描述（function calling）
    tool_type       TEXT         NOT NULL CHECK (tool_type IN ('internal', 'http_api', 'db_query', 'function')),
    endpoint        TEXT,                                    -- HTTP endpoint（tool_type=http_api 時）
    auth_method     TEXT,                                    -- 'none' | 'api_key' | 'bearer' | 'basic' | 'hmac'
    auth_config     JSONB,                                   -- 加密的 auth 設定（key/token/secret）
    input_schema    JSONB        NOT NULL,                   -- JSON Schema for input
    output_schema   JSONB,                                   -- JSON Schema for output
    risk_tier       TEXT         NOT NULL DEFAULT 'safe'
                    CHECK (risk_tier IN ('safe', 'caution', 'restricted')),
    rate_limit_rpm  INT          NOT NULL DEFAULT 60,        -- requests per minute per tenant
    timeout_ms      INT          NOT NULL DEFAULT 5000,      -- 呼叫逾時
    retry_policy    JSONB        NOT NULL DEFAULT '{"max_retries": 2, "backoff_ms": 500}',
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_tool_tenant_slug ON tool (COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug);
CREATE INDEX idx_tool_type ON tool (tool_type, enabled);

-- ToolInvocation = 每次工具呼叫的記錄
CREATE TABLE tool_invocation (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL REFERENCES tenant(id),
    conversation_id UUID,                                    -- FK conversation(id)
    message_id      UUID,                                    -- FK message(id)
    tool_id         UUID         NOT NULL REFERENCES tool(id),
    employee_id     UUID,                                    -- FK employee(id)
    skill_version_id UUID,                                   -- 哪個 Skill 觸發的
    input           JSONB        NOT NULL,                   -- 已 PII mask
    output          JSONB,                                   -- 已 PII mask; null if error
    status          TEXT         NOT NULL CHECK (status IN ('success', 'error', 'timeout', 'rejected_by_policy')),
    error_message   TEXT,
    latency_ms      INT,
    cost_token      INT,                                     -- LLM token cost (if applicable)
    policy_decision JSONB,                                   -- { "allowed": true, "rule": "rule-003", "reason": "..." }
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_invocation_tenant_time ON tool_invocation (tenant_id, created_at DESC);
CREATE INDEX idx_tool_invocation_tool        ON tool_invocation (tool_id, created_at DESC);
CREATE INDEX idx_tool_invocation_conversation ON tool_invocation (conversation_id);

-- Policy Rule = YAML-driven 靜態規則（Phase 1）
CREATE TABLE tool_policy (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         REFERENCES tenant(id),    -- null = 全局規則
    name            TEXT         NOT NULL,
    description     TEXT,
    rule_yaml       TEXT         NOT NULL,                   -- YAML 規則內容
    priority        INT          NOT NULL DEFAULT 0,         -- 越高越優先
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE tool ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_invocation ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_policy ENABLE ROW LEVEL SECURITY;
```

### Policy YAML 格式（Phase 1）

```yaml
# tool-policies/default.yaml
rules:
  - id: rule-001
    description: "safe tools 所有 skill 可用"
    match:
      risk_tier: safe
    action: allow

  - id: rule-002
    description: "caution tools 需 skill 明確綁定"
    match:
      risk_tier: caution
    condition:
      tool_slug_in_skill_bindings: true
    action: allow

  - id: rule-003
    description: "restricted tools 預設拒絕"
    match:
      risk_tier: restricted
    action: deny
    override: "需 admin 手動加入 skill 的 tool_bindings"

  - id: rule-004
    description: "停用的 tool 一律拒絕"
    match:
      enabled: false
    action: deny
```

## Interface

### Internal Python API — ToolRegistryService + ToolGateway

```python
class ToolRegistryService:
    async def register_tool(
        self,
        tenant_id: str | None,  # None = system built-in
        slug: str,
        name: str,
        description: str,
        tool_type: str,
        input_schema: dict,
        risk_tier: str = "safe",
        **kwargs
    ) -> Tool: ...

    async def get_tool(self, tool_id: str) -> Tool: ...

    async def list_tools(
        self, tenant_id: str, enabled_only: bool = True
    ) -> list[Tool]: ...

    async def get_tools_for_skill(
        self, skill_version: SkillVersion
    ) -> list[Tool]: ...
    # 根據 skill_version.tool_bindings 回傳可用 tools

    async def update_tool(self, tool_id: str, **kwargs) -> Tool: ...

    async def disable_tool(self, tool_id: str, reason: str) -> Tool: ...


class ToolGateway:
    """所有 tool 呼叫的唯一出口。"""

    async def invoke(
        self,
        tool_id: str,
        input_data: dict,
        context: InvocationContext  # tenant_id, employee_id, skill_version_id, conversation_id, message_id
    ) -> ToolInvocationResult: ...
    # 流程：
    # 1. Policy check → allow / deny
    # 2. If denied → audit.log(tool.denied) → return denied
    # 3. PII mask input
    # 4. Rate limit check
    # 5. Execute tool (with timeout)
    # 6. PII mask output
    # 7. Record ToolInvocation
    # 8. audit.log(tool.invoked)
    # 9. Return result
```

### REST Endpoints

| Endpoint | Method | 用途 | Scope |
|---|---|---|---|
| `/api/v1/tools` | GET | 列出 tools（filter: type, risk_tier, enabled） | `read` |
| `/api/v1/tools/{id}` | GET | 單一 tool 詳情（含 schema） | `read` |
| `/api/v1/admin/tools` | POST | 註冊新 tool | `admin` |
| `/api/v1/admin/tools/{id}` | PATCH | 更新 tool 設定 | `admin` |
| `/api/v1/admin/tools/{id}/disable` | POST | 停用 tool（立即生效） | `admin` |
| `/api/v1/admin/tools/{id}/enable` | POST | 啟用 tool | `admin` |
| `/api/v1/tool-invocations` | GET | 查詢呼叫記錄（filter: tool_id, status, date range） | `read` |
| `/api/v1/tool-invocations/stats` | GET | 聚合統計（per tool: count, avg_latency, error_rate） | `read` |

### Tool Gateway 流程圖

```
Employee Runtime 要求呼叫 tool
          │
          ▼
   ┌─────────────┐
   │ Policy Check │──denied──→ audit.log(tool.denied) → return REJECTED
   └──────┬──────┘
          │ allowed
          ▼
   ┌─────────────┐
   │ PII Mask    │ ← 遮罩 input 中的 PII
   │ Input       │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Rate Limit  │──exceeded──→ return RATE_LIMITED
   │ Check       │
   └──────┬──────┘
          │ ok
          ▼
   ┌─────────────┐
   │ Execute     │──timeout/error──→ record error + audit.log
   │ Tool        │
   └──────┬──────┘
          │ success
          ▼
   ┌─────────────┐
   │ PII Mask    │ ← 遮罩 output 中的 PII
   │ Output      │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────┐
   │ Record           │ → tool_invocation table
   │ ToolInvocation   │ → audit.log(tool.invoked)
   └──────┬───────────┘
          │
          ▼
   Return result to Employee Runtime
```

### Event Types

```
tool.registered
tool.updated
tool.enabled
tool.disabled
tool.invoked
tool.denied
tool.timeout
tool.policy_updated
```

## Dependencies

```
 呼叫方                              提供方
 ┌────────────────┐                 ┌────────────────┐
 │ Employee Runtime│──invoke()──→   │                │
 │ (AI 員工執行時) │                │  Tool Gateway  │
 └────────────────┘                │  (policy +     │
                                   │   execution)   │
 ┌────────────────┐                │                │
 │ Skill Registry │──tool_bindings→│  Tool Registry │
 │ (MC-005)       │                │  (tool table)  │
 └────────────────┘                └───────┬────────┘
                                           │
                    ┌──────────────────────┼──────────────┐
                    │ audit.log()          │ PII mask     │
                    ▼                      ▼              ▼
         ┌────────────────┐    ┌──────────────┐   ┌──────────┐
         │ Audit Service  │    │ PII Boundary │   │ External │
         │ (MC-001)       │    │ Filter       │   │ APIs     │
         └────────────────┘    └──────────────┘   └──────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| `tool` + `tool_invocation` + `tool_policy` table | 動態 policy engine（OPA / Cedar） |
| ToolRegistryService（CRUD） | Tool 健康度監控 dashboard |
| ToolGateway（policy -> audit -> PII -> execute -> log） | 非同步 tool 呼叫（Phase 1 全同步） |
| YAML policy 規則（3 級 risk_tier） | 動態 rate limit 調整 |
| Rate limiting（fixed RPM per tool） | Tool marketplace / 第三方 tool 接入 |
| 3 個內建 tools：`search_knowledge`, `get_business_hours`, `handoff_to_human` | 自訂 tool 註冊 UI（Phase 1 用 API / 手動） |
| 每次呼叫 → `audit.log()` + `tool_invocation` record | 跨 tenant tool 共享 |

### Phase 1 內建 Tools

| Tool slug | Type | Risk | 說明 |
|---|---|---|---|
| `search_knowledge` | internal | safe | 搜尋 Knowledge Cards（RAG） |
| `get_business_hours` | internal | safe | 查詢營業時間 |
| `handoff_to_human` | internal | caution | 轉接真人客服 |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
3 built-in tools         10-30 tools                    100+ tools
──────────────────────────────────────────────────────────────────
YAML policy             → OPA / Cedar engine          → policy-as-code + version control
同步呼叫                → async queue (heavy tools)    → tool orchestration DAG
固定 rate limit         → adaptive rate limit          → per-tenant quota pool
手動註冊                → tool registration UI         → tool marketplace
PII mask in-process     → dedicated PII service        → streaming PII filter
單一 invocation table   → partition by month           → ClickHouse for analytics
```
