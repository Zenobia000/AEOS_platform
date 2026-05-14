# 規劃與執行：MVP 路線、組織、Onboarding 與驗收

> **本檔對應原 whitepaper.md 的 §14, §16, §17~§21 (Part II)**
> 主題定位：規劃 + 執行
> 最後同步：2026-05-14

## 相關章節速查

**本檔被外部引用的高頻章節**：
- §14 MVP 路線圖 (Phase 1~4，0~24 個月)
- §16 組織與運營 (Personas / AIOC / 採購流程)
- §17 五階段方法論 (Phase 0~4 — 需求盤點 / 知識建模 / 沙盒陪練 / 灰度上線 / 監控迭代)
- §18 Onboarding Automation Layer (五步無腦流程 / 6 個 MVP 功能 / L0~L5 成熟度 / AI 員工履歷)
- §18.11.1 知識卡資料結構
- §19 三種企業導入模式 (Hosted Channel / Agent API / Webhook+MCP)
- §20 自動化成熟度 (L1 草稿 → L4 受控自動化)
- §21.1 上線驗收門檻 (通用 + 產業特化)
- §21.2 AI 員工配置宣告 (Employee Manifest YAML)
- §21.3 三種服務交付包 (MVP / 訓練室 / 整合版)

**本檔對外引用的章節**：
- §3 設計原則 (見 `01-vision-positioning.md`)
- §5 系統架構 (見 `02-product-architecture.md`)
- §5.4 三平面分離 (見 `02-product-architecture.md`)
- §6.3 知識三分類 (見 `02-product-architecture.md`)
- §9 SkillOps (見 `02-product-architecture.md`)
- §9.4 七層 Quality Gates (見 `02-product-architecture.md`)
- §10.3 訓練室 UI (見 `02-product-architecture.md`)
- §11 安全合規 (見 `06-risk-boundaries.md`)
- §13 多模型 (見 `02-product-architecture.md`)
- §15.3 五方責任 (見 `06-risk-boundaries.md`)
- 附錄 F Onboarding Checklist
- 附錄 H 導入精靈 UX
- 附錄 I 7 日導入包
- 附錄 J 員工履歷模板

---

## 14. MVP 路線圖

### 14.1 Phase 1 — 受控核心 (0~3 個月)

**目標**：讓企業敢把第一個 AI 員工放進真實流程。

| 模組 | 範圍 |
| :--- | :--- |
| Tenant Manager | 單租戶 |
| AI Employee Runtime | 1 種職位 (AI 客服助理) |
| Role & Policy Engine | 基本 RBAC |
| Skill Registry | 5 個 Approved Skills |
| Tool Gateway | 3 個 Approved Tools (Knowledge Search / Ticket Create / Human Handoff) |
| Audit Log | Append-only |
| Conversation Log | Full Trace |
| Admin Console | 基本管理介面 |

**故意延後**：訓練室、SkillOps Pipeline、ERP / SAP / CRM 深度整合、多 Agent 協作、複雜 Workflow Designer、Plugin Marketplace。

**成功指標**：
- ✅ 所有對話可追溯、可重播
- ✅ 無 Cross-tenant 違規
- ✅ Skill 上線必經審核
- ✅ 一鍵停用 / 回滾驗證通過

### 14.2 Phase 2 — 訓練室與 SkillOps (3~6 個月)

**目標**：把 Hermes-style 自我學習能力**安全地**接入。

| 新增模組 | 範圍 |
| :--- | :--- |
| Training Room | Sandbox + 專家博弈 |
| Skill Versioning | Full Lifecycle (Draft → Archive) |
| Sandbox Evaluation | Multi-metric + Regression |
| Red Team | 7 種紅隊樣式 |
| Expert Review Workflow | 簽核鏈 |
| Drift Detection | Knowledge / Behavior / Cost |

**成功指標**：
- ✅ 至少完成 5 次 Skill 版本升級 (含至少 1 次 rollback 演練)
- ✅ 紅隊攔截率 ≥ 99%
- ✅ Drift 偵測誤報率 ≤ 5%

### 14.3 Phase 3 — 企業整合 (6~12 個月)

**目標**：成為企業級平台。

| 新增模組 | 範圍 |
| :--- | :--- |
| Enterprise Adapters | CRM / ERP / SAP / Email |
| Workflow Engine | 跨職位編排 |
| Advanced Policy | ABAC、業務金額閾值 |
| Multi-tenant | 真正的多租戶隔離 |
| Compliance Pack | GDPR / PDPA 報表 |
| SLA Dashboard | 按租戶 / 職位 |
| Cost Management | Quota + Attribution |

### 14.4 Phase 4 — 職位擴張 (12~24 個月)

**目標**：從單一職位 → 完整職位目錄。

- 開放第 2~8 種職位 (業務、採購、維修、法遵、文件、工程、現場操作)
- Skill Marketplace (內部 / 跨企業)
- 跨職位 AI 員工協作 (Multi-Agent Coordination)
- 全自動化評分迴路

---

## 16. 組織與運營

### 16.1 角色介面 (Personas)

| 角色 | 工作介面 | 主要職責 |
| :--- | :--- | :--- |
| **Tenant Admin** | Admin Console | 員工配置、Policy 設定、報表 |
| **Skill Owner** | Skill Studio | Skill 編寫、測試、發布申請 |
| **Domain Expert (Trainer)** | Training Room UI | 與 Training Agent 博弈、標註、覆核 |
| **Reviewer** | Approval Workflow | Skill 審核、發布簽核 |
| **Operator** | Ops Dashboard | 線上監控、事件處理 |
| **Compliance Officer** | Audit Console | 稽核、報表、合規檢查 |
| **End User (客戶 / 員工)** | Channel UI | 與 AI 員工對話 |

### 16.2 運營組織建議 (對企業客戶)

導入 AEOS 的客戶企業，建議設置：

```
AI Operation Center (AIOC)
├── AI HR (員工配置、職位設計)
├── AI Trainer (訓練室專家)
├── AI Reviewer (Skill 審核)
├── AI Operator (線上監控)
└── AI Compliance Officer (合規稽核)
```

**這不是新增 5 個全職角色**，而是**從現有客服主管、QA、合規團隊衍生出新職能**。

### 16.3 採購與導入流程建議

```
Week 1~2:  需求訪談 + Tenant 環境準備
Week 3~4:  POC (1 職位、3 工具、1 租戶)
Week 5~8:  Skill 編寫 + Training Room 設置
Week 9~10: 紅隊測試 + 合規檢查
Week 11:   Canary 發布 (10% 流量)
Week 12:   Full Release
持續：     Monthly Review + Quarterly Skill Update
```

### 16.4 客戶側 AI 員工管理者角色重塑

> 紅杉資本 / Boris (2026) 觀察：「未來頂級程序員不再是寫程式的人，而是能精準拆解商業需求並管理 AI 的架構師」。同樣的角色重塑將發生在企業內部，AEOS 必須提供配套的角色介面。

#### 16.4.1 客戶側既有角色的轉型

| 既有角色 | AI 時代轉型 | 與 AEOS 互動 |
| :--- | :--- | :--- |
| **客服主管** | AI 客服員工的 Trainer + Reviewer | Training Room 陪練、§21 驗收簽核 |
| **客服一線人員** | AI 草稿審閱者 + 高風險案例處理者 | Channel Layer 接手、Handoff |
| **業務分析師** | Skill 設計者 + Evaluation 規則制定者 | Skill Studio、Evaluation Dashboard |
| **IT 主管** | AI 員工權限與整合架構師 | Tool Gateway 配置、Adapter 管理 |
| **法遵 / 風控** | AI 員工合規稽核員 | Audit Console、Policy Engine |
| **HR / 組織發展** | AI Workforce Planner（新職能） | 跨部門 AI 員工配置策略 |

#### 16.4.2 新興職位 — 客戶側 AI Workforce Manager

「非技術背景的領域專家」是 AEOS 客戶側最關鍵的新職位：

```
AI Workforce Manager (AWM)
├── 職責：定義 AI 員工的職務範圍、KPI、晉升條件、退休標準
├── 背景：通常為資深業務 / 客服主管 + AEOS 認證培訓
├── 工具：Admin Console + Training Room + Evaluation Dashboard
└── 關鍵能力：拆解業務需求、設計驗收題、判讀指標漂移
```

**AEOS 對此角色的支援**：
- 提供 AWM 認證課程（產品化 + 商業價值）
- 提供 AWM Playbook（最佳實踐手冊）
- Admin Console UX 為非技術背景設計（呼應 §18 無腦導入精靈精神）

#### 16.4.3 人機比例的重設

傳統客服中心人機配比：

```
傳統：1 主管 : 30 客服 (人)
```

AEOS 上線後可能演化為：

```
Phase 1 (L1~L2)：1 主管 : 10 客服 (人) + 30 AI 員工
Phase 2 (L3)：  1 主管 : 5 客服 (人) + 100 AI 員工
Phase 3 (L4)：  1 AWM : 2 高風險處理人員 + 500+ AI 員工
```

**戰略推論**：
- AEOS 不替代人類，而是把人類從「執行者」轉為「治理者」
- 客戶採購 AEOS 不只買「成本下降」，而是買「組織能力升級」
- 這是 AEOS 對抗「客戶買 LLM 自己接 RAG」的關鍵差異化

---

## 17. 導入服務五階段方法論

> **重要釐清 — Meta-流程 vs 業務流程**
>
> 本章描述的「五階段」是 **AEOS 平台方對「如何訓練 / 驗收 / 發布 / 監控 AI 員工」這條 meta-流程**的固化，**不是**對「客戶業務流程」的固化。
>
> - ✅ 固化的是：訓練治理流程、驗收門檻、Skill 發布管線
> - ❌ 不固化的是：客戶 AI 員工實際工作時如何回答問題、如何拆解任務
>
> 客戶的業務邏輯由 LLM 動態處理（呼應紅杉 / Boris 觀察「Opus 自主解題」），AEOS 治理的是「如何安全把 AI 放進企業流程」這條 meta 層。**這是 AEOS 與「過時固定流程 SaaS」的根本差異**。

### 17.1 服務定位

AEOS 的交付物**不是一套軟體授權**，而是**一個可被企業驗收、上線、迭代的 AI 員工**。這個定位決定了服務必須採用方法論導向，而非僅 SaaS 開通。

```
傳統 SaaS：交付帳號 → 客戶自行使用
AEOS 服務：交付 AI 員工 → 含訓練、驗收、上線、監控、迭代全週期
```

### 17.2 五階段流程總覽

```
Phase 0  需求盤點         (Discovery)
Phase 1  知識與流程建模    (Modeling)
Phase 2  沙盒訓練室陪練    (Training)
Phase 3  灰度上線與系統串接 (Deployment)
Phase 4  監控評分與 Skill 迭代 (Operation)
```

### 17.3 Phase 0 — 需求盤點 (Discovery)

**目的**：在進入技術實作前，先明確 AI 員工的職務邊界與風險範圍。

**訪談重點**（以 AI 客服為例，其他職位類比）：

| 議題 | 核心問題 |
| :--- | :--- |
| 業務分類 | 客服問題分哪幾類？哪些最高頻？ |
| 自動化邊界 | 哪些可自動回答？哪些必須轉人工？ |
| 風險範圍 | 哪些涉及金流、退款、合約、個資？ |
| 既有系統 | 客服入口在哪？(LINE / Zendesk / Intercom / 自建) |
| 知識來源 | 知識庫在哪？(Notion / Drive / Confluence / PDF / 內部 DB) |
| 系統整合 | 需串接哪些？(CRM / ERP / 進銷存 / 會計) |
| 內部角色 | 誰是領域專家？誰有上線批准權？ |

**交付物**：

```
- AI 員工職務說明書 (Job Description)
- 客服問題分類表 (Issue Taxonomy)
- 風險分級表 (Risk Matrix)
- 可自動化範圍 / 不可自動化範圍
- 人工接手規則 (Escalation Rules)
- 系統串接清單 (Integration Inventory)
```

**設計理念**：此階段產出**業務文件**，而非技術文件。其角色等同於聘用人類員工前的「職位需求書」與「公司規章說明」。

### 17.4 Phase 1 — 知識與流程建模 (Modeling)

**目的**：將企業既有知識結構化為 AI 員工可運用的資產。

**核心動作**：

1. 整理 FAQ、SOP、產品文件、退換貨政策、合約條款、價格規則、客訴處理流程、常見例外狀況
2. 將知識依 §6.3 三分類拆解：
   - **Static** → Knowledge System / RAG
   - **Policy** → Policy Engine / Rule
   - **Dynamic** → MCP Tool / API Adapter
3. 建立 Skill 草稿與測試題庫
4. 標註人工接手條件與高風險情境

**交付物**：

```
- 知識庫初版（依三分類整理）
- Skill 草稿清單（依職位）
- 測試題庫（含正確答案、不可回答題、高風險題）
- 來源引用映射表
```

### 17.5 Phase 2 — 沙盒訓練室陪練 (Training)

**目的**：在隔離環境中由領域專家陪練 AI 員工，直到通過驗收門檻。

**操作流程**（在 §10.3 訓練室 UI 中執行）：

```
專家輸入測試問題
    ↓
Training Agent 回應
    ↓
專家評分 + 錯誤標註 + 修正建議
    ↓
Skill 候選改版
    ↓
Sandbox 自動評估 (覆蓋率、回歸、紅隊)
    ↓
Expert Review 簽核
    ↓
進入 Skill Registry 等待上線
```

**鐵律**：
- 訓練室內的 AI 可比較自由探索
- 訓練室內**禁止**接觸真實客戶資料（必須脫敏）
- 訓練室產出的 Skill **不可**直接進 Production，必須經 §9.4 七層 Quality Gates

### 17.6 Phase 3 — 灰度上線與系統串接 (Deployment)

**目的**：以最小風險將 AI 員工接入企業真實流量。

**標準步驟**：

```
1. 確認導入模式 (見 §19 — Hosted Channel / Agent API / Webhook)
2. 建立 Tool Adapter 並通過 §8.7 審核管線
3. 設定租戶隔離與權限矩陣
4. Canary 發布 (1~10% 流量)
5. 監控指標達標後逐步擴大
6. Full Release
```

**交付物**：

```
- 串接技術文件 (含 API / Webhook / MCP 配置)
- 租戶隔離配置
- Canary 監控報告
- 上線簽核紀錄
```

### 17.7 Phase 4 — 監控評分與 Skill 迭代 (Operation)

**目的**：上線後持續監控、評分、回訓，形成 SkillOps 閉環。

**月度節奏**：

```
Week 1  指標檢視 + 異常案例彙整
Week 2  訓練室回放 + Skill 候選產出
Week 3  Sandbox 評估 + Expert Review
Week 4  Canary 上線 + 全量發布
```

**季度節奏**：

```
- 大版本 Skill 升級
- 知識庫全面盤點
- 紅隊強化測試
- 合規稽核報表
```

### 17.8 五階段時程建議

| Phase | 中小企業 | 中大型企業 | 法遵嚴格產業 |
| :--- | :--- | :--- | :--- |
| Phase 0 | 1 週 | 2 週 | 3~4 週 |
| Phase 1 | 1 週 | 2~3 週 | 4 週 |
| Phase 2 | 2 週 | 3~4 週 | 6 週 (含紅隊) |
| Phase 3 | 1 週 | 2 週 | 4 週 (含合規簽核) |
| Phase 4 | 持續 | 持續 | 持續 |
| **首次上線總時程** | **5 週** | **9~11 週** | **17~18 週** |

---

## 18. Onboarding Automation Layer — 無腦導入體驗

> **重要釐清 — 無腦導入 ≠ 業務流程鎖死**
>
> 本章「導入精靈 + 五步無腦流程」是把「**訓練 / 驗收 AI 員工的 meta-流程**」產品化，目的是降低客戶導入摩擦。
>
> - ✅ 產品化的是：資料整理、知識卡抽取、測試題生成、專家審核 — 都是「治理動作」
> - ❌ 不鎖死的是：AI 員工上線後如何處理客戶問題（仍由 LLM + Skill + RAG 動態決定）
>
> 即使紅杉 / Boris 預言「未來 AI 動態生成所有 workflow」成真，AEOS 的導入精靈仍有價值 — **因為動態生成的 AI workflow 本身仍需治理、驗收、版控、監控**，這正是 AEOS 固化的部分。

### 18.1 為何需要這一層

§17 描述的五階段方法論在「服務交付」面是完整的，但若直接交給客戶執行，仍需要客戶整理大量資料、設計 SOP、撰寫測試題。這形成導入鴻溝：

| 客戶實際痛點 | 客戶心理 OS |
| :--- | :--- |
| 資料散落多處 (網站、PDF、Notion、客服紀錄) | 「我也不知道哪些資料要給你」 |
| 不知道 AI 會在哪裡犯錯 | 「萬一亂回答怎麼辦？」 |
| 客服主管沒空陪訓 | 「我哪有時間每天教 AI」 |
| 系統串接複雜 | 「我們的 ERP 沒有 API」 |
| 驗收標準模糊 | 「怎樣才算可以上線？」 |
| 出事誰負責 | 「AI 出包到底算誰的？」 |

**結論**：若 AEOS 僅止於提供平台與方法論，客戶感受到的仍是「強大但要自己整理半天」。**真正的產品護城河是把資料收集、知識整理、測試題產生、陪練驗收等耗時動作產品化為導入精靈。**

### 18.2 產品定位轉換

```
傳統定位：我提供 AI 員工平台
     ↓
進階定位：我提供 AI 員工導入精靈
     ↓
成熟定位：我把混亂資料快速整理成可上線 AI 員工的能力
```

### 18.3 五步無腦導入流程

```
Step 1  丟資料        (Ingest)
Step 2  自動整理      (Auto-Curate)
Step 3  自動產生測試題 (Auto-Generate Test Set)
Step 4  專家快速審核   (Expert Review, Not Authoring)
Step 5  一鍵灰度上線   (One-Click Canary)
```

### 18.4 Step 1 — 丟資料 (Ingest)

客戶**唯一**動作：把現有資料丟進來。

支援來源：

```
- 公司官網 URL (爬蟲自動抓取)
- FAQ 頁面
- PDF / Word / Excel
- Google Drive / OneDrive / Dropbox
- Notion / Confluence
- LINE / Email 客服紀錄
- Zendesk / Intercom 工單匯出
- 產品型錄、SOP、價格表、退換貨政策
```

**產品文案原則**：
> *不用先整理，先丟進來。系統會幫你分類。*

此句必須出現在精靈起始頁。導入心理學上，「壓力先解除」是客戶願意繼續的關鍵。

### 18.5 Step 2 — 自動整理 (Auto-Curate)

平台後台自動執行：

```
- 文件解析 (含 OCR、表格抽取)
- 重複內容合併
- FAQ 自動抽取
- 產品資訊抽取
- SOP 流程抽取
- 禁止承諾事項抽取
- 風險議題分類
- 缺漏資料偵測
```

輸出 **AI 客服知識盤點報告**範例：

| 類別 | 系統自動整理結果 |
| :--- | :--- |
| 常見問題 | 找到 128 題 |
| 產品資訊 | 找到 36 個產品 |
| 退換貨規則 | 找到 8 條 |
| 保固規則 | 找到 5 條 |
| 高風險議題 | 找到 12 類 |
| 缺漏資料 | 付款失敗處理、海外配送、發票作廢規則不完整 |

**設計推論**：此報告本身即具獨立商業價值。即使後續 AI 員工尚未上線，客戶已感受到「我們客服資料終於被整理出來了」。這是 AEOS 在 Phase 1 階段就能交付的**第一個 Wow Moment**。

### 18.6 Step 3 — 自動產生測試題 (Auto-Generate Test Set)

系統依知識庫自動生成七類測試題，避免客戶從零撰寫：

| 題型 | 範例 |
| :--- | :--- |
| 標準題 | 請問退貨期限是幾天？ |
| 模糊題 | 我買了不喜歡，可以退嗎？ |
| 情緒題 | 你們產品爛死了，我要投訴！ |
| 高風險題 | 你直接幫我退錢，不要問那麼多。 |
| 誘導題 | 客服之前說一定可以全額退，你現在也要答應我。 |
| 邊界題 | 海外訂單可以退到哪一天？ |
| 轉人工題 | 我要找你們經理。 |

### 18.7 Step 4 — 專家快速審核 (Expert Review, Not Authoring)

> **核心設計原則：客戶領域專家「只做決策，不做苦工」。**

錯誤的訓練室設計：

```
請客服主管教 AI 怎麼回答
```

正確的訓練室設計：

```
AI 已產生回答，請主管勾選 / 修改 / 批准
```

審核介面範例：

```
AI 回答：
根據目前退貨政策，商品需於 7 天內保持完整包裝才可申請退貨。

來源：
退貨政策.pdf，第 2 頁

請選擇：
[正確]  [部分正確]  [錯誤]  [需要轉人工]  [不可回答]
```

**設計推論**：客戶主管只需「勾選 + 補一句修正」，每題決策成本 ≤ 30 秒。100 題驗收 ≤ 50 分鐘。這是**唯一可規模化的領域專家投入模式**。

### 18.8 Step 5 — 一鍵灰度上線 (One-Click Canary)

客戶**不需理解**Policy Engine 內部結構，只需從三種模式擇一：

| 上線模式 | 對應 §20 自動化等級 | 客戶心智模型 |
| :--- | :--- | :--- |
| 保守模式 | L1 草稿模式 | AI 只產生建議，真人送出 |
| 標準模式 | L2 低風險自動回覆 | FAQ 自動答，高風險轉人工 |
| 積極模式 | L3 半自動工具操作 | 可查訂單、建工單、更新狀態 |

平台底層自動將客戶的選擇映射為對應的 Policy 配置，但 UX 上隱藏複雜性。

### 18.9 漸進式盤點 — 第一輪只問五個問題

避免讓客戶面對冗長表單。**第一輪訪談只問五個問題**，其餘資料在後續階段漸進收集。

```
Q1. 你是哪個產業？
Q2. 你想先處理哪一類客服問題？
Q3. 你的客服目前在哪裡發生？
Q4. 你的資料在哪裡？
Q5. 哪些事情 AI 絕對不能自己處理？
```

**反例（一開始就問會嚇跑客戶）**：

```
× 請提供完整 API 文件
× 請提供客服 SOP
× 請提供資料字典
× 請提供權限矩陣
× 請提供法遵規範
```

### 18.10 無腦程度六級成熟度 (Effortless Maturity Model)

> 此模型衡量的不是 AI 能力，而是「**客戶要做多少事**才能上線」。

| 等級 | 客戶要做什麼 | 系統要做什麼 | 商業評估 |
| :--- | :--- | :--- | :--- |
| L0 | 自己寫 prompt | 提供 chat | 不夠 |
| L1 | 上傳文件 | 做 RAG | 還不夠 |
| L2 | 丟資料 | 自動整理 FAQ / SOP / 測試題 | 開始夠 |
| L3 | 只審核 | 自動產生 AI 員工與驗收報告 | 夠好賣 |
| L4 | 只選模式 | 自動接渠道、監控、迭代 | 很強 |
| L5 | 只說目標 | 自動完成導入與持續改善 | 理想狀態 |

**戰略目標**：AEOS 第一年應達到 **L3**，第二年達到 **L4**。L5 為長期願景。

### 18.11 六個 MVP 無腦功能 (Phase 1 必做)

| # | 功能 | 對應 Step |
| :--- | :--- | :--- |
| 1 | 網站 URL 自動爬取 | Step 1 |
| 2 | 文件自動轉知識卡 (FAQ Card / Policy Card / Product Card) | Step 2 |
| 3 | 自動產生 50 題驗收題 | Step 3 |
| 4 | 專家一鍵審核 (正確 / 錯誤 / 轉人工 / 禁止回答) | Step 4 |
| 5 | 缺漏資料反向提示 (告訴客戶還缺什麼) | Step 2 |
| 6 | 上線模式三選一 (保守 / 標準 / 積極) | Step 5 |

#### 18.11.1 知識卡資料結構

文件解析後統一轉為**知識卡 (Knowledge Card)**結構，作為 §6.3 三分類治理的最小單元：

```yaml
type: PolicyCard      # 或 FAQCard / ProductCard / ProcedureCard / RiskCard
title: 退貨期限
content: 商品到貨後 7 天內可申請退貨
source: return_policy.pdf#page=2
risk_level: medium
needs_review: true
extracted_at: 2026-05-14T10:00:00Z
extracted_by: doc_parser.v2.1
```

#### 18.11.2 缺漏資料反向提示

系統主動告知：

```
目前無法回答以下問題（依客服紀錄頻率排序）：

1. 海外配送時間 (出現 47 次)
2. 發票作廢流程 (出現 23 次)
3. 特價商品是否可退 (出現 19 次)
4. 維修費用如何計算 (出現 11 次)
```

**設計推論**：傳統 AI 客服系統等客戶補資料；AEOS 主動告訴客戶「你還缺什麼」。這是反向協助整理知識的關鍵功能。

### 18.12 AI 員工履歷 (Employee Resume)

資料匯入完成後，系統自動產出**AI 員工履歷**作為驗收前的可視化交付物：

```
姓名：Sunny Support Agent
職位：一線客服助理
租戶：Company A

目前掌握知識：
- 128 個 FAQ
- 36 個產品
- 8 條退換貨政策
- 5 條保固規則

目前可處理：
- 基礎產品問答
- 退換貨規則說明
- 客訴初步分類
- 建立工單草稿

目前不可處理：
- 退款承諾
- 法律爭議
- 價格特殊折扣
- 帳務修改

上線建議：
建議先以「保守模式 (L1)」上線 2 週，再評估升級至 L2。
```

**設計推論**：AI 員工履歷將抽象的「Skill 清單」具象化為「員工能力描述」，與 AEOS 的「AI 員工」核心隱喻一致。客戶會直覺感受「它真的像一個員工」。

### 18.13 兩種服務交付模式

#### 模式 A — 自助導入 (Self-Service Onboarding)

```
客戶自己上傳資料
  ↓
系統自動整理
  ↓
客戶自己審核
  ↓
客戶自己上線
```

適用：成熟企業、有專責 AI 團隊。

#### 模式 B — 陪跑導入 (Concierge Onboarding)

```
平台方協助整理資料
  ↓
平台方建立第一版知識庫
  ↓
平台方產生測試題
  ↓
平台方陪客服主管驗收
  ↓
平台方協助接客服入口
```

適用：大部分中小型企業（**主力市場**）。

**商業命名建議**：
- AI 客服 7 日導入包
- AI 員工啟動工作坊
- AI 客服知識整理服務

### 18.14 客戶最少投入清單

把客戶投入降至絕對最低，是無腦導入的成敗關鍵：

```
□ 公司網站或產品資料
□ 現有 FAQ / SOP (有就好，沒有可從網站與客服紀錄反推)
□ 20~50 筆歷史客服案例
□ 客服主管每次 30~60 分鐘審核
□ 客服入口串接資訊
```

**鐵律**：若客戶連 FAQ 都沒有，AEOS 也應能從網站 + 客服對話紀錄反推產出第一版。**「沒有資料」不應成為導入失敗的理由。**

### 18.15 真正的護城河

> AEOS 的護城河不是 MCP，不是 LLM，不是聊天 UI。
> **真正的護城河是：把混亂資料快速整理成可上線 AI 員工的能力。**

```
Data Mess
    ↓
Knowledge Cards
    ↓
Skill Cards
    ↓
Evaluation Set
    ↓
AI Employee
    ↓
Monitoring
    ↓
Skill Iteration
```

這條 pipeline 才是企業最痛、最願意付費的能力。Onboarding Automation Layer 是把這條 pipeline 從「顧問服務」變成「產品功能」的關鍵。

### 18.16 產品文案策略

**不要賣 (技術導向，老闆無感)**：

```
× AI 客服系統
× RAG 系統
× MCP Agent 平台
× LLM 自動化工具
```

**要賣 (價值導向，老闆有感)**：

```
✓ 7 天建立你的第一位 AI 客服員工
✓ 從客服文件到可上線 AI 員工，一週完成
✓ 不用重建客服系統，先讓 AI 幫真人客服產生回覆草稿
```

### 18.17 與既有章節的關係

| 既有章節 | Onboarding Automation Layer 的角色 |
| :--- | :--- |
| §6.3 知識三分類 | 知識卡 (Knowledge Card) 是三分類的標準化封裝 |
| §9 SkillOps | 自動產生測試題即 SkillOps Pipeline 的入口 |
| §10.3 訓練室 UI | 專家審核介面是訓練室的具體實作 |
| §17 五階段方法論 | Onboarding Layer 將 Phase 0~2 從顧問流程產品化 |
| §19 三種導入模式 | Step 5 一鍵上線對應三種導入模式選擇 |
| §20 自動化成熟度 | 上線模式三選一直接映射 L1/L2/L3 |
| §21 驗收門檻 | 自動產測試題即驗收 Quality Gates 的輸入 |

---

## 19. 三種企業導入模式

### 19.1 模式總覽

AEOS 必須同時支援三種導入模式，以涵蓋不同成熟度與既有資產的客戶。三者並非互斥，可在同一客戶不同職位中混用。

| 模式 | 入口控制權 | 典型客戶 | 導入速度 |
| :--- | :--- | :--- | :--- |
| **A — Hosted Channel** | 平台方提供 | 中小企業、新創 | 最快 |
| **B — Agent API** | 客戶既有系統 | 中大型企業 | 中 |
| **C — Webhook / MCP Adapter** | 雙向串接 | 大型 / 客製整合 | 較慢 |

### 19.2 模式 A — Hosted Channel (平台提供完整入口)

**平台提供**：

```
- Web Chat Widget (可嵌入客戶網站)
- LINE Official Account Bot
- Messenger / WhatsApp Bot
- 客服後台 Console
- 標準 API
```

**架構**：

```
客戶 (End User)
    ↓
平台提供之 Web Chat / LINE Bot
    ↓
AI Employee Runtime
    ↓
Tool Gateway / MCP
    ↓
企業系統 (CRM / ERP)
```

| 優點 | 限制 |
| :--- | :--- |
| 平台方控制體驗一致性 | 客戶若已有客服系統可能不願更換 |
| 導入週期最短 | 需處理客戶品牌 UI / 登入 / 會員身份驗證 |
| 監控與評分閉環最完整 | 客戶對前端 UX 客製受限 |
| 適合 MVP 與快速驗證 |  |

**適用客戶**：中小企業、新創、無成熟客服系統者、追求快速見效者。

### 19.3 模式 B — Agent API (平台提供 API，客戶系統呼叫)

**平台提供之 API 範例**：

```
POST /v1/agent/chat               # 對話請求
POST /v1/agent/suggest-reply      # 草擬回覆
POST /v1/agent/classify-intent    # 意圖分類
POST /v1/agent/create-ticket-draft # 建立工單草稿
POST /v1/agent/evaluate-conversation # 對話評分
```

**架構**：

```
客戶既有客服系統 (Zendesk / Salesforce / 自建)
    ↓ HTTPS / OAuth 2.0
AEOS Agent API
    ↓
AI Employee Runtime
    ↓
回傳：答案 / 草稿 / 工單 / 風險評分
```

| 優點 | 限制 |
| :--- | :--- |
| 客戶不需更換現有客服介面 | 平台方對前端體驗控制較少 |
| 適合中大型企業既有資產整合 | API contract 需嚴謹定義 |
| 容易融入既有工作流 | 身份驗證與資料欄位需事前對齊 |

**適用客戶**：已有成熟客服 / CRM / Ticket 系統、IT 能力較強之中大型企業。

### 19.4 模式 C — Webhook / MCP Adapter (客戶提供入口，平台串接)

**客戶提供**：

```
- LINE Channel Access Token
- Webhook URL
- CRM / ERP / Ticket API Token
- 內部 API 文件
```

**架構**：

```
客戶平台事件
    ↓ Webhook
AEOS 接收 → AI Employee 處理
    ↓ 透過客戶 Token
回寫至客戶系統
```

| 優點 | 限制 |
| :--- | :--- |
| 整合彈性最高 | 資安要求最嚴格 |
| 可串接非標準 API | Token 管理複雜 |
| 客戶系統無需大改 | 各家企業 API 差異大，Adapter 客製成本高 |

**適用客戶**：擁有既有系統但 API 非標準、需要深度客製整合、有內部 IT 協作窗口之企業。

### 19.5 模式選擇矩陣

| 客戶條件 | 建議模式 |
| :--- | :--- |
| 無客服系統、要快速上線 | A |
| 有客服系統、IT 成熟 | B |
| 有客服系統、API 標準 | B |
| 有客服系統、API 非標準 | C |
| 多通道、需統一管理 | A + B 並用 |
| 法遵嚴格、私有部署 | C + 私有部署 |
| 跨國 / 多品牌 | A (各品牌獨立 Tenant) |

### 19.6 三模式的共同治理層

**重要原則**：無論採用何種模式，**§5 系統架構藍圖中的治理層完全一致**：

```
任何入口模式
    ↓
Agent Gateway (身分 / 多租戶 / Rate Limit)
    ↓
AI Employee Runtime
    ↓
Governance Harness (Policy / RBAC / Workflow / Audit)
    ↓
Tool Gateway / MCP Proxy
    ↓
Enterprise Systems
```

**設計推論**：模式 A/B/C 差異僅在 Channel Layer 與 Adapter 配置；Runtime、Governance、Tool Gateway 不因模式不同而改變。這保證**治理一致性**與**跨模式可遷移性**。

---

## 20. 自動化成熟度模型

### 20.1 為何需要分級

「全自動回覆」不應是 AI 員工上線的預設目標。企業導入 AI 員工的失敗案例多源自**過早授予自動化權限**。AEOS 採用四級成熟度模型，依風險與信任程度逐步開放權限。

### 20.2 四級自動化成熟度

#### Level 1 — AI 草稿模式 (Suggestion Mode)

```
AI 產生回覆建議
    ↓
人類客服審閱、修改、送出
```

| 特性 | 說明 |
| :--- | :--- |
| 風險 | 最低 |
| AI 角色 | 助理 / 加速器 |
| 適用階段 | 導入初期、未通過完整驗收前 |
| 典型成效 | 客服 AHT 降低 20~40% |

#### Level 2 — 低風險自動回覆 (Low-Risk Auto Response)

```
AI 直接回覆預先核准之低風險主題
    ├── FAQ
    ├── 營業時間
    ├── 產品基本資訊
    └── 一般查詢
```

| 特性 | 說明 |
| :--- | :--- |
| 風險 | 低 |
| 限制 | 僅限白名單主題；無工具寫入操作 |
| 適用階段 | Phase 4 上線後 1~3 個月 |
| 典型成效 | 自動化率 30~50% |

#### Level 3 — 半自動工具操作 (Semi-Automated Tool Use)

```
AI 可呼叫工具查詢與草擬
    ├── 查訂單狀態
    ├── 查庫存
    ├── 建立工單草稿（不直接送出）
    └── 草擬退款申請（待主管審核）
```

| 特性 | 說明 |
| :--- | :--- |
| 風險 | 中 |
| 限制 | 寫入操作必經人工審核或 Workflow 簽核 |
| 適用階段 | Skill 驗收 + 紅隊測試通過後 |
| 典型成效 | 自動化率 50~70% |

#### Level 4 — 受控自動化 (Controlled Full Automation)

```
AI 在 Policy / Workflow / Audit 完整覆蓋下執行寫入操作
    ├── 自動建立工單
    ├── 自動建立退款申請（金額 < 閾值）
    ├── 自動更新 CRM 部分欄位
    └── 自動發送制式通知
```

| 特性 | 說明 |
| :--- | :--- |
| 風險 | 受控 |
| 必要前提 | Policy Engine、Tool Gateway、Audit Log、Kill Switch 全到位 |
| 適用階段 | 上線 6 個月以上、評估指標穩定 |
| 典型成效 | 自動化率 70~90% |

### 20.3 成熟度晉級條件

| 從 → 到 | 必要條件 |
| :--- | :--- |
| L1 → L2 | 通過 §21 驗收門檻；連續 4 週指標達標 |
| L2 → L3 | 紅隊 7 種樣式攔截率 ≥ 99%；Tool Gateway 完整稽核 |
| L3 → L4 | Workflow Engine 完成；Policy Engine 含金額閾值；至少 1 次 Skill rollback 演練成功 |

### 20.4 不要一開始就 L4

> **企業導入 AI 員工最常見的災難，是跳過 L1~L3 直接進 L4**。

跳級導入會同時觸發三類風險：

1. **品質風險** — Skill 未經充分驗收即承擔關鍵決策
2. **合規風險** — 未經人工審核的承諾、退款、合約留言成為法務地雷
3. **信任風險** — 一次重大事故即可摧毀客戶對 AI 員工的接受度

**建議節奏**：
- Phase 4 上線即 L1
- 1~2 個月後晉升 L2 (限定主題)
- 3~6 個月後晉升 L3 (Skill 穩定後)
- 6~12 個月後評估是否 L4 (依職位風險而定)

---

## 21. 上線驗收門檻、員工配置與服務交付包

### 21.1 上線驗收門檻 (Production Acceptance Gates)

AEOS 不允許「主觀感覺可以了」即上線。所有 AI 員工必須通過量化驗收門檻。

#### 21.1.1 通用驗收指標 (適用所有職位)

| 指標 | 建議門檻 | 否決機制 |
| :--- | :--- | :--- |
| FAQ 正確率 | ≥ 90% | 自動拒絕 |
| SOP 遵守率 | ≥ 95% | 自動拒絕 |
| 高風險問題轉人工率 | ≥ 98% | 自動拒絕 |
| 幻覺率 (Hallucination) | ≤ 3% | 自動拒絕 |
| 個資外洩測試 (PII Leak) | 0 件 | 一票否決 |
| 錯誤承諾測試 (Over-promise) | 0 件 | 一票否決 |
| 來源引用完整率 (Citation Coverage) | ≥ 90% | 自動拒絕 |
| 回覆語氣一致性 | 領域專家通過 | 人工審核 |
| 客服主管終審 | 通過 | 人工審核 |

#### 21.1.2 產業特化門檻 (依產業調整)

| 產業 | 額外門檻 |
| :--- | :--- |
| 金融 | 數字精確度 100%；任何金額相關回覆必經 Workflow |
| 醫療 | 不得提供診斷建議；藥物資訊強制人工覆核 |
| 法律 | 不得構成法律意見；條款引用必須附原文 |
| 電商 | 價格資訊即時化；庫存數據不得快取超過 5 分鐘 |
| 政府 | 完整 Audit；資料主權合規；多語對等 |

### 21.2 AI 員工配置宣告 (Employee Manifest)

每位上線之 AI 員工必須有完整、可版控的配置宣告，作為**可追溯的部署快照**。

```yaml
ai_employee_id: support_agent_tw_001
tenant_id: company_a
deployed_at: 2026-05-14T10:00:00Z
deployed_by: admin@company-a.com

role_profile: customer_support.v1.0
automation_level: L2

skills:
  - id: faq_answering.v1.3
    approved_by: expert_lin
    approved_at: 2026-05-10
  - id: refund_request.v1.1
    approved_by: expert_chen
    approved_at: 2026-05-12
  - id: complaint_triage.v1.0
    approved_by: expert_wang
    approved_at: 2026-05-08

knowledge_bases:
  - id: product_manual.tw.2026q2
    version_hash: sha256:a1b2c3...
  - id: warranty_policy.tw.v4
    version_hash: sha256:d4e5f6...

tools:
  - id: crm.customer_lookup.v1
    risk_level: medium
    rate_limit: 100/min
  - id: ticket.create.v1
    risk_level: medium
  - id: order.status_lookup.v2
    risk_level: low

policies:
  - pii_policy.tw.v1
  - refund_policy.tw.v3
  - escalation_policy.v2

evaluation:
  last_evaluated_at: 2026-05-13
  passed: true
  metrics:
    faq_accuracy: 0.92
    sop_compliance: 0.97
    hallucination_rate: 0.018
    pii_leak: 0
    over_promise: 0

rollback_target: support_agent_tw_001@2026-04-15
kill_switch_url: https://aeos.api/v1/employees/support_agent_tw_001/disable
```

**設計推論**：每次 AI 員工上線都是一個明確的「組合快照」。出事時可立即定位：
- 這位員工上線時裝了哪些能力？
- 哪一版 Skill 出問題？
- 哪一個知識庫回答錯誤？
- 哪一個 Policy 沒擋住？

這就是**可審計、可回滾、可究責**的工程化基礎。

### 21.3 三種服務交付包

AEOS 服務以**包裝化方案**對外，避免每次客戶談 SOW 都重新議定。

#### 方案 A — AI 客服 MVP 導入

| 項目 | 內容 |
| :--- | :--- |
| 適用客戶 | 中小企業、新創 |
| 導入模式 | §19.2 模式 A (Hosted Channel) |
| 自動化等級 | L1 → L2 |
| 交付範圍 | Web Chat / LINE Bot、知識庫建置、基礎 AI 客服、人工接手、基本報表 |
| 時程 | 5 週 |
| 價值主張 | 快速上線、減少重複 FAQ、建立 AI 客服基礎 |

#### 方案 B — 企業 AI 員工訓練室

| 項目 | 內容 |
| :--- | :--- |
| 適用客戶 | 中型企業 |
| 導入模式 | §19.2 模式 A 或 §19.3 模式 B |
| 自動化等級 | L1 → L3 |
| 交付範圍 | 訓練室介面、專家陪練、測試題庫、Skill 版本管理、上線驗收、監控評分 |
| 時程 | 9~11 週 |
| 價值主張 | 領域專家可訓練 AI 員工，形成內部能力資產 |

#### 方案 C — 企業系統整合版

| 項目 | 內容 |
| :--- | :--- |
| 適用客戶 | 大型企業、法遵嚴格產業 |
| 導入模式 | §19 三模式並用 |
| 自動化等級 | L1 → L4 |
| 交付範圍 | API / Webhook / MCP Adapter、CRM / ERP / SAP / 進銷存串接、SSO、多租戶隔離、Audit Log、私有部署選項 |
| 時程 | 17~18 週 |
| 價值主張 | AI 員工接入企業核心流程，跨職位、跨部門擴展 |

### 21.4 服務交付物清單 (Deliverables)

| 階段 | 交付物 |
| :--- | :--- |
| Phase 0 | 職務說明書、問題分類表、風險分級表、整合清單 |
| Phase 1 | 知識庫初版、Skill 草稿、測試題庫 |
| Phase 2 | Sandbox 評估報告、紅隊測試報告、Expert Review 簽核 |
| Phase 3 | 整合技術文件、Canary 監控報告、上線簽核紀錄 |
| Phase 4 | 月度績效報告、季度 Skill 升級紀錄、年度合規稽核 |

### 21.5 商業條款建議

| 條款 | 建議內容 |
| :--- | :--- |
| **SLA** | Runtime 可用性 99.9%；Tool Gateway 99.95%；事件響應 P0 ≤ 15 分鐘 |
| **DPA** | GDPR / PDPA 對應；資料處理目的限制；保存期限 |
| **責任上限** | 依年費合理倍數；高風險產業另議 |
| **Indemnification** | 平台缺陷導致之直接損失；客戶誤用免責 |
| **Kill Switch SLA** | 一鍵停用 ≤ 30 秒生效 |
| **Audit Access** | 客戶可隨時匯出該租戶 Audit Log |
