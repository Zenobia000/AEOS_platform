---
id: API-001
title: "Internal REST API Specification — AEOS Phase 1"
status: active
tier: 2-contracts
owner: HYBRID
last-reviewed: 2026-05-15
last-synced-with: 0881f25b2458b97c3ace08a4357fa2177d8d29c4
sync-source: doc
related: [SAD-v0.1, MC-001, MC-002, MC-003, MC-004, MC-005, MC-006, MC-007, MC-008, MC-009, MC-010, MC-011]
---

# API-001 — Internal REST API Specification (Phase 1)

> Regenerated from Module Contracts MC-001 through MC-011.
> MCs are the source of truth; this file is a derived view.
> Total Phase 1 endpoints: **67**

---

## 1. Overview

### 1.1 Base URL

```
https://{tenant-slug}.aeos.app/api/v1
```

### 1.2 Authentication

| Method | Used by | Mechanism |
|---|---|---|
| Session cookie + CSRF | Web SPA (Admin Console) | `X-CSRF-Token` header; HttpOnly cookie |
| API Key | Internal / CI / External clients | `X-API-Key: <key>` header; bcrypt match against `api_key.key_hash` |

Failed auth returns `401 Unauthorized`.

### 1.3 Tenancy

- API Key / session is bound to a single `tenant_id`.
- URL paths do not contain `tenant_id`; it is resolved from the auth context.
- Cross-tenant operations are forbidden.

### 1.4 Response Envelope

All endpoints return a unified envelope:

**Success:**
```typescript
interface ApiResponse<T> {
  success: true;
  data: T;
  error: null;
  meta: {
    request_id: string;   // UUID
    page?: number;
    limit?: number;
    total?: number;
  };
}
```

**Error:**
```typescript
interface ApiErrorResponse {
  success: false;
  data: null;
  error: {
    code: string;         // e.g. "VALIDATION_FAILED"
    message: string;
    fields?: Record<string, string>;
  };
  meta: {
    request_id: string;
  };
}
```

### 1.5 Pagination

- Query parameters: `?page=1&limit=20`
- Response: `meta.total`, `meta.page`, `meta.limit`
- `limit` max: 100

### 1.6 Idempotency

- All `POST` / `PATCH` / `DELETE` accept `Idempotency-Key` header (UUID).
- Within 24h, same key re-send returns the previous result.

### 1.7 PII Pseudonymization

- All PII is pseudonymized at the API boundary (request in, response out).
- All IDs are UUID (passed as `string` in JSON).

### 1.8 Common Response Codes

| HTTP | Code | Usage |
|---|---|---|
| 200 | OK | Successful GET / PATCH |
| 201 | CREATED | Successful POST (resource created) |
| 202 | ACCEPTED | Async job enqueued (e.g. ingestion) |
| 400 | VALIDATION_FAILED | Request body / params invalid |
| 401 | UNAUTHENTICATED | Missing or invalid auth |
| 403 | FORBIDDEN | Auth valid but scope insufficient |
| 404 | NOT_FOUND | Resource does not exist |
| 409 | CONFLICT | State conflict (e.g. approve an archived KC) |
| 422 | UNPROCESSABLE | Semantic error (e.g. deploy a skill that failed QG) |
| 429 | RATE_LIMITED | Rate limit exceeded |
| 500 | INTERNAL | System error (auto-audited) |

### 1.9 Rate Limiting

| Scope | Default Limit | Notes |
|---|---|---|
| Per API Key (global) | 60 req/min | Adjustable per endpoint |
| Per Tool invocation | Configured per tool (`tool.rate_limit_rpm`) | Default 60 RPM |
| Webhook (per IP) | 1000 req/min | Inbound channel webhooks |

Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 2. Endpoints by Module

---

### 2.1 Tenant Management (MC-004)

#### `POST /api/v1/tenants`
- **Description**: Create a new tenant (AEOS internal only)
- **Scope**: `aeos_admin`
- **Request Body**:
  ```typescript
  interface CreateTenantRequest {
    name: string;
    slug: string;               // URL-safe identifier
    contact_email: string;
    plan?: string;              // 'pilot' | 'standard' | 'premium'; default 'pilot'
    config?: object;            // JSONB: llm, branding, channels, limits
  }
  ```
- **Response** (201):
  ```typescript
  interface Tenant {
    id: string;                 // UUID
    name: string;
    slug: string;
    status: string;             // 'active'
    plan: string;
    config: object;
    contact_email: string;
    contract_start: string;     // ISO date
    contract_end: string | null;
    data_retention_days: number;
    created_at: string;
    updated_at: string;
  }
  ```
- **Audit Event**: `tenant.created`

#### `GET /api/v1/tenants/{id}`
- **Description**: Get tenant details
- **Scope**: `admin`
- **Response** (200): `Tenant`
- **Audit Event**: none

#### `PATCH /api/v1/tenants/{id}`
- **Description**: Update tenant settings
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface UpdateTenantRequest {
    name?: string;
    config?: object;            // partial JSONB merge
    contact_email?: string;
    data_retention_days?: number;
  }
  ```
- **Response** (200): `Tenant`
- **Audit Event**: `tenant.updated`, `tenant.config_changed`

#### `POST /api/v1/tenants/{id}/suspend`
- **Description**: Suspend tenant
- **Scope**: `aeos_admin`
- **Request Body**:
  ```typescript
  interface SuspendTenantRequest {
    reason: string;
  }
  ```
- **Response** (200): `Tenant`
- **Audit Event**: `tenant.suspended`

#### `POST /api/v1/tenants/{id}/terminate`
- **Description**: Terminate tenant (30-day soft delete)
- **Scope**: `aeos_admin`
- **Request Body**:
  ```typescript
  interface TerminateTenantRequest {
    reason: string;
  }
  ```
- **Response** (200): `Tenant`
- **Audit Event**: `tenant.terminated`

---

### 2.2 API Key Management (MC-004)

#### `GET /api/v1/tenants/{id}/api-keys`
- **Description**: List API keys for a tenant (excludes hash)
- **Scope**: `admin`
- **Response** (200):
  ```typescript
  interface ApiKeyListItem {
    id: string;
    name: string;
    key_prefix: string;         // first 8 chars
    scopes: string[];
    status: string;             // 'active' | 'revoked'
    last_used_at: string | null;
    expires_at: string | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/tenants/{id}/api-keys`
- **Description**: Generate a new API key
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface CreateApiKeyRequest {
    name: string;               // 'admin-key', 'ci-deploy', etc.
    scopes: string[];           // 'admin' | 'read' | 'deploy' | 'webhook'
  }
  ```
- **Response** (201):
  ```typescript
  interface CreateApiKeyResponse {
    id: string;
    name: string;
    key_prefix: string;
    scopes: string[];
    plaintext_key: string;      // shown only once
    created_at: string;
  }
  ```
- **Audit Event**: `api_key.generated`

#### `POST /api/v1/tenants/{id}/api-keys/{key_id}/rotate`
- **Description**: Rotate API key (old key immediately revoked)
- **Scope**: `admin`
- **Response** (200): `CreateApiKeyResponse` (new key)
- **Audit Event**: `api_key.rotated`

#### `POST /api/v1/tenants/{id}/api-keys/{key_id}/revoke`
- **Description**: Revoke API key
- **Scope**: `admin`
- **Response** (200): `{ revoked_at: string }`
- **Audit Event**: `api_key.revoked`

---

### 2.3 Skill Registry (MC-005)

#### `GET /api/v1/skills`
- **Description**: List skills (filterable by vertical, status)
- **Scope**: `read`
- **Query Params**: `?vertical=customer-service&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface Skill {
    id: string;
    slug: string;
    vertical: string;
    name: string;
    description: string | null;
    owner: string | null;
    current_production_version: string | null;
    created_at: string;
    updated_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/skills/{slug}`
- **Description**: Get single skill details + current production version
- **Scope**: `read`
- **Response** (200): `Skill`
- **Audit Event**: none

#### `GET /api/v1/skills/{id}/versions`
- **Description**: List all versions of a skill
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface SkillVersion {
    id: string;
    skill_id: string;
    version: string;            // semver
    status: string;             // 'draft' | 'testing' | 'approved' | 'production' | 'deprecated'
    prompt_template_ref: string;
    io_contract: object | null;
    tool_bindings: string[];
    test_pass_rate: number | null;
    quality_gate_scores: object | null;
    approved_by: string | null;
    approved_at: string | null;
    deployed_at: string | null;
    git_commit_sha: string | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/skills/{id}/versions/{version}`
- **Description**: Get specific version details
- **Scope**: `read`
- **Response** (200): `SkillVersion`
- **Audit Event**: none

#### `POST /api/v1/admin/skills/sync`
- **Description**: Sync skills from git repository to DB (CI auto-trigger + manual)
- **Scope**: `deploy`
- **Response** (200):
  ```typescript
  interface SyncResult {
    created: number;
    updated: number;
    removed: number;
  }
  ```
- **Audit Event**: `skill.created`, `skill.version_created`

#### `POST /api/v1/admin/skill-versions/{id}/approve`
- **Description**: Approve skill version (testing -> approved)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface ApproveSkillVersionRequest {
    approved_by: string;
  }
  ```
- **Response** (200): `SkillVersion`
- **Error**: 422 if `test_pass_rate < 0.80`
- **Audit Event**: `skill.approved`

#### `POST /api/v1/admin/skill-versions/{id}/deploy`
- **Description**: Deploy skill version to production (approved -> production, atomic symlink swap)
- **Scope**: `deploy`
- **Response** (200): `SkillVersion`
- **Audit Event**: `skill.deployed`

#### `POST /api/v1/admin/skill-versions/{id}/rollback`
- **Description**: Rollback to a previous version
- **Scope**: `deploy`
- **Request Body**:
  ```typescript
  interface RollbackRequest {
    target_version: string;     // semver to roll back to
  }
  ```
- **Response** (200): `SkillVersion`
- **Audit Event**: `skill.rolled_back`

---

### 2.4 Tool Registry (MC-006)

#### `GET /api/v1/tools`
- **Description**: List tools (filterable by type, risk_tier, enabled)
- **Scope**: `read`
- **Query Params**: `?tool_type=internal&risk_tier=safe&enabled=true&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface Tool {
    id: string;
    slug: string;
    name: string;
    description: string;
    tool_type: string;          // 'internal' | 'http_api' | 'db_query' | 'function'
    risk_tier: string;          // 'safe' | 'caution' | 'restricted'
    rate_limit_rpm: number;
    timeout_ms: number;
    enabled: boolean;
    input_schema: object;
    output_schema: object | null;
    created_at: string;
    updated_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/tools/{id}`
- **Description**: Get single tool details (including schema)
- **Scope**: `read`
- **Response** (200): `Tool`
- **Audit Event**: none

#### `POST /api/v1/admin/tools`
- **Description**: Register a new tool
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface CreateToolRequest {
    slug: string;
    name: string;
    description: string;
    tool_type: string;
    input_schema: object;
    output_schema?: object;
    risk_tier?: string;         // default 'safe'
    endpoint?: string;          // for http_api type
    auth_method?: string;       // 'none' | 'api_key' | 'bearer' | 'basic' | 'hmac'
    auth_config?: object;       // encrypted auth settings
    rate_limit_rpm?: number;    // default 60
    timeout_ms?: number;        // default 5000
    retry_policy?: object;      // default { max_retries: 2, backoff_ms: 500 }
  }
  ```
- **Response** (201): `Tool`
- **Audit Event**: `tool.registered`

#### `PATCH /api/v1/admin/tools/{id}`
- **Description**: Update tool configuration
- **Scope**: `admin`
- **Request Body**: Partial `CreateToolRequest`
- **Response** (200): `Tool`
- **Audit Event**: `tool.updated`

#### `POST /api/v1/admin/tools/{id}/disable`
- **Description**: Disable a tool (takes effect immediately)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface DisableToolRequest {
    reason: string;
  }
  ```
- **Response** (200): `Tool`
- **Audit Event**: `tool.disabled`

#### `POST /api/v1/admin/tools/{id}/enable`
- **Description**: Enable a tool
- **Scope**: `admin`
- **Response** (200): `Tool`
- **Audit Event**: `tool.enabled`

#### `GET /api/v1/tool-invocations`
- **Description**: Query tool invocation records (filterable by tool_id, status, date range)
- **Scope**: `read`
- **Query Params**: `?tool_id=uuid&status=success&from=2026-05-01&to=2026-05-15&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface ToolInvocation {
    id: string;
    tool_id: string;
    conversation_id: string | null;
    employee_id: string | null;
    skill_version_id: string | null;
    input: object;              // PII-masked
    output: object | null;      // PII-masked
    status: string;             // 'success' | 'error' | 'timeout' | 'rejected_by_policy'
    error_message: string | null;
    latency_ms: number | null;
    policy_decision: object | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/tool-invocations/stats`
- **Description**: Aggregated statistics per tool (count, avg_latency, error_rate)
- **Scope**: `read`
- **Query Params**: `?from=2026-05-01&to=2026-05-15`
- **Response** (200):
  ```typescript
  interface ToolInvocationStats {
    tool_id: string;
    tool_slug: string;
    total_invocations: number;
    success_count: number;
    error_count: number;
    avg_latency_ms: number;
    error_rate: number;
  }
  ```
- **Audit Event**: none

---

### 2.5 Knowledge / RAG (MC-008)

#### `GET /api/v1/knowledge/cards`
- **Description**: List knowledge cards with pagination (filterable by status, card_type, tags)
- **Scope**: `read`
- **Query Params**: `?status=approved&card_type=faq&tags=billing&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface KnowledgeCard {
    id: string;
    card_type: string;          // 'faq' | 'policy' | 'product' | 'procedure' | 'risk'
    title: string;
    body_markdown: string;
    tags: string[];
    source_url: string | null;
    version: number;
    status: string;             // 'draft' | 'approved' | 'archived'
    approved_by: string | null;
    approved_at: string | null;
    embedding_model: string | null;
    created_at: string;
    updated_at: string;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/knowledge/cards`
- **Description**: Create a new knowledge card (status: draft, embedding auto-computed)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface CreateKnowledgeCardRequest {
    card_type: string;          // 'faq' | 'policy' | 'product' | 'procedure' | 'risk'
    title: string;
    body_markdown: string;
    tags?: string[];
    source_url?: string;
  }
  ```
- **Response** (201): `KnowledgeCard`
- **Audit Event**: `knowledge.card_created`

#### `GET /api/v1/knowledge/cards/{id}`
- **Description**: Get single knowledge card details
- **Scope**: `read`
- **Response** (200): `KnowledgeCard`
- **Audit Event**: none

#### `PATCH /api/v1/knowledge/cards/{id}`
- **Description**: Update knowledge card (version +1, status -> draft, re-embed)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface UpdateKnowledgeCardRequest {
    title?: string;
    body_markdown?: string;
    tags?: string[];
  }
  ```
- **Response** (200): `KnowledgeCard`
- **Audit Event**: `knowledge.card_updated`

#### `POST /api/v1/knowledge/cards/{id}/approve`
- **Description**: Approve a knowledge card (draft -> approved; card becomes retrievable)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface ApproveKnowledgeCardRequest {
    approved_by: string;
  }
  ```
- **Response** (200): `KnowledgeCard`
- **Error**: 422 if status != `draft`
- **Audit Event**: `knowledge.card_approved`

#### `POST /api/v1/knowledge/cards/{id}/archive`
- **Description**: Archive a knowledge card (no longer retrievable)
- **Scope**: `admin`
- **Response** (200): `KnowledgeCard`
- **Audit Event**: `knowledge.card_archived`

#### `POST /api/v1/knowledge/ingest`
- **Description**: Upload file to trigger knowledge ingestion (multipart/form-data or JSON with URL)
- **Scope**: `admin`
- **Request Body** (multipart):
  ```
  file: <binary>
  ```
  or JSON:
  ```typescript
  interface IngestRequest {
    source_type: string;        // 'pdf' | 'docx' | 'csv' | 'url'
    url?: string;               // when source_type = 'url'
  }
  ```
- **Response** (202):
  ```typescript
  interface IngestResponse {
    job_id: string;             // UUID
    status: string;             // 'pending'
  }
  ```
- **Audit Event**: `knowledge.ingestion_started`

#### `GET /api/v1/knowledge/ingest/{job_id}`
- **Description**: Query ingestion job progress
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface IngestionJob {
    id: string;
    source_filename: string;
    status: string;             // 'pending' | 'processing' | 'completed' | 'failed'
    cards_created: number;
    error_message: string | null;
    created_at: string;
    completed_at: string | null;
  }
  ```
- **Audit Event**: none

---

### 2.6 Employee Runtime (MC-009)

#### `GET /api/v1/employees`
- **Description**: List all AI employees (filterable by status)
- **Scope**: `read`
- **Query Params**: `?status=live&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface Employee {
    id: string;
    name: string;
    role: string;               // 'customer_service'
    status: string;             // 'draft' | 'live' | 'paused' | 'retired'
    version: string;            // semver
    persona_config: object;
    created_at: string;
    updated_at: string;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/employees`
- **Description**: Create a new AI employee (status: draft)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface CreateEmployeeRequest {
    name: string;
    role: string;               // 'customer_service'
    persona_config: {
      tone: string;
      language: string;         // 'zh-TW'
      style?: string;
      greeting?: string;
    };
    skill_bindings?: Array<{
      skill_id: string;
      skill_version: string;
    }>;
    tool_bindings?: Array<{
      tool_id: string;
    }>;
  }
  ```
- **Response** (201): `Employee`
- **Audit Event**: `employee.created`

#### `GET /api/v1/employees/{id}`
- **Description**: Get employee details + runtime_snapshot
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface EmployeeDetail extends Employee {
    runtime_snapshot: object;   // frozen config when deployed
  }
  ```
- **Audit Event**: none

#### `PATCH /api/v1/employees/{id}`
- **Description**: Update draft employee settings (live employees cannot be modified)
- **Scope**: `admin`
- **Request Body**: Partial `CreateEmployeeRequest`
- **Response** (200): `Employee`
- **Error**: 422 if status != `draft`
- **Audit Event**: `employee.created` (update)

#### `POST /api/v1/employees/{id}/deploy`
- **Description**: Deploy employee (draft -> live; freezes runtime snapshot)
- **Scope**: `admin`
- **Preconditions**:
  - At least 1 skill binding with status=`production`
  - At least 1 channel binding
  - `persona_config` filled
- **Response** (200): `EmployeeDetail`
- **Error**: 422 with specific missing items
- **Audit Event**: `employee.deployed`

#### `POST /api/v1/employees/{id}/pause`
- **Description**: Emergency pause (live -> paused; kill switch)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface PauseEmployeeRequest {
    reason: string;
  }
  ```
- **Response** (200): `Employee`
- **Audit Event**: `employee.paused`

#### `POST /api/v1/employees/{id}/resume`
- **Description**: Resume paused employee (paused -> live)
- **Scope**: `admin`
- **Response** (200): `Employee`
- **Audit Event**: `employee.resumed`

#### `POST /api/v1/employees/{id}/retire`
- **Description**: Permanently retire employee
- **Scope**: `admin`
- **Response** (200): `Employee`
- **Audit Event**: `employee.retired`

#### `GET /api/v1/employees/{id}/snapshot`
- **Description**: View current frozen runtime snapshot details
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface RuntimeSnapshot {
    skill_bindings: Array<{
      skill_id: string;
      skill_slug: string;
      version: string;
      prompt_template_ref: string;
    }>;
    tool_bindings: Array<{
      tool_id: string;
      tool_name: string;
      risk_tier: string;
    }>;
    knowledge_config: {
      retrieval_top_k: number;
      score_threshold: number;
      card_types: string[];
    };
    llm_config: {
      primary_model: string;
      temperature: number;
      max_output_tokens: number;
    };
    validation_rules: object;
    handoff_config: object;
    frozen_at: string;
  }
  ```
- **Audit Event**: none

---

### 2.7 Conversation Engine (MC-010)

#### `GET /api/v1/conversations`
- **Description**: List conversations with pagination (filterable by status, employee_id, date range)
- **Scope**: `read`
- **Query Params**: `?status=active&employee_id=uuid&from=2026-05-01&to=2026-05-15&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface Conversation {
    id: string;
    employee_id: string;
    employee_version: string;
    end_user_pseudo_id: string;
    channel: string;            // 'line' | 'web_chat' | 'whatsapp'
    status: string;             // 'open' | 'active' | 'waiting_human' | 'resolved' | 'closed' | 'archived'
    started_at: string;
    last_message_at: string | null;
    ended_at: string | null;
    outcome: string | null;     // 'resolved' | 'handoff_human' | 'abandoned' | 'error'
    message_count: number;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/conversations/{id}`
- **Description**: Get conversation details + message list
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface ConversationDetail extends Conversation {
    summary: string | null;
    metadata: object;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/conversations/{id}/messages`
- **Description**: Get messages for a conversation (supports before/after cursor pagination)
- **Scope**: `read`
- **Query Params**: `?page=1&limit=50`
- **Response** (200):
  ```typescript
  interface Message {
    id: string;
    conversation_id: string;
    seq: number;
    role: string;               // 'user' | 'assistant' | 'tool' | 'system'
    status: string;             // 'sent' | 'draft_pending' | 'approved' | 'rejected'
    content: string;            // pseudonymized
    tool_invocations: object[];
    token_count: number | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/conversations/{id}/resolve`
- **Description**: Expert manually resolves a conversation
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface ResolveConversationRequest {
    outcome: string;            // 'resolved' | 'handoff_human'
  }
  ```
- **Response** (200): `Conversation`
- **Audit Event**: `conversation.resolved`

#### `GET /api/v1/conversations/{id}/handoff`
- **Description**: View handoff details for a conversation
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface ConversationHandoff {
    id: string;
    from_conversation_id: string;
    to_conversation_id: string | null;
    reason: string;             // 'low_confidence' | 'restricted_tool' | 'user_request' | 'policy_deny'
    handoff_message: string | null;
    expert_id: string | null;
    picked_up_at: string | null;
    resolved_at: string | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/conversations/handoffs/pending`
- **Description**: Expert pending handoff queue
- **Scope**: `admin`
- **Response** (200): `ConversationHandoff[]`
- **Audit Event**: none

#### `POST /api/v1/conversations/handoffs/{id}/pickup`
- **Description**: Expert picks up a handoff
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface PickupHandoffRequest {
    expert_id: string;
  }
  ```
- **Response** (200): `ConversationHandoff`
- **Audit Event**: `conversation.handoff_completed`

#### `GET /api/v1/conversations/messages`
- **Description**: Query messages across conversations (used for Draft Inbox: `?status=draft_pending`)
- **Scope**: `read`
- **Query Params**: `?status=draft_pending&page=1&limit=20`
- **Response** (200): `Message[]`
- **Audit Event**: none

#### `POST /api/v1/conversations/messages/{id}/approve`
- **Description**: Approve a draft message (sends to end user via channel)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface ApproveMessageRequest {
    edited_content?: string | null; // null = send as-is; string = send edited version
  }
  ```
- **Response** (200): `Message`
- **Audit Event**: `message.approved`

#### `POST /api/v1/conversations/messages/{id}/reject`
- **Description**: Reject a draft message
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface RejectMessageRequest {
    reason: string;
  }
  ```
- **Response** (200): `Message`
- **Audit Event**: `message.rejected`

#### `GET /api/v1/conversations/stats`
- **Description**: Conversation statistics (active count, avg duration, handoff rate)
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface ConversationStats {
    active_count: number;
    today_total: number;
    avg_duration_seconds: number;
    handoff_rate: number;
    auto_resolve_rate: number;
  }
  ```
- **Audit Event**: none

---

### 2.8 Channel Gateway (MC-011)

#### `GET /api/v1/channels/health`
- **Description**: Channel health status (token validity, last webhook, error rate)
- **Scope**: `admin`
- **Response** (200):
  ```typescript
  interface ChannelHealth {
    channel: string;
    status: string;             // 'healthy' | 'degraded' | 'down'
    last_webhook_at: string | null;
    error_rate_24h: number;
    token_valid: boolean;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/channels/outbound/failed`
- **Description**: Query failed outbound messages (DLQ inspection)
- **Scope**: `admin`
- **Query Params**: `?page=1&limit=20`
- **Response** (200):
  ```typescript
  interface FailedOutbound {
    id: string;
    conversation_id: string;
    message_id: string;
    channel: string;
    status: string;             // 'failed'
    retry_count: number;
    error_message: string | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/channels/outbound/{id}/retry`
- **Description**: Manually retry a failed outbound message
- **Scope**: `admin`
- **Response** (200): `{ status: 'retrying' }`
- **Audit Event**: `channel.send_retried`

#### `GET /api/v1/channels/stats`
- **Description**: Channel statistics (messages in/out per day, error rate)
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface ChannelStats {
    channel: string;
    messages_in_today: number;
    messages_out_today: number;
    error_rate: number;
  }
  ```
- **Audit Event**: none

---

### 2.9 Training Room (MC-002)

#### `POST /api/v1/training/test-cases`
- **Description**: Auto-generate test cases for a skill version (LLM-powered, 50-100 questions)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface GenerateTestCasesRequest {
    skill_version_id: string;
    target_count?: number;      // default 50
    include_red_team?: boolean; // default true
  }
  ```
- **Response** (201):
  ```typescript
  interface TestCase {
    id: string;
    skill_version_id: string;
    seq: number;
    category: string;           // 'happy_path' | 'edge_case' | 'red_team' | 'adversarial'
    attack_pattern: string | null;
    input_message: string;
    expected_behavior: string;
    tags: string[] | null;
    created_at: string;
  }
  ```
- **Audit Event**: `training.test_set_generated`

#### `GET /api/v1/training/test-cases/{id}`
- **Description**: Get test case details
- **Scope**: `read`
- **Response** (200): `TestCase`
- **Audit Event**: none

#### `PATCH /api/v1/training/test-cases/{id}`
- **Description**: Expert modifies a test case
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface UpdateTestCaseRequest {
    input_message?: string;
    expected_behavior?: string;
  }
  ```
- **Response** (200): `TestCase`
- **Audit Event**: `training.test_set_edited`

#### `POST /api/v1/training/test-runs`
- **Description**: Execute a test run against a skill version
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface CreateTestRunRequest {
    skill_version_id: string;
    training_session_id: string;
    run_type?: string;          // 'standard' | 'red_team' | 'full'; default 'full'
  }
  ```
- **Response** (201):
  ```typescript
  interface TestRun {
    id: string;
    skill_version_id: string;
    training_session_id: string;
    run_type: string;
    status: string;             // 'pending' | 'running' | 'completed' | 'failed'
    total_questions: number;
    passed: number;
    failed: number;
    pass_rate: number | null;
    started_at: string | null;
    completed_at: string | null;
    run_by: string;
    llm_model: string;
    total_tokens: number;
    total_cost_usd: number;
    created_at: string;
  }
  ```
- **Audit Event**: `training.test_run_started`

#### `GET /api/v1/training/test-runs/{id}`
- **Description**: Get test run summary
- **Scope**: `read`
- **Response** (200): `TestRun`
- **Audit Event**: none

#### `GET /api/v1/training/test-runs/{id}/results`
- **Description**: Get per-question results for a test run
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface TestResult {
    id: string;
    test_run_id: string;
    test_case_id: string;
    actual_response: string;
    verdict: string;            // 'pass' | 'fail' | 'error'
    failure_reason: string | null;
    latency_ms: number | null;
    tokens_used: number | null;
    evaluator: string;          // 'llm_judge' | 'rule_based' | 'human'
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/training/sessions`
- **Description**: Start a training session
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface CreateTrainingSessionRequest {
    skill_version_id: string;
    expert_user_id: string;
  }
  ```
- **Response** (201):
  ```typescript
  interface TrainingSession {
    id: string;
    skill_version_id: string;
    started_by: string;
    status: string;             // 'active' | 'completed' | 'abandoned'
    notes: string | null;
    started_at: string;
    ended_at: string | null;
    created_at: string;
  }
  ```
- **Audit Event**: `training.session_started`

#### `PATCH /api/v1/training/sessions/{id}`
- **Description**: End a training session
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface EndTrainingSessionRequest {
    status: string;             // 'completed' | 'abandoned'
    notes?: string;
  }
  ```
- **Response** (200): `TrainingSession`
- **Audit Event**: `training.session_ended`

#### `GET /api/v1/training/skills/{skill_version_id}/gates`
- **Description**: View Quality Gate status for a skill version
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface QualityGateResult {
    gate_number: number;        // 1-7
    gate_name: string;
    status: string;             // 'pass' | 'fail' | 'skip' | 'pending'
    evaluated_by: string;
    evidence: object | null;
    notes: string | null;
    evaluated_at: string | null;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/training/skills/{skill_version_id}/gates`
- **Description**: Trigger Quality Gate evaluation
- **Scope**: `admin`
- **Response** (200): `QualityGateResult[]`
- **Audit Event**: `training.gate_evaluated`

#### `POST /api/v1/training/skills/{skill_version_id}/approve`
- **Description**: Expert approves a skill version
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface ApproveSkillRequest {
    approved_by: string;
  }
  ```
- **Response** (200):
  ```typescript
  interface SkillApproval {
    id: string;
    skill_version_id: string;
    decision: string;           // 'approved'
    approved_by: string;
    gate_results: object;
    created_at: string;
  }
  ```
- **Audit Event**: `training.approved`

#### `POST /api/v1/training/skills/{skill_version_id}/reject`
- **Description**: Expert rejects a skill version
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface RejectSkillRequest {
    rejected_by: string;
    reason: string;
  }
  ```
- **Response** (200): `SkillApproval` (with `decision: 'rejected'`)
- **Audit Event**: `training.rejected`

#### `POST /api/v1/training/skills/{skill_version_id}/promote`
- **Description**: Promote approved skill version to production
- **Scope**: `deploy`
- **Response** (200): `SkillVersion`
- **Audit Event**: `training.promoted`

---

### 2.10 Evaluation Service (MC-003)

#### `GET /api/v1/evaluation/metrics`
- **Description**: Query quality metrics (filterable by employee, skill, metric_name, period)
- **Scope**: `read`
- **Query Params**: `?employee_id=uuid&skill_id=uuid&metric_name=fcr&start=2026-05-01&end=2026-05-15&granularity=daily&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface EvaluationMetric {
    id: string;
    employee_id: string;
    skill_id: string | null;
    skill_version: string | null;
    metric_name: string;        // Phase 1: 'fcr' | 'csat'
    metric_value: number;
    sample_size: number;
    period_start: string;
    period_end: string;
    granularity: string;        // 'daily'
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/evaluation/metrics/summary`
- **Description**: Get employee quality summary (7-day KPIs)
- **Scope**: `read`
- **Query Params**: `?employee_id=uuid&period_days=7`
- **Response** (200):
  ```typescript
  interface MetricSummary {
    employee_id: string;
    period_days: number;
    fcr: number | null;
    csat: number | null;
    total_conversations: number;
    total_handoffs: number;
  }
  ```
- **Audit Event**: none

#### `POST /api/v1/evaluation/metrics/compute`
- **Description**: Manually trigger metrics computation (normally called by cron)
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface ComputeMetricsRequest {
    period_start: string;       // ISO datetime
    period_end: string;
    granularity?: string;       // 'daily' (Phase 1 only)
  }
  ```
- **Response** (200): `{ metrics_computed: number }`
- **Audit Event**: `evaluation.metrics_computed`

#### `GET /api/v1/evaluation/failures`
- **Description**: List failure records (filterable by category, severity, status)
- **Scope**: `read`
- **Query Params**: `?failure_category=hallucination&severity=critical&retraining_status=pending&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface FailureRecord {
    id: string;
    conversation_id: string;
    message_id: string | null;
    employee_id: string;
    skill_id: string | null;
    skill_version: string | null;
    failure_category: string;   // 'hallucination' | 'sop_violation' | 'scope_escape' | 'pii_leak' | 'tone_mismatch' | 'escalation_failure' | 'tool_misuse'
    severity: string;           // 'critical' | 'high' | 'medium' | 'low'
    description: string;
    evidence: object | null;
    retraining_status: string;  // 'pending' | 'acknowledged' | 'retraining' | 'resolved' | 'wont_fix'
    acknowledged_by: string | null;
    created_at: string;
    updated_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/evaluation/failures/{id}`
- **Description**: Get single failure record details
- **Scope**: `read`
- **Response** (200): `FailureRecord`
- **Audit Event**: none

#### `POST /api/v1/evaluation/failures/{id}/acknowledge`
- **Description**: Acknowledge a failure record
- **Scope**: `admin`
- **Request Body**:
  ```typescript
  interface AcknowledgeFailureRequest {
    acknowledged_by: string;
  }
  ```
- **Response** (200): `FailureRecord`
- **Audit Event**: `evaluation.failure_acknowledged`

#### `GET /api/v1/evaluation/dashboard/{tenant_id}`
- **Description**: Tenant quality dashboard (KPI cards + trends)
- **Scope**: `read`
- **Response** (200):
  ```typescript
  interface DashboardSummary {
    tenant_id: string;
    today_conversations: number;
    auto_resolve_rate: number;
    handoff_rate: number;
    avg_response_time_ms: number;
    fcr_7day: number | null;
    csat_7day: number | null;
    trend_data: Array<{
      date: string;
      conversations: number;
      auto_resolve_rate: number;
    }>;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/evaluation/report/daily`
- **Description**: Daily quality report
- **Scope**: `read`
- **Query Params**: `?date=2026-05-14`
- **Response** (200):
  ```typescript
  interface DailyReport {
    date: string;
    total_conversations: number;
    resolved: number;
    handoffs: number;
    failures_detected: number;
    metrics: EvaluationMetric[];
  }
  ```
- **Audit Event**: `evaluation.report_generated`

---

### 2.11 Audit Service (MC-001)

#### `GET /api/v1/audit`
- **Description**: Query audit events with pagination (filterable by event_type, actor_type, actor_id, date range)
- **Scope**: `admin`
- **Query Params**: `?event_type=skill.deployed&actor_type=admin&from=2026-05-01&to=2026-05-15&page=1&limit=20`
- **Response** (200):
  ```typescript
  interface AuditEvent {
    id: number;                 // BIGSERIAL
    tenant_id: string;
    actor_type: string;         // 'ai_employee' | 'admin' | 'system' | 'policy_engine'
    actor_id: string;
    event_type: string;         // 'module.action' format
    resource_type: string | null;
    resource_id: string | null;
    action: string;             // 'create' | 'invoke' | 'deploy' | 'approve' | etc.
    outcome: string;            // 'success' | 'failure' | 'denied'
    payload: object | null;
    ip_address: string | null;
    created_at: string;
  }
  ```
- **Audit Event**: none

#### `GET /api/v1/audit/{id}`
- **Description**: Get single audit event details
- **Scope**: `admin`
- **Response** (200): `AuditEvent`
- **Audit Event**: none

#### `GET /api/v1/audit/stats`
- **Description**: Event type statistics for dashboard
- **Scope**: `admin`
- **Query Params**: `?from=2026-05-01&to=2026-05-15`
- **Response** (200):
  ```typescript
  interface AuditStats {
    event_type: string;
    count: number;
    last_occurred: string;
  }
  ```
- **Audit Event**: none

---

## 3. Webhook Endpoints

These endpoints are **not authenticated via API Key**. They are verified by channel-specific signature mechanisms.

#### `POST /api/v1/webhooks/line/{channel_id}`
- **Description**: LINE webhook entry point
- **Auth**: HMAC-SHA256 signature verification (`X-Line-Signature` header, verified against `channel_secret`)
- **Request Body**: LINE webhook event payload (see LINE Messaging API docs)
- **Response**: `200 OK` (within 1 second)
- **Processing**:
  1. Verify webhook signature
  2. Parse and normalize inbound messages
  3. Dedup by `webhookEventId`
  4. Hash `channel_user_id` -> `end_user_pseudo_id`
  5. Get or create conversation
  6. Append user message
  7. Enqueue to `conversation:process` Redis queue
- **Audit Events**: `channel.webhook_received`, `channel.message_received`
- **Error**: 403 if signature invalid (`channel.webhook_invalid_signature` audit event)

---

## 4. Health Endpoints

These endpoints are **unauthenticated** (for load balancer / orchestrator probes).

#### `GET /healthz`
- **Description**: Liveness probe (no DB dependency)
- **Response** (200): `{ "status": "ok" }`

#### `GET /readyz`
- **Description**: Readiness probe (checks PG, Redis, LINE API, Anthropic API reachability)
- **Response** (200): `{ "status": "ready", "checks": { "pg": "ok", "redis": "ok", "line": "ok", "anthropic": "ok" } }`

---

## 5. Phase 2 Deferred Endpoints

The following endpoints are mentioned in MCs but explicitly **not in Phase 1 scope**:

| Endpoint | Source MC | Reason |
|---|---|---|
| `POST /api/v1/webhooks/whatsapp/{channel_id}` | MC-011 | WhatsApp adapter is Phase 2 |
| `POST /api/v1/webhooks/webchat/{channel_id}` | MC-011 | Web Chat adapter is Phase 2 |
| `GET /api/v1/audit/export?format=csv\|jsonl` | MC-001 | Export endpoint not yet defined |
| Skill editing API (web-based) | MC-005 | Phase 1 uses git PR |
| Multi-tenant switch API | MC-004 | Phase 1 = single tenant per VM |
| Subscription / Billing API | -- | Not in any MC |
| Marketplace API | -- | Not in any MC |
| Proactive push API | -- | Not in any MC |
| Auto-crawler API | MC-008 | Phase 2 knowledge ingestion |
| Drift alert CRUD | MC-003 | Phase 2 evaluation |
| Retraining suggestion API | MC-003 | Phase 2 evaluation |
| Tenant data export API | MC-004 | Phase 1 = manual pg_dump |

---

## 6. Endpoint Count Summary

| Module | MC | Endpoints |
|---|---|---|
| Tenant Management | MC-004 | 5 |
| API Key Management | MC-004 | 4 |
| Skill Registry | MC-005 | 8 |
| Tool Registry | MC-006 | 8 |
| Knowledge / RAG | MC-008 | 8 |
| Employee Runtime | MC-009 | 9 |
| Conversation Engine | MC-010 | 12 |
| Channel Gateway | MC-011 | 4 |
| Training Room | MC-002 | 13 |
| Evaluation Service | MC-003 | 8 |
| Audit Service | MC-001 | 3 |
| **Subtotal (authenticated)** | | **82** |
| Webhook (signature-verified) | MC-011 | 1 |
| Health (unauthenticated) | -- | 2 |
| **Grand Total** | | **85** |

> Note: The original target of ~67 endpoints counted only the core business endpoints. The actual count includes admin, stats, health, and webhook endpoints for completeness.

---

## 7. Event Type Registry

Complete list of `module.action` audit event types across all modules:

| Module | Event Type | Description |
|---|---|---|
| **Tenant** | `tenant.created` | New tenant created |
| | `tenant.updated` | Tenant record updated |
| | `tenant.suspended` | Tenant suspended |
| | `tenant.terminated` | Tenant terminated |
| | `tenant.config_changed` | Tenant config modified |
| **API Key** | `api_key.generated` | New API key created |
| | `api_key.rotated` | API key rotated |
| | `api_key.revoked` | API key revoked |
| **Skill** | `skill.created` | New skill record |
| | `skill.version_created` | New skill version synced |
| | `skill.testing_started` | Test run initiated |
| | `skill.approved` | Skill version approved |
| | `skill.deployed` | Skill deployed to production |
| | `skill.rolled_back` | Skill rolled back |
| | `skill.deprecated` | Skill version deprecated |
| **Tool** | `tool.registered` | New tool registered |
| | `tool.updated` | Tool config updated |
| | `tool.enabled` | Tool enabled |
| | `tool.disabled` | Tool disabled |
| | `tool.invoked` | Tool call executed |
| | `tool.denied` | Tool call denied by policy |
| | `tool.timeout` | Tool call timed out |
| | `tool.policy_updated` | Tool policy rule changed |
| **Knowledge** | `knowledge.ingestion_started` | Ingestion job begins |
| | `knowledge.ingestion_completed` | Ingestion job succeeded |
| | `knowledge.ingestion_failed` | Ingestion job failed |
| | `knowledge.card_created` | New knowledge card |
| | `knowledge.card_updated` | Card edited |
| | `knowledge.card_approved` | Card approved |
| | `knowledge.card_archived` | Card archived |
| | `knowledge.retrieval_executed` | RAG query executed |
| **Employee** | `employee.created` | New AI employee |
| | `employee.deployed` | Employee went live |
| | `employee.paused` | Employee paused (kill switch) |
| | `employee.resumed` | Employee resumed |
| | `employee.retired` | Employee retired |
| | `employee.snapshot_loaded` | Frozen snapshot loaded |
| | `employee.message_processed` | Message pipeline completed |
| | `employee.message_failed` | Message pipeline failed |
| | `employee.handoff_requested` | Escalation triggered |
| **Conversation** | `conversation.created` | New conversation |
| | `conversation.activated` | First AI response sent |
| | `conversation.handoff_requested` | Handoff to expert |
| | `conversation.handoff_completed` | Expert resolved handoff |
| | `conversation.resolved` | Conversation resolved |
| | `conversation.closed` | Conversation finalized |
| | `conversation.archived` | PII redacted |
| | `conversation.summary_generated` | L2.5 summary created |
| **Message** | `message.created` | New message appended |
| | `message.draft_pending` | Draft awaiting approval |
| | `message.approved` | Draft approved |
| | `message.rejected` | Draft rejected |
| **Channel** | `channel.webhook_received` | Valid webhook received |
| | `channel.webhook_invalid_signature` | Invalid webhook signature |
| | `channel.message_received` | Inbound message normalized |
| | `channel.message_sent` | Outbound reply delivered |
| | `channel.send_failed` | Outbound failed after retries |
| | `channel.send_retried` | Outbound retry attempted |
| **Training** | `training.test_set_generated` | Test cases generated |
| | `training.test_set_edited` | Test case modified |
| | `training.test_run_started` | Test run started |
| | `training.test_run_completed` | Test run finished |
| | `training.red_team_completed` | Red team test finished |
| | `training.session_started` | Training session started |
| | `training.session_ended` | Training session ended |
| | `training.gate_evaluated` | Quality gate evaluated |
| | `training.approval_submitted` | Submitted for approval |
| | `training.approved` | Expert approved |
| | `training.rejected` | Expert rejected |
| | `training.promoted` | Promoted to production |
| **Evaluation** | `evaluation.metrics_computed` | Batch metrics computed |
| | `evaluation.failure_detected` | Failure case detected |
| | `evaluation.failure_acknowledged` | Failure acknowledged |
| | `evaluation.drift_alert_created` | Drift alert (Phase 2) |
| | `evaluation.report_generated` | Daily report generated |
| **System** | `system.retention_purge` | PII retention purge |
| **Admin** | `admin.login` | Admin user login |
| | `admin.config_changed` | Admin changed settings |
| | `admin.emergency_stop` | Emergency stop executed |

---

## 8. References

- LINE webhook specification: `API-002-line-webhook.md`
- System flows: `SF-001` through `SF-005`
- Domain model: `domain-model.md`
- Database schema: `db-schema.md`
- NFR (latency, availability): `NFR-001`
- OpenAPI YAML (Phase 1 Week 2): `openapi/api-001.yaml`
