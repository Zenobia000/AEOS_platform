---
id: PILOT-ICP-2026-05
title: Pilot Customer ICP and Target List
status: draft
type: exploration
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CEO + CTO
tier: 4
related: [PILOT-001, PRD-001, BF-001, 04-strategy-business]
---

# PILOT-ICP-2026-05 — Pilot 客戶 ICP 與目標名單

> 「**Pilot 不是賣得越多越好，是學得越多越好。**」5 家對的客戶 >> 15 家錯的客戶。本文鎖定 ICP（Ideal Customer Profile），列出目標清單，定義篩選與淘汰標準。

## 1. ICP 定義（Ideal Customer Profile）

### 1.1 公司條件（Firmographic）

| 維度 | 條件 |
|---|---|
| **規模** | 員工 10~200 人；年營收 $500K~$10M USD |
| **產業** | 電商 / SaaS / 數位服務 / 教育訓練 / 諮詢服務（**不**金融、醫療、政府） |
| **地域** | 台灣（語言 + 法遵熟悉度）；Phase 2 拓海外華語區 |
| **成熟度** | 已有 LINE 官方帳號 ≥ 6 個月；月對話量 ≥ 500 則 |
| **數位化程度** | 已用 CRM / 客服系統；不是「紙本作業」 |

### 1.2 痛點條件（Pain）

ICP 必須有至少 2 項：

- [ ] 客服 / 諮詢人力成本高（≥ 2 名專職客服 / 月薪總 ≥ NT$ 100K）
- [ ] 客戶問題高度重複（80% 問題可由 FAQ 答）
- [ ] 已有累積知識（FAQ、SOP、產品說明 ≥ 50 頁）
- [ ] 非工時客戶流失明顯（晚上/週末沒人接訊息）
- [ ] 想做客服自動化但 ChatGPT 內接太爛（試過但效果差）

### 1.3 採購條件（Buying Behavior）

- 決策者：老闆 / 創辦人 / 行銷主管（**不是**大企業採購流程）
- 預算：月 US$ 500~2,000 可決策範圍內（無需 board approval）
- 採購週期：1 ~ 4 週（不是 6 個月）
- 接受 Pilot 模式：願意共寫 50 題 test set + 提供反饋

### 1.4 文化條件（Cultural Fit）

- 老闆 / 主管「敢用 AI」：理解 AI 會出錯但願意 iterate
- 願意配合：每 2 週 30 分鐘 sync call、配合改 KB
- 不會「期望 100% 完美」（這種客戶後續會非常痛苦）
- 願意給 reference / case study（GA 後重要資產）

### 1.5 反向 ICP（淘汰標準）

**任一觸發 → 不接 Pilot**：

- ❌ 金融 / 醫療 / 法律 / 政府（合規負擔超出 Pilot 能力）
- ❌ 月對話量 < 200（學習樣本不足）
- ❌ 月對話量 > 50,000（規模超出 Pilot 容量）
- ❌ 沒有結構化知識（連 FAQ 都沒有）
- ❌ 要求「無條件 SLA」（Pilot 不適用）
- ❌ 預算 < US$ 500 或想免費（無 commitment）
- ❌ 不接受我方 sub-processor（OpenAI/Anthropic）
- ❌ 國際客戶（語言以外的時區、文化、合規負擔）

## 2. 用例分類（依痛點）

| Use Case | 主要場景 | 預期 Auto-reply 率 | 預期客戶月費 |
|---|---|---|---|
| **U1 — 電商客服** | 訂單查詢、退換貨、產品問題 | 70~80% | $500~1,000 |
| **U2 — SaaS 技術支援** | 功能使用、bug 通報、計費問題 | 60~70% | $1,000~2,000 |
| **U3 — 教育 / 課程** | 課程資訊、報名、進度詢問 | 75~85% | $500~800 |
| **U4 — 專業諮詢預約** | FAQ + 預約引導 | 70~80% | $500~1,000 |

Pilot 5 家分布建議：U1 × 2, U2 × 1, U3 × 1, U4 × 1（多樣性學習）。

## 3. 目標客戶池（Target List）

> 此清單為**模板示例**；實際填入 CEO/CTO 既有 network。每位列為候選須有：聯絡人 + 預估規模 + 痛點 + 已試過什麼。

### 3.1 候選清單格式

| # | 公司名 | 產業 / 用例 | 規模 | 聯絡人 | 痛點摘要 | 已試過 | 狀態 | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | <<填入>> | <<U1 電商>> | <<50 人>> | <<姓名/職位>> | <<客服 3 人，週末沒人接>> | <<試過 ChatGPT 內接，效果差>> | 待初訪 | |
| 2 | <<填入>> | <<U2 SaaS>> | <<30 人>> | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |
| 6 | | | | | | | | |
| 7 | | | | | | | | |
| 8 | | | | | | | | |
| 9 | | | | | | | | |
| 10 | | | | | | | | |

### 3.2 名單來源

- CEO/CTO 既有 network（最高 conversion，最先談）
- 既有種子用戶 / 早期 sign-up
- 推薦來源（投資人、顧問引薦）
- 內容 inbound（部落格、IG、LinkedIn 帶來的詢問）
- 冷觸（最低 conversion，不投入大量時間）

### 3.3 漏斗目標

```
30 個 ICP-matched 候選
    ↓ 60% 同意 initial call
18 個初訪
    ↓ 50% 進入 POC discovery
9 個 POC 規劃
    ↓ 60% 簽 Pilot
5 個 Pilot 客戶  ← PILOT-001 §1 規模
```

時程：2026-05-15 ~ 2026-05-31（兩週 sales sprint）。

## 4. Discovery 訪談大綱（30 min）

### 4.1 暖場（5 min）
- 公司 / 業務簡介
- 我方背景（不超過 3 句）

### 4.2 現況（10 min）
- 目前客服流程？幾人？工具？
- 客戶問題 Top 3？
- 平均處理一個對話多久？
- 月對話量 / 非工時佔比？
- 既有 KB / FAQ 數量 / 結構？

### 4.3 痛點（5 min）
- 最痛的環節？
- 為什麼還沒解？
- 試過什麼？為什麼沒成功？
- 不解這個會怎樣？

### 4.4 我方提案（5 min）
- 7 天 onboarding 流程（PRD-001）
- Pilot 條件：月費 50% off + 共寫 50 題
- 12 週後決定是否進 GA

### 4.5 收尾（5 min）
- 興趣 / 顧慮
- 下一步：發送 follow-up + 試算 → 決策週

## 5. Pilot 簽約條件

對應 LEGAL-002 SOW 範本：

| 項目 | 條件 |
|---|---|
| 試用期 | 12 週（2026-06-01 ~ 2026-08-31，含 1 週 onboarding） |
| 費用 | 標價 50% off；按月 NT$ TBD |
| 退出 | 任一方 14 天書面通知；資料 30 天內回傳 + 刪除 |
| 義務 | 共寫 50 題 test set；每兩週 30 min sync；提供反饋；接受 case study（後續）|
| SLA | PILOT-001 §2.1 + PLAYBOOK-001 §3 |
| 資料 | LEGAL-001 DPA |
| 轉 GA | Week 12 雙方協商 GA 條件 |

## 6. 客戶健康評分（每兩週 update）

每 Pilot 客戶在 Notion / Airtable 維護一個 health score（1~5）：

| 維度 | 5（綠） | 1（紅） |
|---|---|---|
| **使用率** | 月對話量 > 預估 80% | < 30% |
| **回饋頻率** | 每週主動反饋 | 連續 2 週靜默 |
| **NPS** | ≥ 8 | ≤ 4 |
| **支付準時** | 準時 | 拖延 / 拒繳 |
| **共寫進度** | test set 已寫 ≥ 80% | < 30% |

整體紅 / 黃 → 立即 outreach。

## 7. Pilot 之後

- 至少 3 家轉 GA = Pilot 成功（PILOT-001 §2.2）
- 拒簽 GA 客戶 → exit interview 取得「為什麼不簽」洞察
- 成功轉 GA 客戶 → 索取 case study + 推薦 reference

---

**See also**:
- `PILOT-001-success-criteria.md` — Pilot 整體標準
- `PRD-001-7day-ai-cs-onboarding.md` — 產品定義
- `BF-001-customer-onboarding.md` — Onboarding flow
- `LEGAL-002-SOW-template.md` (TODO) — Pilot 合約範本
- `04-strategy-business.md` — 整體 GTM 策略
- `PLAYBOOK-001-cs-escalation.md` §8 — Pilot 客戶承諾
