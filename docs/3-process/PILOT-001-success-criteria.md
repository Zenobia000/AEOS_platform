---
id: PILOT-001
title: Pilot Success / Kill Criteria
status: active
type: pilot-criteria
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO + CEO
tier: 3
related: [PRD-001, BF-001, AC-001-to-005, NFR-001, PROJ-001]
---

# PILOT-001 — Pilot 成功與終止標準

> **定錨整個 Pilot 的單一文件。** 沒有客觀標準，3 個月後會陷入主觀爭論；GA 決策必須建立在這些可量測指標上。

## 1. Pilot 範圍定義

| 項目 | 值 |
|---|---|
| **Pilot 期間** | 2026-06-01 ~ 2026-08-31（13 週，對應 PROJ-001 S1~S12） |
| **Pilot 客戶數** | 3 ~ 5 家（中小企業 / SaaS 客服場景） |
| **每客戶 AI 員工數** | 1 ~ 2 名 |
| **使用者規模** | 每客戶 ≤ 500 終端使用者 / 月 |
| **付費模式** | 試點價（月費 50% off）+ 共寫 50 題 test set 義務 |
| **退出機制** | 任一方 14 天書面通知終止；資料於 30 天內回傳 + 刪除 |

## 2. ✅ Success Criteria — 全部滿足才可宣告 GA-Ready

### 2.1 產品健康（Product Health）

| 指標 | 目標 | 量測方式 | 來源 |
|---|---|---|---|
| **AI auto-reply 採用率** | ≥ 70% 對話完全自動處理（無人介入） | `conversation.auto_resolved / total` | 對應 AC-001 |
| **回答準確度**（test set） | ≥ 85% 通過率 | 共寫 50 題每週跑 | 對應 AC-002 |
| **人類介入正確率** | ≥ 95% 當 AI 不確定時正確 escalate | escalation correctness audit | 對應 AC-003 |
| **End-to-end latency p95** | ≤ 8s | NFR-001 §1 | NFR-001 |
| **可用性** | ≥ 99.5%（月度） | uptime monitor | NFR-001 §2 |

### 2.2 商業健康（Commercial Health）

| 指標 | 目標 | 量測方式 |
|---|---|---|
| **Pilot 留存率** | ≥ 60%（5 家中至少 3 家續約 GA） | 簽約轉換 |
| **NPS（Pilot 客戶）** | ≥ 30 | 月度問卷 |
| **Pilot → GA 升級意願** | ≥ 3 家明確表達 LOI | 訪談紀錄 |
| **單 tenant 月毛利率** | ≥ 50%（含 LLM 成本） | 對應 QUOTA-001 cost model |

### 2.3 技術健康（Tech Health）

| 指標 | 目標 |
|---|---|
| **無 P0 事故** | Pilot 期間 0 次資料外洩、0 次永久資料遺失 |
| **P1 事故** | ≤ 2 次/月，且每次 24 小時內 RCA |
| **LLM cost overrun** | ≤ 預算 110%（QUOTA-001 monthly cap） |
| **Test coverage** | ≥ 80%（NFR-001 §6） |
| **Deployment frequency** | ≥ 每週 1 次（可控部署能力證明） |

## 3. ❌ Kill Criteria — 任一觸發則暫停 Pilot 並重新評估

| # | 觸發條件 | 動作 |
|---|---|---|
| K1 | **P0 事故**（資料外洩 / 永久遺失 / 服務中斷 > 4 小時） | 立即啟動 RUNBOOK-001 §危機通報；72 小時內 RCA + 客戶通報；CEO/CTO 決定是否繼續 |
| K2 | **連續 2 個月可用性 < 99%** | 暫停新客戶 onboarding，全力修穩定性 |
| K3 | **LLM 月成本超預算 150%** 且毛利率 < 0% | 啟動 QUOTA-001 §緊急降級；暫停高耗能 feature |
| K4 | **2 家以上 Pilot 客戶主動終止** | 召開 product offsite，重新評估 PMF 假設 |
| K5 | **連續 2 週 test set 通過率 < 70%** | 凍結新功能開發，全力修品質 |
| K6 | **核心人員流失**（CTO / 唯一 LLM engineer 離職） | 暫停新承諾，啟動 HIRING-001 接班計畫 |

## 4. Decision Gates

### Gate 1 — Week 4 Checkpoint（2026-06-30）

**目的**：技術可行性確認。
**Go 標準**：
- 至少 1 家客戶完成 onboarding 並進入 production
- Auto-reply rate ≥ 50%（早期門檻）
- 無 P0 事故

**No-Go 動作**：延長 S1~S4 範圍 4 週；不擴大客戶。

### Gate 2 — Week 8 Checkpoint（2026-07-31）

**目的**：產品市場匹配確認。
**Go 標準**：
- 3 家客戶 production
- Auto-reply rate ≥ 65%
- NPS ≥ 20

**No-Go 動作**：暫停新客戶；focus on 既有客戶健康度。

### Gate 3 — Week 13 GA Decision（2026-08-31）

**目的**：是否進入 GA。
**Go 標準**：§2 全部達標。
**No-Go 動作**：延長 Pilot 4~8 週；或回到 Phase 0 修正 PMF 假設。

## 5. 量測與通報

| 頻率 | 對象 | 內容 | 工具 |
|---|---|---|---|
| 每日 | Engineering | latency p95 / error rate / LLM token spend | OBS-001 dashboard |
| 每週 | 客戶 + 內部 | auto-reply rate / accuracy / 重大事件 | weekly email + Slack |
| 每兩週 | 全 Pilot 客戶 | 共同 retro + roadmap sync | 1-hour Zoom |
| 每月 | Investor / Board | 全部 KPI + 財務 | Board deck |

## 6. 責任歸屬

| 指標類 | Owner | Backup |
|---|---|---|
| Product Health | CTO | LLM engineer |
| Commercial Health | CEO | CTO |
| Tech Health | CTO | DevOps（如已 hire） |
| Kill Criteria 啟動 | CEO + CTO 共同決議 | 任一可單方暫停 |

## 7. 版本與審計

- 本文件每次 Gate checkpoint 後更新「實績」欄位（後續加入）
- 任何標準調整需 CR（Change Request）+ 雙方同意
- Pilot 結束 7 天內出 **Pilot Postmortem** → `docs/4-exploration/PILOT-POSTMORTEM-2026-08.md`

---

**See also**:
- `PRD-001-7day-ai-cs-onboarding.md` — 產品定義
- `AC-001-to-005-acceptance-criteria.md` — 功能驗收
- `NFR-001-non-functional-requirements.md` — 技術指標基線
- `QUOTA-001-llm-budget.md` — 成本上限
- `RUNBOOK-001-incident-response.md` — Kill criteria 觸發後的程序
