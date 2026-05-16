---
id: DB-SCHEMA
title: "Database Schema — AEOS Phase 1"
status: active
tier: 2-contracts
owner: HYBRID
last-reviewed: 2026-05-15
last-synced-with: 2b70986920c67fe4e9b80c76cefef998036ee957
sync-source: doc
related: [SAD-v0.1, MC-001, MC-002, MC-003, MC-004, MC-005, MC-006, MC-008, MC-009, MC-010, MC-011]
---

# AEOS Database Schema — Phase 1

> Regenerated from Module Contracts MC-001 through MC-011.
> MC is the source of truth; this file is a derived view.

## Conventions

| Convention | Rule |
|---|---|
| **Table names** | Singular (`tenant`, `skill`, `employee`, not plurals) |
| **Primary keys** | `UUID DEFAULT gen_random_uuid()` everywhere, except `audit_log.id` which is `BIGSERIAL` (append-only sequence) |
| **String enums** | `TEXT NOT NULL CHECK (column IN (...))` — no VARCHAR(N) anywhere |
| **Free-form strings** | Bare `TEXT` — no VARCHAR(N) anywhere |
| **Rates / percentages** | `NUMERIC(5,4)` (e.g. 0.0000 ~ 1.0000) |
| **Scores / costs** | `NUMERIC(10,4)` |
| **Timestamps** | `TIMESTAMPTZ` everywhere; standard columns: `created_at`, `updated_at`; domain-specific: `started_at`, `completed_at`, etc. |
| **Tenant isolation** | All tables carry `tenant_id` except: (1) `audit_log` has its own cross-tenant `tenant_id` column; (2) junction/child tables where tenant can be derived, but we prefer having `tenant_id` directly for query simplicity |
| **Event type naming** | `module.action` lowercase dotted format (e.g. `tenant.created`, `skill.deployed`) |
| **API paths** | `/api/v1/{resource}` (not stored in DB, noted for reference) |

## Tenant Isolation Strategy

Phase 1 deploys one VM per tenant (ADR-0004), but every table already carries `tenant_id` to enable Phase 2 multi-tenant migration. RLS is enabled on business tables. `audit_log` is cross-tenant by design — its `tenant_id` is a data column, not a filter enforced by RLS.

---

## 1. Shared Foundation

### 1.1 `tenant` — MC-004

```sql
CREATE TABLE tenant (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT         NOT NULL,
    slug                TEXT         NOT NULL UNIQUE,
    status              TEXT         NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'suspended', 'terminated', 'purged')),
    plan                TEXT         NOT NULL DEFAULT 'pilot'
                        CHECK (plan IN ('pilot', 'standard', 'premium')),
    config              JSONB        NOT NULL DEFAULT '{}',     -- LLM model, branding, channel settings
    contact_email       TEXT         NOT NULL,
    contract_start      DATE         NOT NULL,
    contract_end        DATE,                                   -- NULL = no end date
    data_retention_days INT          NOT NULL DEFAULT 90,       -- ADR-0005
    suspended_at        TIMESTAMPTZ,
    terminated_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE tenant ENABLE ROW LEVEL SECURITY;

CREATE UNIQUE INDEX idx_tenant_slug ON tenant (slug);
```

### 1.2 `api_key` — MC-004

```sql
CREATE TABLE api_key (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL REFERENCES tenant(id),
    name            TEXT         NOT NULL,                      -- 'admin-key', 'ci-deploy', etc.
    key_prefix      TEXT         NOT NULL,                      -- first 8 chars for identification (not secret)
    key_hash        TEXT         NOT NULL,                      -- bcrypt hash of full key
    scopes          TEXT[]       NOT NULL DEFAULT '{}',         -- 'admin', 'read', 'deploy', 'webhook'
    status          TEXT         NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'revoked')),
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,                                -- NULL = no expiry (manual rotation)
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);

CREATE INDEX idx_api_key_tenant  ON api_key (tenant_id, status);
CREATE INDEX idx_api_key_prefix  ON api_key (key_prefix) WHERE status = 'active';
```

---

## 2. Governance Plane

### 2.1 `audit_log` — MC-001

Append-only, cross-tenant by design. Uses `BIGSERIAL` PK (sequence is fine for append-only workloads).

```sql
CREATE TABLE audit_log (
    id              BIGSERIAL    PRIMARY KEY,
    tenant_id       UUID         NOT NULL,                      -- cross-tenant; no FK to tenant(id) by design
    actor_type      TEXT         NOT NULL
                    CHECK (actor_type IN ('ai_employee', 'admin', 'system')),
    actor_id        TEXT         NOT NULL,
    event_type      TEXT         NOT NULL,                      -- 'module.action' format: 'conversation.message_sent', 'skill.deployed', etc.
    resource_type   TEXT,                                       -- 'conversation', 'skill', 'tool', etc.
    resource_id     TEXT,                                       -- ID of the affected resource
    action          TEXT         NOT NULL
                    CHECK (action IN ('create', 'read', 'update', 'delete', 'invoke', 'deploy', 'rollback', 'approve', 'reject', 'deny', 'disable', 'enable')),
    outcome         TEXT         NOT NULL
                    CHECK (outcome IN ('success', 'failure', 'denied')),
    payload         JSONB,                                      -- event-specific data (may contain conversation content)
    ip_address      INET,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Append-only protection
CREATE OR REPLACE FUNCTION reject_audit_mutation() RETURNS TRIGGER AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_no_update
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation();

-- Phase 1 indexes (minimal set)
CREATE INDEX idx_audit_tenant_time  ON audit_log (tenant_id, created_at DESC);
CREATE INDEX idx_audit_event_type   ON audit_log (event_type, created_at DESC);
CREATE INDEX idx_audit_resource     ON audit_log (resource_type, resource_id);
```

### 2.2 Training Room tables (Phase 1 minimal) — MC-002

Phase 1 includes 5 of 7 MC-002 tables. Excluded: `test_set` (merged into `training_session` / `test_case` workflow), `quality_gate_result` (derivable from `test_run`).

#### 2.2.1 `training_session`

```sql
-- Tracks a single expert-AI co-training session for a skill version
CREATE TABLE training_session (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    skill_version_id    UUID         NOT NULL REFERENCES skill_version(id),
    started_by          TEXT         NOT NULL,                  -- domain expert user ID
    status              TEXT         NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'completed', 'abandoned')),
    notes               TEXT,
    started_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_training_session_tenant ON training_session (tenant_id, created_at DESC);
CREATE INDEX idx_training_session_skill  ON training_session (skill_version_id);
```

#### 2.2.2 `test_case`

```sql
-- A single test question within a training context (renamed from test_question for clarity)
CREATE TABLE test_case (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    skill_version_id    UUID         NOT NULL REFERENCES skill_version(id),
    seq                 INT          NOT NULL,
    category            TEXT         NOT NULL
                        CHECK (category IN ('happy_path', 'edge_case', 'red_team', 'adversarial')),
    attack_pattern      TEXT
                        CHECK (attack_pattern IS NULL OR attack_pattern IN (
                            'prompt_injection', 'pii_extraction', 'jailbreak',
                            'hallucination_bait', 'scope_escape', 'policy_bypass',
                            'emotional_manipulation'
                        )),
    input_message       TEXT         NOT NULL,
    expected_behavior   TEXT         NOT NULL,                  -- expected behavior description (not exact match)
    tags                TEXT[],
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (skill_version_id, seq)
);

CREATE INDEX idx_test_case_skill ON test_case (skill_version_id);
```

#### 2.2.3 `test_run`

```sql
-- Tracks execution of a test set against a skill version
CREATE TABLE test_run (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    skill_version_id    UUID         NOT NULL REFERENCES skill_version(id),
    run_type            TEXT         NOT NULL
                        CHECK (run_type IN ('standard', 'red_team', 'full')),
    status              TEXT         NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_questions     INT          NOT NULL,
    passed              INT          NOT NULL DEFAULT 0,
    failed              INT          NOT NULL DEFAULT 0,
    pass_rate           NUMERIC(5,4),                           -- 0.0000 ~ 1.0000
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    run_by              TEXT         NOT NULL,
    llm_model           TEXT         NOT NULL,                  -- which model was used
    total_tokens        INT          DEFAULT 0,
    total_cost_usd      NUMERIC(10,4) DEFAULT 0,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_test_run_skill ON test_run (skill_version_id, created_at DESC);
```

#### 2.2.4 `test_result`

```sql
-- Individual question result within a test run
CREATE TABLE test_result (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_id         UUID         NOT NULL REFERENCES test_run(id),
    test_case_id        UUID         NOT NULL REFERENCES test_case(id),
    actual_response     TEXT         NOT NULL,
    verdict             TEXT         NOT NULL
                        CHECK (verdict IN ('pass', 'fail', 'error')),
    failure_reason      TEXT,
    latency_ms          INT,
    tokens_used         INT,
    evaluator           TEXT         NOT NULL
                        CHECK (evaluator IN ('llm_judge', 'rule_based', 'human')),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_test_result_run ON test_result (test_run_id);
```

#### 2.2.5 `skill_approval`

```sql
-- Expert final approval record for a skill version
CREATE TABLE skill_approval (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    skill_version_id    UUID         NOT NULL UNIQUE,           -- one approval per version
    decision            TEXT         NOT NULL
                        CHECK (decision IN ('approved', 'rejected', 'revoked')),
    approved_by         TEXT         NOT NULL,
    rejection_reason    TEXT,
    gate_results        JSONB        NOT NULL,                  -- snapshot of quality gate state at approval time
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

### 2.3 Evaluation Service tables (Phase 1 minimal) — MC-003

Phase 1 includes 2 of 4 MC-003 tables. Excluded: `drift_alert` (Phase 2), `retraining_suggestion` (Phase 2).

#### 2.3.1 `evaluation_metric`

```sql
-- Hourly/daily aggregated quality metrics (batch-computed)
CREATE TABLE evaluation_metric (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL REFERENCES tenant(id),
    employee_id     UUID         NOT NULL REFERENCES employee(id),
    skill_id        UUID,                                       -- NULL = employee-level metric
    skill_version   TEXT,
    metric_name     TEXT         NOT NULL
                    CHECK (metric_name IN ('fcr', 'aht_seconds', 'csat', 'hallucination_rate',
                                           'sop_compliance', 'drift_score', 'escalation_rate')),
    metric_value    NUMERIC(10,4) NOT NULL,
    sample_size     INT          NOT NULL,                      -- conversations used to compute this metric
    period_start    TIMESTAMPTZ  NOT NULL,
    period_end      TIMESTAMPTZ  NOT NULL,
    granularity     TEXT         NOT NULL
                    CHECK (granularity IN ('hourly', 'daily', 'weekly')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eval_metric_tenant_time ON evaluation_metric (tenant_id, metric_name, period_start DESC);
CREATE INDEX idx_eval_metric_employee    ON evaluation_metric (employee_id, metric_name, period_start DESC);
CREATE INDEX idx_eval_metric_skill       ON evaluation_metric (skill_id, metric_name, period_start DESC);
```

#### 2.3.2 `failure_record`

```sql
-- Classified failure instances from production conversations
-- Failure Taxonomy: F1=hallucination, F2=sop_violation, F3=scope_escape,
--   F4=pii_leak, F5=tone_mismatch, F6=escalation_failure, F7=tool_misuse
CREATE TABLE failure_record (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    conversation_id     UUID         NOT NULL REFERENCES conversation(id),
    message_id          UUID,                                   -- optional: points to the specific problematic message
    employee_id         UUID         NOT NULL REFERENCES employee(id),
    skill_id            UUID,
    skill_version       TEXT,
    failure_category    TEXT         NOT NULL
                        CHECK (failure_category IN (
                            'hallucination', 'sop_violation', 'scope_escape',
                            'pii_leak', 'tone_mismatch', 'escalation_failure', 'tool_misuse'
                        )),
    severity            TEXT         NOT NULL
                        CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    description         TEXT         NOT NULL,
    evidence            JSONB,                                  -- e.g. expected vs actual, matched rule
    retraining_status   TEXT         NOT NULL DEFAULT 'pending'
                        CHECK (retraining_status IN ('pending', 'acknowledged', 'retraining', 'resolved', 'wont_fix')),
    acknowledged_by     TEXT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_failure_tenant_time ON failure_record (tenant_id, created_at DESC);
CREATE INDEX idx_failure_category    ON failure_record (failure_category, severity);
CREATE INDEX idx_failure_retraining  ON failure_record (retraining_status)
    WHERE retraining_status IN ('pending', 'retraining');
```

---

## 3. Control Plane

### 3.1 `skill` — MC-005

```sql
-- A versionable AI capability asset. Git is source of truth; DB is query mirror (ADR-0003).
-- tenant_id is NULLABLE: NULL = platform-level skill (Phase 2).
-- Phase 1: all skills have tenant_id set (per-tenant). Platform skills are Phase 2.
CREATE TABLE skill (
    id                          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID         REFERENCES tenant(id),  -- NULL = platform-level skill (Phase 2)
    slug                        TEXT         NOT NULL,               -- 'customer-service/faq-respond'
    vertical                    TEXT         NOT NULL,               -- 'customer-service'
    name                        TEXT         NOT NULL,
    description                 TEXT,
    owner                       TEXT,
    current_production_version  TEXT,                                -- semver, e.g. '1.2.0'
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_skill_tenant_slug ON skill (COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug);

-- RLS
ALTER TABLE skill ENABLE ROW LEVEL SECURITY;
```

### 3.2 `skill_version` — MC-005

```sql
CREATE TABLE skill_version (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id            UUID         NOT NULL REFERENCES skill(id),
    tenant_id           UUID         REFERENCES tenant(id),     -- redundant, for query speed; NULL follows skill.tenant_id
    version             TEXT         NOT NULL,                   -- semver
    status              TEXT         NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'testing', 'approved', 'production', 'deprecated')),
    prompt_template_ref TEXT         NOT NULL,                   -- git path: 'skills/cs/faq/prompt/v1.0.0.md'
    io_contract         JSONB,                                   -- input/output JSON Schema
    tool_bindings       TEXT[]       NOT NULL DEFAULT '{}',      -- tool slugs this skill can use
    policy_refs         TEXT[]       NOT NULL DEFAULT '{}',      -- policy IDs
    test_set_ref        TEXT,                                    -- git path to test cases
    test_pass_rate      NUMERIC(5,4),                            -- 0.0000 ~ 1.0000
    quality_gate_scores JSONB,                                   -- { "pass_rate": 0.85, "latency_p95_ms": 1200, ... }
    approved_by         TEXT,
    approved_at         TIMESTAMPTZ,
    deployed_at         TIMESTAMPTZ,
    deprecated_at       TIMESTAMPTZ,
    git_commit_sha      TEXT,                                    -- corresponding git commit (40 chars)
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (skill_id, version),
    CHECK (
        (status <> 'production') OR
        (approved_by IS NOT NULL AND approved_at IS NOT NULL AND test_pass_rate >= 0.80)
    )
);

CREATE INDEX idx_skill_version_skill_version ON skill_version (skill_id, version);
CREATE INDEX idx_skill_version_tenant_status ON skill_version (tenant_id, status);

-- RLS
ALTER TABLE skill_version ENABLE ROW LEVEL SECURITY;
```

### 3.3 `skill_binding` — MC-005

```sql
-- Which Employee uses which Skill version
CREATE TABLE skill_binding (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    employee_id         UUID         NOT NULL REFERENCES employee(id),
    skill_version_id    UUID         NOT NULL REFERENCES skill_version(id),
    priority            INT          NOT NULL DEFAULT 0,         -- ordering when employee has multiple skills
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_skill_binding_emp_sv ON skill_binding (employee_id, skill_version_id);

-- RLS
ALTER TABLE skill_binding ENABLE ROW LEVEL SECURITY;
```

### 3.4 `tool` — MC-006

```sql
-- External capability an AI Employee can invoke
CREATE TABLE tool (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         REFERENCES tenant(id),         -- NULL = system built-in tool
    slug            TEXT         NOT NULL,                       -- 'search_knowledge', 'lookup_order'
    name            TEXT         NOT NULL,
    description     TEXT         NOT NULL,                       -- LLM-facing description (function calling)
    tool_type       TEXT         NOT NULL
                    CHECK (tool_type IN ('internal', 'http_api', 'db_query', 'function')),
    endpoint        TEXT,                                        -- HTTP endpoint (when tool_type = 'http_api')
    auth_method     TEXT
                    CHECK (auth_method IS NULL OR auth_method IN ('none', 'api_key', 'bearer', 'basic', 'hmac')),
    auth_config     JSONB,                                       -- encrypted auth settings (key/token/secret)
    input_schema    JSONB        NOT NULL,                       -- JSON Schema for input
    output_schema   JSONB,                                       -- JSON Schema for output
    risk_tier       TEXT         NOT NULL DEFAULT 'safe'
                    CHECK (risk_tier IN ('safe', 'caution', 'restricted')),
    rate_limit_rpm  INT          NOT NULL DEFAULT 60,            -- requests per minute per tenant
    timeout_ms      INT          NOT NULL DEFAULT 5000,
    retry_policy    JSONB        NOT NULL DEFAULT '{"max_retries": 2, "backoff_ms": 500}',
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_tool_tenant_slug ON tool (COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug);
CREATE INDEX idx_tool_type ON tool (tool_type, enabled);
```

### 3.5 `tool_invocation` — MC-006

```sql
-- Every tool call record (append-only)
CREATE TABLE tool_invocation (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    conversation_id     UUID,                                    -- FK conversation(id)
    message_id          UUID,                                    -- FK message — note: message PK is composite (id, created_at)
    tool_id             UUID         NOT NULL REFERENCES tool(id),
    employee_id         UUID,                                    -- FK employee(id)
    skill_version_id    UUID,                                    -- which Skill triggered this call
    input               JSONB        NOT NULL,                   -- PII-masked
    output              JSONB,                                   -- PII-masked; NULL on error
    status              TEXT         NOT NULL
                        CHECK (status IN ('success', 'error', 'timeout', 'rejected_by_policy')),
    error_message       TEXT,
    latency_ms          INT,
    cost_token          INT,                                     -- LLM token cost (if applicable)
    policy_decision     JSONB,                                   -- { "allowed": true, "rule": "rule-003", "reason": "..." }
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_invocation_tenant_time ON tool_invocation (tenant_id, created_at DESC);
CREATE INDEX idx_tool_invocation_tool        ON tool_invocation (tool_id, created_at DESC);
CREATE INDEX idx_tool_invocation_conv        ON tool_invocation (conversation_id);
```

### 3.6 `tool_policy` — MC-006

```sql
-- YAML-driven static policy rules (Phase 1)
CREATE TABLE tool_policy (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         REFERENCES tenant(id),         -- NULL = global rule
    name            TEXT         NOT NULL,
    description     TEXT,
    rule_yaml       TEXT         NOT NULL,                       -- YAML rule content
    priority        INT          NOT NULL DEFAULT 0,             -- higher = evaluated first
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE tool_policy ENABLE ROW LEVEL SECURITY;
```

---

## 4. Data Plane

### 4.1 `employee` — MC-009

```sql
CREATE TABLE employee (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    name                TEXT         NOT NULL,
    role                TEXT         NOT NULL,                   -- 'customer_service' (Phase 1)
    status              TEXT         NOT NULL
                        CHECK (status IN ('draft', 'live', 'paused', 'retired')),
    version             TEXT         NOT NULL,                   -- semver snapshot
    persona_config      JSONB        NOT NULL DEFAULT '{}',     -- { tone, style, language, greeting }
    runtime_snapshot    JSONB        NOT NULL DEFAULT '{}',     -- frozen config: skill_bindings, tool_bindings, llm_config, etc.
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_employee_tenant  ON employee (tenant_id);
CREATE INDEX idx_employee_status  ON employee (tenant_id, status);
```

### 4.2 `knowledge_card` — MC-008

```sql
CREATE TABLE knowledge_card (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    card_type           TEXT         NOT NULL
                        CHECK (card_type IN ('faq', 'policy', 'product', 'procedure', 'risk')),
    title               TEXT         NOT NULL,
    body_markdown       TEXT         NOT NULL,
    tags                TEXT[]       NOT NULL DEFAULT '{}',
    source_url          TEXT,                                    -- original source URL
    source_file_ref     TEXT,                                    -- S3 path to original uploaded file
    version             INT          NOT NULL DEFAULT 1,
    status              TEXT         NOT NULL
                        CHECK (status IN ('draft', 'approved', 'archived')),
    approved_by         TEXT,
    approved_at         TIMESTAMPTZ,
    valid_from          TIMESTAMPTZ,
    valid_until         TIMESTAMPTZ,
    embedding           vector(1024),                            -- pgvector
    embedding_model     TEXT,                                    -- e.g. 'voyage-3-lite' for traceability
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kc_tenant_status ON knowledge_card (tenant_id, status);
CREATE INDEX idx_kc_tags          ON knowledge_card USING GIN (tags);
CREATE INDEX idx_kc_embedding     ON knowledge_card USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX idx_kc_type          ON knowledge_card (tenant_id, card_type);
```

### 4.3 `ingestion_job` — MC-008

```sql
-- Tracks file upload -> Knowledge Card creation pipeline
CREATE TABLE ingestion_job (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    source_file_ref     TEXT         NOT NULL,                   -- S3 path
    source_filename     TEXT         NOT NULL,                   -- original filename
    status              TEXT         NOT NULL
                        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    cards_created       INT          NOT NULL DEFAULT 0,
    error_message       TEXT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX idx_ingestion_tenant ON ingestion_job (tenant_id, created_at DESC);
```

### 4.4 `conversation` — MC-010

```sql
CREATE TABLE conversation (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    employee_id         UUID         NOT NULL REFERENCES employee(id),
    employee_version    TEXT         NOT NULL,                   -- snapshot version at conversation start
    end_user_pseudo_id  TEXT         NOT NULL,                   -- pseudonymized (ADR-0005)
    channel             TEXT         NOT NULL
                        CHECK (channel IN ('line', 'web_chat', 'whatsapp')),
    channel_user_id     TEXT         NOT NULL,                   -- channel-specific user ID (hashed)
    status              TEXT         NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'active', 'waiting_human', 'resolved', 'closed', 'archived')),
    started_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_message_at     TIMESTAMPTZ,                             -- for idle timeout detection
    ended_at            TIMESTAMPTZ,
    outcome             TEXT
                        CHECK (outcome IS NULL OR outcome IN ('resolved', 'handoff_human', 'abandoned', 'error')),
    summary             TEXT,                                    -- L2.5 session summary (generated on close)
    message_count       INT          NOT NULL DEFAULT 0,         -- denormalized counter
    metadata            JSONB        NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_conv_tenant_started ON conversation (tenant_id, started_at DESC);
CREATE INDEX idx_conv_employee       ON conversation (employee_id);
CREATE INDEX idx_conv_status         ON conversation (tenant_id, status);
CREATE INDEX idx_conv_end_user       ON conversation (tenant_id, end_user_pseudo_id);
CREATE INDEX idx_conv_idle           ON conversation (status, last_message_at)
    WHERE status IN ('open', 'active', 'waiting_human');
```

### 4.5 `message` — MC-010

Partitioned by month (append-only). Note: composite PK `(id, created_at)` due to partitioning.

```sql
CREATE TABLE message (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    conversation_id     UUID         NOT NULL,                   -- FK conversation(id) — not enforced across partitions
    seq                 INT          NOT NULL,
    role                TEXT         NOT NULL
                        CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content             TEXT         NOT NULL,                   -- pseudonymized
    content_raw_ref     UUID,                                    -- FK encrypted_pii(id) if PII vault is used
    skill_invocation_id UUID,
    tool_invocations    JSONB        NOT NULL DEFAULT '[]',
    token_count         INT,                                     -- for context window budget tracking
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at),
    UNIQUE (conversation_id, seq, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions via cron or migration (Phase 1 manual; Phase 2 automated)
-- Example:
-- CREATE TABLE message_2026_05 PARTITION OF message
--     FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```

### 4.6 `conversation_handoff` — MC-010

```sql
-- Tracks AI -> human -> AI handoff events
CREATE TABLE conversation_handoff (
    id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    from_conversation_id    UUID         NOT NULL REFERENCES conversation(id),
    to_conversation_id      UUID,                                -- NULL until Expert picks up
    reason                  TEXT         NOT NULL
                            CHECK (reason IN ('low_confidence', 'restricted_tool', 'user_request', 'policy_deny')),
    handoff_message         TEXT,                                -- context for Expert
    expert_id               TEXT,                                -- who picked up
    picked_up_at            TIMESTAMPTZ,
    resolved_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_handoff_pending ON conversation_handoff (created_at)
    WHERE to_conversation_id IS NULL;
```

### 4.7 `channel_binding` — MC-011

```sql
-- Maps an Employee to a channel (e.g. LINE OA)
CREATE TABLE channel_binding (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID         NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    channel         TEXT         NOT NULL
                    CHECK (channel IN ('line', 'web_chat', 'whatsapp')),
    config          JSONB        NOT NULL DEFAULT '{}',          -- encrypted channel credentials
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, channel)
);
```

### 4.8 `webhook_event` — MC-011

```sql
-- Dedup table to prevent reprocessing webhooks
CREATE TABLE webhook_event (
    id              TEXT         NOT NULL,                       -- e.g. LINE webhookEventId
    channel         TEXT         NOT NULL,
    received_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, channel)
);

-- Auto-purge events older than 7 days (dedup window)
CREATE INDEX idx_webhook_event_purge ON webhook_event (received_at);
```

### 4.9 `outbound_message` — MC-011

```sql
-- Tracks outbound message delivery (retry + audit)
CREATE TABLE outbound_message (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    conversation_id     UUID         NOT NULL REFERENCES conversation(id),
    message_id          UUID         NOT NULL,                   -- internal message that triggered this
    channel             TEXT         NOT NULL
                        CHECK (channel IN ('line', 'web_chat', 'whatsapp')),
    channel_user_id     TEXT         NOT NULL,                   -- target user (hashed)
    status              TEXT         NOT NULL
                        CHECK (status IN ('pending', 'sent', 'failed', 'retrying')),
    retry_count         INT          NOT NULL DEFAULT 0,
    error_message       TEXT,
    sent_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_outbound_pending ON outbound_message (status, created_at)
    WHERE status IN ('pending', 'retrying');
```

---

## 5. Table Ownership Cross-Reference

| Table | Owner MC | Plane |
|---|---|---|
| `tenant` | MC-004 | Shared Foundation |
| `api_key` | MC-004 | Shared Foundation |
| `audit_log` | MC-001 | Governance |
| `training_session` | MC-002 | Governance |
| `test_case` | MC-002 | Governance |
| `test_run` | MC-002 | Governance |
| `test_result` | MC-002 | Governance |
| `skill_approval` | MC-002 | Governance |
| `evaluation_metric` | MC-003 | Governance |
| `failure_record` | MC-003 | Governance |
| `skill` | MC-005 | Control |
| `skill_version` | MC-005 | Control |
| `skill_binding` | MC-005 | Control |
| `tool` | MC-006 | Control |
| `tool_invocation` | MC-006 | Control |
| `tool_policy` | MC-006 | Control |
| `employee` | MC-009 | Data |
| `knowledge_card` | MC-008 | Data |
| `ingestion_job` | MC-008 | Data |
| `conversation` | MC-010 | Data |
| `message` | MC-010 | Data |
| `conversation_handoff` | MC-010 | Data |
| `channel_binding` | MC-011 | Data |
| `webhook_event` | MC-011 | Data |
| `outbound_message` | MC-011 | Data |

**Total Phase 1 tables: 25**

---

## 6. Phase 2 Deferred Tables

The following tables are defined in their respective MCs but excluded from Phase 1:

### From MC-002 (Training Room)

| Table | Reason for deferral |
|---|---|
| `test_set` | Merged into `training_session` + `test_case` workflow; test cases are directly linked to `skill_version` |
| `quality_gate_result` | Can be derived from `test_run` pass rates + `skill_approval.gate_results` JSONB snapshot |

### From MC-003 (Evaluation Service)

| Table | Reason for deferral |
|---|---|
| `drift_alert` | Phase 2: requires embedding-based drift detection or sustained metric monitoring pipeline |
| `retraining_suggestion` | Phase 2: requires automated retraining loop integration with Training Room |

### Other Phase 2 tables (not yet in any MC)

| Table | Description |
|---|---|
| `encrypted_pii` | PII vault for raw data isolation (ADR-0005); Phase 1 uses pseudonymization at API boundary |
| `cost_attribution` | Per-conversation / per-tool cost tracking |
| `policy` / `policy_decision` | Dedicated policy engine tables (Phase 1 uses YAML in `tool_policy`) |

---

## 7. Migration Strategy

- Use **Alembic** (Python) for all schema migrations
- Each migration file contains exactly **one schema change** (single responsibility)
- Destructive migrations (drop column, rename) require an ADR and follow a **2-step process**: add new -> backfill -> drop old
- Monthly partitions for `message` are created via migration or cron job

## 8. References

- `domain-model.md` -- domain concepts
- `ADR-0003` -- Skill Git source of truth, DB is query mirror
- `ADR-0004` -- single-tenant deployment retains tenant_id
- `ADR-0005` -- PII retention policy
- `ADR-0007` -- multi-tenant isolation strategy
- `ADR-0009` -- Quality Gate pass rate threshold
- `ADR-0010` -- L2.5 Session Summary design
