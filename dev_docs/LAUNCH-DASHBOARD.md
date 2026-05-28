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
| **S1** | **PM Layer + 開工準備** | **IN PROGRESS** | **Week 2.5** | AC/PROJ-001/開工 checklist |
| S2 | KB & KC (UF-001) | 待 | Week 3-4 | 需已簽 pilot 客戶 |
| S3 | TestSet & Skill v1.0 | 待 | Week 5-6 | AC-001 全通過 |
| S4 | LINE + Draft Mode | 待 | Week 7-8 | AC-002 全通過 |
| S5 | Canary + Kill Switch + Audit UI | 待 | Week 9-10 | AC-003 全通過 |
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
| 程式碼行數 | 0 | — | — |

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
| Test coverage（main） | n/a | ≥ 80% | [TEST-001 §4](2-contracts/TEST-001-test-plan.md) |
| CI pass rate（過去 7 天） | n/a | ≥ 95% | TEST-001 |
| Flaky tests | n/a | ≤ 3 | TEST-001 §7 |
| Open critical CVE | n/a | 0 | [SEC-001 §6.1](2-contracts/SEC-001-threat-model.md) |
| Open S1/S2 support tickets | 0 | 0 active | [PLAYBOOK-001 §3.2](3-process/PLAYBOOK-001-cs-escalation.md) |
| SEC-001 §6.1 Go/No-Go checklist | 0 / 13 ✅ | 13 / 13 ✅ | SEC-001 §6.1 |

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

1. **OBS-001 §10 W1 交付**：Prometheus + Grafana + Loki on Hetzner；service 出 Golden Signals
2. **TEST-001 §10 W1 交付**：測試骨架 + CI gates；TC-001, 010, 030 happy path
3. **SEC-001 §6.1 Go/No-Go 開始打勾**：13 項中先攻 HMAC 驗證、RLS、secret scanning、TLS
4. **接 RUNBOOK-001 primary oncall**：通報路徑（Slack / PagerDuty）設置完成

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

白皮書敘事檔 (00-07, 99)、北極星願景 (07)、投資人視角 (05)、ADR 全集、法務模板、招募 JD、visual prompts、附錄 A/B/D/E/G/J

---

*上次更新：2026-05-16 | 更新者：CTO（新增 Engineering Health section）*
