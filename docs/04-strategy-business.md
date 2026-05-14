# 戰略與商業

> **本檔對應原 whitepaper.md 的 §23~§25 (Part III)**
> 主題定位：戰略
> 最後同步：2026-05-14

## 相關章節速查

**本檔被外部引用的高頻章節**：
- §23.3 Adapter Contract 自握 — 被 §27 反覆引用作為 B1 反噬迴路緩解策略
- §23.4 Core / Supporting / Generic Domain 分層 — DDD 戰略決策依據
- §24.7 服務公司脫離指標 — 客戶導入時間 / Skill 重用率 / 客製 Adapter 比例
- §25.2 三階段商業模式演進 — Phase 1/2/3 定價

**本檔對外引用的章節**：
- §6.3 知識三分類 (見 `02-product-architecture.md`)
- §9 SkillOps (見 `02-product-architecture.md`)
- §11 安全合規 (見 `06-risk-boundaries.md`)
- §12 監控評估 (見 `02-product-architecture.md`)
- §13 多模型 (見 `02-product-architecture.md`)
- §15.3 五方責任契約 (見 `06-risk-boundaries.md`)
- §18 Onboarding Layer (見 `03-execution-onboarding.md`)
- §20 自動化成熟度 (見 `03-execution-onboarding.md`)
- §22 戰略定位 (見 `01-vision-positioning.md`)

---

## 23. 自研 vs 外包決策矩陣

### 23.1 鐵律與判斷原則

> **凡是不形成護城河的，外包。
> 凡是會累積資料、標準、流程、評分、客戶黏性的，握在手裡。**

#### 八點判斷矩陣

| 問題 | 答案是 Yes | 策略 |
| :--- | :--- | :--- |
| 會形成專有資料嗎？ | 是 | **自研** |
| 會決定客戶導入速度嗎？ | 是 | **自研** |
| 會影響安全與信任嗎？ | 是 | **自研** |
| 會成為評分與迭代閉環嗎？ | 是 | **自研** |
| 市面上已有成熟方案嗎？ | 是 | 外包 / 採購 |
| 客戶不會因為這個買單嗎？ | 是 | 外包 |
| 做了也難以差異化嗎？ | 是 | 外包 |
| 早期做了會拖慢交付嗎？ | 是 | 外包 |

**一句話原則**：
> **客戶感受到的價值、你累積的資料、你能形成的標準 → 自研。
> 底層通用能力、成熟基礎設施、非差異化元件 → 外包。**

### 23.2 必須自研的六大核心系統

| # | 核心系統 | 解決的問題 | 為何不能外包 |
| :--- | :--- | :--- | :--- |
| 1 | **Onboarding Automation** (§18) | 把混亂資料變成可上線 AI 員工 | 客戶第一眼感受到價值的地方；外包即失去產品主權 |
| 2 | **Knowledge Card System** (§6.3) | 把資料結構化為可治理知識 | 知識卡標準是內部資產 |
| 3 | **Skill Registry / SkillOps** (§9) | 能力可版本化、可測試、可發布 | 跨客戶累積形成 Skill 模板與 Benchmark |
| 4 | **Evaluation & Monitoring** (§12) | 線上品質、漂移、成本監控 | **真正的資料飛輪所在** |
| 5 | **Policy / Governance Harness** (§5.4 / §11) | 企業可控、可審計、可信任 | 與一般 chatbot 最核心差異 |
| 6 | **Tool Gateway 抽象層** (§8.5) | 控制企業系統串接、權限、稽核 | Adapter 可外包，Contract 必須自定 |

#### 為何 Evaluation 是「真正護城河」

```
線上對話 → 評分 → 錯誤分類 → 訓練題生成 → Skill 改版 → 上線 → 再次監控
```

這個閉環一旦建立，平台會：
- 越服務越多客戶 → 越懂客服情境
- 越懂客服情境 → 越快交付新客戶
- 越快交付新客戶 → 越多資料回饋
- 越多資料回饋 → 越強的 Skill Benchmark

**這就是 AI 原生公司的 Scale Learning**。

### 23.3 應外包或採購的七類元件

| 類別 | 採用方案 | AEOS 自研層 |
| :--- | :--- | :--- |
| **LLM 模型** | OpenAI / Anthropic / Google / Local (Ollama, vLLM) | Model Gateway / Prompt Adapter / Cost Control / Fallback Routing |
| **向量資料庫** | Postgres + pgvector / Qdrant / Weaviate / Pinecone | 知識切片策略 / 知識版本控管 / 來源引用 / 過期偵測 / 知識卡結構 |
| **Auth / SSO / Billing** | Clerk / Auth0 / Keycloak / Stripe | Tenant / Role / Permission 業務邏輯 |
| **客服入口** | LINE Messaging API / Intercom / Zendesk / Slack / Teams / Web Chat SDK | AI Employee Layer (覆蓋於既有客服系統之上) |
| **企業系統 Adapter** | Zapier / Make / n8n / 客戶 API / Webhook Bridge | **Adapter Contract** (Tool Gateway 內部統一介面) |
| **DevOps / Infra** | Render / Railway / Fly.io / Cloud Run / ECS / Managed Postgres / Redis / S3 | 部署可重現 / 租戶隔離 / Audit / Secret 管理 / Rollback |
| **Document OCR / Parser** | Unstructured / LlamaParse / Azure Document Intelligence / AWS Textract | Parser → Knowledge Card 結構化 (FAQ / Policy / Product / Procedure / Risk) |

**核心原則**：
> **Adapter 可外包，Adapter Contract 必須自握。**

無論底層是 MCP、API、Webhook、RPA，AEOS 內部永遠只認以下標準 Tool 介面：

```
CustomerLookupTool
OrderStatusTool
TicketCreateTool
InventoryCheckTool
RefundRequestTool
KnowledgeSearchTool
HumanHandoffTool
```

### 23.4 Core / Supporting / Generic Domain 分層

依 DDD 戰略設計，AEOS 各能力區分為三層：

#### 23.4.1 Core Domain（自研，戰略投資）

> **這是公司價值所在，必須投入最強人力與時間。**

```
- AI Employee Lifecycle Management
- SkillOps Pipeline
- Evaluation & Monitoring
- Knowledge Card System
- Governance Policy Engine
- Tool Permission Abstraction
```

#### 23.4.2 Supporting Domain（部分外包，須掌握介面）

> **可以使用第三方，但介面契約自己定。**

```
- Document Ingestion (用第三方 OCR，但 Card 結構自定)
- MCP Adapter (Adapter 可外包，Contract 自定)
- Webhook Integration
- Customer-specific Workflow
- Dashboard UI
- Report Templates
```

#### 23.4.3 Generic Domain（直接買，不要花一秒自研）

> **市場上已有成熟方案，自研沒有 ROI。**

```
- Auth / SSO / Billing
- Cloud Hosting
- Database / Object Storage
- Vector DB (基礎能力層)
- OCR
- Email Service
- Logging / APM 基礎設施
```

### 23.5 應對「VC 護城河質疑」的標準答案

| VC 可能質疑 | AEOS 標準回應 |
| :--- | :--- |
| 「你只是 LLM Wrapper」 | 我們的價值在 §22.5 四層護城河，模型只是底層元件 |
| 「OpenAI 升級會吃掉你」 | 模型升級反而強化平台價值（Skill / Evaluation 不變） |
| 「Zendesk / Salesforce 會做 AI」 | 我們不打客服系統，我們是跨系統 AI 員工治理層 |
| 「為何客戶不能自己用 OpenAI 接 RAG？」 | 因為缺 Skill 治理、評估、回滾、合規、多租戶 |
| 「Open source 框架會追上你」 | 框架解決 Agent Loop，不解決企業治理 |

---

## 24. 商業本質：訓練治理三轉換

### 24.1 公司核心能力的精煉表述

AEOS 的商業本質，可用四個字概括：

```
訓練治理
```

完整定義：

> **把企業 know-how 轉化為可治理 AI 員工的能力。**

這個能力由三組「資產轉換」構成：

```
資料 → 知識 → 技能 → 改版
```

### 24.2 轉換 1：資料 → 知識 (Data → Knowledge)

**輸入**：

```
公司網站、PDF、Word、Excel、Notion、Confluence
LINE / Email / Zendesk 客服紀錄
產品型錄、SOP、價格表、退換貨政策
```

**輸出**：結構化知識卡 (對應 §6.3 三分類 + §18.11.1)

```
FAQ Card        (Static Knowledge)
Policy Card     (Policy Knowledge)
Product Card    (Static Knowledge)
Procedure Card  (Static Knowledge)
Risk Card       (Policy Knowledge)
DynamicQuery    (Dynamic Knowledge → MCP Tool)
```

**商業價值**：客戶從未把自家知識結構化過。AEOS 的第一個 Wow Moment 來自於此。

### 24.3 轉換 2：知識 → 技能 (Knowledge → Skill)

**輸入**：Knowledge Cards + 角色定義 + 風險邊界

**輸出**：可上線 AI 員工能力包

```
Knowledge Cards
    ↓
Skill Cards
    ↓
SkillVersion (含 prompt_spec / input_schema / output_schema /
              tool_requirements / test_results / approval_status)
    ↓
AI Employee 配置 (見 §21.2 Employee Manifest)
```

**商業價值**：把「文件」變成「員工能力」，這是企業 ERP 從未做到的事。

### 24.4 轉換 3：對話 → 改版 (Conversation → Iteration)

**輸入**：線上 Production 對話紀錄

**輸出**：下一版 SkillVersion

```
線上對話 (Production Logs)
    ↓
評分 (LLM-as-Judge + Rule-based + Human Review)
    ↓
錯誤類型分類 (Failure Taxonomy)
    ↓
訓練資料生成 (脫敏後)
    ↓
Skill Version Upgrade (對應 §9 SkillOps Pipeline)
    ↓
Sandbox 評估 → Expert Review → Canary → Full Release
    ↓
新一版上線 → 回到第一步
```

**商業價值**：這就是**資料飛輪**。每位客戶的對話都讓平台變得更聰明，跨客戶的洞察可形成產業級 Benchmark。

### 24.5 三轉換對應的 DDD Aggregate

```
Conversion 1：Data → Knowledge
Aggregate：KnowledgeCard, KnowledgeBase, IngestionRun

Conversion 2：Knowledge → Skill
Aggregate：Skill, SkillVersion, AIEmployee, RoleProfile

Conversion 3：Conversation → Iteration
Aggregate：Conversation, EvaluationResult, TrainingDataset, ReleaseGate
```

**設計推論**：三組 Aggregate 對應 §7 Bounded Context 中的：
- Knowledge Context
- Skill Governance Context + Employee Runtime Context
- Evaluation Context + Training Room Context

這是 AEOS 系統設計與商業本質完全自洽的證明。

### 24.6 Core Domain 的精準命名

依 §23.4 三層分類，AEOS 真正的 Core Domain 不是 Chat、不是 RAG、不是 Tool Calling。

```
AI Employee Lifecycle Management
```

完整生命週期：

```
Hire (建立)
  → Train (訓練室博弈)
  → Evaluate (Sandbox 評估)
  → Approve (Expert Review)
  → Deploy (Canary → Full Release)
  → Monitor (AgentOps)
  → Improve (SkillOps Pipeline)
  → Retire (Skill Deprecation / Employee Retirement)
```

**這個 Lifecycle 才是公司的真正 Core Domain。** 所有其他能力（Knowledge、Skill、Tool、Policy、Evaluation）都是支撐這個 Lifecycle 的子系統。

### 24.7 不能變成接案公司的設計

> **AI 原生公司最大陷阱：每個客戶都客製，最後變成接案公司。**

避免方法：每次客製必須沉澱為下列至少一項可重用資產：

```
□ Skill 模板  (產業可重用)
□ 知識卡結構  (跨客戶可重用)
□ Adapter      (跨客戶可重用)
□ Evaluation Set (產業 Benchmark)
□ Policy 模板  (法遵可重用)
□ 導入 SOP    (內部交付加速)
```

**內部度量**：

| 指標 | 目標 |
| :--- | :--- |
| 第 N 個客戶導入時間 / 第 1 個客戶 | ≤ 50% (第 10 個) → ≤ 20% (第 50 個) |
| 第 N 個客戶 Skill 重用率 | ≥ 60% (第 10 個) → ≥ 80% (第 50 個) |
| 客製 Adapter 比例 | ≤ 30% (其餘走標準 Adapter) |

達不到上述指標即代表未脫離服務公司階段。

---

## 25. 商業模式與市場切入

### 25.1 切入點敘事 (Wedge Narrative)

> **不要賣「平台」。平台太抽象，老闆無感。**

#### 不要這樣賣 (技術導向，難以成交)

```
× AI 客服系統
× RAG 系統
× MCP Agent 平台
× LLM 自動化工具
```

#### 要這樣賣 (價值導向，老闆有感)

```
✓ 7 天建立你的第一位 AI 客服員工
✓ 從客服文件到可上線 AI 員工，一週完成
✓ 不用重建客服系統，先讓 AI 幫真人客服產生回覆草稿
```

**戰略邏輯**：賣「具體交付物」，背後是平台；賣「平台」，沒有人懂。

### 25.2 三階段商業模式演進

#### Phase 1：MVP 驗證期 (Year 1)

```
Setup Fee + Monthly SaaS
```

| 項目 | 建議區間 (NTD) | 說明 |
| :--- | :--- | :--- |
| 導入費 | 10 萬 ~ 50 萬 | 含 Phase 0~3 顧問交付 |
| 月費 | 1 萬 ~ 10 萬 | 依知識庫量、對話量、整合數、員工數計價 |

**目標**：取得 5~10 個 Logo 客戶，建立交付 SOP。

#### Phase 2：產品化擴張期 (Year 2)

```
Platform Fee + AI Employee Seat + Usage
```

| 項目 | 計價維度 |
| :--- | :--- |
| 平台月費 | 固定 |
| AI 員工席次 | 每位月費 |
| 系統 Adapter | 每個月費 |
| 高階監控 / 評估 | 加購模組 |
| Token 用量 | 成本轉嫁 + 加成 |

**目標**：30~50 個客戶；NRR ≥ 120%。

#### Phase 3：企業級平台期 (Year 3+)

```
Private Deployment + Annual Contract
```

| 項目 | 說明 |
| :--- | :--- |
| 年度授權 | 大型企業 / 集團 |
| 私有部署 | 法遵嚴格產業 |
| 資安審查 | SOC 2 / ISO 27001 加值 |
| SLA | 99.95% / 24x7 支援 |
| 客製 Adapter | 專屬 ERP / SAP / 自建系統 |

**目標**：跨產業、跨地區擴張；ARPU 提升 5~10 倍。

### 25.3 商業陷阱清單與緩解

| # | 陷阱 | 風險本質 | 緩解策略 |
| :--- | :--- | :--- | :--- |
| 1 | **變成接案公司** | 客製吃掉產品化能量 | §24.7 度量指標；每次客製必沉澱資產 |
| 2 | **被大型 SaaS 吃掉** (Zendesk / Salesforce) | 它們會內建 AI | 定位為「跨系統 AI 員工治理層」，能接它們而非取代 |
| 3 | **被模型能力進步吃掉** | 純 prompt wrapper 無護城河 | 護城河放在治理 / 評估 / 多租戶 (§22.5) |
| 4 | **過早平台化** | Marketplace / 多角色 / 自動編排 | Phase 1 只做第一位 AI 客服員工 |
| 5 | **過早多通道** | 通道整合分散資源 | Phase 1 只做 1~2 個通道 |
| 6 | **過早全自動** | L4 跳級風險 | §20.4 強制 L1 → L4 漸進 |
| 7 | **過早多模型** | 模型評估與成本失控 | §13 Model Gateway，初期固定 1~2 個 Provider |
| 8 | **過度承諾客戶** | 法務 + 信任雙輸 | §15.3 五方責任契約 |

### 25.4 初期團隊配置 (極小團隊架構)

> **不要超過 5~7 人**。每人都需是 Player-Coach。

#### 必須內部 (核心)

| 角色 | 職責 | 不能外包原因 |
| :--- | :--- | :--- |
| **Founder / Product Architect** | 客戶訪談、需求收斂、定位、銷售敘事、Lifecycle 設計、驗收標準 | 公司方向性 |
| **AI / Backend Engineer** | Agent Runtime、Skill Registry、Evaluation、Tool Gateway、Knowledge Pipeline | Core Domain |
| **Full-stack Engineer** | 導入精靈、訓練室 UI、審核介面、管理後台、Dashboard | 客戶感受層 |

#### 可外包 / 兼職

| 角色 | 職責 | 外包模式 |
| :--- | :--- | :--- |
| **Integration Contractor** | LINE / CRM / ERP / Webhook / n8n / Zapier 整合 | 按 Adapter 計價 |
| **UI Designer** | 視覺設計 (產品流程仍由內部定) | 專案制 |
| **Data / Prompt Ops Assistant** | 客服案例整理、測試題建立、知識卡校對 | 兼職 / 實習 |
| **Sales / SE** | 早期創辦人親自；中期才招募 | 暫不需要 |

### 25.5 募資階段與估值錨點

| 階段 | 訊號 | 募資用途 |
| :--- | :--- | :--- |
| Pre-seed | 1~3 個 Logo 客戶 + Onboarding Layer 雛形 | 完成 Phase 1 MVP |
| Seed | 5~10 個客戶 + NRR > 100% + Skill 重用率 ≥ 50% | 完成 Phase 2 產品化 |
| Series A | 30+ 客戶 + 多職位驗證 + 跨產業 | 完成 Phase 3 企業擴張 |
| Series B | 多區域 + 大型 Logo + 護城河驗證 (Layer 3+) | 國際化 |

### 25.6 對外溝通的三句話標籤

| 對象 | 一句話 |
| :--- | :--- |
| 創辦人圈 / VC | 模型外包，治理自研。Adapter 可外包，Tool Contract 要自握。 |
| 企業 CEO | 客服是入口，AI 員工生命週期才是護城河。 |
| 工程界 | Narrow wedge, broad architecture — 切口窄，架構寬。 |
