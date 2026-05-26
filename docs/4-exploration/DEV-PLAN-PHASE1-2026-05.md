---
id: DEV-PLAN-PHASE1-2026-05
title: Phase 1 開發執行計畫 (S1 收尾 + S2~S8 共 13 週)
status: active
date: 2026-05-17
owner: CTO
tier: 4
related: [PRD-001, PROJ-001, SAD-v0.1, ADR-0011, BF-001, AC-001-to-005]
---

# Phase 1 開發執行計畫 — 7-Day AI 客服 Onboarding

> 本檔將 `PRD-001`（產品範圍）與 `PROJ-001`（90 天 sprint 骨架）合成為可直接照做的執行手冊。
> 各 sprint 細節詳見對應 MC contract；本檔聚焦「順序、依賴、平行化、exit gate」。
>
> **隨 Sprint 進度 weekly 更新（每週五）**：完成的任務劃 ✅，受阻或調整在最末「變更紀錄」追加一行。

## 1. 範圍邊界

- **包含**：S1 (PM Layer 收尾) → S2 (KB & KC) → S3 (TestSet & Skill v1.0) → S4 (LINE + Draft Mode) → S5 (Canary + Kill Switch + Audit UI) → S6 (Pilot Hardening) → S7 (Pilot Live) → S8 (Template + Retro)
- **不包含**：Phase 2+ 功能 — Training Room 進階、SkillOps Pipeline、ERP/CRM 深度整合、多 AI 員工協作、Workflow Designer、Plugin Marketplace（見 `docs/03-execution-onboarding.md §14.1` "故意延後"）

## 2. 鎖定的工程決策

| 項目 | 決定 | 來源 |
|---|---|---|
| Backend 語言 | Python 3.12 + FastAPI | ADR-0011 |
| Web stack | Pydantic v2 + SQLAlchemy 2.0 (async) + Alembic | ADR-0011 |
| Frontend | Vite + React 18 + TypeScript + Tailwind + shadcn/ui | SAD-v0.1 §3.1 |
| DB | PostgreSQL 15 + pgvector + RLS | ADR-0007 |
| Cache / Queue | Redis 7（list + DLQ pattern） | ADR-0008 |
| LLM | Claude Sonnet 4.6 主力 + Haiku 4.5 高頻 | ADR-0001 |
| Skill 儲存 | Git monorepo + YAML manifest | ADR-0003 |
| Auth | Email+Password+MFA（admin）/ LINE userId hash（end user）/ Google SSO（內部） | ADR-0006 |
| Tenant 隔離 | 共享 PG + RLS + 應用層雙重檢查 | ADR-0007 |
| Observability | Prometheus + Loki + Tempo + Grafana on Hetzner | ADR-0008 |
| Prompt 版本 | Git YAML + SemVer + 系統/tenant 兩層疊加 | ADR-0009 |
| Memory 架構 | L1 工作 + L2 會話 + L2.5 摘要 + L3 知識（L4 待定） | ADR-0010 |
| 部署 | 單租戶 per customer、Docker Compose | ADR-0004 |
| Runtime | 借鑑 nanobot 設計 + 自寫 AEOS 精簡版 EmployeeRuntime | ADR-0002 + ADR-0012 |

## 3. 13 週時間軸

| Sprint | 週次 | 主題 | 對應 UF/AC | 關鍵 MC | Exit Gate |
|---|---|---|---|---|---|
| S1 | W2.5 | PM Layer + 開工準備 | — | — | 本文件 + ADR-0011 + KICKOFF-CHECKLIST 進 main |
| S2 | W3-4 | KB & KC（pilot 客戶簽下後啟動）| UF-001 / AC-001 | MC-008, MC-001, MC-004 | AC-001 三條全綠 |
| S3 | W5-6 | TestSet & Skill v1.0 | UF-002 / AC-002 | MC-005, MC-002 | AC-002 三條全綠 + 首個 Skill 過 quality gate |
| S4 | W7-8 | LINE + Draft Mode | UF-003 / AC-003 | MC-011, MC-009, MC-010 | AC-003 三條全綠 |
| S5 | W9-10 | Canary + Kill Switch + Audit UI | UF-004, UF-005 / AC-004, AC-005 | MC-007, MC-003 | AC-004 + AC-005 全綠；kill switch ≤30s 演練通過 |
| S6 | W11 | Pilot Hardening | BF-001 dogfood | 全部 | SEC §6.1 13/13 ✅；3 runbook drill 通過 |
| S7 | W12 | Pilot Live | BF-001 Day 0-7 | 全部 | Day 7 Canary 100% live；無 P0；收齊 setup fee |
| S8 | W13 | Template Extraction + Retro | — | MC-005 | Vertical-X Skill template；第二客戶 ≤2h 配置 |

## 4. 各 Sprint 任務分解

### 4.1 S1 — PM Layer + 開工準備（本週）

| ID | 任務 | 交付物 | 狀態 |
|---|---|---|---|
| S1-1 | 補 backend 語言 ADR | `docs/1-decisions/ADR-0011-backend-language.md` | ✅ 2026-05-17 |
| S1-2 | 本 dev plan 進 repo | 本檔 | ✅ 2026-05-17 |
| S1-3 | Day 1 開工 checklist | `docs/3-process/KICKOFF-CHECKLIST.md` | ✅ 2026-05-17 |
| S1-4 | OBS-001 W1：Prom+Grafana+Loki on Hetzner | `infra/` 目錄 + Hetzner VM | 🚫 blocked（無 Hetzner 帳號）— 詳 `docs/report/S1-2026-05-17.md` Part B #1 |
| S1-5 | TEST-001 W1：測試骨架 + CI gates | `pyproject.toml` + `app/` + `tests/` + `.github/workflows/ci.yml` | ✅ 2026-05-17 (`feat/s1-scaffold-ci`，coverage 100% / gate 80%) |
| S1-6 | SEC-001 §6.1 起步 4 項：HMAC / RLS / secret scanning / TLS | SEC §6.1 4/13 ✅ | 🟡 部分 — secret scanning ✅；HMAC/RLS/TLS deferred 至 S2/S4/部署 |
| S1-7 | RUNBOOK-001 oncall 接線 | Slack / PagerDuty 通道完成 | 🚫 blocked（無 Slack workspace + PagerDuty 訂閱） |

**S1 Exit**：S1-1~S1-3 合入 main（本 PR）；S1-4~S1-7 至少各起一 PR，可橫跨 S2 完成。

> **進度更新（2026-05-17）**：S1-1/2/3/5 完成；S1-6 部分（secret scanning）完成；S1-4/7 待外部資源解鎖。詳 `docs/report/S1-2026-05-17.md`（合併版含 blocker 細節）。

### 4.2 S2 — KB & KC（W3-4，hard gate：pilot 簽下）

對應：`UF-001` / `AC-001` / `MC-008` / `MC-001` / `MC-004`

任務塊：
- ✅ 專案骨架：FastAPI app + Alembic + Docker Compose + CI pipeline（`feat/s1-scaffold-ci`、`feat/s2-db-foundation`）
- ✅ Auth 基礎：Tenant + API Key (bcrypt) + RLS context middleware（SQLAlchemy session-scoped variable via `set_config`）
- 🟡 DB migration：**9 / 25 表完成**（tenant / api_key / audit_log / knowledge_card / ingestion_job / employee / conversation / message + 8 monthly partition / conversation_handoff）；剩 16 表隨對應 sprint 加入
- 🚫 KB ingest pipeline (Worker)：PDF / DOCX / MD / URL → chunks → KC draft（待 pilot 客戶提供真實 KB）
- ✅ pgvector embedding：schema 層完成（1024-dim + ivfflat cosine index + GIN tags）；實際 embedding 寫入待 Worker
- 🚫 KC CRUD UI (Web SPA)：list / edit / approve / archive（待 S2 前端 sprint）
- ✅ Audit Service：append-only DB trigger + `app/services/audit.py:emit()`；KC 狀態變更發 AuditEvent 接線待業務 endpoint

> **進度更新（2026-05-22 早）**：Tier 0 + Tier 1 資料層全部完成；3 個 feat branch 已 push (`feat/s2-db-foundation` + `feat/s2-knowledge-cards` + `feat/s2-conversation-engine`)。40 tests / 99.68% coverage。詳 `docs/report/S2-PROGRESS-2026-05-22.md`。
>
> **進度更新（2026-05-22 中午）**：**Tier 2 完成**——LLMClient (ADR-0001 薄層 + AnthropicClient) + MC-005 Skill Registry (3 表 + git monorepo) + MC-006 Tool Registry (3 表) + faq-respond v1.0.0 skill scaffold。`feat/s2-llm-and-registries` 已 push。71 tests / 99.63% coverage。DB 表 15/25 (60%)。Skill production Quality Gate (`pass_rate ≥ 0.80 + approved`) 已落地為 DB CHECK constraint。
>
> **進度更新（2026-05-26 — CR-0001 Multi-Vertical Framework Sprint 完工）**：
> 9 branch（schema / ADR-0013 / router / draft-routing / new_skill CLI / 3 stub verticals / admin API / Expert UI / doc-sync）全部落地。framework 從「1 個 customer-service」擴展為「**4 個 vertical**（+hr / it-helpdesk / sales）」。+42 Python tests / +8 vitest / +5 Playwright。詳 [`CR-0001-multi-vertical-framework.md §10`](CR-0001-multi-vertical-framework.md)。

**Exit**：AC-001 三條全綠（PDF ingest <3min/100頁、KC approve 進 audit、archive 不被檢索）— 仍受阻於 pilot 客戶 KB 來源 + Worker 實作。

### 4.3 S3 — TestSet & Skill v1.0（W5-6）

對應：`UF-002` / `AC-002` / `MC-005` / `MC-002`

任務塊：
- ✅ Skill 倉庫結構：`skills/customer-service/faq-respond/v1.0.0/{manifest.yaml, system.md, tools.yaml}`（提前完成於 S2 Tier 2，`feat/s2-llm-and-registries`）
- 🚫 Skill loader：API 讀 git，產 SkillVersion 快照，atomic symlink swap
- 🚫 Test set co-author UI：Expert 輸入 50 題 + expected outcome
- 🚫 Test runner (Worker)：批次跑 50 題、pass rate 計算
- ✅ LLM judge：Haiku 4.5 語意比對；Judge Protocol 可換 (KeywordJudge / LLMJudge)；
  Expert override 透過 test_run_case 編輯（API 已存在；UI 待 P2）(`feat/s3-llm-judge`)
- 🟡 Quality Gate CI：Skill commit 觸發 test，pass rate ≥ 0.80 才可 promote — **DB CHECK 守門已落地（`ck_skill_version_production_quality_gate`）**；CI test 跑流程仍待

**Exit**：AC-002 三條全綠 + 第一個 Skill v1.0.0 過 quality gate。

### 4.4 S4 — LINE + Draft Mode（W7-8）

對應：`UF-003` / `AC-003` / `MC-011` / `MC-009` / `MC-010`

任務塊：
- ✅ MC-011 Channel Gateway: webhook_event dedup + channel_binding + outbound_message retry (`feat/s2-channel-gateway`)
- ✅ LINE webhook 端點：HMAC-SHA256 驗簽 + dedup (via webhook_event PK) + ≤1s ACK (`feat/s2-line-webhook`)
- ✅ Conversation Engine：6 態狀態機 + monthly partition + 30min idle timeout — `app/services/conversation_idle.py` 已實作 + 已掛 worker run_iteration（每 iter 跑一次）
- ✅ Employee Runtime + LLMClient (Anthropic) + AnthropicClient (`feat/s2-employee-runtime` / `feat/s2-llm-and-registries`)
- ✅ Governance Hooks (Audit / Policy / Quota)
- ✅ ToolExecutor (依 MC-006 tool_type 分派) + 2 builtin tools (search_knowledge / request_human_handoff) (`feat/s2-tool-executor`)
- ✅ DraftProcessor：載入 conversation 歷史 + SkillLoader + EmployeeRuntime + 寫 assistant message + outbound_message (`feat/s2-draft-processor`)
- ✅ LINE Push OutboundProcessor：429/5xx → retrying；4xx → failed；max_retries → DLQ；audit channel.message_pushed/failed (`feat/s2-outbound-worker`)
- ✅ DLQ Inspector + Requeue API：admin /dlq/outbound list + requeue endpoint（Phase 1 後續 #18 `de25607`）
- 🚫 L2.5 Session Summary：Haiku 對話結束摘要寫回 context（pilot 後再做）
- ✅ Draft Mode 推播給 Expert：`awaiting_review` → Slack notify info（Phase 1 後續 #16 `de25607`）
- ✅ Expert review 後端 API：approve / edit / reject + ExpertReviewError + audit (`feat/s2-expert-review-api`)
- ✅ Expert Console UI：Vite + React + Tailwind；1-click approve / edit-send / reject + diff 進 audit (`feat/s2-expert-review-ui`)
- ✅ Worker polling loop：DraftPoll + OutboundPoll + SKIP LOCKED + idle/exception backoff (`feat/s2-worker-loop`)
- ✅ Draft Mode E2E smoke：inbound → AI draft → expert approve → LINE Push 全鏈路 + reject 路徑 (`test/draft-mode-e2e`)

**Exit**：AC-003 三條全綠（webhook ≤1s ACK、draft 生成 p95 ≤5s、approve/edit/reject 全進 audit）。L2.5 + Draft 推播 留待 pilot 上線後依需要補。

### 4.5 S5 — Canary + Kill Switch + Audit UI（W9-10）

對應：`UF-004` + `UF-005` / `AC-004` + `AC-005` / `MC-007` / `MC-003`

任務塊：
- ✅ Auto reply 路徑：per-tenant canary_percent (0-100) + 確定性 bucket
  （SHA256(uuid)[:4] mod 100）→ pending / awaiting_review (`feat/s5-canary-routing`)
- ✅ Canary toggle：admin API `/api/v1/admin/canary/{tenant_id}` GET/POST；切換進 audit
- ✅ 緊急 kill switch：DISABLE_AI 二次確認、< 1 秒 DB 查 + 即時生效、attendee
  → conversation_handoff (`feat/s5-kill-switch`)
- ✅ Auth backend：bcrypt + bearer token + 30 天 session +
  `AEOS_AUTH_REQUIRED` env gate (`feat/s5-auth-backend`)
- ✅ Auth frontend：Login.tsx + App auth state machine + Bearer attach to all
  API calls + logout (`feat/s5-auth-frontend`)
- ✅ Audit 瀏覽 UI：3 endpoint (events / conversations / detail timeline) +
  Expert Console "Audit" tab，含 conversation 完整時間軸 (messages +
  outbounds + audit events) (`feat/s5-audit-browse-ui`)
- ✅ Slack 通知：best-effort webhook — kill switch disable P0 / enable info /
  outbound permanent fail P1；未設 `SLACK_WEBHOOK_URL` silently skip
  (`feat/s5-slack-notifications`)
- 🚫 Daily digest email — 待 Slack/SES 整合
- 🚫 D3 cost dashboard（OBS-001 W6 交付）— 待 Hetzner 部署實際抓到資料

**Exit**：AC-004 + AC-005 全綠 ✅；kill switch ≤30s 演練通過（單元測試
已驗 < 1s 生效，未實機 drill）。

### 4.6 S6 — Pilot Hardening（W11）

任務塊：
- 內部 dogfood：CTO / CEO 兩 dummy tenant，跑完 BF-001 Day 0~7
- Bug 補洞：dogfood 收集到的 issue 全修，無 P0/P1
- pilot 客戶 KB 真實 ingest 跑通
- SEC §6.1 13/13 全綠
- RUNBOOK-001/002/003 各 drill 一次（incident / rollback / backup PITR）

**Exit**：SEC §6.1 13/13；客戶 KB ingest 完成；3 runbook drill 通過。

### 4.7 S7 — Pilot Live（W12）

按 `BF-001 Day 0~7`：
- Day 0~5 內部執行（建 tenant、KB ingest、KC review、test set、dry run）
- Day 6 Draft Mode 真上線（pilot expert 1-click approve）
- Day 7 Canary 10% → 50% → 100% + 24h 觀察

**Exit**：Day 7 Canary 100%；24h 無 P0；收齊剩餘 50% setup fee。

### 4.8 S8 — Template Extraction + Retro（W13）

任務塊：
- Vertical-X Skill template：把 customer-service Skill 抽象為 template；目標第二客戶配置 ≤2h
- Phase 1 retro：what worked / didn't；補 ADR for Phase 2 重要決策
- Phase 2 backlog 進 `4-exploration/`：Training Room / Multi-channel / ERP adapter

## 5. 平行化策略

S2 開始可同時推（主線 + 平行三條）：
- **主線**：FastAPI 骨架 → Auth → DB migration → KB ingest（critical path）
- **平行 A**：OBS-001 W2~W4（KPI metrics、tracing、alerts）
- **平行 B**：SEC §6.1 逐項打勾
- **平行 C**：Skill repo 初始化 + faq-respond v1.0 prompt 設計（S3 提前準備）

S4 開始可同時推：
- **主線**：LINE webhook + Draft Mode
- **平行 A**：Audit UI 雛形（S5 提前準備）
- **平行 B**：Test set runner CI 化（S3 延伸）

## 6. 風險與緩解

| Risk | 影響 | Mitigation | 觸發指標 |
|---|---|---|---|
| R-01 KB 品質拉不到 70% | 高 | EX-1 補 KC 上限 3 輪；超則 EX-5 縮 scope | Day 5 dry run pass rate < 70% |
| R-02 Expert 投入時間超 3h | 高 | 簽約義務條款；S2~S4 weekly check-in | Expert session 累計 > 2h |
| R-04 LLM 怪話致 PR 危機 | 極高 | Draft Mode + Canary + Kill Switch 三層強制 | Canary 期間 expert override > 50% |
| R-09 Scope creep | 中 | CIA 強制；新需求進 Phase 2 backlog | 客戶提需求即觸發 CIA |
| R-10 第二客戶配置 >2h | 高 | S8 專門 template extraction | S8 結束時新客戶配置時間量測 |
| R-11 pilot 簽約延後 → 時間軸右移 | 高 | S1-4~S1-7 (OBS/TEST/SEC/Oncall) 在無客戶下推進 | CEO 本週簽約進度 |

## 7. 每 Sprint Exit 驗證 checklist

每個 sprint 結束 PR merge 前：
- [ ] `pytest --cov` 覆蓋率 ≥ 80%（TEST-001 §4 gate）
- [ ] `mypy` + `ruff` 全綠
- [ ] 對應 AC 的 acceptance test 全綠
- [ ] `sunnydata-doc-freshness` skill 跑過：tier-2 文件 `last-synced-with` 對齊
- [ ] `sunnydata-flow-audit` skill 跑過：BF/UF/SF/API/TC 一致性
- [ ] SEC §6.1 對應項打勾（若 sprint 觸及）
- [ ] PR 經 human review + `sunnydata-code-review` skill
- [ ] Merge 後 `git tag sN-complete`
- [ ] 每週五更新 `docs/LAUNCH-DASHBOARD.md`

## 8. 關鍵文件參考（依查閱頻率）

1. `docs/LAUNCH-DASHBOARD.md`
2. `docs/2-contracts/SAD-v0.1.md`
3. `docs/2-contracts/db-schema.md`
4. `docs/2-contracts/MC-008-knowledge-rag.md` (S2)
5. `docs/2-contracts/MC-005-skill-registry.md` (S3)
6. `docs/2-contracts/MC-011-channel-gateway.md` (S4)
7. `docs/2-contracts/MC-009-employee-runtime.md` (S4)
8. `docs/2-contracts/AC-001-to-005-acceptance-criteria.md`
9. `docs/2-contracts/API-001-internal.md`
10. `docs/2-contracts/API-002-line-webhook.md`
11. `docs/2-contracts/NFR-001-non-functional-requirements.md`
12. `docs/2-contracts/OBS-001-observability-spec.md`
13. `docs/2-contracts/SEC-001-threat-model.md` §6.1
14. `docs/2-contracts/TEST-001-test-plan.md`
15. `docs/2-contracts/QUOTA-001-llm-budget.md`
16. `docs/0-principles/engineering-charter.md`

## 變更紀錄

| 日期 | 變更 | Owner |
|---|---|---|
| 2026-05-17 | 初版發布；S1-1~S1-3 ✅ | CTO |
| 2026-05-17 | S1-5 ✅（FastAPI 骨架 + CI + 80% coverage gate，`feat/s1-scaffold-ci`）；S1-6 部分 ✅（gitleaks + Dependabot + Trivy fs scan + PR template）；S1-4/S1-7 標記受阻並引 blockers 報告 | CTO |
| 2026-05-18 | ADR-0012 觸發：§2 工程決策表加 Runtime 行（借鑑 nanobot 設計 + 自寫精簡版）；pi 評估報告 + nanobot 評估報告產出於 `docs/report/` | CTO |
| 2026-05-22 | S2 Tier 0+1 完成：DB Foundation + KnowledgeCard/IngestionJob + Conversation Engine（9/25 表）。3 個 feat branch 已 push。§4.2 S2 任務塊 status 更新 | CTO |
| 2026-05-22 | **S2 Tier 2 完成**：MC-005 Skill Registry (3 表 + git monorepo + faq-respond v1.0.0) + MC-006 Tool Registry (3 表 + YAML policy) + LLMClient (ADR-0001 薄層 + AnthropicClient) + DB Quality Gate CHECK 落地。DB 表 9→15 (60%)。71 tests / 99.63% coverage。§4.3/§4.4 部分任務提前完成標 🟡 | CTO |
| 2026-05-22 | **S2 Tier 3 完成**：EmployeeRuntime (MC-009 借鑑 nanobot agent loop) + 3 governance hooks (Audit/Policy/Quota) — engineering-charter §1 三大支柱全部以 hook 形式串入 LLM/tool call 周圍。108 tests / 98.74% coverage。§4.4 S4 Employee Runtime 任務塊標 ✅；剩 LINE webhook + ToolExecutor + KC ingest worker (Tier 4)。`feat/s2-employee-runtime` 已 push | CTO |
| 2026-05-22 | **MC-011 Channel Gateway DB schema 完成**：channel_binding (FK→employee CASCADE + unique(emp,channel)) + webhook_event (composite PK dedup) + outbound_message (4 態 status + partial idx_pending) + 3 RLS policies。DB 表 15→18 (72%)。119 tests / 98.82% coverage。§4.4 新增 MC-011 行標 🟡（schema ✅；application 層待）。`feat/s2-channel-gateway` 已 push | CTO |
| 2026-05-22 | **S2 Tier 4 application 層完成**：(1) ToolExecutor + 2 builtin tools `feat/s2-tool-executor`；(2) LINE webhook endpoint (HMAC + dedup + 1s ACK) `feat/s2-line-webhook`；(3) SkillLoader + DraftProcessor `feat/s2-draft-processor`；(4) LINE Push OutboundProcessor (retry + DLQ + audit) `feat/s2-outbound-worker`。LINE 端到端鏈路 inbound → AI → outbound 在 DB 層全跑通。180 tests / 93.16% coverage。§4.4 S4 任務塊全部 ✅，剩 worker polling loop + Expert review UI（Phase 1 待） | CTO |
| 2026-05-22 | **Worker polling + KB ingest + Draft Mode 端到端**：(1) Worker polling loop `feat/s2-worker-loop`；(2) KB ingest pipeline (parser + embedding + KC drafts) `feat/s2-kb-ingest`；(3) Expert review 後端 API (4 endpoint + service + migration 6 態 outbound status) `feat/s2-expert-review-api`；(4) Expert Console UI (Vite + React + Tailwind + 7 vitest) `feat/s2-expert-review-ui`；(5) CI 拆 backend + web-expert + path filter + ci-gate `ci/web-expert`；(6) Draft Mode E2E smoke (inbound→approve→Push + reject 路徑) `test/draft-mode-e2e`。238 tests / 93.30% coverage。§4.4 Expert review UI / Worker polling 標 ✅。剩外部 blocker：Hetzner / Slack-PagerDuty / LINE sandbox / pilot 簽約 | CTO |
| 2026-05-23 | **S3 完整 + S5 第一波 + dev 整合**：10 支新 branch：KC review (feat/s2-kc-review)、OBS IaC (chore/obs-iac-prep)、Prometheus instrumentation (feat/s5-prometheus-instrumentation)、kill switch (feat/s5-kill-switch)、idle timeout (feat/s4-idle-timeout)、TestSet schema (feat/s3-testset-schema)、TestSet UI (feat/s3-testset-ui)、seed demo (chore/seed-demo-script)、TestRunPoll cycle (feat/s3-testset-auto-runner)、Worker entrypoint (chore/worker-entrypoint)。建 `dev` 分支整合 14 支 branch，`main` 暫不動。**312 Python + 18 vitest = 330 tests / 93.07% coverage / 22 / 25 DB 表**。S3 完整鏈路通；S5 §kill switch 落地；Worker `python -m app.worker` 可獨立跑。剩 S5 三件：MFA / Canary / Audit UI | CTO |
| 2026-05-23 | **S5 完整收尾**：(1) auth backend — expert_account + expert_session + bcrypt + bearer token + `AEOS_AUTH_REQUIRED` gate (`feat/s5-auth-backend`)；(2) auth frontend — Login.tsx + App auth state machine + Bearer attach (`feat/s5-auth-frontend`)；(3) canary routing — per-tenant 0-100% + 確定性 bucket + admin API (`feat/s5-canary-routing`)；(4) audit browse — 3 endpoint + Expert Console 4th tab，conversation 完整時間軸 (`feat/s5-audit-browse-ui`)。**360 Python + 23 vitest = 383 tests / 93%+ coverage / 24 / 25 DB 表**。Expert Console 完整 4 tab（drafts/kc/testset/audit）+ Login + logout。AC-004/005 ✅。SEC-001 §6.1 從 2 → 4/13。剩 LLM judge 升級 + Slack webhook + admin 帳號管理 UI（P1，非 hard gate）| CTO |
| 2026-05-24 | **P1 工作收 2 件**：(1) LLM judge 升級 — `Judge` Protocol + `KeywordJudge` / `LLMJudge` (Haiku 4.5) 可注入到 TestSetRunner；LLMJudge 用 structured JSON prompt + 容錯 `{}` 抓取 + score clamp [0,1] + `keyword_fallback_on_error=True` (LLM 抖動不會炸 test run) (`feat/s3-llm-judge`)；(2) Slack 通知 — `app/services/notifications.py` best-effort webhook，kill_switch disable→P0 / enable→info / outbound permanent fail→P1；未設 `SLACK_WEBHOOK_URL` silently skip (`feat/s5-slack-notifications`)。**381 Python + 23 vitest = 404 tests / 93%+ coverage / 24/25 DB 表 / 22 支 branch 合入 dev**。剩 P1：Admin 帳號 UI / Message metadata 加 KC ref / PII masking | CTO |
| 2026-05-24 | **P1 全部收尾**：(1) Admin 帳號管理 UI — 4 endpoint (list/create/disable/enable) + Expert Console 第 5 個 tab (admin role only)，disable 同步 revoke active sessions (`feat/s5-admin-accounts-ui`)；(2) Message tool_invocations + KC refs — DraftProcessor 包 _dispatch 收集每次 tool 呼叫 (name/sanitized input/ok/error/kc_refs)，寫入 JSONB；Audit UI 渲染「引用 N 張 KC」chip，**AC-005 §2 完整** (`feat/s5-message-kc-refs`)；(3) PII masking — webhook ingress 6 種 pattern (email/tw_mobile/tw_landline/tw_id/credit_card+Luhn/bank_like)，raw PII 不會進 DB / log，audit `pii.redacted_in_ingress` + Prometheus counter，**SEC-001 §6.1 從 4 → 5/13** (`feat/sec-pii-masking`)。**408 Python + 29 vitest = 437 tests / 93%+ coverage / 24/25 DB 表 / 28 支 branch 合入 dev**。Phase 1 code 階段全部 P0/P1 hard gate 清完；剩全部外部 blocker（Hetzner / Slack-PagerDuty / LINE sandbox / pilot 簽約） | CTO |
