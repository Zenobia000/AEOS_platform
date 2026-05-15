---
id: TM-0001
title: "Traceability Matrix — AEOS Platform"
status: active
tier: 2-contracts
owner: AI-AUTO
last-reviewed: 2026-05-15
last-synced-with: 9f85145cec3d0dae247b3304cac85fa75fe53015
sync-source: doc
source-paths: []
synced-at: 2026-05-15
generated-by: sunnydata-auto-regen
generation-source: cross-reference of BF/UF/SF/AC/API/MC/TC IDs across docs/2-contracts/
product-version: Phase 1
supersedes: null
superseded-by: null
---

# Traceability Matrix — AEOS Platform

> **Tier**: 2-contracts → cross-layer coverage map
> **Purpose**: single source of truth for 「Flow → Module → API → Data → Test → CI」
> **Status**: Phase 0（pre-code）— TC 與 CI Job 為「規劃中」標記；Phase 1 實作後重生
> **Updated by**: `sunnydata-auto-regen` skill（never hand-edit）

---

## How to read this table

每一列是一個 end-to-end verifiable slice。左到右回答「BF-X 壞了該檢查什麼 / TC-Y 失敗代表什麼回歸」。

- 空白 cell = 「尚未存在」(gap to plan)
- `—` = 「故意不適用」（e.g. UF 不需 API surface）
- ID 前綴遵循 `PRIN-0001-flow-id-conventions`
- 🟡 _planned_ = TC/CI 已在 TEST-001 / OBS-001 中規劃但 src/ 尚未實作

---

## Coverage Matrix

| BF | UF | SF | AC | Modules (MC) | API | Data Entity | TC | CI Job |
|---|---|---|---|---|---|---|---|---|
| `BF-001` Onboarding | `UF-001` KB upload → KC review → approve | `SF-001` KB ingest pipeline | `AC-001` | MC-008 (RAG), MC-001 (audit), MC-007 (Admin UI) | `API-001` `POST /kb/upload`, `POST /knowledge_cards/*` | `knowledge_source`, `knowledge_card`, `audit_log` | 🟡 TC-010~012 (int), TC-E01 (e2e) | 🟡 `test-kb-ingest` |
| `BF-001` | `UF-002` 共寫 50 題 test set + 跑測試 | `SF-002` Test Set Run | `AC-002` | MC-003 (eval), MC-007 (UI), MC-001 (audit) | `API-001` `POST /tests/*`, `POST /test_runs/*` | `test_set`, `test_case`, `test_run`, `test_result` | 🟡 TC-020~025 | 🟡 `test-test-set-run` |
| `BF-001` | `UF-003` Draft Mode (LINE → Expert approve → 送出) | `SF-003` LINE Inbound → Draft Mode → Approve | `AC-003` | MC-011 (channel), MC-010 (conv), MC-009 (runtime), MC-007 (UI), MC-001 (audit) | `API-002` LINE webhook, `API-001` `POST /drafts/*` | `conversation`, `message`, `draft_review`, `audit_log` | 🟡 TC-030~035, TC-E03 | 🟡 `test-draft-mode` |
| `BF-001` | `UF-004` Canary Live with confidence threshold | `SF-004` Canary Auto Reply | `AC-004` | MC-010 (conv), MC-009 (runtime), MC-008 (RAG), MC-011 (channel), MC-001 (audit) | `API-002` LINE webhook (auto path) | `conversation`, `message`, `confidence_log` | 🟡 TC-040~042, TC-E04 | 🟡 `test-canary-auto-reply` |
| `BF-001` | `UF-005` Emergency Kill Switch | `SF-005` Emergency Kill Switch | `AC-005` | MC-007 (Admin UI), MC-009 (runtime), MC-011 (channel), MC-001 (audit) | `API-001` `POST /employees/{id}/kill` | `employee`, `kill_event`, `audit_log` | 🟡 TC-050, TC-E05 (staging drill) | 🟡 `test-kill-switch` |
| `BF-001` Day 0–1 | (Tenant provisioning, no UF — automation) | — | — | MC-004 (tenant), MC-001 (audit) | `API-001` `POST /tenants` | `tenant`, `api_key`, `audit_log` | 🟡 TC-001 (int) | 🟡 `test-tenant-create` |

---

## Module → Flow 反向覆蓋

確認每個 MC 至少有一條 flow 觸及：

| Module (MC) | Touched By Flow(s) | Phase 1 Status |
|---|---|---|
| MC-001 Audit Service | **all** (BF-001, UF-001~005) | ✅ 必建 |
| MC-002 Training Room | (none Phase 1) | ❌ Phase 2 |
| MC-003 Evaluation Service | UF-002 (test runs) | ❌ Phase 2（Phase 1 用 manual metrics）|
| MC-004 Tenant Manager | BF-001 Day 0–1 | ✅ 必建 |
| MC-005 Skill Registry | UF-001（Skill deploy） | ✅ 必建（最小版） |
| MC-006 Tool Registry | UF-003, UF-004（Tool invocation） | ⚠️ 半建 |
| MC-007 Admin Console | UF-001, UF-002, UF-003, UF-005 | ✅ 必建 |
| MC-008 Knowledge RAG | UF-001（ingest）, UF-003/004（retrieval） | ✅ 必建 |
| MC-009 Employee Runtime | UF-003, UF-004, UF-005 | ✅ 必建 |
| MC-010 Conversation Engine | UF-003, UF-004 | ✅ 必建 |
| MC-011 Channel Gateway | UF-003, UF-004 | ✅ 必建 |

---

## NFR Coverage

來自 `NFR-001-non-functional-requirements.md`：

| NFR | Description | Verified by | Status |
|---|---|---|---|
| NFR-001 §1 latency | P95 ≤ 8s LLM 路由 | 🟡 TC-PERF-001~005 (locust + production p95 monitor) | planned |
| NFR-001 §2 availability | 99.5% Phase 1 / 99.9% Phase 2 | 🟡 OBS-001 uptime check | planned |
| NFR-001 §3 security | 全部 Tier-2 security spec 落地 | 🟡 TC-SEC-001~010 (SEC-001 threat model) | planned |
| NFR-001 §4 PII | PII masking + audit 抽檢 | 🟡 TC-PII-001~005 | planned |
| NFR-001 §5 cost | 月度 LLM budget ≤ 30% 月費 | QUOTA-001 hard cap + OBS-001 cost dashboard | partial (policy active, alerts pending) |
| NFR-001 §6 coverage | 測試覆蓋率 ≥ 80% | CI gate（block merge） | planned |

---

## Domain Event Coverage

跨模組事件 — 每個 event 至少一個 consumer test（Phase 1 規劃）：

| Event | Producer | Consumers | Producer Test | Consumer Test(s) |
|---|---|---|---|---|
| `tenant.created` | MC-004 | MC-001 (audit), MC-007 (UI refresh) | 🟡 TC-001 | 🟡 TC-AUD-001 |
| `kc.draft.created` | MC-008 | MC-007 (review queue), MC-001 (audit) | 🟡 TC-011 | 🟡 TC-AUD-002 |
| `kc.approved` | MC-008 | MC-009 (Employee KB refresh), MC-001 (audit) | 🟡 TC-012 | 🟡 TC-EMP-001 |
| `test_run.completed` | MC-003 (Phase 1 manual / Phase 2 auto) | MC-007 (UI), MC-001 (audit) | 🟡 TC-025 | — |
| `draft.approved` | MC-009 | MC-011 (LINE outbound), MC-001 (audit) | 🟡 TC-035 | 🟡 TC-LINE-001 |
| `message.auto_replied` | MC-010 | MC-001 (audit), MC-008 (retrieval log) | 🟡 TC-042 | 🟡 TC-AUD-003 |
| `employee.killed` | MC-007 / MC-009 | MC-011 (stop outbound), MC-001 (audit) | 🟡 TC-050 | 🟡 TC-LINE-002 |

---

## External Dependency Coverage

第三方 API — 每個 dependency 一份 contract test + fallback plan。資料源：`API-003-third-party-integrations.md`：

| Dependency | Used In | Contract Test | Fallback | Vendor SLA |
|---|---|---|---|---|
| OpenAI / Claude LLM | UF-003, UF-004 (Canary), UF-001 (KC draft generation) | 🟡 `contract/llm-api.yaml` → TC-LLM-001 | Multi-vendor routing（OpenAI ↔ Anthropic），熔斷後 fallback Draft Mode | 99.9% (advertised) |
| LINE Messaging API | UF-003, UF-004, UF-005 | 🟡 `contract/line-webhook.yaml` → TC-LINE-001 | Retry with exp backoff；queue + manual replay | 99.5% |
| pgvector (PostgreSQL extension) | UF-001 (KB store), UF-003/004 (retrieval) | DB-level，無外部 contract | — | self-managed |
| Redis (session hot cache) | MC-009, MC-010 | DB-level | Session 不可用時 degrade to DB read | self-managed |

---

## Gaps & Coverage Debt

| Gap | Severity | Owner | Target |
|---|---|---|---|
| `src/` 尚未建立，所有 TC 為 🟡 planned | High | CTO | Phase 1 implementation kickoff |
| State machine（Employee deployment mode、Conversation session）尚未抽取為 SM-NNN | Medium | CTO | Phase 1 end |
| MC-002 Training Room / MC-003 Evaluation Service 規劃完備但無 flow 觸發 | Low (by design) | — | Phase 2 |
| CI workflow files (`.github/workflows/test-*.yml`) 尚未建立 | High | CTO | Phase 1 implementation kickoff |
| QUOTA-001 cost alert 接到 OBS-001 dashboard 後才算閉環 | Medium | CTO | Phase 1 implementation kickoff |

---

## Update Procedure

This file is **AI-AUTO**. Do not hand-edit.

每次 CR 完成後：

1. 開 `CR-NNN` 文件 §2-§7 看新增/修改/刪除項目
2. 跑 `sunnydata-auto-regen` skill → 本檔自動重生
3. `last-synced-with` frontmatter 由 post-write hook 自動更新

如果發現本檔錯誤，**不要直接編輯**，改去修：
- Source flow files (BF/UF/SF/AC)
- Module contracts (MC-001~011)
- 然後重跑 auto-regen

---

## Deleted IDs (do not reuse)

| ID | Deleted in | Reason |
|---|---|---|
| — | — | (none yet) |

---

## See also

- `PRIN-0001-flow-id-conventions` — ID semantics and allocation
- `flow-index.md` — Flow existence + status view (sibling)
- `TEST-001-test-plan.md` — original TC catalog and traceability rules
- `CIA-0000-change-impact-analysis.template.md` — what to update in this matrix per CR
- `.claude/skills/sunnydata-doc-freshness/SKILL.md` — freshness verification
- `.claude/skills/sunnydata-auto-regen/SKILL.md` — regenerates this file
