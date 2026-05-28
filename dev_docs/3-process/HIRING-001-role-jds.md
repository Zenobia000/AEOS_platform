---
id: HIRING-001
title: Hiring Plan and Role JDs
status: active
type: hiring-plan
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CEO + CTO
tier: 3
related: [PROJ-001, COST-MODEL-2026-05, PILOT-001, CTO-team-build-plan-2026-05-14]
---

# HIRING-001 — 招募計畫與角色 JD

> 「**早期創業最貴的錯誤是太早或太晚 hire。**」本文定義 trigger 條件（什麼時候 hire）、各角色 JD（要 hire 什麼人）、面試流程（怎麼篩）。

## 1. Trigger 條件（什麼時候開始招）

招募決策 = MRR + 痛點 + runway 同時滿足。

| 角色 | Trigger（**全部滿足**才動） | Earliest 期 |
|---|---|---|
| **Senior LLM/Backend Engineer** | MRR ≥ $5K **AND** CTO 個人 > 50hr/週 ≥ 4 週 **AND** ≥ 9 個月 runway | Month 4 |
| **DevOps / SRE** | MRR ≥ $15K **AND** active incidents > 4/月 **AND** ≥ 9 個月 runway | Month 7 |
| **Customer Success Lead** | Paying tenants ≥ 15 **AND** CEO > 50% 時間 in CS | Month 6 |
| **Sales / GTM** | Pilot conversion ≥ 60% verified **AND** CEO < 50% 時間能 close | Month 8 |
| **Junior Backend Engineer** | 已 hire senior 並穩定 ≥ 2 個月 **AND** MRR ≥ $25K | Month 10+ |
| **Designer / Frontend Engineer** | UX 反覆是 churn 原因 **AND** MRR ≥ $20K | Month 9+ |

任何 trigger 未滿足前，**創辦人撐**。不可情緒化 hire。

## 2. 招募順序原則

```
創辦人（CEO + CTO + 1 Eng）   <-- 起點（PROJ-001）
        │
        ▼ Trigger 1
+ Senior LLM/Backend Engineer  ← 解 CTO 過勞 + 加快 product
        │
        ▼ Trigger 2 + 3 並行
+ Customer Success Lead        ← 解 CEO 客戶服務時間
+ DevOps / SRE                 ← 解 incident response 規模
        │
        ▼ Trigger 4
+ Sales                        ← 規模化 GTM
        │
        ▼ Trigger 5 + 6
+ Junior Engineer + Designer   ← 拓展工程與產品
```

## 3. 角色 JD

### 3.1 Senior LLM / Backend Engineer

#### 一句話定位
做出可靠的 AI 產品的工程師：既懂 LLM 整合也懂 prod-grade backend。

#### 招聘預算
- 月薪：US$ 5,000~7,000（or 等值 TWD）
- 期權：0.3% ~ 0.8% vest 4 年 1 年 cliff
- 工作型態：Hybrid（台北 1~2 天/週）or remote（時區限 UTC+6~+10）

#### 必備
- ≥ 5 年 backend 經驗（Python or Go preferred）
- ≥ 1 年 production LLM / agent 系統經驗（OpenAI/Anthropic SDK，非僅 demo）
- 熟悉 Postgres + Redis + queue 系統
- 寫過 prod-grade 系統（不只 prototype）
- 英文閱讀 ✅（contract / API doc）

#### 加分
- RAG / Vector DB 經驗（Qdrant, pgvector）
- 多租戶 SaaS 經驗
- Observability / SRE mindset
- 開源 contribution
- 中小團隊 / startup 經歷

#### 文化匹配
- 實用主義（Linus 信條 §3）
- 願意自己接 oncall
- 樂於 review 別人 PR
- 直接溝通（用問題不用情緒）

#### 不適合
- 想做 research 不想做 product
- 一切要 design doc 完美再寫 code
- 不願 hands-on 部署 / 看 log

#### 30/60/90 Day Plan
- **Day 30**：完成 onboarding；shipped 1 個 medium feature；接 1 次 oncall（shadowing）
- **Day 60**：獨立 own 1 個 service（如 quota-guard or prompt-registry）；接 P2 incident
- **Day 90**：能代替 CTO 的 50% 工程決策；接 P1 incident 主導

---

### 3.2 DevOps / SRE

#### 一句話定位
讓系統「半夜不出事，出事 5 分鐘止血」的人。

#### 招聘預算
- 月薪：US$ 4,500~6,500
- 期權：0.2% ~ 0.5%

#### 必備
- ≥ 4 年 SRE / DevOps 經驗
- 熟 Docker / K8s / Terraform / Ansible 至少 3 樣
- 熟 Prometheus / Grafana / Loki / Tempo（ADR-0008 stack）
- 寫過 production runbook
- 主導過 incident response

#### 加分
- 多 cloud 經驗（Hetzner + AWS + GCP）
- Postgres ops（replication, PITR, tuning）
- Cost optimization 經驗
- 接過 SOC 2 / ISO 審計

#### 30/60/90 Day Plan
- **Day 30**：接管 oncall primary；OBS-001 dashboards 完善
- **Day 60**：自動化 RUNBOOK-002 / 003 80% 操作；通過第一次外部 pentest
- **Day 90**：cost down 20%；MTTR 降至 < 1 小時

---

### 3.3 Customer Success Lead

#### 一句話定位
讓客戶**自己想續約**的人，不只是「處理客訴」。

#### 招聘預算
- 月薪：US$ 3,500~5,000 + 客戶留存 bonus
- 期權：0.2% ~ 0.4%

#### 必備
- ≥ 3 年 B2B SaaS CS 經驗
- 服務過至少 20 個 SaaS 客戶
- 有 onboarding + QBR + escalation handling 實戰
- 中文母語 + 商業英文

#### 加分
- AI / 客服產品經驗
- 寫過 CS playbook
- Sales-influenced（能識別 upsell / expansion 機會）
- 數據驅動（會看 product metric）

#### 文化匹配
- 客戶第一但不無條件 yes
- 能在客戶與工程之間翻譯
- 處理衝突不情緒化

#### 30/60/90 Day Plan
- **Day 30**：接管所有 Pilot 客戶溝通；建立 weekly cadence
- **Day 60**：主導 ≥ 2 個 Pilot → GA 轉換；建立 customer health scoring
- **Day 90**：churn rate < 10%；NPS ≥ 35

---

### 3.4 Sales / GTM Lead

#### 一句話定位
能在創辦人不在場、自己 close 訂單的人。

#### 招聘預算
- 月薪 base：US$ 3,000~4,500
- Commission：年度業績的 5~10%（OTE: $60K~100K）
- 期權：0.3% ~ 0.6%

#### 必備
- ≥ 3 年 B2B SaaS sales 經驗
- 個人 close 過 ≥ 20 個 $5K+ ACV 訂單
- 熟 outbound + inbound + referral 多管道
- 有 CRM workflow 紀律（Notion / HubSpot）

#### 加分
- AI / 客服 / 中小企業 segment 經驗
- 既有 network in ICP（PILOT-ICP-2026-05 §1）
- 寫過 sales playbook

#### 30/60/90 Day Plan
- **Day 30**：完成 product enablement；shadow CEO 5 次 demo；接 5 inbound leads
- **Day 60**：獨立 close ≥ 2 新客；建立 outbound playbook
- **Day 90**：MRR contribution ≥ $5K from new logos

---

### 3.5 Junior Backend Engineer

#### 一句話定位
有 senior 帶就能快速產出的執行者。

#### 招聘預算
- 月薪：US$ 2,500~3,500
- 期權：0.1% ~ 0.2%

#### 必備
- ≥ 1 年 backend 經驗 OR 應屆 + 強 portfolio
- Python or TypeScript 主力
- 寫過至少一個 prod-deployed 專案
- 願意被 code review 並改進

#### 加分
- LLM tinkering（個人 project）
- 寫過測試
- 開源 contribution（即使小）

---

### 3.6 Designer / Frontend Engineer

#### 一句話定位
讓 tenant admin / end-user 第一次用就會用的人。

#### 招聘預算
- 月薪：US$ 3,000~5,000
- 期權：0.2% ~ 0.4%

#### 必備
- Figma + React/Next.js 熟練
- ≥ 3 年 B2B SaaS / dashboard UX 經驗
- 能 hands-on coding（不只 design）
- 有 design system 經驗

---

## 4. 面試流程（所有角色）

```
1. Sourcing
   - LinkedIn outreach
   - 既有 network referral（priority）
   - AngelList / 104 / Cake（local）
   - Open source / GitHub（for eng）

2. Phone screen（30 min, CEO 或 CTO）
   - 動機 + 經歷
   - 文化匹配快篩

3. Skill round（60~90 min）
   - Engineer: live coding（中等難度，重 problem-solving > 演算法）
   - CS: case study + role play
   - Sales: pitch back + objection handling
   - DevOps: incident scenario walkthrough

4. Take-home（≤ 4 小時）
   - Engineer: 小型 feature implementation
   - CS: 寫一份 onboarding plan for 假設客戶
   - Sales: 寫一個 outbound campaign for 假設 ICP

5. Final（CEO + CTO + 未來同事 1）
   - Take-home review
   - Culture deep dive
   - Q&A from candidate
   - Reference check （≥ 2，至少 1 個前主管）

6. Offer
   - 24~48 小時回覆
   - 包含期權 vesting schedule
   - 試用 3 個月（國際慣例）

整體目標 timeline：phone screen → offer ≤ 2 週
```

## 5. 公開招募文案範本

放在公司網站 `/careers` + LinkedIn job posting：

```
## We're hiring: Senior LLM/Backend Engineer

**About us**: AEOS builds production-grade AI employees for SMB customer service. Pilot in progress with 5 paying customers. ~$XX in funding/revenue.

**Why now**: We've validated the wedge. The AI infrastructure decisions are made. The product works. We need a second engineer who's actually shipped LLM systems to production—not just played with notebooks.

**What you'll do**:
- Build / own production systems (Python + Postgres + LLM agents)
- Take ownership of a major component (agent runtime, RAG, or quota-guard)
- Participate in oncall rotation (~1 week / month)
- Help shape product direction

**Required**:
- 5+ years backend engineering
- 1+ year production LLM/agent integration
- Comfortable with ambiguity but disciplined about tests, observability, and post-mortems

**Compensation**:
- $5K~7K USD / month
- 0.3~0.8% equity
- Remote or Taipei hybrid

**How to apply**: Send a link to one production system you built (with brief description of what was hard) to <<email>>.
```

## 6. Onboarding Checklist（所有 hire）

| Day | Item |
|---|---|
| -7 | Offer accept；準備設備、帳號 |
| -1 | Welcome email + Day 1 schedule |
| 1 | Slack / GitHub / 1Password / Linear / Notion 開通；讀 0-principles + 1-decisions |
| 2 | Local 環境設好；跑通 dev；接 1 個 small first-PR（typo or test） |
| 3 | 與每位 founder 1:1（45 min each）|
| 4-5 | Shadow CTO 或 CEO 一天 |
| 6-10 | 第一個 medium task（≤ 1 週可完成）|
| 14 | 30-day plan 對齊 |
| 30 | 30-day check-in；雙向反饋 |

## 7. 開除 / 不續用標準（明確期望）

文化：**清晰的 expectation + 明確的 reedback 循環 + 短的 review cycle**。

### 7.1 試用期 3 個月

- 30 天 / 60 天 / 90 天 check-in；不達標 → 提早結束（無 stigma，且我方先說明）

### 7.2 試用後 PIP（Performance Improvement Plan）

- 連續 2 個 quarter 未達 OKR ⇒ PIP（4~8 週明確改進目標）
- PIP 結束 review；達標 continue；未達 mutually exit

### 7.3 立即 termination 條件

- 違反 confidentiality / 資料安全
- 騷擾 / 歧視
- 重大不誠信

## 8. 多元與包容

主動做的：

- JD 不寫「years of experience」hard limit > 用「demonstrate X」
- Sourcing pool 多元（不只 Stanford / NTU 校友）
- 面試 panel 多元（避免單一視角篩人）
- Code-test 提供合理時間（4 小時 max）
- 開放遠距 / hybrid

## 9. 預算上限（Year 1）

對應 COST-MODEL-2026-05 §2.2 假設：

| Quarter | 累計人數 | 月人力成本 USD |
|---|---|---|
| Q1（Pilot Month 1~3） | 3（CEO+CTO+Eng1） | $13K |
| Q2 | 4（+Senior Eng） | $19K |
| Q3 | 5~6（+CS, +DevOps） | $27~33K |
| Q4 | 6~7（+Sales） | $32~38K |

Year 2 Q1 預估 9~10 人，月人力 $50K。

任何超出 → board / investor approval。

---

**See also**:
- `CTO-team-build-plan-2026-05-14.md` — 既有 team build 思考
- `PROJ-001-90day-sprint-plan.md` — RACI 起始
- `COST-MODEL-2026-05.md` §2.2 — 預算上限
- `PILOT-001-success-criteria.md` §3 K6 — 核心人員流失 kill criteria
- `PILOT-ICP-2026-05.md` — Sales hire 對應的 ICP
