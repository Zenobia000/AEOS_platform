---
id: LAUNCH-DASHBOARD
title: CEO Launch Dashboard
status: active
type: view
created: 2026-05-15
owner: CEO
tier: 5
related: [PROJ-001, PILOT-001, PRD-001, COST-MODEL-2026-05, PILOT-ICP-2026-05]
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

### 開發中按需查閱

UF/SF 流程、NFR、UX wireframe、threat model、test plan、observability spec、LINE webhook API、third-party integrations

### 不急（Phase 2+ 或特定場景才看）

白皮書敘事檔 (00-06, 99)、投資人視角 (05)、ADR 全集、法務模板、招募 JD、visual prompts、附錄 A/B/D/E/G/J

---

*上次更新：2026-05-15 | 更新者：CEO*
