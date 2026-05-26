---
id: LAUNCH-DASHBOARD
title: Launch Dashboard
status: active
type: view
created: 2026-05-15
owner: CEO + CTO
tier: 5
related: [PROJ-001, PILOT-001, PRD-001, COST-MODEL-2026-05, PILOT-ICP-2026-05, OBS-001, RUNBOOK-001, TEST-001, SEC-001]
---

# Launch Dashboard

> 產品上線的唯一入口。每週五更新。

## 現在在哪

| Sprint | 主題 | 狀態 | 目標週 | Gate |
|---|---|---|---|---|
| S0 | Specs (ADR/Domain/DB/PRD) | DONE | Week 1 | — |
| S0.5 | SA + SD Layer (BF/UF/NFR/SAD/API/UX) | DONE | Week 2 | — |
| **S1** | **PM Layer + 開工準備** | **DONE (pilot-independent 部分)** | **Week 2.5** | AC/PROJ-001/開工 checklist + scaffold ✅ |
| **S2** | **KB & KC (UF-001)** | **IN PROGRESS** (DB 18/25 表 + LINE 端到端 + Draft Mode 後端 + Expert UI + E2E smoke ✅；KB worker pipeline 待 pilot) | Week 3-4 | 需已簽 pilot 客戶才能 exit |
| S3 | TestSet & Skill v1.0 | 待 | Week 5-6 | AC-001 全通過 |
| S4 | LINE + Draft Mode | 待 | Week 7-8 | AC-002 全通過 |
| **S5** | **Canary + Kill Switch + Audit UI** | **DONE** (6/7 任務塊，剩 Slack digest) | Week 9-10 | AC-004 + AC-005 ✅ |
| S6 | Pilot Hardening | 待 | Week 11 | 客戶 KB 真實 ingest |
| S7 | Pilot Live | 待 | Week 12 | BF-001 全流程跑通 |
| S8 | Template Extraction + Retro | 待 | Week 13 | Pilot live + 收齊 setup fee |

## 上線就緒

| 類別 | 狀態 | 說明 | 檢核來源 |
|---|---|---|---|
| 治理 | RED | Skill/Tool/Policy Engine 尚未實作 | [Appendix C §C.1](appendices/C-pre-launch-checklist.md) |
| 安全 | RED | PII Masking/隔離/紅隊未建 | [Appendix C §C.2](appendices/C-pre-launch-checklist.md) |
| 合規 | RED | DPA 未簽、資料保留未設定 | [Appendix C §C.3](appendices/C-pre-launch-checklist.md) |
| 運營 | RED | Dashboard/Drift 偵測/On-call 未建 | [Appendix C §C.4](appendices/C-pre-launch-checklist.md) |
| 商業 | RED | 計價/Quota/SLA 未落實 | [Appendix C §C.5](appendices/C-pre-launch-checklist.md) |

## 模型迭代能力（2026-05-26 snapshot）

**技術閉環 ✅，真實資料 🚫**。迭代模型需要的 5 個齒輪，Phase 1 都建好了：

| 齒輪 | 狀態 | Phase 1 落點 |
|---|---|---|
| **量品質**（pass rate） | ✅ 可跑 | TestSet tab + TestSetRunner + KeywordJudge |
| **改 prompt / skill** | ✅ 可版控 | `skills/<slug>/<version>/system.md` semver |
| **跑回歸測試** | ✅ 可一鍵 | Expert UI「跑一次 test run」按鈕 |
| **灰度放出** | ✅ 可調 | Admin API canary 0→100% |
| **出包剎車** | ✅ 可關 | Kill switch < 30s |

→ 現在**可以**改 `faq-respond/v1.0.0/system.md` → bump v1.0.1 → 跑 testset → 看 pass rate 升或降 → 決定要不要 canary 10% → 不對勁就 kill。**閉環完整**。

但**缺彈藥**：

| 缺什麼 | 為什麼缺 | 解鎖 |
|---|---|---|
| 真實對話資料 | LINE channel 沒接 / 沒 pilot 客戶 | 簽 pilot |
| 真實 KB | demo 只有 3 張 FAQ KC | pilot 提供文件 |
| 真實 test set | 只有 5 筆 demo case | 從 pilot 對話蒐集 |
| LLMJudge | Phase 1 用 KeywordJudge 為主，LLM 版本還在 fallback 模式 | S5 升級（不卡 pilot） |

**白話**：機器組好了會動，但**輸入端是空的**。自己跟自己玩可以練流程，看不出模型真好不好；要拿到第一個 pilot 客戶的真實對話 + 真實 KB，迭代才有意義。

**現在能做的「乾迭代」**（不等 pilot）：

1. 自己擴 test set 到 50 題（依 [PRD-001](4-exploration/PRD-001-7day-ai-cs-onboarding.md) §AC-001）→ 跑 baseline pass rate
2. 改 `faq-respond` system.md tone / few-shot → 看 pass rate 變動
3. 練 canary + kill switch SOP（演練用，不是真實流量）

## CEO 本週行動

1. **簽第一個 Pilot 客戶** — 目標清單待填入 [PILOT-ICP §3](4-exploration/PILOT-ICP-2026-05.md)；簽約條件見 [PILOT-ICP §5](4-exploration/PILOT-ICP-2026-05.md)
2. **回答 PRD-001 開放問題** — [PRD-001](4-exploration/PRD-001-7day-ai-cs-onboarding.md) status: draft，需 CEO 決策後轉 active
3. **確認資金跑道** — Pilot 期 net burn ~$35K/3個月 ([COST-MODEL §3](4-exploration/COST-MODEL-2026-05.md))；需確認現金是否到位
4. **填入候選客戶名單** — [PILOT-ICP §3.1](4-exploration/PILOT-ICP-2026-05.md) 目前全空白，目標 30 個 ICP-matched 候選

## 關鍵指標

| 指標 | 現值 | 目標 | 來源 |
|---|---|---|---|
| Pilot 客戶簽約數 | 0 | 3-5 家 | [PILOT-001 §1](3-process/PILOT-001-success-criteria.md) |
| MRR | $0 | ~$2,300/月 (5 家 Pilot) | [COST-MODEL §3.1](4-exploration/COST-MODEL-2026-05.md) |
| AI auto-reply 採用率 | n/a | >= 70% | [PILOT-001 §2.1](3-process/PILOT-001-success-criteria.md) |
| Test set 通過率 | n/a | >= 85% | [PILOT-001 §2.1](3-process/PILOT-001-success-criteria.md) |
| 程式碼行數 | 24,000+ (app 8515 + tests 9410 + alembic 2020 + skills 236 + web/expert/src 3770) | — | `dev` |
| DB 表完成數 | 24 / 25 (96%) | 25 | [db-schema.md](2-contracts/db-schema.md) |
| Governance Layer (Audit/Policy/Quota) | 3 / 3 ✅ | 3 | engineering-charter §1 |
| LINE 端到端鏈路 (DB 層) | inbound + draft + outbound 全跑通 ✅ | ✓ | AC-003 |
| Draft Mode 鏈路（Expert review） | 後端 API + UI + E2E smoke ✅ | ✓ | PRD-001 §5.4 |
| KC review 鏈路 | service + API + UI（policy/faq/etc 4 endpoint）✅ | ✓ | MC-008 / `feat/s2-kc-review` |
| Kill switch（per-tenant） | tenant_setting + admin API + DraftProcessor 攔截 ✅ | ✓ | PRD-001 §5.5 |
| Worker polling | idle / draft / outbound / test_run 4 cycle 全跑通 ✅ | ✓ | `feat/s3-testset-auto-runner` |
| Worker entrypoint | `python -m app.worker` graceful shutdown ✅ | ✓ | `chore/worker-entrypoint` |
| TestSet 鏈路 | schema + runner + keyword judge + REST API + UI tab + 背景自動跑 ✅ | ✓ | AC-001 / S3 |
| Prometheus 量測 | FastAPI middleware + 7 業務 metric + 2 Grafana dashboard ✅ | ✓ | OBS-001 §2-3 |
| 認證鏈路 (S5) | expert_account + bearer token + Login UI + AEOS_AUTH_REQUIRED gate ✅ | ✓ | `feat/s5-auth-*` |
| Canary 路由 (S5) | per-tenant 0-100% auto-reply 比例 + admin API + 確定性 bucket ✅ | ✓ | PRD-001 §5.5 / `feat/s5-canary-routing` |
| Audit Browse UI (S5) | 3 endpoint + conversation 完整時間軸 + Expert Console tab ✅ | ✓ | AC-005 / `feat/s5-audit-browse-ui` |
| LLM Judge (Haiku 語意比對) | Judge Protocol + KeywordJudge / LLMJudge + 容錯 JSON parse + keyword fallback ✅ | ✓ | AC-001 升級 / `feat/s3-llm-judge` |
| Slack 通知 | best-effort webhook：kill switch P0 + outbound permanent P1 + emoji 對映 ✅ | ✓ | RUNBOOK-001 / `feat/s5-slack-notifications` |
| Admin 帳號管理 UI | 4 endpoint (list/create/disable/enable) + Expert Console 第 5 個 tab (admin role only) ✅ | ✓ | `feat/s5-admin-accounts-ui` |
| Message KC refs | DraftProcessor 寫 tool_invocations 含 kc_refs + Audit UI 渲染「引用 N 張 KC」 ✅ | ✓ | AC-005 §2 完整 / `feat/s5-message-kc-refs` |
| PII Masking | webhook ingress 6 種 pattern (email/手機/市話/身分證/credit_card+Luhn/bank) + Prometheus counter + audit ✅ | ✓ | SEC-001 §6.1 #11 / `feat/sec-pii-masking` |

## Engineering Health

> CTO 本週主要追蹤。Pilot 期目標：W4 起所有指標脫離 n/a，W8 全綠。

### 交付節奏

| 指標 | 現值 | 目標 | 來源 |
|---|---|---|---|
| Deploy frequency（prod） | 0 / 週 | ≥ 1 / 週 | [RUNBOOK-002 §1](3-process/RUNBOOK-002-deploy-rollback.md) |
| Lead time（commit → prod） | n/a | < 1 day | RUNBOOK-002 |
| Change failure rate | n/a | < 15% | RUNBOOK-002 §4 |
| MTTR（事故平均恢復時間） | n/a | < 2 hour | [RUNBOOK-001 §1](3-process/RUNBOOK-001-incident-response.md) |

### 系統健康

| 指標 | 現值 | 目標 | 來源 |
|---|---|---|---|
| 可用性（webhook，月度） | n/a | ≥ 99.5% | [OBS-001 §8](2-contracts/OBS-001-observability-spec.md) |
| E2E p95 latency | n/a | ≤ 8s | [NFR-001 §1](2-contracts/NFR-001-non-functional-requirements.md) |
| Open P0 incidents | 0 | 0 | RUNBOOK-001 |
| Open P1 incidents | 0 | ≤ 2 / month | RUNBOOK-001 |
| Error budget burn（月度） | n/a | < 100% | OBS-001 §8 |
| 最後一次成功 backup | n/a | < 24h ago | [RUNBOOK-003 §7](3-process/RUNBOOK-003-backup-dr.md) |

### 品質與安全

| 指標 | 現值 | 目標 | 來源 |
|---|---|---|---|
| Test coverage（dev） | 93%+ (408 tests, `dev`) | ≥ 80% | [TEST-001 §4](2-contracts/TEST-001-test-plan.md) |
| Test 數量 | 408 Python + 29 vitest = **437** | — | tests/ + web/expert/src |
| CI pass rate（過去 7 天） | n/a（首次 push 後可量） | ≥ 95% | TEST-001 |
| Flaky tests | 0 | ≤ 3 | TEST-001 §7 |
| Open critical CVE | 0（Dependabot 首掃待跑） | 0 | [SEC-001 §6.1](2-contracts/SEC-001-threat-model.md) |
| Open S1/S2 support tickets | 0 | 0 active | [PLAYBOOK-001 §3.2](3-process/PLAYBOOK-001-cs-escalation.md) |
| SEC-001 §6.1 Go/No-Go checklist | 5 / 13 ✅ (+ PII masking at webhook ingress)；剩 pentest / DPA / oncall drill / container scan / TLS prod | 13 / 13 ✅ | SEC-001 §6.1 |
| Skill production Quality Gate | DB CHECK 落地 (pass_rate ≥ 0.80 + approved) | — | MC-005 / migration `89c67361deb1` |

### 成本

| 指標 | 現值 | 目標 | 來源 |
|---|---|---|---|
| LLM 月支出（全系統） | $0 | < $300（5 家 Pilot 上限） | [QUOTA-001 §1](2-contracts/QUOTA-001-llm-budget.md) |
| Infra 月支出 | ~$50 | < $150 | [ADR-0008](1-decisions/ADR-0008-observability-stack.md) |
| Single tenant 月毛利率 | n/a | ≥ 50%（Pilot）/ ≥ 75%（GA） | [COST-MODEL §1.4 §4.1](4-exploration/COST-MODEL-2026-05.md) |

### Oncall

| 項目 | 現值 |
|---|---|
| 本週 Primary | CTO |
| 本週 Secondary | LLM eng |
| 上次事故 | n/a |
| 下次 incident drill | 待排（每月一次，RUNBOOK-001 §8） |

## CTO 本週行動

1. ~~**TEST-001 §10 W1 交付**~~ ✅
2. ~~**SEC-001 §6.1 secret scanning**~~ ✅
3. ~~**DB Foundation Tier 0+1**~~ ✅ 9 表（`feat/s2-db-foundation` / `feat/s2-knowledge-cards` / `feat/s2-conversation-engine`）
4. ~~**Tier 2 — LLMClient + Skill/Tool Registry + faq-respond v1.0.0**~~ ✅ +6 表
5. ~~**Tier 3 — EmployeeRuntime (MC-009) + 3 Governance Hooks**~~ ✅
6. ~~**MC-011 Channel Gateway 3 表**~~ ✅
7. ~~**Tier 4 完整：ToolExecutor + LINE webhook (inbound) + DraftProcessor + LINE Push (outbound)**~~ ✅ — LINE 端到端 DB 層全跑通（`feat/s2-tool-executor` / `feat/s2-line-webhook` / `feat/s2-draft-processor` / `feat/s2-outbound-worker`）
8. ~~**Worker polling loop**~~ ✅ （`feat/s2-worker-loop`）
9. ~~**KB ingest worker**~~ ✅ （`feat/s2-kb-ingest`）— file parser + embedding + KC drafts
10. ~~**Draft Mode 後端 API**~~ ✅ （`feat/s2-expert-review-api`）— 4 endpoint + service layer + 14 tests
11. ~~**Expert Console UI**~~ ✅ （`feat/s2-expert-review-ui`）— Vite + React + Tailwind + 7 vitest
12. ~~**CI 拆 backend / web-expert**~~ ✅ （`ci/web-expert`）— path filter + ci-gate
13. ~~**Draft Mode E2E smoke**~~ ✅ （`test/draft-mode-e2e`）— inbound→draft→approve→Push 全鏈路
14. ~~**OBS-001 §10 W1 IaC 預備**~~ ✅ （`chore/obs-iac-prep`）— `infra/observability/` Prometheus + Loki + Grafana docker-compose + dashboards + nginx TLS template + Hetzner CX22 runbook
15. ~~**Prometheus instrumentation**~~ ✅ （`feat/s5-prometheus-instrumentation`）— FastAPI middleware + 7 業務 metric + 3 worker 接入
16. ~~**Kill switch (per-tenant)**~~ ✅ （`feat/s5-kill-switch`）— tenant_setting + admin API + DraftProcessor 攔截
17. ~~**Conversation idle timeout**~~ ✅ （`feat/s4-idle-timeout`）— S4 收尾
18. ~~**S3 TestSet schema + runner + judge**~~ ✅ （`feat/s3-testset-schema`）
19. ~~**S3 TestSet REST API + UI tab**~~ ✅ （`feat/s3-testset-ui`）
20. ~~**TestSet auto-runner in worker loop**~~ ✅ （`feat/s3-testset-auto-runner`）— pending run 自動跑
21. ~~**Worker entrypoint**~~ ✅ （`chore/worker-entrypoint`）— `python -m app.worker` graceful shutdown
22. ~~**Seed demo script**~~ ✅ （`chore/seed-demo-script`）— 1 鍵餵 3 個 tab
23. ~~**所有 branch 合入 `dev`**~~ ✅ — 14 個 merge commit；`main` 仍未動
24. **OBS infra 部署**：Prometheus + Grafana 跑在 Hetzner — 🚫 待 CTO 開 Hetzner 帳號
25. **接 RUNBOOK-001 primary oncall**：Slack / PagerDuty — 🚫 待 CEO/CTO 註冊
26. **LINE sandbox channel 註冊** — 🚫 待 CTO 登入 LINE Developers Console
27. ~~**Auth backend (bearer token + bcrypt)**~~ ✅ (`feat/s5-auth-backend`) — `AEOS_AUTH_REQUIRED` env gate
28. ~~**Auth frontend (Login.tsx + Bearer attach)**~~ ✅ (`feat/s5-auth-frontend`)
29. ~~**Canary 路由 (per-tenant 0-100%)**~~ ✅ (`feat/s5-canary-routing`)
30. ~~**Audit browse API + UI tab**~~ ✅ (`feat/s5-audit-browse-ui`)
31. ~~**LLM judge 升級 Haiku**~~ ✅ (`feat/s3-llm-judge`) — Judge Protocol + KeywordJudge / LLMJudge 可注入 + 容錯 JSON parse + keyword fallback
32. ~~**Slack webhook 通知**~~ ✅ (`feat/s5-slack-notifications`) — kill switch P0 + outbound permanent fail P1，best-effort（未設 webhook silently skip）
33. ~~**Admin 帳號管理 UI**~~ ✅ (`feat/s5-admin-accounts-ui`) — list/create/disable/enable，admin role 才看得到 tab
34. ~~**Message tool_invocations + KC refs**~~ ✅ (`feat/s5-message-kc-refs`) — AC-005 §2 完整；Audit UI 顯示「引用 N 張 KC」
35. ~~**SEC-001 §6.1 #11 PII masking**~~ ✅ (`feat/sec-pii-masking`) — webhook ingress 6 patterns + Luhn 驗證 + audit + Prometheus counter
36. **Phase 1 code 階段完成 — 純技術上進無可進，剩全部外部 blocker**：Hetzner / Slack-PagerDuty / LINE sandbox / pilot 客戶簽約

詳見 [`docs/report/S5-PROGRESS-2026-05-24-p1-complete.md`](report/S5-PROGRESS-2026-05-24-p1-complete.md)（P1 全收尾）、[`docs/report/STATUS-REPORT-2026-05-24-phase1-code-complete.html`](report/STATUS-REPORT-2026-05-24-phase1-code-complete.html)（HTML）、[`docs/report/S5-PROGRESS-2026-05-24-llm-judge-slack.md`](report/S5-PROGRESS-2026-05-24-llm-judge-slack.md)、[`docs/report/S5-PROGRESS-2026-05-23-complete.md`](report/S5-PROGRESS-2026-05-23-complete.md)、[`docs/report/S2-PROGRESS-2026-05-22-expert-review.md`](report/S2-PROGRESS-2026-05-22-expert-review.md)、[`docs/report/S2-PROGRESS-2026-05-22-tier4-complete.md`](report/S2-PROGRESS-2026-05-22-tier4-complete.md)、[`docs/report/S2-PROGRESS-2026-05-22-tier4.md`](report/S2-PROGRESS-2026-05-22-tier4.md)、[`docs/report/S2-PROGRESS-2026-05-22.md`](report/S2-PROGRESS-2026-05-22.md)、[`docs/report/S1-PROGRESS-2026-05-17.md`](report/S1-PROGRESS-2026-05-17.md) 與 [`docs/report/S1-BLOCKERS-2026-05-17.md`](report/S1-BLOCKERS-2026-05-17.md)。

## 必讀文件（依角色）

### CEO 必讀（現在就要熟）

| 文件 | 一句話說明 | 為什麼現在要讀 |
|---|---|---|
| [PRD-001](4-exploration/PRD-001-7day-ai-cs-onboarding.md) | Phase 1 唯一產品範圍 | 你要對外解釋賣什麼 |
| [PILOT-001](3-process/PILOT-001-success-criteria.md) | 成功/失敗標準 | 簽客戶前要對齊期望 |
| [PILOT-ICP](4-exploration/PILOT-ICP-2026-05.md) | 目標客戶畫像 + 名單 | 決定找誰談 |
| [COST-MODEL](4-exploration/COST-MODEL-2026-05.md) | 單位經濟 + burn rate | 確認燒得起 |
| [PROJ-001](3-process/PROJ-001-90day-sprint-plan.md) | 90 天 sprint 計畫 + RACI | 知道誰做什麼、何時到 |
| [BF-001](2-contracts/BF-001-customer-onboarding.md) | 客戶 onboarding 端到端流程 | 對外展示流程 |

### CTO 必讀（開工前）

| 文件 | 一句話說明 |
|---|---|
| [SAD-v0.1](2-contracts/SAD-v0.1.md) | 系統架構 |
| [domain-model](2-contracts/domain-model.md) | DDD 領域模型 |
| [db-schema](2-contracts/db-schema.md) | 資料庫設計 |
| [API-001](2-contracts/API-001-internal.md) | 內部 API 規格 |
| [AC-001-005](2-contracts/AC-001-to-005-acceptance-criteria.md) | 驗收標準 |
| [engineering-charter](0-principles/engineering-charter.md) | 工程原則 |
| [ADR-0010](1-decisions/ADR-0010-memory-architecture.md) | 記憶四層架構 |
| [OBS-001](2-contracts/OBS-001-observability-spec.md) | 可觀測性規範（W1 開工） |
| [RUNBOOK-001](3-process/RUNBOOK-001-incident-response.md) | 事故回應（CTO 即 primary oncall） |
| [QUOTA-001](2-contracts/QUOTA-001-llm-budget.md) | LLM 成本控制 |
| [SEC-001](2-contracts/SEC-001-threat-model.md) | 威脅模型 + §6.1 上線前 checklist |
| [TEST-001](2-contracts/TEST-001-test-plan.md) | 測試計畫與追溯矩陣 |

### 開發中按需查閱

UF/SF 流程、NFR、UX wireframe、threat model、test plan、observability spec、LINE webhook API、third-party integrations

### 不急（Phase 2+ 或特定場景才看）

白皮書敘事檔 (00-06, 99)、投資人視角 (05)、ADR 全集、法務模板、招募 JD、visual prompts、附錄 A/B/D/E/G/J

---

*上次更新：2026-05-24 | 更新者：CTO（**S2-S5 全任務塊 + 全部 P1 完成 ✅** — Admin UI / KC refs / PII masking 全清；**408 Python + 29 vitest = 437 tests** / 93%+ coverage / 24/25 DB 表 / **28 支 branch 合入 `dev`** / SEC-001 §6.1 5/13；Phase 1 code 階段進無可進，剩全部外部 blocker：Hetzner / Slack-PagerDuty / LINE sandbox / pilot 簽約）*
