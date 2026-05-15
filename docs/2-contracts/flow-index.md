---
id: FI-0001
title: "Flow Index — AEOS Platform"
status: active
tier: 2-contracts
owner: AI-AUTO
last-reviewed: 2026-05-15
last-synced-with: 0881f25b2458b97c3ace08a4357fa2177d8d29c4
sync-source: doc
source-paths: []
synced-at: 2026-05-15
generated-by: sunnydata-auto-regen
generation-source: frontmatter scan of docs/2-contracts/{BF,UF,SF}-*.md + heading scan of consolidated flow files
product-version: Phase 1
supersedes: null
superseded-by: null
---

# Flow Index — AEOS Platform

> **Tier**: 2-contracts → project-wide Flow aggregation view
>
> **Why**: AEOS Phase 1 跨越 11 個子系統，沒有單頁 Flow 地圖時，AI 與工程師都會迷路。本文件回答「有哪些 BF / UF / SF / SM？status 各是什麼？」
>
> **Different from `traceability-matrix.md`**: 本檔列「Flow 存在性 + status」；TM 列「跨層覆蓋」（Flow → Module → API → Test）。
>
> **Note**: AEOS Phase 1 的 Flow 採取「合併檔策略」— UF-001~005 寫在 `UF-001-to-005-user-flows.md` 同一份檔案，SF/AC 亦同。Sub-section heading 是真實 ID 來源；本索引是 derived view。

---

## How to read

- **ID** — Flow ID per `PRIN-0001-flow-id-conventions`
- **Status** — frontmatter / sub-section status（active / draft / deprecated）
- **Owner** — Phase 1 多為 CTO+CEO 二人責任制
- **Related Modules** — 觸及哪些 MC-NNN（forward link to MC contracts）
- **Related** — for UF: parent BF; for SF: BF/UF that consume it

---

## Business Flows (L1 — BF)

> End-to-end across roles. Phase 1 只定義一條主流：Pilot 客戶 Day 0–7 完整 onboarding。

| ID | Name | Status | Owner | Related Modules | Notes |
|---|---|---|---|---|---|
| `BF-001` | 客戶 Onboarding 端到端（Day 0–7） | active | CTO + CEO | MC-001, MC-004, MC-005, MC-007, MC-008, MC-009, MC-010, MC-011 | Pilot 唯一主幹 BF；含付款、KB ingest、test set、Draft→Canary→Live |

## User Flows (L2 — UF)

> Single-actor surface flows. AEOS Phase 1 全部歸屬 BF-001。

| ID | Name | Parent BF | Actor | Status | Owner |
|---|---|---|---|---|---|
| `UF-001` | Expert 上傳 KB → KC draft → review → approve | BF-001 | Expert | active | CTO |
| `UF-002` | Expert 共寫 50 題 test set + 跑測試 | BF-001 | Expert | active | CTO |
| `UF-003` | Draft Mode：LINE 收訊 → Expert approve → 送出 | BF-001 | Expert + Customer | active | CTO |
| `UF-004` | Canary Live：信心閾值自動 fallback | BF-001 | AI System + Customer | active | CTO |
| `UF-005` | 緊急 Kill Switch | BF-001 | CTO / Tenant Admin | active | CTO |

## Sub Flows (L3 — SF)

> Reusable building blocks. AEOS Phase 1 每個 UF 對應一個 SF（1:1 對應，未來 SF 會被多 UF 共用）。

| ID | Name | Used By | Status | Owner |
|---|---|---|---|---|
| `SF-001` | KB Upload → KC Draft → Approve | UF-001 | active | CTO |
| `SF-002` | Test Set Run | UF-002 | active | CTO |
| `SF-003` | LINE Inbound → Draft Mode → Expert Approve | UF-003 | active | CTO |
| `SF-004` | Canary Auto Reply with Confidence Threshold | UF-004 | active | CTO |
| `SF-005` | Emergency Kill Switch | UF-005 | active | CTO |

## State Machines (SM)

> Per-entity state machines (extracted when ≥5 states).

| ID | Entity | Module | Status | File |
|---|---|---|---|---|
| — | (none yet) | — | — | Phase 1 entities 狀態機尚未抽取；候選：Tenant lifecycle、Employee deployment mode、Conversation session |

## Acceptance Criteria (AC — 對應 UF)

> AC 是 BDD 形式的可驗收條件，每個 UF 對應一份 AC。

| ID | Title | Maps to | Status |
|---|---|---|---|
| `AC-001` | Expert 上傳 KB → KC draft → review → approve | UF-001 | active |
| `AC-002` | Test Set Co-Authoring + Run | UF-002 | active |
| `AC-003` | Draft Mode 收訊 + Expert Approve | UF-003 | active |
| `AC-004` | Canary Auto Reply with Confidence | UF-004 | active |
| `AC-005` | Emergency Kill Switch | UF-005 | active |

---

## Coverage View (cross-cutting summary)

Quick health snapshot — full detail in `traceability-matrix.md`:

| BF | UFs | SFs | ACs | APIs | TCs | CI Jobs | Status |
|---|---|---|---|---|---|---|---|
| BF-001 | 5 | 5 | 5 | 3 (API-001/002/003) | ~25 planned | 0 (Phase 0) | 🟡 specs complete, implementation pending |

**Pipeline state**: AEOS 處於 Phase 0（文件完備、`src/` 尚未實作）。CI/TC 數字為「規劃中」。Phase 1 啟動後本表 status 改為 🔴 not started 直到實作開始。

---

## Module Coverage View (MC ↔ Flow)

> 11 個 Module Contract 對應哪些 Flow？以下從 MC 的 `related` frontmatter 反推。

| Module (MC) | Plane | Touches BF/UF/SF | Phase 1 |
|---|---|---|---|
| `MC-001` Audit Service | Governance | 全部（所有 flow 都寫 audit log） | ✅ 必建 |
| `MC-002` Training Room | Training | — | ❌ Phase 2 |
| `MC-003` Evaluation Service | Evaluation | UF-002（指標來源），未來自動化 | ❌ Phase 2 |
| `MC-004` Tenant Manager | Tenant | BF-001（Day 0–1 建 tenant） | ✅ 必建 |
| `MC-005` Skill Registry | Governance | UF-001（部署 Skill 給 Employee） | ✅ 必建（最小版） |
| `MC-006` Tool Registry | Governance | UF-003, UF-004（Tool invocation） | ⚠️ 半建 |
| `MC-007` Admin Console | Frontend | UF-002（test approve UI）, UF-005（kill switch UI） | ✅ 必建 |
| `MC-008` Knowledge (RAG) | Knowledge | UF-001（ingest）、UF-003/004（retrieval） | ✅ 必建（最小版） |
| `MC-009` Employee Runtime | Runtime | UF-003, UF-004（執行 AI 員工） | ✅ 必建 |
| `MC-010` Conversation Engine | Runtime | UF-003, UF-004（對話狀態機） | ✅ 必建 |
| `MC-011` Channel Gateway | Runtime | UF-003, UF-004（LINE 接線） | ✅ 必建 |

---

## Deprecation / Supersession Ledger

When a Flow is deprecated or superseded, log it here so the ID is **never reused**:

| ID | Status | Reason | Superseded By | Date |
|---|---|---|---|---|
| — | — | (none yet) | — | — |

---

## Open Questions Aggregation

> Pulled from each Flow doc / AC / TEST-001 / 跨模組審查紀錄。

| Source | Question | Owner | Status |
|---|---|---|---|
| UF-003 §邊界 | Draft Mode 超過 X 分鐘 Expert 未回應的 fallback 行為？ | CTO + Expert | open |
| UF-004 §邊界 | Canary confidence threshold 的初始值（0.7 / 0.8 / 0.9）需 A/B test | CTO | open |
| MC-006 §scope | Tool Registry policy engine vs. 直呼工具 + audit 的時程切換點？ | CTO | scheduled Phase 2 |
| MC-008 §RAG | pgvector 在 100 萬+ knowledge cards 是否需切到 Qdrant？ | CTO | watch |
| TEST-001 §perf | P95 latency ≤ 8s 的 LLM 路由 fallback 條件待定 | CTO | open |

---

## How AI uses this index

1. **First read** in any task touching Flows — gives map without scanning every file
2. **Reference resolution** — when a CR mentions "BF-001" / "UF-003" / "MC-009", look up here for status + related modules
3. **Coverage gap detection** — empty cells in Coverage View signal where work is needed
4. **Audit input** — `sunnydata-flow-audit` skill cross-references this index against actual files

---

## Maintenance procedure

This file is **AI-AUTO**. Do not hand-edit.

After every CR that creates / modifies / deprecates a Flow or Module:

1. Run `sunnydata-auto-regen` skill to regenerate this index
2. Frontmatter `last-synced-with` updates automatically
3. If deprecating, the ledger picks up the change next regen

---

## See also

- `PRIN-0001-flow-id-conventions` (in VibeCoding_Workflow_Templates/0-principles/) — ID semantics
- `BF-001-customer-onboarding.md`, `UF-001-to-005-user-flows.md`, `SF-001-to-005-system-flows.md`, `AC-001-to-005-acceptance-criteria.md` — Flow source files
- `MC-001` ~ `MC-011` — Module Contract source files
- `traceability-matrix.md` — execution-layer cross-coverage (sibling)
- `.claude/skills/sunnydata-flow-audit/SKILL.md` — verifies this index against reality
- `.claude/skills/sunnydata-auto-regen/SKILL.md` — regenerates this file
