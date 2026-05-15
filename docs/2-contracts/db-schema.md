---
name: db-schema
description: AEOS PostgreSQL schema v0 — 對應 domain-model.md，Phase 1 最小可用
status: active
type: contract
created: 2026-05-14
last-synced-with: efb63b3efff9a280e178f46124f39db8d0141b54
owner: CTO
tier: 2
---

# AEOS DB Schema v0（PostgreSQL）

> 對應 `domain-model.md`。Phase 1 = 單租戶單 VM，但 schema 已預留 `tenant_id` 以利 Phase 2 遷移。

## 設計原則

1. **All tables carry `tenant_id`**（除 `audit_event` 用 partition by tenant_id）— Phase 1 雖然單租戶，但欄位先有
2. **Append-only tables 用 partition by month**（`message`, `audit_event`, `tool_invocation`）
3. **Soft delete 預設不用** — Skill / KnowledgeCard 用 `status=archived` 表示停用
4. **所有時間欄位用 `timestamptz`**，存 UTC，App 層轉時區
5. **JSONB 用於 schema-less 部分**（metadata、io_contract、payload），但**核心關聯欄位**用一級 column
6. **Index policy**：
   - PK + FK + `tenant_id` 必有 index
   - 時間欄位查詢 → BRIN
   - JSONB 查詢 → GIN（只在已知查詢模式上建）

## Schema

```sql
-- ============================================================
-- Tenant & Identity
-- ============================================================

CREATE TABLE tenant (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL CHECK (status IN ('active', 'suspended', 'churned')),
    contract_start  DATE,
    data_retention_days INT NOT NULL DEFAULT 90,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE api_key (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    key_hash        TEXT NOT NULL UNIQUE,             -- bcrypt 或類似
    label           TEXT,
    scopes          TEXT[] NOT NULL DEFAULT '{}',
    last_used_at    TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_api_key_tenant ON api_key(tenant_id);

-- ============================================================
-- Employee
-- ============================================================

CREATE TABLE employee (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,                     -- 'customer_service' (Phase 1)
    status          TEXT NOT NULL CHECK (status IN ('draft', 'live', 'paused', 'retired')),
    version         TEXT NOT NULL,                     -- semver snapshot
    persona_config  JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_employee_tenant ON employee(tenant_id);

CREATE TABLE skill_binding (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    skill_id        UUID NOT NULL REFERENCES skill(id),
    skill_version   TEXT NOT NULL,                     -- semver, references skill_version.version
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, skill_id)
);
CREATE INDEX idx_skill_binding_employee ON skill_binding(employee_id);

CREATE TABLE channel_binding (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL CHECK (channel IN ('line', 'web_chat', 'whatsapp')),
    config          JSONB NOT NULL DEFAULT '{}',       -- e.g. LINE channel access token (encrypted)
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, channel)
);

-- ============================================================
-- Skill & SkillVersion (DB mirror; Git 是 source of truth, 見 ADR-0003)
-- ============================================================

CREATE TABLE skill (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            TEXT NOT NULL UNIQUE,              -- e.g. 'customer-service/faq-respond'
    vertical        TEXT NOT NULL,
    owner           TEXT,
    description     TEXT,
    current_production_version TEXT,                   -- semver, FK semantic to skill_version
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_skill_vertical ON skill(vertical);

CREATE TABLE skill_version (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id        UUID NOT NULL REFERENCES skill(id),
    version         TEXT NOT NULL,                     -- semver
    status          TEXT NOT NULL CHECK (status IN ('draft', 'approved', 'production', 'deprecated')),
    prompt_template_ref TEXT NOT NULL,                 -- git path
    io_contract     JSONB NOT NULL,                    -- input/output schema
    policy_refs     TEXT[] NOT NULL DEFAULT '{}',
    test_set_ref    TEXT NOT NULL,
    test_pass_rate  REAL,
    approved_by     TEXT,
    approved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (skill_id, version),
    CHECK (
      (status != 'production') OR
      (approved_by IS NOT NULL AND approved_at IS NOT NULL AND test_pass_rate >= 0.80)
    )
);
CREATE INDEX idx_skill_version_skill ON skill_version(skill_id);
CREATE INDEX idx_skill_version_status ON skill_version(status);

-- ============================================================
-- Knowledge
-- ============================================================

CREATE TABLE knowledge_card (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    title           TEXT NOT NULL,
    body_markdown   TEXT NOT NULL,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    source_url      TEXT,
    version         INT NOT NULL DEFAULT 1,
    status          TEXT NOT NULL CHECK (status IN ('draft', 'approved', 'archived')),
    approved_by     TEXT,
    approved_at     TIMESTAMPTZ,
    valid_from      TIMESTAMPTZ,
    valid_until     TIMESTAMPTZ,
    embedding       vector(1024),                      -- pgvector，Phase 1 用 small embedding model
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_kc_tenant_status ON knowledge_card(tenant_id, status);
CREATE INDEX idx_kc_tags ON knowledge_card USING GIN (tags);
CREATE INDEX idx_kc_embedding ON knowledge_card USING ivfflat (embedding vector_cosine_ops);

-- ============================================================
-- Tool
-- ============================================================

CREATE TABLE tool (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenant(id),        -- NULL = 系統內建
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    input_schema    JSONB NOT NULL,
    risk_tier       TEXT NOT NULL CHECK (risk_tier IN ('safe', 'caution', 'restricted')),
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);
CREATE INDEX idx_tool_tenant ON tool(tenant_id);

-- ============================================================
-- Conversation & Message
-- ============================================================

CREATE TABLE conversation (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    employee_id     UUID NOT NULL REFERENCES employee(id),
    employee_version TEXT NOT NULL,                    -- snapshot
    end_user_pseudo_id TEXT NOT NULL,                  -- pseudonymized
    channel         TEXT NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    outcome         TEXT CHECK (outcome IN ('resolved', 'handoff_human', 'abandoned', 'error')),
    metadata        JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_conv_tenant_started ON conversation(tenant_id, started_at DESC);
CREATE INDEX idx_conv_employee ON conversation(employee_id);

-- message partition by month
CREATE TABLE message (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    seq             INT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content         TEXT NOT NULL,                     -- pseudonymized
    content_raw_ref UUID,                              -- FK encrypted_pii.id
    skill_invocation_id UUID,
    tool_invocations JSONB NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at),
    UNIQUE (conversation_id, seq, created_at)
) PARTITION BY RANGE (created_at);
-- create monthly partitions via cron (Phase 1 manual; Phase 2 自動化)

-- ============================================================
-- PII Vault (隔離儲存原始 PII)
-- ============================================================

CREATE TABLE encrypted_pii (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    pii_type        TEXT NOT NULL CHECK (pii_type IN ('phone', 'national_id', 'email', 'credit_card', 'address')),
    ciphertext      BYTEA NOT NULL,                    -- AES-256-GCM
    nonce           BYTEA NOT NULL,
    purge_at        TIMESTAMPTZ NOT NULL,              -- 對應 retention policy
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_pii_purge ON encrypted_pii(purge_at);

-- ============================================================
-- ToolInvocation (append-only)
-- ============================================================

CREATE TABLE tool_invocation (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    conversation_id UUID NOT NULL,
    message_id      UUID NOT NULL,
    tool_id         UUID NOT NULL,
    input           JSONB NOT NULL,
    output          JSONB,
    status          TEXT NOT NULL CHECK (status IN ('success', 'error', 'rejected_by_policy')),
    latency_ms      INT,
    cost_token      INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- ============================================================
-- AuditEvent (append-only, NEVER UPDATE/DELETE, 永久保留)
-- ============================================================

CREATE TABLE audit_event (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    actor_type      TEXT NOT NULL CHECK (actor_type IN ('employee', 'user', 'system', 'policy_engine')),
    actor_id        TEXT NOT NULL,
    event_type      TEXT NOT NULL,                     -- e.g. 'llm.call', 'tool.invoke', 'policy.deny'
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE INDEX idx_audit_tenant_created ON audit_event(tenant_id, created_at DESC);
CREATE INDEX idx_audit_event_type ON audit_event(event_type);

-- Trigger: 拒絕 audit_event 的 UPDATE / DELETE
CREATE OR REPLACE FUNCTION audit_event_immutable() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_event is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_event_no_update BEFORE UPDATE ON audit_event
    FOR EACH ROW EXECUTE FUNCTION audit_event_immutable();

CREATE TRIGGER audit_event_no_delete BEFORE DELETE ON audit_event
    FOR EACH ROW EXECUTE FUNCTION audit_event_immutable();
```

## 不在 Phase 1 的 Table（明文 out of scope）

- `training_session`, `training_run` — Training Room（Phase 2）
- `eval_run`, `eval_metric` — Evaluation（Phase 2）
- `policy`, `policy_decision` — Policy Engine（Phase 2，Phase 1 用 YAML）
- `cost_attribution` — Cost Tracker（Phase 2）

## Migration 策略

- 用 Alembic（若 Python）或 node-pg-migrate（若 Node）
- 每個 migration ≤ 1 個 schema 變更（單一職責）
- DESTRUCTIVE migration（drop column / rename）需 ADR 並 2 步走（add new → backfill → drop old）

## 參考

- `domain-model.md` — 對應領域概念
- `ADR-0003` — Skill 為何 Git 是 source of truth，DB 只是 mirror
- `ADR-0004` — 單租戶部署為何仍保留 tenant_id
- `ADR-0005` — encrypted_pii 設計與 retention 政策
