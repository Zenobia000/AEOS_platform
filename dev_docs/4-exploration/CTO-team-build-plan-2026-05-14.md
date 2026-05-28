---
name: cto-team-build-plan
description: CTO 視角的 AEOS 團隊建置與必備文件規劃，針對 bootstrapped + 已有 pilot + 1-3 人小團隊的具體情境
status: active
type: exploration
created: 2026-05-14
owner: CTO
tier: 4
---

# AEOS 團隊建置與必備文件規劃（CTO 視角）

## Context

**為什麼做這個規劃**：`docs/` 已完成白皮書 v1.0（4,048 行，9 主文 + 10 附錄），策略密度極高，但目前是**純文件階段，0% 程式碼**。CTO 的第一個責任不是「照白皮書蓋一個 14 人團隊」，而是把白皮書翻譯成**可執行的 90 天 MVP 計畫**，並判斷「現在該招誰、現在該寫哪些文件、現在不該做什麼」。

## 你的具體狀態（規劃基礎）

| 變數 | 狀態 | 對規劃的影響 |
|---|---|---|
| **團隊** | 1–3 人小團隊已組 | Phase 1 **不該再招人**，先把現有人配置打通 |
| **資金** | Bootstrapped / 自有 | Setup Fee 是現金流命脈，**每個 pilot 至少 50K NTD setup + 月費**，不夠不收 |
| **客戶** | 已有 1+ 願付費 pilot | 跳過「假設驗證」階段，直接共創、回收現金 |

**這個組合的特性**：
- ✅ **乾淨**：有人付錢 → 不是 PPT 公司；自有資金 → 沒有 VC 逼成長的扭曲
- ⚠️ **危險**：bootstrapped 最容易掉進「客製化外包陷阱」，賺到錢但變成 service company
- 🎯 **CTO 的真正工作**：在 service work 與 product work 中切出護城河 — 每接一個 pilot，必須抽出至少 1 個跨客戶可重用的 Skill / Template，否則就是在燒自己的命

**Linus 第五準則套用**：理論上 bootstrapped 該招 4 人 Phase 1 團隊。實務上你沒這筆錢。**Theory loses.** Phase 1 真實答案是「3 人 + 1 個 pilot 跑通」。

**白皮書已經給的硬約束**（Phase 1, 0–3 個月）：
- 1 個角色（AI 客服 / 接單員）
- 3 個工具（Knowledge / FAQ / 1 個外部 API）
- 1 個租戶（pilot customer）
- 7 天上線
- 團隊 ≤ 5–7 人（player-coach 模式）

CTO 不能違背這個約束去蓋大平台。

---

## 1. 商業現實判讀（CTO 看完白皮書的 5 個結論）

| # | 結論 | 對應工程決策 |
|---|---|---|
| 1 | **Wedge 是 AI 藍領，不是 AI Copilot** | 不蓋 web-first 後台；LINE / WhatsApp / 行動優先 |
| 2 | **真正的護城河是「三個 Compiler」**（資料→知識 / 知識→技能 / 對話→改善） | 不蓋 Agent Framework；蓋資料管線與治理 |
| 3 | **客戶買的不是 LLM，是治理與可追溯性** | 第一行程式碼就要有 audit log + Skill 版本化 |
| 4 | **Pricing 是 Setup Fee + 月費**（10–50K NTD setup） | 第一階段允許「半人工 onboarding」，不必全自動 |
| 5 | **Phase 1 KPI：7 天上線 + 專家 ≤ 3 小時** | MVP 範圍砍到「Knowledge Card + Draft Mode + 監看儀表」就停 |

**Linus 第三準則套用**：白皮書講的 SkillOps / Tool Gateway / Multi-tenant / Policy Engine 在 Phase 1 **都不該全建**。Phase 1 只要能驗證「7 天讓一家小店有 AI 客服」這一件事。

---

## 2. 團隊建置策略（分三階段，依里程碑解鎖）

> **核心鐵律**：每個階段先驗證一個假設，假設過了再解鎖下個階段的招募預算。不要超前部署。

### Phase 1（0–3 個月）：把 pilot 跑通 + 抽出第一份可複用 SOP — **不招人，用現有 1–3 人**

**目標**：
1. 把現有 pilot 客戶從「demo 階段」推進到「production live + 客戶願意 case study 推薦」
2. **抽 1 份跨客戶可重用的 Skill Template**（這是你還沒驗證的最重要假設）
3. **驗證 setup fee 單位經濟**：1 個 pilot 上線需要的「自有人力小時數」必須 ≤ setup fee / 你的 hourly cost。算不過 → 商業模式破

**現有 1–3 人怎麼分工**（player-coach 模式，沒有純管理職）：

| 你目前的人 | Phase 1 角色定位 | 不該做的事 |
|---|---|---|
| **創辦人 / 你（CTO）** | 70% 寫 code（治理核心 + Knowledge 管線）、20% 跟客戶、10% 寫 ADR / SAD | 不要花時間做 deck、不要去寫 marketing 文案 |
| **隊員 A**（若是工程） | Onboarding Wizard + LINE bridge + 客戶交付 | 不要去研究 Agent Framework |
| **隊員 B**（若是業務 / 領域） | Pilot 客戶 success + 把 SOP 抽成 Knowledge Card schema | 不要再去找新客戶（先把現有 pilot 做到 case study）|

**如果你的 3 人裡缺工程能力**：
- 第一個外援應該是**合約制 Full-stack（part-time, 月費 30-60K NTD）**，3 個月後若 pilot 成功且第二客戶簽約，再轉正職
- **絕對不要全職招 senior**：bootstrapped 公司全職 senior = 6 個月內現金流斷裂

**這階段刻意不做的事**：
- ❌ 招 DevOps / SRE / Designer / Sales / QA / PM / Security — 任一個都會壓垮現金流
- ❌ 用 VC 等級的架構（K8s、Service Mesh、多模型 router）
- ❌ 同時開發兩個產品方向（必須 100% 服務這個 pilot）
- ❌ 接第二個 pilot 之前不投資任何「未來才用得到」的工程

**Phase 1 結束的硬指標**（任一沒達成 → 不解鎖 Phase 2）：
- [ ] 第一個 pilot 客戶 live 在生產環境
- [ ] 收到 setup fee + 至少 1 個月月費
- [ ] **抽出 1 份 Skill Template，可在 ≤ 2 小時內配置給第二客戶**
- [ ] 你（CTO）每週投入此 pilot ≤ 10 小時（否則無法擴張）

---

### Phase 2（3–9 個月）：Bootstrap 擴張 → 3–5 個付費客戶 — **擴到 4–5 人**

**解鎖條件**：Phase 1 四個硬指標全部達成 + 已收到 2 個獨立客戶的 setup fee。
**資金來源**：用 setup fee + 月費滾雪球，**不依賴外部募資**。

| 新增角色 | 人數 | 任務 | 為何 bootstrapped 也能負擔 |
|---|---|---|---|
| **Full-stack #2**（合約 → 正職） | 1 | Admin Console、Eval Dashboard、第二客戶交付 | 用第 2、第 3 個 pilot 的 setup fee 養 |
| **Customer Success / Onboarding Engineer** | 1 | 半人工 onboarding → SOP；客戶教育 | 直接 attribut 到月費續訂率 |
| **領域顧問**（part-time, equity + 小額現金） | 0.3 | 跨垂直 Skill Template 設計 | 用 equity，不耗現金 |

**這階段刻意不招的**：Designer（用 Tailwind UI / shadcn 模板）、GTM AE（客戶來自 pilot referral）、Security Lead、SRE、Data Engineer。

**Phase 2 結束的硬指標**：
- [ ] 3–5 個付費客戶，月經常性收入（MRR）≥ 30 萬 NTD
- [ ] **Skill reuse ≥ 50%**（第二客戶上線時 ≥ 50% 用既有 Skill Template）
- [ ] 客戶 NRR ≥ 100%
- [ ] 達成後再決定：繼續 bootstrap 還是募 Seed（不是 default 必募）

---

### Phase 3（9–24 個月）：是否募資的選擇點 + 規模化 — **依路線分歧**

**到這個時點你會面對兩條路**：

| 路線 | 條件 | 團隊規模 |
|---|---|---|
| **A. 繼續 Bootstrap**（service 化為主） | MRR ≥ 100 萬，現金流穩，創辦人想保有控制權 | 8–12 人 |
| **B. 募 Seed → Series A**（產品平台化） | Skill reuse 跨垂直驗證、NRR ≥ 120%、想加速 | 15–25 人 |

**路線 B 子團隊拆分**：

```
Platform 團隊 (5–7 人)        Skills / Vertical 團隊 (4–6 人)    Customer / Onboarding (4–6 人)
├── Runtime / LLM 整合        ├── 餐飲垂直 Skill Pack            ├── Onboarding Engineer
├── Tool Gateway              ├── 零售垂直 Skill Pack            ├── Customer Success
├── Skill Registry            ├── 長照垂直 Skill Pack            ├── Solution Engineer
├── Policy Engine             └── Skill QA / Eval                └── Implementation Manager
└── Multi-tenant infra

跨團隊 (3–5 人)
├── Security & Compliance Lead（SOC 2 籌備）
├── SRE / DevOps
├── Data Engineer（成本歸因、eval data warehouse）
└── PM × 1–2
```

---

## 3. 必備文件清單（按 6 層穩定性 Tier）

### Tier 0 — Principles ✅ 基本完備
- ✅ Mission / Non-goals：`00-executive-summary.md`, `06-risk-boundaries.md`
- ✅ 技術不變式：`02-product-architecture.md`
- 🆕 **Engineering Charter**：`docs/0-principles/engineering-charter.md`（已新增）

### Tier 1 — Decisions / ADRs ❌ 完全缺失，分批補

| ADR | 必要性 | 何時寫 |
|---|---|---|
| ADR-0001：LLM Provider 策略 | CRITICAL | **Week 1** ✅ |
| ADR-0002：Agent Runtime 自建 vs 包 | CRITICAL | **Week 1** ✅ |
| ADR-0003：Skill Registry 儲存與版本化 | CRITICAL | **Week 1–2** ✅ |
| ADR-0004：部署模型 | HIGH | **Week 1** ✅ |
| ADR-0005：資料保存與 PII 政策 | HIGH | **Week 2** ✅ |
| ADR-0006：MCP Host 實作策略 | MEDIUM | Week 8–10 |
| ADR-0007：多租戶隔離模型 | MEDIUM | Phase 2 初 |
| ADR-0008：Frontend stack | LOW | 前端入職前 1 週 |
| ADR-0009：成本歸因模型 | LOW | Phase 2 後段 |
| ADR-0010：Eval / Quality Gates 演進 | MEDIUM | 隨 pilot 經驗補 |

**Bootstrapped 鐵律**：每份 ADR ≤ 1 頁，5 段（Context / Decision / Alternatives / Consequences / Status）。

### Tier 2 — Contracts ❌ 起手 v0 已建
- 🆕 Domain Model v0：`docs/2-contracts/domain-model.md`
- 🆕 DB Schema v0：`docs/2-contracts/db-schema.md`
- ⏳ SAD v0.1：Week 3–6 補
- ⏳ API Contracts (Onboarding + Skill)：Week 3–6 補

### Tier 3 — Process ⚠️ 部分有
- ✅ Pre-launch / Onboarding：`appendices/C, F, H, I`
- ⏳ Code Review Checklist：Week 4–6 補
- ⏳ Quality Gates 詳細版：Week 7–10 補
- ⏳ Incident Response v0：Week 7–10 補
- ⏳ Engineering Onboarding：Week 11–13 補

### Tier 4 — Exploration
- 🆕 此規劃檔
- 🆕 PRD-001 — 7-Day AI 客服 Onboarding：`docs/4-exploration/PRD-001-7day-ai-cs-onboarding.md`

### Tier 5 — Views（自動生成）— Phase 2 再啟用

---

## 4. 90 天執行優先序

```
Week 1–2  ┃ 客戶共識：跟 pilot 客戶共寫 50 題 test set + 收 50% setup fee
           ┃ 文件：寫 ADR-0001~0005（必要 5 份）+ Domain Model + DB Schema 起手版
           ┃ 動作：把整個 docs/ 結構搬成 6-tier 目錄
           ┃ ⚠️ 文件做 1 天就停，剩下時間寫 code

Week 3–6  ┃ 出貨：Onboarding Wizard MVP + Knowledge Card schema + Draft Mode
           ┃ 內部測試：對 pilot 客戶的 50 題跑通，accuracy ≥ 70% 才往下
           ┃ 文件：補 SAD（System Architecture v0.1）+ PRD-001
           ┃ ⚠️ 不要做 Eval Dashboard、不要做 Multi-tenant UI

Week 7–10 ┃ Pilot 上線：Draft Mode → Canary（10% 流量）→ Live
           ┃ 收尾 setup fee + 啟動月費；客戶簽 case study 同意書
           ┃ 文件：寫 Incident Response v0
           ┃ ⚠️ 這時你會很想開發新功能，忍住

Week 11–13 ┃ 抽 Template：把 pilot 的知識卡 / Skill / Policy 抽成「Vertical-X 通用模板 v1」
            ┃ 第二客戶試水：用 Template 對第二客戶試裝，量「配置時間」（必須 ≤ 2 小時）
            ┃ 文件：產出 ADR-0006~0010（依需要追加）、Engineering Onboarding v0
            ┃ 動作：寫 Phase 2 招募 JD + 估算現金流可否養新人
```

---

## 5. CTO 必須拒絕的事（Anti-patterns）

| 誘惑 | 拒絕的理由 |
|---|---|
| 「我們先把多模型 router 蓋好」 | Phase 1 一個模型就夠，省下兩週 |
| 「我們要先有 Kubernetes」 | Phase 1 一台 VM + Docker Compose 就夠 |
| 「先把 Policy Engine 蓋完整再上客戶」 | Policy Engine 在 Phase 1 = 一份 YAML + 人工 review |
| 「我們招個 Senior ML Researcher」 | 不需要訓練模型，需要的是治理工程 |
| 「我們做 Agent Marketplace / 多 agent orchestration」 | 白皮書明文 forbidden in MVP |
| 「先建 SOC 2 架構」 | 等客戶數到 10+ 再說，現在做就是 over-engineering |
| 「我們要支援 ERP / SAP 整合」 | 等到 Phase 3，第一階段只接 LINE + 1 個 API |

---

## 6. 驗證方式

| 時點 | 驗證指標 |
|---|---|
| Day 30 | 5 份 ADR + Domain Model + DB Schema v0；pilot 客戶 50 題 test set 共寫完 |
| Day 60 | MVP 跑通 happy path；pilot test set ≥ 70% pass；收 50% setup fee |
| Day 90 | Pilot live；收齊 setup fee + 1+ 月費；Skill Template v1 抽出；CTO 週工時 ≤ 10h on pilot |
| Day 180 | 3 個付費客戶；MRR ≥ 30 萬；Skill reuse ≥ 50%（Phase 2 解鎖） |
| Day 270 | 決策點：繼續 bootstrap vs 募 Seed |

---

## 7. 給 Bootstrapped CTO 的最後三句話

1. **每接一個 pilot 都必須讓平台「比上一次更通用」**。否則你不是在蓋產品，是在做客製化外包。
2. **文件是降本工具，不是裝飾**。寫 ADR 是為了下次不再吵同一件事，不是為了「看起來像有 process」。一份 ADR 1 頁。
3. **CTO 在 bootstrapped 階段最重要的能力不是寫 code，是說「不」**。對新功能說不，對新客戶（如果是白領場景）說不，對招 senior 說不，對 K8s 說不。每說一次「不」，現金流多撐 1 個月。
