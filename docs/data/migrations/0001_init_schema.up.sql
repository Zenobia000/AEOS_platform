-- 0001_init_schema.up.sql
-- care-copilot 薄切片 schema (W2 handoff 的 source of truth)。
-- 對應 docs/data/erd-care-copilot.md。所有業務表帶 tenant_id + RLS。
-- W1 (eval-only) 不接 DB；本 schema 於 W2 全鏈路上線時套用。

CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector (W2 RAG)
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

-- RLS 租戶解析：app 連線每 request 前先 `SET app.current_tenant = '<uuid>'`。
-- 缺值回 NULL → policy 比對失敗 → deny by default。
CREATE OR REPLACE FUNCTION current_tenant() RETURNS uuid
  LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid
$$;

-- ── Tables ─────────────────────────────────────────────────────────
CREATE TABLE tenant (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name               text NOT NULL,
  data_retention_days int  NOT NULL DEFAULT 90,   -- 隨 DPA
  compliance_profile text NOT NULL DEFAULT 'direct-sales',
  created_at         timestamptz NOT NULL DEFAULT now()
);

-- 活檔案 7 欄位 (結構化 contact，ADR-0003)
CREATE TABLE contact (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  display_name text NOT NULL,
  health_focus text,            -- 特種個資 (見 consent-and-dpa.md)
  family       text,
  work         text,
  interests    text,
  comm_pref    text,
  tags         jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- append-only 互動時間軸
CREATE TABLE interaction (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  contact_id uuid NOT NULL REFERENCES contact(id) ON DELETE CASCADE,
  at         timestamptz NOT NULL DEFAULT now(),
  kind       text NOT NULL,
  summary    text                -- PII
);

-- doc-RAG (pgvector)；W2 才填 embedding
CREATE TABLE knowledge_chunk (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  source     text NOT NULL,
  text       text NOT NULL,      -- 脫敏後
  embedding  vector(1024),       -- ASSUMPTION: Voyage voyage-3 (1024 維)；W2 選定 embedding 模型後須與其維度一致
  created_at timestamptz NOT NULL DEFAULT now()
);

-- 對話 + 草稿 + 稽核 + 訓練素材 (一表多用，消滅複製)
CREATE TABLE message (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  contact_id  uuid REFERENCES contact(id) ON DELETE SET NULL,
  role        text NOT NULL,             -- user / assistant
  text        text,                      -- 客戶訊息原文 (PII)
  draft_text  text,                      -- AI 草稿 (PII)
  decision    text,                      -- approve/edit/reject/needs_human/manual_override (人決定「什麼」)
  decided_by  text,                      -- 人類審核者；NULL = 未審
  sent_at     timestamptz,               -- 實際送達客戶時間；NULL = 未送 (與 decision 正交)
  compliance  text,                      -- green/yellow/red
  used_chunks jsonb NOT NULL DEFAULT '[]'::jsonb,
  model       text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- append-only、永久、去識別化 (不存原文) — ERD R2 C1/B-3
CREATE TABLE audit_event (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL,
  event_type  text NOT NULL,
  message_id  uuid,
  used_chunks jsonb NOT NULL DEFAULT '[]'::jsonb,
  model       text,
  decision    text,
  decided_by  text,
  at          timestamptz NOT NULL DEFAULT now()
);

-- ── Indexes ────────────────────────────────────────────────────────
CREATE INDEX idx_contact_tenant            ON contact(tenant_id);
CREATE INDEX idx_interaction_tenant_contact ON interaction(tenant_id, contact_id);
CREATE INDEX idx_knowledge_tenant          ON knowledge_chunk(tenant_id);
CREATE INDEX idx_message_tenant_contact    ON message(tenant_id, contact_id);
CREATE INDEX idx_audit_tenant_at           ON audit_event(tenant_id, at);
-- pgvector HNSW (W2 RAG)；維度由 column type 固定
CREATE INDEX idx_knowledge_embedding_hnsw  ON knowledge_chunk
  USING hnsw (embedding vector_cosine_ops);

-- ── RLS：鐵律「跨 tenant = 0」 ──────────────────────────────────────
-- ENABLE + FORCE (FORCE 讓 table owner 也受限，防 app 以 owner 連線繞過)。
ALTER TABLE contact         ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact         FORCE  ROW LEVEL SECURITY;
ALTER TABLE interaction     ENABLE ROW LEVEL SECURITY;
ALTER TABLE interaction     FORCE  ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunk ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunk FORCE  ROW LEVEL SECURITY;
ALTER TABLE message         ENABLE ROW LEVEL SECURITY;
ALTER TABLE message         FORCE  ROW LEVEL SECURITY;
ALTER TABLE audit_event     ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_event     FORCE  ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON contact
  USING (tenant_id = current_tenant()) WITH CHECK (tenant_id = current_tenant());
CREATE POLICY tenant_isolation ON interaction
  USING (tenant_id = current_tenant()) WITH CHECK (tenant_id = current_tenant());
CREATE POLICY tenant_isolation ON knowledge_chunk
  USING (tenant_id = current_tenant()) WITH CHECK (tenant_id = current_tenant());
CREATE POLICY tenant_isolation ON message
  USING (tenant_id = current_tenant()) WITH CHECK (tenant_id = current_tenant());
-- audit_event：租戶讀隔離 + append-only。
CREATE POLICY tenant_isolation ON audit_event
  USING (tenant_id = current_tenant()) WITH CHECK (tenant_id = current_tenant());
-- append-only 在 schema 層收口 (不外包給角色 migration)：policy 直接 deny 任何 UPDATE/DELETE，
-- 即使 app role 被誤授權也擋得住 (threat-model T-T-02 audit 不可竄改)。
CREATE POLICY audit_no_update ON audit_event FOR UPDATE USING (false);
CREATE POLICY audit_no_delete ON audit_event FOR DELETE USING (false);
