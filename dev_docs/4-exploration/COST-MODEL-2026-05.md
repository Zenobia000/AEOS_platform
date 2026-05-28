---
id: COST-MODEL-2026-05
title: Unit Economics and Cost Model
status: draft
type: exploration
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CEO + CTO
tier: 4
related: [PILOT-001, QUOTA-001, ADR-0001, ADR-0004, ADR-0008, PILOT-ICP-2026-05]
---

# COST-MODEL-2026-05 — 單位經濟與成本模型

> 「**Pilot 期間不能停止思考錢從哪來、要燒到哪。**」本文是內部用，定義單 tenant 毛利、固定成本、Pilot 期 burn rate、GA 期可擴展性。

## 0. TL;DR

| 指標 | Pilot（單 tenant） | GA（單 tenant，預估） |
|---|---|---|
| 月費（標價） | US$ 1,000 | US$ 1,000~2,000 |
| Pilot 折扣 | 50% off → 500 | n/a |
| 直接成本（LLM + infra + sub） | ~$280 | ~$250 |
| **毛利率（Pilot）** | ~44% | n/a |
| **毛利率（GA）** | n/a | **~75%** |
| 突破點 tenant 數（cover fixed cost） | n/a | **~12 paying tenants** |
| 月固定成本（infra + 人力 + tooling） | ~$10K | ~$12~15K |
| Pilot 期月 burn（5 tenant 假設） | **~$7.6K/month** | n/a |
| GA 期 break-even tenant 數 | n/a | **~15** |

詳細展開見下方。

---

## 1. 單 tenant 變動成本

### 1.1 LLM Cost（最大變動）

依 QUOTA-001 §1.2 假設使用 OpenAI gpt-4o-mini，平均對話 ~$0.00048。

| 月對話量 | LLM Cost | 占月費 |
|---|---|---|
| 1,000 | $0.50 | 0.05% |
| 5,000 | $2.40 | 0.24% |
| 10,000 | $4.80 | 0.48% |
| 50,000 | $24 | 2.4% |
| 100,000 | $48 | 4.8% |
| 500,000 | $240 | 24% |

**關鍵發現**：對 ICP（月對話 1K~50K）來說，LLM 成本占月費 < 5%。**勝負不在 LLM 成本，在固定成本攤平**。

但要警惕：
- 一次 prompt injection 或 agent loop 可瞬間燒 10K 對話的量 → QUOTA-001 §6 hard cap 是命脈
- T2/T3 模型（gpt-4o, claude-opus）單價 25~150 倍 → router 必須誠實降級到 T1

### 1.2 RAG / Vector DB

- Embedding：OpenAI text-embedding-3-small，$0.02/M tokens
- KB chunk 500 token × 1000 chunks = 500K tokens = $0.01（一次性）
- 重 ingest：每年 ~1 次 → 可忽略
- Vector DB（Qdrant self-host）：含在 infra 固定成本

### 1.3 第三方服務（per tenant attributable）

| 項目 | 月成本 |
|---|---|
| LINE push messages（假設 Pro Plus 已含） | $0（含在 LINE 月費內，客戶自付）|
| Email（Postmark）：~50 emails/tenant/month | $0.05 |
| Object storage（5GB/tenant） | $0.05 |
| Sub-total per-tenant attributable | **~$5（包含 LLM + 餘）** |

### 1.4 Pilot 期單 tenant 直接成本（5 家 Pilot 平均）

假設 Pilot 客戶用量保守（月對話 5K，KB ingest 一次，無 abuse）：

```
LLM:        $2.40
Embedding:  $0.10
Email:      $0.05
Storage:    $0.05
Misc:       $0.30
─────────────────
Subtotal:   ~$3 / tenant / month
```

非常低。**Pilot 期真正燒錢的是固定成本不是變動**。

### 1.5 預計 GA 期單 tenant（U2 SaaS, 月對話 20K）

```
LLM (gpt-4o-mini 主, 5% gpt-4o):  $20
Embedding (KB updates):             $1
Email:                              $0.20
Storage (20GB):                     $0.20
Misc:                               $1
────────────────────────────────────────
Subtotal:                          ~$22 / tenant / month
```

對應 US$ 1,000 月費 → 變動成本占 **2.2%**。極健康。

---

## 2. 固定成本（Pilot 期月度）

### 2.1 基礎設施

| 項目 | 月成本 | 備註 |
|---|---|---|
| Hetzner production server（CCX23, 4 vCPU, 16GB） | €30 = $35 | App + Postgres |
| Hetzner staging server（CX31） | €15 = $17 | |
| Hetzner observability server（CX31） | €15 = $17 | ADR-0008 |
| Hetzner storage box（1TB） | €4 = $5 | KB + backup hot |
| AWS / B2 S3 cross-region backup | $10 | |
| Cloudflare（free） | $0 | DDoS / DNS / TLS |
| Postmark email | $15 | starter |
| Sentry self-host | $0 | (Phase 1 self-host on existing server) |
| Better Stack uptime | $0 | free tier |
| Domain | $1 | $12/year |
| GitHub Team | $4 | per user |
| Linear / Notion | $20 | team |
| Misc SaaS（password mgmt, etc） | $15 | |
| **小計基礎設施** | **~$140/月** | |

### 2.2 人力（按 PROJ-001 假設 3 人團隊）

按市場價估月薪：

| 角色 | 月薪 USD（含勞健保） | 備註 |
|---|---|---|
| CEO（CEO 不一定領薪 Pilot 期；假設 50% 員工薪） | $4,000 | |
| CTO | $5,000 | 含期權 |
| LLM Engineer / Full-stack | $4,000 | |
| **小計人力** | **$13,000/月** | |

Pilot 期創辦人通常拿低於市場薪資；可調 $7~10K total burn from founder 補貼。

### 2.3 法務 / 會計 / 顧問

| 項目 | 月平均（攤平年度）|
|---|---|
| 律師（合約 review）| $200~500（不固定）|
| 會計（月結） | $100~300 |
| 顧問 / 諮詢 | $200 |
| **小計** | **~$500/月** |

### 2.4 行銷 / 業務（Pilot 期極省）

| 項目 | 月平均 |
|---|---|
| 內容（一個人兼） | $0（時間成本已含人力）|
| 廣告 | $200~500 |
| 活動 | $100 |
| **小計** | **~$300/月** |

### 2.5 月固定成本總計

| 場景 | 月總固定成本 |
|---|---|
| Lean（CEO 不領薪，CTO/Eng 半薪） | **~$6K** |
| Pilot baseline（市場薪資）| **~$14K** |
| 含緩衝（招新人前準備） | **~$18K** |

---

## 3. Pilot 期 Burn Rate

### 3.1 Income（Pilot 客戶月費收入）

假設 5 家 Pilot × NT$ 15,000（≈ US$ 470）/ month with 50% off：
- 標價 NT$ 30,000 × 50% = NT$ 15,000
- 5 家 × NT$ 15,000 = **NT$ 75,000 (~$2,300/月)**

收 12 週 = 3 個月 ≈ **$7,000 Pilot 期總收入**。

### 3.2 Burn

```
3 個月 × $14K/月（baseline 固定）= $42K
+ 5 tenant × $3 × 3 個月 = $45（可忽略）
- $7K（Pilot 收入）
─────────────────────────
Net Pilot burn ≈ $35K（3 個月）
```

折合月 **~$11.7K**。

### 3.3 Pre-Pilot Capital Need

```
Pilot burn:          $35K
GA preparation buffer:  $20K（hire, marketing, legal）
Safety margin (3 month runway post-Pilot): $42K
───────────────────────────────────────────
Total runway need:   ~$97K
```

對應 ~**US$ 100K seed funding** 或創辦人自掏。

---

## 4. GA 期經濟模型

### 4.1 單 tenant 經濟（U2 SaaS 典型）

```
月費（GA 標價）:     $1,000
變動成本:           -$22
──────────────────────────
單 tenant 月毛利:    $978
毛利率:              97.8% (per tenant marginal)
```

但這不算入固定成本（基礎設施 / 人力 / 行銷）。真實情況：

```
全公司月支出（人力 / infra / 行銷 / 法務）：~$15~25K（隨成長）
```

### 4.2 Break-even Tenant 數

| 月固定成本 | Break-even（每 tenant 平均 $800 月費）|
|---|---|
| $15K | **19 tenants** |
| $20K | **25 tenants** |
| $30K | **38 tenants** |

中位數：**~25 paying tenants** = break-even。

對應 Pilot 後路徑：
- Month 1~3 Pilot：5 tenants（$2.3K MRR）
- Month 4~6 早期 GA：10 paying tenants（$8K MRR）
- Month 7~12：25 paying tenants（$20K MRR，達 break-even）
- Year 2：50~100 tenants（$40~80K MRR）

### 4.3 Sensitivity Analysis

**LLM 成本暴升 5 倍**（如 GPT-5 全面替換但價格未降）：

- per-tenant 變動成本 $22 → $110
- 仍占月費 11%
- 毛利率仍 ~89%（per tenant marginal）
- **結論**：LLM 漲價非致命

**對話量暴增**：
- 客戶月對話 200K（10 倍 ICP 假設）
- LLM 變動 $220
- 仍占月費 ~22%（如月費 $1,000）
- 但要重新議價：對話高的客戶月費應拉到 $2,000+
- QUOTA-001 §10 月度 review 觸發定價調整

**人力暴增**（hire 第 4~5 人）：
- 月固定增至 $30K
- Break-even 拉到 38 tenants
- 需在 Month 9~12 達成 → 與 Phase 2 GTM 配合

---

## 5. 風險與避免

### 5.1 LLM Cost 失控

- **風險**：prompt injection / agent loop / abuse 把月 LLM 燒到月費 50%
- **緩解**：QUOTA-001 全套機制；月度 review；T2/T3 router 嚴管

### 5.2 客戶超用但不加價

- **風險**：Pilot 期客戶 5K 對話/月，GA 後變 50K，但月費沒漲
- **緩解**：合約 Annex A usage allowance + overage clause（LEGAL-002 §4.1）

### 5.3 Churn

- **風險**：Pilot → GA 轉換率 < 預期；既有 GA 客戶 churn 高
- **緩解**：PILOT-001 §2.2 量化追蹤；NPS 月測；PLAYBOOK-001 主動介入紅燈客戶

### 5.4 固定成本失控（hire 太多）

- **風險**：MRR 還沒到 break-even 就 hire 5 人 → runway 燒光
- **緩解**：HIRING-001 hiring trigger 條件嚴格綁定 MRR / tenant 數

### 5.5 LLM provider 漲價或停服

- **風險**：OpenAI 突漲 2 倍 + Anthropic 配額不夠 fallback
- **緩解**：ADR-0001 多 provider 預備；每季 review；保留 open-source 模型 fallback option（Phase 3+）

---

## 6. 監控與 Cadence

### 6.1 Weekly（每週五）

- MRR / new bookings / churn（如有）
- 月度 LLM cost vs budget
- Cash on hand / runway

### 6.2 Monthly

- P&L summary
- Per-tenant economics review
- Vendor cost 變動
- 對應 PILOT-001 §5 monthly report

### 6.3 Quarterly

- Cost model 重算（基於實際 3 個月數據）
- 定價 review
- Vendor 替代方案評估

---

## 7. Key Levers for Improvement

依優先級：

1. **拉長平均合約期**：年付 vs 月付 → 改善現金流 + 減少 churn 計算負擔
2. **提高 ICP 月費上限**：U2 SaaS 客戶可接受 $1,500~2,000；U1 電商較難
3. **Usage-based add-on**：對話量 / 多 AI 員工 / 多 channel
4. **Cross-sell**：Phase 2 增加 channel（Messenger, web chat）= 月費 +30%
5. **降固定成本**：自動化運維（OBS-001 + RUNBOOK-* 完善）省下 1 名 Engineer

---

## 8. 投資人視角 KPI（為了 Series A）

未來 6~12 個月需 demonstrate：

| KPI | 目標（Year 1 末）|
|---|---|
| MRR | ≥ $20K |
| Paying tenants | ≥ 25 |
| LTV / CAC | ≥ 3x |
| Gross margin | ≥ 70% |
| Logo retention（年度） | ≥ 90% |
| NRR（Net Revenue Retention） | ≥ 110% |

---

**See also**:
- `PILOT-001-success-criteria.md` §2.2 — Commercial health 指標
- `QUOTA-001-llm-budget.md` — LLM 成本上限與 router
- `ADR-0001-llm-provider-strategy.md` — Provider 選擇與 fallback
- `ADR-0004-deployment-model.md` — Infra 選擇（Hetzner）
- `ADR-0008-observability-stack.md` — Self-host vs cloud 成本權衡
- `PILOT-ICP-2026-05.md` — 客戶月費假設來源
- `HIRING-001-role-jds.md` — hire 觸發條件
- `05-investor-thesis.md` — 投資人視角整合
