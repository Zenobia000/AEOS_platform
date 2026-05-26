---
id: MC-005
title: "Module Contract — Skill Registry"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 2a5ff7daab4de9ec6268fc5bb23d3e1b4f386acf
sync-source: doc
source-paths:
  - src/control/skill_registry/
related: [SAD-v0.1, ADR-0003, ADR-0009, MC-001, MC-006, MC-007, domain-model]
---

# Skill Registry — One-Page Module Contract

> **Plane**: Control | **Priority**: #3 (Employee Runtime 依賴它載入 Skill) | **Phase 1 必做**

## Purpose

作為 AI 員工能力的 source of truth。Skill = YAML manifest + prompt template + tool bindings，儲存在 Git monorepo（ADR-0003）。Skill Registry 維護 Skill 的 metadata DB 鏡像（從 git sync），管理 Skill 的生命週期（draft -> testing -> approved -> production -> deprecated），並在 Employee Runtime 需要時提供 Skill 載入介面。這是「Skill as Asset」原則的技術基礎 -- 沒有版本化、測試化、可回滾的 Skill 管理，AI 員工的行為就不可治理。

## Responsibilities

| 做 | 不做 |
|---|---|
| 從 git `skills/` 目錄同步 Skill metadata 到 DB | 執行 Skill（→ Employee Runtime） |
| 維護 Skill + SkillVersion 的生命週期狀態機 | 管理 prompt 內容本身（→ git，prompt 是 Skill 的一部分） |
| 提供 Skill 查詢 / 載入 API | 執行 test set（→ Training Room / CI pipeline） |
| 記錄 Quality Gate 通過結果（test_pass_rate, approved_by） | 決定哪個 Employee 綁定哪個 Skill（→ Employee Runtime） |
| 觸發 atomic symlink swap 做 zero-downtime 部署（ADR-0009） | Tool 的 runtime 呼叫（→ Tool Registry / MC-006） |
| 提供版本比較 / rollback 入口 | Skill 的 A/B test 流量分配（→ Employee Runtime） |

> **Approve/Deploy ownership**: MC-002 (Training Room) owns the `testing -> approved` transition (runs QG, gets expert sign-off). MC-005 owns the `approved -> production` transition (deployment mechanics: symlink swap, version activation). The boundary is: Training Room says "this version is good"; Skill Registry says "this version is live".

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | Git 是 source of truth；DB 只是查詢鏡像（ADR-0003） | :green_circle: | 免費獲得 diff/blame/PR/review；Phase 1 < 50 Skill | Skill > 100 且 DB sync lag > 30s → :yellow_circle: event-driven sync |
| D2 | `POST /admin/skills/sync` 從 git 掃目錄 → upsert DB | :green_circle: | CI 部署時自動呼叫；手動可用；簡單可靠 | 需即時反映 git push → :yellow_circle: git webhook trigger |
| D3 | Atomic symlink swap 做 Skill 部署（ADR-0009） | :green_circle: | Zero-downtime；rollback = 切回舊 symlink | 多 VM 需同步 → :yellow_circle: 分散式部署 coordinator |
| D4 | SkillVersion 5 態生命週期（draft/testing/approved/production/deprecated） | :green_circle: | 與 Quality Gate 流程對齊；每態有明確 invariant | 需 canary / blue-green per skill → :yellow_circle: 加 canary 態 |
| D5 | Quality Gate：test_pass_rate >= 0.80 才能 approve → production | :green_circle: | 工程憲章明文要求；Phase 1 門檻保守 | 客戶要求更高 SLA → 上調至 0.90 + 加 latency/cost gate |

## Data Model

```sql
-- Skill = 一個 AI 能力的可版本化資產
CREATE TABLE skill (
    id                          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID         REFERENCES tenant(id),
                                -- NULLABLE: NULL = platform-level skill
                                -- Phase 1: all skills are tenant-scoped (tenant_id NOT NULL enforced at app layer)
                                -- Phase 2: platform-level skills have tenant_id = NULL
    slug                        TEXT         NOT NULL,          -- 'customer-service/faq-respond'
    vertical                    TEXT         NOT NULL,          -- 'customer-service'
    name                        TEXT         NOT NULL,          -- 人類可讀名稱
    description                 TEXT,
    owner                       TEXT,                           -- 負責人
    current_production_version  TEXT,                           -- semver, e.g. '1.2.0'
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_skill_tenant_slug ON skill (tenant_id, slug);

-- SkillVersion = 特定版本的 Skill 快照
CREATE TABLE skill_version (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id            UUID         NOT NULL REFERENCES skill(id),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),  -- 冗餘，加速查詢
    version             TEXT         NOT NULL,              -- semver
    status              TEXT         NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'testing', 'approved', 'production', 'deprecated')),
    prompt_template_ref TEXT         NOT NULL,              -- git path: 'skills/cs/faq/prompt/v1.0.0.md'
    io_contract         JSONB,                              -- input/output JSON Schema
    tool_bindings       TEXT[]       NOT NULL DEFAULT '{}', -- tool slugs this skill can use
    policy_refs         TEXT[]       NOT NULL DEFAULT '{}', -- policy IDs 引用
    test_set_ref        TEXT,                               -- git path to test cases
    test_pass_rate      NUMERIC(5,4),                       -- 0.0000-1.0000, last CI run
    quality_gate_scores JSONB,                              -- { "pass_rate": 0.85, "latency_p95_ms": 1200, "cost_per_turn_usd": 0.003 }
    approved_by         TEXT,
    approved_at         TIMESTAMPTZ,
    deployed_at         TIMESTAMPTZ,
    deprecated_at       TIMESTAMPTZ,
    git_commit_sha      TEXT,                               -- 對應 git commit (40 chars)
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_sv_skill_version ON skill_version (skill_id, version);
CREATE INDEX idx_sv_tenant_status ON skill_version (tenant_id, status);

-- Skill-Employee 綁定（哪個 Employee 用哪個 Skill 的哪個版本）
CREATE TABLE skill_binding (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID         NOT NULL REFERENCES tenant(id),
    employee_id         UUID         NOT NULL,            -- FK employees(id)
    skill_version_id    UUID         NOT NULL REFERENCES skill_version(id),
    priority            INT          NOT NULL DEFAULT 0,  -- 多 Skill 時的優先順序
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_sb_emp_skill ON skill_binding (employee_id, skill_version_id);

-- RLS
ALTER TABLE skill ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_binding ENABLE ROW LEVEL SECURITY;
```

## Interface

### Internal Python API — SkillRegistryService

```python
class SkillRegistryService:
    async def sync_from_git(self, tenant_id: str) -> SyncResult: ...
    # 掃 skills/ 目錄，upsert DB；回傳新增/更新/移除數量

    async def list_skills(
        self, tenant_id: str, vertical: str | None = None
    ) -> list[Skill]: ...

    async def get_skill(self, tenant_id: str, slug: str) -> Skill: ...

    async def get_version(
        self, skill_id: str, version: str
    ) -> SkillVersion: ...

    async def get_production_version(
        self, skill_id: str
    ) -> SkillVersion | None: ...

    async def load_prompt_template(
        self, skill_version: SkillVersion
    ) -> str: ...
    # 從 git path 讀取 prompt markdown 內容

    async def submit_test_result(
        self, version_id: str, pass_rate: float, scores: dict
    ) -> SkillVersion: ...
    # CI 回報測試結果；更新 quality_gate_scores

    async def approve_version(
        self, version_id: str, approved_by: str
    ) -> SkillVersion: ...
    # testing -> approved；需 test_pass_rate >= 0.80

    async def deploy_version(
        self, version_id: str
    ) -> SkillVersion: ...
    # approved -> production；執行 atomic symlink swap
    # 舊 production version -> deprecated

    async def rollback_skill(
        self, skill_id: str, target_version: str
    ) -> SkillVersion: ...
    # 將指定版本重新標記為 production；當前 production -> deprecated
```

### REST Endpoints

| Endpoint | Method | 用途 | Scope |
|---|---|---|---|
| `/api/v1/skills` | GET | 列出 Skill（filter: vertical, status） | `read` |
| `/api/v1/skills/{slug}` | GET | 單一 Skill 詳情 + 當前 production version | `read` |
| `/api/v1/skills/{id}/versions` | GET | 某 Skill 的所有版本 | `read` |
| `/api/v1/skills/{id}/versions/{version}` | GET | 特定版本詳情 | `read` |
| `/api/v1/admin/skills/sync` | POST | 從 git 重新同步（CI 自動 + 手動） | `deploy` |
| `/api/v1/admin/skill-versions/{id}/approve` | POST | 核准版本（testing -> approved） | `admin` |
| `/api/v1/admin/skill-versions/{id}/deploy` | POST | 部署到 production（approved -> production） | `deploy` |
| `/api/v1/admin/skill-versions/{id}/rollback` | POST | 回滾到指定版本 | `deploy` |

### SkillVersion 狀態機

```
       git push + CI sync
              │
              ▼
         ┌─────────┐
         │  draft   │
         └────┬─────┘
              │ CI trigger test run
              ▼
         ┌──────────┐
         │ testing   │
         └────┬──────┘
              │ test_pass_rate >= 0.80
              │ + CTO/Expert approve
              ▼
         ┌───────────┐
         │ approved   │
         └────┬───────┘
              │ deploy (atomic symlink swap)
              ▼
         ┌─────────────┐
         │ production   │ ← Frozen; immutable
         └────┬─────────┘
              │ new version deployed OR manual deprecate
              ▼
         ┌──────────────┐
         │ deprecated    │ ← 保留 30 天可 rollback
         └───────────────┘
```

### Git Sync 流程

```
CI deploy pipeline
    │
    ├─ 1. git pull latest
    ├─ 2. scan skills/ directory for skill.yaml files
    ├─ 3. POST /admin/skills/sync → upsert DB
    ├─ 4. for each new version:
    │      ├─ run test set (50 cases)
    │      ├─ POST test results → status: testing
    │      └─ if pass_rate >= 0.80 → ready for approve
    └─ 5. atomic symlink: /opt/aeos/skills/current → /opt/aeos/skills/v1.2.0/
```

### Event Types

```
skill.created
skill.version_created
skill.testing_started
skill.approved
skill.deployed
skill.rolled_back
skill.deprecated
```

## Dependencies

```
 寫入方                              讀取方
 ┌────────────────┐                 ┌────────────────┐
 │ Git Repo       │──sync──→        │ Employee Runtime│
 │ (skills/ dir)  │         ┌──────→│ (載入 Skill)    │
 │                │         │       └────────────────┘
 └────────────────┘         │
                            │       ┌────────────────┐
 ┌────────────────┐         │       │ Admin Console  │
 │ CI Pipeline    │──test──→│       │ (Skill 管理 UI) │
 │                │  result ├──────→└────────────────┘
 └────────────────┘         │
                     ┌──────┴──────┐
                     │Skill Registry│
                     │ (skill +    │──audit.log()──→ Audit Service
                     │  versions)   │                  (MC-001)
                     └──────┬──────┘
                            │ tool_bindings
                            ▼
                     ┌────────────────┐
                     │ Tool Registry  │
                     │ (MC-006)       │
                     └────────────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| `skill` + `skill_version` + `skill_binding` table | Skill Web 編輯 UI（Phase 1 用 git PR） |
| Git → DB sync (`/admin/skills/sync`) | Event-driven sync（git webhook → auto sync） |
| 5 態 lifecycle 狀態機 | Canary 部署（Phase 1 全量切換） |
| Quality Gate（test_pass_rate >= 0.80） | Latency / cost quality gate（Phase 2） |
| Atomic symlink swap 部署 | 多 VM 同步部署 coordinator |
| Rollback 到歷史版本 | A/B test per skill version |
| 每個操作 → `audit.log()` | Skill dependency graph |
| `load_prompt_template()` 從 git path 讀取 | Prompt registry cache（Phase 2 Redis cache） |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
< 50 skills              50-200 skills                 200+ skills
──────────────────────────────────────────────────────────────────
git scan sync           → git webhook trigger         → event bus + incremental sync
全量部署                → canary per skill            → blue-green + traffic split
file system 讀取        → Redis prompt cache          → CDN-backed prompt delivery
手動 approve            → auto-approve if score > 0.95→ ML-based quality prediction
單一 Quality Gate       → multi-gate (latency, cost)  → SLO-based auto-gate
flat skill list         → skill dependency graph      → skill marketplace
```

## See Also

- [`skills/AUTHORING-GUIDE.md`](../../skills/AUTHORING-GUIDE.md) — Skill 撰寫與維護心法（6 章：需求識別 / 雙路徑開發 + EDD / Description 三鐵律 / 心法 vs SOP / 200-500 行 / 維護清債）。新增 vertical / slug / version bump 前必讀。
- [`skills/README.md`](../../skills/README.md) — 目錄結構與上線流程 SOP。
- [`docs/1-decisions/ADR-0003-skill-registry.md`](../1-decisions/ADR-0003-skill-registry.md) — git monorepo 為 source of truth 的根本決策。
