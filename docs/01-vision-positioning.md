# 願景與定位

> **本檔對應原 whitepaper.md 的 §1, §2, §3, §22**
> 主題定位：願景
> 最後同步：2026-05-14

## 相關章節速查

**本檔被外部引用的高頻章節**：
- §1 問題陳述 — 治理鴻溝六大風險
- §2 產品定位 — AI 員工平台抽象階梯、職位目錄、商業模式
- §3 設計原則 — 七大原則
- §22 戰略定位 — 公司本質、Wedge 三段敘事、VC 七大關鍵問題、護城河四層遞進

**本檔對外引用的章節**：
- §13 多模型策略 (見 `02-product-architecture.md`)
- §17 五階段方法論 (見 `03-execution-onboarding.md`)
- §18 Onboarding Layer (見 `03-execution-onboarding.md`)
- §29 三 Compiler (見 `05-investor-thesis.md`)

---

## 1. 問題陳述 — AI 員工的治理鴻溝

### 1.1 市場現況

當前企業導入 AI Agent 的常見路徑：

```
我要做 AI 客服
  → 找一套 Agent framework
  → 接 LINE / Web Chat / Email
  → 接 RAG (FAQ + 知識庫)
  → 接 CRM
  → 上線
```

這條路 6 週可以見成果，但隱含**六個無法承擔的風險**：

| 風險 | 來源 | 後果 |
| :--- | :--- | :--- |
| 知識污染 | Agent 自動把客戶 A 的對話寫入全域 memory | 回答客戶 B 時資料外洩 |
| 不當承諾 | 沒有 Policy Engine 約束話術 | 法務責任、品牌損傷 |
| 權限蔓延 | Agent 直接握有 ERP / SAP 憑證 | 內鬼風險、誤刪資料、未授權交易 |
| 技能漂移 | Self-improvement 在線上偷偷改 prompt 與 skill | SOP 退化、回歸測試失效 |
| 多租戶污染 | Multi-user 不等於 Multi-tenant，跨品牌資料外流 | GDPR / PDPA 違規 |
| 無法追溯 | 沒有完整 Audit Log，事故無從調查 | 合規不過、保險拒賠 |

### 1.2 治理鴻溝的本質

> **AI 加速時代真正要治理的不是「程式碼產出速度」，而是「需求變更、知識污染、技能漂移、權限蔓延如何被吸收、追蹤、驗證、同步」。**

沒有這層治理，AI 會把矛盾文件腦補成「合理版本」，把「看起來合理」的錯誤訊息產出量產化——這就是 AI slop 的根源。在企業場景，AI slop 不只是品質問題，是**法律責任問題**。

### 1.3 為什麼開源 Agent 框架不夠？

開源框架（Hermes、nanobot、CheetahClaws、各類 OpenClaw 衍生）解決的是 **Agent Loop + Tool Calling + Memory** 的工程實作。它們不解決：

- 多租戶資料隔離
- 角色化權限矩陣 (RBAC / ABAC)
- 技能版本管理與回滾
- 工具風險分級與閘道審批
- 對話品質評分與漂移檢測
- PII 偵測、遮罩與保留策略
- 法遵稽核 (GDPR、PDPA、SOC 2、ISO 27001)
- 跨職位、跨部門的工作流編排

**這些不是工程實作可以一次性解決的功能，是需要一套持續營運的「治理體系」。**

### 1.4 歷史定位 — AI 革命的「企業勞動力管理層」

紅杉資本 2026 年內部對談指出，AI 對 SaaS 產業的衝擊規模相當於「**中世紀重大變革級**」：

- 兩大舊護城河同時失效：技術壁壘（會寫程式）與固定流程工作流軟體
- 三類新護城河浮現：網絡效應 / 生態系統 / 領域知識數據資產

在此格局下，**AEOS 的歷史定位**是：

> **AI 革命中「企業勞動力管理層」的早期定義者。**
>
> 工業革命誕生了人力資源系統與企業 ERP；
> AI 革命同樣需要一套「AI 勞動力的招募、訓練、授權、考核、退休」管理體系。
>
> AEOS 不爭奪 LLM、Agent Runtime、客服 SaaS 的存量市場，而是定義「AI 員工生命週期管理」這個新類別。

**緊迫性**：當前是定義新類別的窗口期。一旦業界對「AI Employee」的心智模型固化於某個競爭對手，後進者將需付出 5~10 倍代價追趕。

---

## 2. 產品定位 — 從「AI 客服」到「AI 員工平台」

### 2.1 抽象階梯

```
Tenant 租戶
  └── Department 部門
        └── Role 職位
              └── AI Employee 員工 (執行物件)
                    ├── Skill 技能 (可版本化能力)
                    ├── Tool 工具 (受控外部能力)
                    ├── Workflow 工作流 (固定程序)
                    ├── Policy 規章 (公司規定)
                    ├── Knowledge 知識 (受治理 KB)
                    └── Evaluation 評核 (持續考績)
```

### 2.2 職位目錄 (Role Catalog)

AEOS 提供的不是單一 Bot，而是**可擴充的職位類別**：

| 職位類別 | 典型任務 | 風險等級 | 上線優先序 |
| :--- | :--- | :--- | :--- |
| AI 客服助理 | FAQ、查單、建工單、分流 | 中 | P0 |
| AI 業務助理 | 報價、行事曆、會議摘要 | 中 | P1 |
| AI 採購助理 | 詢價、比價、合約預審 | 高 | P2 |
| AI 維修助理 | SOP 引導、知識搜尋 | 中 | P1 |
| AI 法遵助理 | 條款檢核、合規問答 | 高 | P2 |
| AI 文件助理 | 摘要、翻譯、格式整理 | 低 | P0 |
| AI 工程助理 | Code review、CI 分析、文件生成 | 中 | P1 |
| AI 現場操作助理 | 巡檢提示、設備記錄 | 高 | P2 |

### 2.3 與既有 AI 客服 / RPA 產品的差異

| 維度 | 傳統 AI 客服 | RPA | **AEOS** |
| :--- | :--- | :--- | :--- |
| 抽象單位 | Bot | Script | **AI Employee** |
| 變更管理 | 改 prompt 上線 | 改腳本上線 | **Skill 版本 + Sandbox + Approval** |
| 範圍 | 單一通道、單一場景 | 單一流程 | **跨通道、跨職位、跨租戶** |
| 學習機制 | 無 / 線上 fine-tune | 無 | **訓練室博弈 + 凍結發布** |
| 評估 | NPS / CSAT | 成功率 | **多維 AgentOps 指標 + 漂移偵測** |
| 治理粒度 | Bot 層級 | Script 層級 | **Tenant × Role × Skill × Tool 矩陣** |

### 2.4 商業模式建議

| 收費維度 | 計價單位 | 適用客戶 |
| :--- | :--- | :--- |
| 平台訂閱 | 月費 / 年費 | 全部 |
| 員工席次 | 每位 AI Employee 月費 | 中大型企業 |
| Skill 商城 | 安裝授權費 + 使用量 | 願意買現成能力的客戶 |
| Token 用量 | LLM 成本轉嫁 + 加成 | 高用量客戶 |
| 訓練室服務 | 專家陪訓時數 | 需垂直客製的客戶 |
| 合規附加 | 稽核報告、法遵套件 | 受監管產業 |

---

## 3. 設計原則 (Design Principles)

### 原則 1：AI 員工不是模型，是受治理的執行物件

```
AIEmployee ≠ LLM
AIEmployee = Role + Skill + Policy + Tool + Workflow + Memory Boundary + Evaluation
```

**推論**：你不能對「一個 LLM」課責；但你可以對「一位被指派角色、配發技能與工具、被監控評核的 AI 員工」課責。

### 原則 2：Skill 是企業資產，不是 prompt 片段

Skill 必須是**完整 package**：

```
Skill =
    Prompt Spec
  + Input / Output Schema
  + Allowed Tools
  + Test Cases
  + Risk Level
  + Evaluation Metrics
  + Owner
  + Version
  + Rollback Target
```

**推論**：Skill 的生命週期應比照軟體套件管理 (Draft → Scan → Sandbox → Approval → Released → Deprecated → Archived)。

### 原則 3：Tool 是受控能力，不是 Agent 的自由權限

任何工具調用都必須經過：

```
Agent → Tool Gateway → Policy Engine → Audit Logger → Sandbox / Adapter → External System
```

**推論**：Agent 不應該知道 ERP / SAP / DB 的真實憑證；它只知道「我可以申請查詢這筆訂單」。

### 原則 4：Training 與 Production 必須分離

| 環境 | 允許 | 禁止 |
| :--- | :--- | :--- |
| Training Agent | 自我學習、Skill 生成、Prompt 變體、專家博弈 | 接觸真實客戶、寫入 Production 系統、自動發布 Skill |
| Production Agent | 使用 Approved Skill、Approved Tool、依 Workflow 執行 | 自我修改、自動擴權、自動安裝 Skill、長期記憶敏感資料 |

**推論**：上線員工是 **Frozen Runtime**。會學習的腦永遠關在訓練室。

### 原則 5：監控評分才是護城河

> 真正難的不是讓 Agent 回答，而是知道：它什麼時候答錯？為什麼答錯？錯誤是否變多？是否偏離 SOP？是否開始產生知識污染？是否某個 Skill 版本退化？是否某類客戶問題開始失控？

這就是 **AgentOps**。Agent 就像模型，**真正的護城河是監控漂移、評估退化、回放重訓**。

### 原則 6：MCP Host 要有，但不能裸奔

MCP 是工具協議，不是治理系統。Enterprise MCP Host 必須是「帶治理能力的 Host」，而非裸用 Claude Desktop / Nanobot。

### 原則 7：Governance-first，DevOps-later

前期不是做大而全的平台工程，而是先做**治理基礎設施**：

| 前期必須保留 | 前期可以延後 |
| :--- | :--- |
| 版本控管 | 多雲部署 |
| 審核紀錄 | Kubernetes |
| 執行日誌 | Service Mesh |
| 錯誤回放 | 多區域 HA |
| 權限設定 | 全自動 retraining pipeline |
| 資料隔離 | 多模型自動路由 |
| 一鍵停用 Agent | 完整 Observability Stack |
| 一鍵 rollback Skill | 多模型 marketplace |

---

## 22. 戰略定位與護城河論述

### 22.1 公司本質的精準定位

AEOS 不是以下任一類公司：

| 容易被誤認的定位 | 為何不是 |
| :--- | :--- |
| AI Chatbot 公司 | Chatbot 是入口，不是本體 |
| RAG 公司 | RAG 是技術手段，不是商業命題 |
| MCP 工具公司 | MCP 是協議，不是產品 |
| 客服系統公司 | 客服系統的戰場屬於 Zendesk / Intercom |
| LLM Wrapper 公司 | 模型會商品化，wrapper 沒有護城河 |

**AEOS 的精準定位**：

> **AI Employee Governance Platform — 把混亂企業知識變成可上線、可監控、可迭代的 AI 員工的能力體系。**

對外的商業敘事：

> *我們幫企業把一個 AI 員工從「資料混亂」訓練到「可以上班」，並且上線後可以被監控、評分、改版與治理。*

### 22.2 客服只是 Wedge，AI 員工平台才是公司本體

| 階段 | 對外產品 | 對內架構 |
| :--- | :--- | :--- |
| Year 1 | AI 客服員工 | AI Employee Lifecycle Engine |
| Year 2 | AI 客服 + AI 業務助理 + AI 採購助理 | 同一 Lifecycle 多職位擴展 |
| Year 3+ | Enterprise AI Workforce Platform | 跨職位、跨部門、跨企業的勞動力平台 |

**戰略原則**：

```
Narrow wedge, broad architecture
切口窄，架構寬
```

對外宣傳專注於「第一位 AI 客服員工」這個具體 wedge，但內部架構自第一天起即為多職位、多租戶、多模型設計。

### 22.3 投資人視角的關鍵問題

頂級 VC 不會只看技術，會問以下問題：

| VC 關鍵問題 | AEOS 應有的答案 |
| :--- | :--- |
| 是否大市場？ | 全球企業客服 + 業務 + 採購 + 法遵助理皆可承載 |
| 尖銳切入點？ | 客服 — 高頻、高痛、可量化 ROI |
| 客戶為何現在買？ | LLM 已成熟，企業急需可治理的落地路徑 |
| 導入後為何離不開？ | Skill / Knowledge / Evaluation History 累積在平台 |
| 資料是否越用越強？ | SkillOps Pipeline 形成資料飛輪 |
| 模型變強會被吃掉嗎？ | 模型變強反而強化平台價值（模型在 §13 抽象層後） |
| 大型 SaaS 能複製嗎？ | 治理體系 + 多租戶 + 跨職位設計需 18~24 個月追趕 |

### 22.4 三段式延展性敘事

對 VC 講故事的標準結構：

```
階段 1：客服切入
我們先幫企業建立第一位可治理的 AI 客服員工。

階段 2：AI Employee OS
所有 AI 員工共用一套訓練、驗收、權限、工具、監控與迭代閉環。

階段 3：Enterprise AI Workforce Platform
企業的 AI 員工就像 ERP 中的人類員工，被招募、訓練、考核、晉升、退休。
```

**VC 評估視角**：階段 1 證明可賣；階段 2 證明可規模；階段 3 證明可定義新品類。

### 22.5 護城河四層遞進

```
Layer 4  平台護城河  (Platform Lock-in)        ← 知識/Skill/Policy/History 全在平台
Layer 3  流程護城河  (Process Standardization) ← AEOS 成為導入標準流程
Layer 2  資料護城河  (Data Flywheel)           ← 跨客戶累積案例、題庫、Benchmark
Layer 1  服務護城河  (Service Excellence)      ← 早期靠交付服務建立信任
```

**重要承認**：AI 原生公司早期幾乎都長得像服務公司。**這不是缺點，是必經路徑**。但每次服務交付都必須沉澱為產品功能、Skill 模板、評估基準，才能逐層往上爬。

### 22.6 三句敘事標籤 (用於 Pitch / 募資文件)

```
1. AI 不缺模型，缺一套能安全進入企業流程的員工管理系統。
2. 我們從客服切入，建立 AI 員工的訓練、驗收、權限、工具、知識、監控與迭代閉環。
3. 客服是入口，AI Employee Operating System 才是公司本體。
```

### 22.7 外部驗證 — 紅杉資本 / Boris 觀點對照

紅杉資本 2026 年內部對談（Boris 等人）對 AI 衝擊 SaaS 的觀察，與 AEOS 戰略方向高度一致。本節整理對照供 Pitch / 募資使用。

#### 22.7.1 兩大舊護城河 vs AEOS 立場

| 紅杉觀察的「將被摧毀」護城河 | AEOS 是否屬於此類 | 說明 |
| :--- | :--- | :--- |
| 「會寫程式」的技術壁壘 | ❌ 不屬於 | AEOS 不賣「幫客戶寫 prompt / 接 RAG」，賣的是 Skill 治理 |
| 「固定流程工作流軟體」(傳統 SaaS) | ❌ 不屬於 | AEOS 固化的是 **meta-流程**（治理）非業務流程，見 §17 / §18 釐清 |

**結論**：紅杉預言「將死的兩種 SaaS」**不包含 AEOS**。

#### 22.7.2 三類新護城河 vs AEOS 對應能力

| 紅杉觀察的「將崛起」護城河 | AEOS 對應章節 | 對應能力 |
| :--- | :--- | :--- |
| 網絡效應 / 生態系統 | §22.5 Layer 4 平台護城河 | Skill / Knowledge / Policy / History 鎖定客戶 |
| 數據資源 (跨客戶累積) | §29.5~29.7 三個 Compiler | Data → Knowledge → Skill → Iteration 飛輪 |
| 領域知識 / 專業 know-how | §29.3 強護城河 (Evaluation Dataset / SkillOps / Governance) | 把客戶 know-how 沉澱為可治理數據資產 |

**結論**：紅杉預言「將崛起的三種護城河」**全部對應 AEOS 既有設計**。

#### 22.7.3 對 Pitch / 募資的話術

```
紅杉資本 2026 觀察：
「AI 摧毀的是『會寫程式 + 固定流程』兩類 SaaS；
 崛起的是『網絡效應 + 數據資源 + 領域知識』三類護城河。」

AEOS 戰略對位：
- 不在被摧毀的兩類 → 我們不賣 prompt / 不賣固定流程
- 完全對應崛起的三類 → 我們賣治理 / 數據飛輪 / Compiler
```

#### 22.7.4 必須警惕的紅線

紅杉觀察隱含的反向警告，AEOS 必須堅守：

| 紅線 | 違反後果 |
| :--- | :--- |
| 不可把產品做成「Agent + RAG + Workflow Designer」 | 必死 — 這些會被 AI 動態生成取代 |
| 不可把護城河放在「我們的 Agent 比較強」 | 必死 — 模型供應商會直接吃掉 |
| 不可固化客戶業務流程 | 必死 — 違反「meta-流程 vs 業務流程」原則 |

→ 凡產品決策觸碰任一紅線，需重新檢視是否偏離 §22.5 護城河四層架構。
