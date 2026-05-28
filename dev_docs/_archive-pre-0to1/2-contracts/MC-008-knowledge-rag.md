---
id: MC-008
title: "Module Contract — Knowledge (RAG)"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 90eaacb470567a3bf631af423e5dbf1ad8053a47
sync-source: doc
source-paths:
  - src/knowledge/
related: [SAD-v0.1, ADR-0001, ADR-0005, MC-001, MC-009, domain-model]
---

# Knowledge (RAG) — One-Page Module Contract

> **Plane**: Data | **Priority**: #2 (Employee Runtime 依賴它做檢索) | **Phase 1 必做**

## Purpose

將客戶的原始資料（FAQ、政策、產品規格、SOP、風控規則）轉化為結構化的 Knowledge Cards，並透過向量檢索在對話時提供最相關的知識片段。這是 COMPILER 1（Data -> Knowledge）的技術實現 — 沒有可靠的知識檢索，AI 員工只能幻覺。

## Responsibilities

| 做 | 不做 |
|---|---|
| 接收客戶上傳的原始文件，執行 chunking + embedding | 管理對話歷史（-> Conversation Engine） |
| 將 chunks 存為 Knowledge Cards + pgvector 向量 | 決定 AI 員工要不要使用某張卡片（-> Employee Runtime） |
| 提供語意檢索 API：給定 query，回傳 top-K 相關卡片 | 生成回覆（-> Employee Runtime + LLM） |
| 管理 Knowledge Card 生命週期（draft -> approved -> archived） | 全文搜尋（Phase 1 不做） |
| Knowledge Card 版本追蹤（編輯後 version +1，status 回 draft） | 自動從外部網站爬取知識（Phase 2） |
| 每次 ingest / approve / archive 發 audit event | 跨租戶知識共享 |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | pgvector (1024-dim) 做向量檢索，不用獨立向量 DB | :green_circle: | Phase 1 知識量 < 10K cards，PG 足夠；省一個 infra 元件 | Cards > 100K 且 p95 檢索 > 200ms -> :yellow_circle: Qdrant / Weaviate |
| D2 | Embedding 用 Anthropic Voyage / OpenAI text-embedding-3-small（1024-dim） | :green_circle: | 便宜、品質夠；透過 EmbeddingClient 抽象，可換模型 | 需要多語言 embedding 或本地模型 -> 換 multilingual-e5 |
| D3 | 5 種 Knowledge Card 類型（FAQ, Policy, Product, Procedure, Risk） | :green_circle: | 覆蓋 Phase 1 客服場景；type 欄位可擴展 | 新增垂直場景需要新類型 -> 加 enum 值 |
| D4 | 整張 card body 做單一 embedding（不拆 chunk） | :yellow_circle: | Phase 1 卡片短（< 2000 字），單一 embedding 夠用 | 卡片平均 > 3000 字 -> :yellow_circle: 改為 chunk-level embedding |
| D5 | approved 狀態才進檢索索引；draft/archived 不被檢索 | :green_circle: | 防止未審核或過期知識被 AI 引用 | 即時生效需求 -> 加 auto-approve 白名單 |
| D6 | 檢索時 top-K=5，用 cosine similarity + score threshold 0.7 | :yellow_circle: | 經驗預設值；需 pilot 調參 | Pilot 反饋 recall 不足 -> 調 K=10 或降 threshold |

## Data Model

```sql
-- knowledge_card 已在 db-schema.md 定義，此處補充 ingestion 追蹤

CREATE TABLE knowledge_card (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    card_type       TEXT NOT NULL CHECK (card_type IN ('faq', 'policy', 'product', 'procedure', 'risk')),
    title           TEXT NOT NULL,
    body_markdown   TEXT NOT NULL,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    source_url      TEXT,                                -- 原始出處
    source_file_ref TEXT,                                -- S3 path to original uploaded file
    version         INT NOT NULL DEFAULT 1,
    status          TEXT NOT NULL CHECK (status IN ('draft', 'approved', 'archived')),
    approved_by     TEXT,
    approved_at     TIMESTAMPTZ,
    valid_from      TIMESTAMPTZ,
    valid_until     TIMESTAMPTZ,
    embedding       vector(1024),                        -- pgvector
    embedding_model TEXT,                                 -- e.g. 'voyage-3-lite' for traceability
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes (defined in db-schema.md, repeated for completeness)
CREATE INDEX idx_kc_tenant_status ON knowledge_card(tenant_id, status);
CREATE INDEX idx_kc_tags ON knowledge_card USING GIN (tags);
CREATE INDEX idx_kc_embedding ON knowledge_card USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX idx_kc_type ON knowledge_card(tenant_id, card_type);

-- Ingestion job tracking
CREATE TABLE ingestion_job (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    source_file_ref TEXT NOT NULL,                        -- S3 path
    source_filename TEXT NOT NULL,                        -- original filename
    status          TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    cards_created   INT NOT NULL DEFAULT 0,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_ingestion_tenant ON ingestion_job(tenant_id, created_at DESC);
```

## Interface

### Internal Python API — KnowledgeService

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RetrievalResult:
    card_id: str
    card_type: str          # 'faq' | 'policy' | 'product' | 'procedure' | 'risk'
    title: str
    body_markdown: str
    score: float            # cosine similarity
    tags: list[str]

class KnowledgeService:
    """Knowledge Card lifecycle + retrieval."""

    # -- Ingestion (called by Worker job handler) --
    async def ingest_file(
        self,
        tenant_id: str,
        file_ref: str,          # S3 path to uploaded file
        filename: str,
    ) -> str:
        """Parse file -> create draft Knowledge Cards -> return ingestion_job.id."""
        ...

    # -- CRUD --
    async def create_card(
        self,
        tenant_id: str,
        card_type: str,
        title: str,
        body_markdown: str,
        tags: list[str] | None = None,
        source_url: str | None = None,
    ) -> str:
        """Create a draft Knowledge Card, compute embedding, return card.id."""
        ...

    async def update_card(
        self,
        card_id: str,
        title: str | None = None,
        body_markdown: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Update card -> version +1, status back to 'draft', recompute embedding."""
        ...

    async def approve_card(self, card_id: str, approved_by: str) -> None:
        """Set status='approved', record approver. Card now retrievable."""
        ...

    async def archive_card(self, card_id: str) -> None:
        """Set status='archived'. Card no longer retrievable."""
        ...

    # -- Retrieval (called by Employee Runtime during conversation) --
    async def retrieve(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        card_types: list[str] | None = None,  # filter by type
        tags: list[str] | None = None,         # filter by tag
    ) -> list[RetrievalResult]:
        """Embed query -> pgvector cosine search -> return ranked cards."""
        ...
```

### Internal Python API — EmbeddingClient (abstraction seam)

```python
class EmbeddingClient:
    """Thin abstraction over embedding provider. Phase 1 = single implementation."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return 1024-dim vectors for each text."""
        ...

    @property
    def model_name(self) -> str:
        """For traceability in knowledge_card.embedding_model."""
        ...
```

### REST API (Admin Console / Expert UI)

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/knowledge/cards` | GET | 分頁查詢（filter: tenant_id, status, card_type, tags） |
| `/api/v1/knowledge/cards` | POST | 建立 Knowledge Card（body: type, title, body_markdown, tags） |
| `/api/v1/knowledge/cards/{id}` | GET | 單筆詳情 |
| `/api/v1/knowledge/cards/{id}` | PATCH | 更新卡片（version +1, status -> draft, re-embed） |
| `/api/v1/knowledge/cards/{id}/approve` | POST | 審核通過 |
| `/api/v1/knowledge/cards/{id}/archive` | POST | 封存 |
| `/api/v1/knowledge/ingest` | POST | 上傳檔案觸發 ingestion（multipart/form-data -> enqueue Worker） |
| `/api/v1/knowledge/ingest/{job_id}` | GET | 查詢 ingestion 進度 |

### Worker Job — IngestKnowledgeCard

```
Redis queue: knowledge:ingest
Payload: { tenant_id, file_ref, filename, job_id }

Pipeline:
  1. Download file from S3
  2. Parse (PDF -> markdown, DOCX -> markdown, CSV -> row-per-card)
  3. Split into candidate Knowledge Cards (heuristic: heading-based for docs, row-based for CSV)
  4. For each candidate:
     a. Classify card_type (FAQ/Policy/Product/Procedure/Risk) via Haiku 4.5
     b. Compute embedding via EmbeddingClient
     c. INSERT knowledge_card (status='draft')
  5. Update ingestion_job.status = 'completed', cards_created = N
  6. Audit: knowledge.ingested { job_id, cards_created }
```

## Event Types

| Event | Trigger | Payload (key fields) |
|---|---|---|
| `knowledge.ingestion_started` | Ingestion job begins processing | `{ job_id, tenant_id, filename }` |
| `knowledge.ingestion_completed` | Ingestion job finishes successfully | `{ job_id, tenant_id, cards_created }` |
| `knowledge.ingestion_failed` | Ingestion job fails | `{ job_id, tenant_id, error_message }` |
| `knowledge.card_created` | New Knowledge Card inserted | `{ card_id, tenant_id, card_type, status }` |
| `knowledge.card_updated` | Knowledge Card body/tags edited | `{ card_id, tenant_id, version }` |
| `knowledge.card_approved` | Card status set to approved | `{ card_id, tenant_id, approved_by }` |
| `knowledge.card_archived` | Card status set to archived | `{ card_id, tenant_id }` |
| `knowledge.retrieval_executed` | Retrieval query executed | `{ tenant_id, query_hash, results_count, top_score }` |

## Cross-Module Interface Notes

- **Employee Runtime (MC-009)** calls `KnowledgeService.retrieve()` during message processing step 3. Parameters: `tenant_id` (`str`), `query` (`str` from user message), `card_types` (optional filter), `top_k` (default 5).

## Dependencies

```
 寫入方                              讀取方
 ┌────────────────┐                ┌────────────────┐
 │ Admin Console  │──┐  CRUD /    │ Employee Runtime│
 │ (Expert UI)    │  │  approve   │ (retrieve)      │
 └────────────────┘  │            └────────────────┘
                     ▼                     │
              ┌──────────────┐             │ retrieve()
              │ Knowledge    │ ◄───────────┘
              │ Service      │
              │ (pgvector)   │──→ Audit Service (log)
              └──────────────┘
                     ↑
              ┌──────────────┐
              │ Worker       │
              │ (IngestKB)   │──→ EmbeddingClient ──→ Anthropic/OpenAI
              └──────────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| 5 種 Knowledge Card 類型 | 自動網頁爬取 |
| pgvector cosine search (top-5) | Hybrid search (vector + BM25) |
| 手動建立 + 檔案上傳 ingestion | 自動 sync 從 Notion/Confluence |
| 單一 embedding model (1024-dim) | Multi-model ensemble |
| Card-level embedding（整張卡片一個向量） | Chunk-level embedding |
| Draft -> Approved -> Archived 生命週期 | 自動過期 / 自動重新 embed |
| PDF / DOCX / CSV 解析 | 影片 / 音檔轉文字 |
| REST API for CRUD + retrieve | GraphQL / streaming |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
< 10K cards              10K-100K cards               100K+ cards
──────────────────────────────────────────────────────────────────
pgvector ivfflat        -> pgvector HNSW             -> Qdrant / Weaviate
card-level embed        -> chunk-level embed         -> multi-modal (image+text)
single embed model      -> re-rank with cross-encoder-> ensemble + learned ranking
manual upload only      -> Notion/web sync           -> real-time sync pipeline
Haiku classification    -> fine-tuned classifier     -> custom NER + auto-tag
no versioned embedding  -> re-embed on model upgrade -> A/B test embedding models
cosine top-5            -> hybrid BM25 + vector      -> learned sparse + dense
```
