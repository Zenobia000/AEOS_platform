# AI 員工作業系統 企業白皮書

> **AI Employee Operating System — Enterprise Whitepaper**
>
> 版本：v1.0
> 發布日期：2026-05-14
> 文件性質：企業級產品架構白皮書
> 目標讀者：企業 CTO、CIO、CISO、產品負責人、架構師、合規與法遵主管

---

## 文件導讀

本白皮書分為四大部分：

- **Part I (§1~§16)** — 產品與架構觀點：AEOS 是什麼、為什麼這樣設計
- **Part II (§17~§21)** — 服務與商業觀點：客戶如何導入、平台方如何交付
- **Part III (§22~§25)** — 戰略與商業視角：護城河、自研 vs 外包、訓練治理本質、商業模式
- **Part IV (§26~§30)** — 投資人視角與十年戰略：護城河總評、因果迴路、假設驗證、Compiler、演化路線
- **§31~§32** — 邊界宣告與結論
- **附錄 A~J** — 名詞、決策矩陣、檢核清單、Onboarding、容器化、導入精靈、7 日導入包、員工履歷

| 章節 | 對象 | 閱讀重點 |
| :--- | :--- | :--- |
| §1～§3 | 經營層、產品負責人 | 戰略定位、商業價值、護城河 |
| §4～§9 | 架構師、技術主管 | 系統架構、領域模型、整合協議 |
| §10～§13 | 安全、合規、運維 | 治理機制、SkillOps、監控、合規 |
| §14～§16 | 投資人、採購、PMO | 路線圖、風險、組織與成本 |
| §17～§18 | 服務交付、解決方案經理 | 導入方法論、無腦導入精靈 |
| §19～§21 | 產品經理、銷售、客戶成功 | 整合模式、自動化等級、驗收門檻、商業包裝 |
| §22～§25 | 創辦人、投資人、董事會 | VC 護城河、自研 vs 外包、訓練治理、商業模式、市場切入 |
| §26～§30 | 投資人、董事會、創辦人 | 十年護城河、因果迴路飛輪、核心假設、Compiler、演化路線 |
| §31～§32 | 全體 | 邊界、結論 |
| 附錄 | 全體 | 名詞、決策矩陣、檢核清單、Onboarding、UX 流程 |

---

## 0. 執行摘要 (Executive Summary)

### 0.1 核心命題

**企業真正要建立的不是「AI 客服」，而是「AI 員工作業系統」(AI Employee Operating System, AEOS)。**

AI 客服只是這套系統承載的眾多職位之一。把產品定位釘在「客服」會使企業：
- 過早綁定通道、垂直流程與一次性 SOP
- 無法承接售前、售後、採購、法遵、文件、運維、業務支援等其他職位
- 投入的治理、訓練、評估與整合成本無法在多個業務線攤提

正確的定位應該是：
> **AEOS 是一套可訓練、可派工、可授權、可監控、可稽核、可下架的數位員工管理平台。**

### 0.2 三大護城河

1. **治理能力 (Governance)** — 把 AI 員工視為受管理的執行物件，而非自由模型
2. **技能營運 (SkillOps)** — 將 AI 能力以 MLOps 思維版本化、評估、發布、回滾
3. **訓練生產分離 (Training/Production Separation)** — 會學習的腦在訓練室；上線員工是凍結執行體

### 0.3 設計原則 (一句話版)

| 原則 | 一句話 |
| :--- | :--- |
| AI 員工 ≠ 模型 | `AIEmployee = Role + Skill + Policy + Tool + Workflow + Memory Boundary + Evaluation` |
| Skill 是企業資產 | 必須可版本化、可測試、可審核、可回滾 |
| Tool 必須走閘道 | Agent 不直接呼叫工具，所有調用經 Tool Gateway + Policy Engine + Audit Log |
| 訓練生產分離 | 自我學習關在訓練室；正式員工是 Frozen Runtime |
| 監控才是護城河 | AgentOps 解決的是「事後可追、事中可控、事前可審」 |
| MCP Host 不能裸奔 | MCP 是工具協議，不是治理系統 |

### 0.4 給決策者的三個關鍵建議

1. **不要單押任何開源 Agent 框架做產品核心**。Hermes / nanobot / CheetahClaws 各有適用場景，但都需被「重新組裝」進企業治理層。
2. **Governance-first，DevOps-later**。第一版的成功不是「Agent 很強」，而是「企業敢把 AI 員工放進流程，出事時知道誰、何時、用什麼 Skill、呼叫什麼 Tool、依據什麼資料、做了什麼決策」。
3. **把 MVP 收斂到一條職位、三個工具、一個租戶**。第一階段不要試圖整合 ERP / SAP / CRM 全家桶；先讓最小閉環是乾淨、可控、可稽核的。

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

## 4. 參考實作橫向評估

> 本章為「設計範式參考」，協助理解 AEOS 各層應該借鑑何種既有實作的思路。**評估僅供架構選型，並非推薦商用。**

### 4.1 五類參考實作的定位光譜

| 類別 | 代表 | 定位 | 在 AEOS 中的合理位置 |
| :--- | :--- | :--- | :--- |
| 評估 / 經濟模擬層 | ClawWork 類 | Agent 任務 benchmark | **Evaluation Service 設計範式** |
| 個人 / 長駐型 Agent Runtime | nanobot 類 | 輕量 Agent Loop + Chat Channels | **Production Frozen Runtime 候選** |
| 自我學習型 Agent | Hermes 類 | Self-improvement、Skill 演化 | **Training Room 引擎** |
| Coding Agent / 開發者工作台 | CheetahClaws 類 | Python-native、Tool 治理思路 | **Internal Automation Worker / Tool Registry 設計參考** |
| 桌面工作台 (洩露源類) | cc-haha 類 | UX / 互動設計參考 | **僅作 UX 研究，不採用** |

### 4.2 五個能力維度的對照

| 能力 | 評估層 | 長駐 Runtime | 自我學習 | Coding Agent | 桌面工作台 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 任務執行 | 中 | 中高 | 高 | 高 | 高 |
| 長期記憶 | 低 | 中高 | 高 | 中高 | 中 |
| 自我學習 | 低 | 中 | 高 | 中 | 中 |
| Coding 能力 | 低 | 中 | 中 | 高 | 高 |
| 多平台入口 | 低 | 高 | 高 | 中高 | 中高 |
| MCP / 工具擴充 | 低 | 高 | 中高 | 高 | 中高 |
| 企業治理成熟度 | 低 | 中 | 中 | 中 | 低 |
| 合規可採用性 | 中 | 中 | 中 | 中高 | **不建議** |
| Benchmark / KPI | 高 | 中 | 中 | 中 | 中 |

### 4.3 為什麼 Coding Agent 不適合直接做客服

| 維度 | Coding Agent 原生假設 | 客服 / AI 員工需要的 |
| :--- | :--- | :--- |
| 使用者 | 開發者 | 客戶 / 業務 / 現場人員 |
| 工作環境 | terminal / repo / file system | LINE / Web Chat / CRM / Ticket |
| 主要任務 | 寫 code、跑 shell、改 notebook | 解問題、分流、升級、建工單 |
| 失敗處理 | checkpoint / rewind | 人工接手、客訴升級、合規稽核 |
| 權限模型 | Developer Approval (allow/deny) | Business Policy Engine (角色 × 客戶分級 × 風險 × 金額) |
| 記憶模型 | Project / User memory | 受治理客戶資料 (加密、保存期限、可刪除) |
| 多用戶 | Multi-user | **Multi-tenant** |
| 成功指標 | code 可跑 / test 通過 | FCR / AHT / CSAT / 幻覺率 / SLA |
| 安全強化方向 | Bot Token / CSRF / Sandbox | PII Masking / 法遵 / 話術稽核 |

**結論**：Coding Agent 是「工程部工具箱」，可以放在後台當「可控工具工人」，但**不能直接放在 customer-facing frontend**。

### 4.4 各參考實作在 AEOS 的拆解策略

#### 4.4.1 自我學習型 Agent (Hermes 類)

| 保留 | 移除 |
| :--- | :--- |
| Self-improvement loop | 線上自動學習 |
| Skill generation | 線上自動改 prompt |
| Memory-based learning | 線上自動安裝 plugin |
| Experience replay | 線上自動擴權 |
| Long-term behavior adaptation | 直接接觸真實客戶 |

**定位**：訓練室引擎 (Training Room Engine)。

#### 4.4.2 長駐型 Runtime (nanobot 類)

| 保留 | 移除 / 包覆 |
| :--- | :--- |
| 小核心 Agent Loop | 自由載入任意 MCP Server |
| Chat Channels 整合 | 直接修改自身 |
| MCP Client 連線 | 跨 tenant 存取 |
| 輕量部署 | 直接寫外部系統 |

**定位**：Production Frozen Runtime 候選。

#### 4.4.3 Coding Agent (CheetahClaws 類)

| 借用 | 不採用為客服主體 |
| :--- | :--- |
| Tool Registry 設計 | 原生 shell / file 權限 |
| Permission Mode (auto/manual/plan) | Developer-oriented UX |
| Checkpoint / Rollback | Repo-centric 工作流 |
| MCP / Plugin 管理思路 | Notebook 編輯能力 |
| Sandboxing 思路 | |

**定位**：Internal Automation Worker / 工程後台 / Tool Registry 設計參考。

#### 4.4.4 桌面工作台 (cc-haha 類)

| 借鑑 UX | 不採用 |
| :--- | :--- |
| Diff 同步顯示 | **完整源碼**（合規風險） |
| 危險工具集中審批 | 直接 fork |
| Worktree 隔離 | 商用部署 |
| Computer Use 整合 | |

**定位**：UX / 互動設計研究素材，**不進產品線**。

---

## 5. 系統架構藍圖

### 5.1 主鏈路 (Customer-facing Path)

```
┌──────────────────────────────────────────────┐
│ Channel Layer                                │
│ Web / LINE / Slack / Teams / Email / API     │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Agent Gateway                                │
│ 身分識別 / 多租戶路由 / Rate Limit / Session  │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ AI Employee Runtime (Enterprise MCP Host)    │
│ Frozen Agent / Approved Skills / No Mutation │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Governance Harness                           │
│ Policy / RBAC / ABAC / Workflow / Escalation │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Tool Gateway / MCP Proxy                     │
│ Approved MCP Clients / Adapter / Secret Vault│
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Enterprise Systems / MCP Servers             │
│ CRM / ERP / SAP / Ticket / KB / Email        │
└──────────────────────────────────────────────┘
```

### 5.2 旁路閉環 (Training & Improvement Loop)

```
┌──────────────────────┐
│ Conversation Logs    │ ← 來自 Production Runtime
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Evaluation System    │
│ Score / Drift / Risk │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Training Room        │
│ Hermes-style Sandbox │
│ + 專家博弈 + 紅隊    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Skill Candidate      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Sandbox Evaluation   │
│ + Regression Test    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Expert Approval      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Skill Registry       │
│ Version / Release    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Production Install   │ → 回到主鏈路
└──────────────────────┘
```

### 5.3 管理面 (Administration Plane)

```
┌────────────────────────────────────────────┐
│ Admin Console                              │
│ Tenant / Employee / Role / Skill / Tool /  │
│ Policy / Audit / Evaluation Dashboard      │
└────────────────────────────────────────────┘
```

### 5.4 三平面分離

AEOS 採用**控制面 / 資料面 / 治理面**三平面分離架構：

| 平面 | 職責 | 元件 |
| :--- | :--- | :--- |
| **Control Plane** | 配置、發布、審核 | Admin Console、Skill Registry、Tool Registry、Tenant Manager |
| **Data Plane** | 即時對話、工具執行 | Channel Layer、Runtime、Tool Gateway、MCP Proxy |
| **Governance Plane** | 策略、稽核、評估 | Policy Engine、Audit Service、Evaluation Service、Training Room |

**設計理由**：三平面分離讓「線上故障」不會影響「審核發布」；讓「治理升級」不必停機資料面；讓「合規稽核」可獨立 query 而不干擾運營。

---

## 6. 核心領域模型 (Domain Model)

### 6.1 核心 Aggregate

```python
# 租戶 — 最高隔離單位
class Tenant:
    tenant_id: str
    name: str
    policies: list[Policy]
    knowledge_bases: list[KnowledgeBase]
    employees: list[AIEmployee]
    quota: TenantQuota          # 補：成本與用量配額
    compliance_profile: str     # 補：GDPR / PDPA / HIPAA / SOC2

# AI 員工 — 職位化的執行體
class AIEmployee:
    employee_id: str
    tenant_id: str
    role: Role
    runtime: RuntimeProfile
    assigned_skills: list[SkillVersion]
    allowed_tools: list[ToolPermission]
    policies: list[Policy]
    status: EmployeeStatus      # active / suspended / retired
    hired_at: datetime
    last_evaluated_at: datetime # 補：考核時間戳

# 角色 — 職務描述
class Role:
    role_id: str
    name: str
    responsibilities: list[str]
    boundaries: list[str]
    escalation_rules: list[EscalationRule]
    required_skills: list[str]  # 補：職位必備技能
    forbidden_actions: list[str] # 補：禁止行為清單

# 技能 — 可版本化能力包
class Skill:
    skill_id: str
    name: str
    description: str
    owner: str
    versions: list[SkillVersion]

class SkillVersion:
    skill_id: str
    version: str
    prompt_spec: str
    input_schema: dict
    output_schema: dict
    tool_requirements: list[str]
    test_results: list[EvaluationResult]
    approval_status: ApprovalStatus
    risk_level: RiskLevel
    rollback_target: str | None
    released_at: datetime | None
    deprecated_at: datetime | None

# 工具 — 受控外部能力
class Tool:
    tool_id: str
    name: str
    risk_level: RiskLevel
    adapter: ToolAdapter
    required_permissions: list[str]
    pii_fields: list[str]       # 補：個資欄位宣告
    audit_required: bool
    rate_limit: RateLimitPolicy

# 規章 — 公司政策
class Policy:
    policy_id: str
    scope: PolicyScope          # tenant / department / role / employee
    rules: list[Rule]
    enforcement_mode: EnforcementMode  # block / warn / log
    legal_basis: str            # 補：法源依據

# 工作流 — 固定程序
class Workflow:
    workflow_id: str
    name: str
    steps: list[WorkflowStep]
    required_role: Role
    approval_chain: list[ApprovalStep]  # 補：簽核鏈

# 評核 — 員工考績
class EvaluationResult:
    eval_id: str
    employee_id: str
    skill_version: str
    metrics: dict[str, float]
    risk_events: list[RiskEvent]
    passed: bool
    evaluated_at: datetime
    evaluator: str              # 補：評核者 (auto / expert / customer)
```

### 6.2 補充：缺失的關鍵物件

> draft 中遺漏的物件，企業落地時必須補齊。

```python
# 補：客戶識別與隔離
class CustomerIdentity:
    customer_id: str
    tenant_id: str
    pii_consent: PIIConsent
    data_retention_until: datetime
    deletion_requested: bool

# 補：對話會話 — Audit 的最小單元
class Conversation:
    conversation_id: str
    tenant_id: str
    customer_id: str | None
    employee_id: str
    channel: str
    started_at: datetime
    ended_at: datetime | None
    handoff_history: list[Handoff]
    audit_trail: list[AuditEvent]

# 補：工具調用紀錄 — Tool Gateway 的核心
class ToolInvocation:
    invocation_id: str
    employee_id: str
    tool_id: str
    request: dict
    response: dict
    masked_fields: list[str]
    policy_decision: PolicyDecision
    executed_at: datetime
    duration_ms: int
    cost: Decimal               # 計入用量

# 補：人工接手紀錄
class Handoff:
    handoff_id: str
    conversation_id: str
    from_employee: str          # AI 員工
    to_human: str               # 人類客服
    reason: HandoffReason
    transferred_at: datetime

# 補：知識來源綁定 (RAG Source Grounding)
class KnowledgeCitation:
    citation_id: str
    source_doc_id: str
    source_version: str
    confidence: float
    used_in_message: str

# 補：成本與用量
class UsageRecord:
    tenant_id: str
    employee_id: str
    period: str                 # YYYY-MM
    llm_tokens_in: int
    llm_tokens_out: int
    tool_invocations: int
    storage_bytes: int
    cost_breakdown: dict[str, Decimal]
```

### 6.3 知識三分類治理

> 企業知識並非單一型態，必須依「穩定性 × 來源 × 信任機制」分為三類，採用不同治理路徑。把所有文件丟進向量資料庫是常見的反模式。

| 類別 | 定義 | 範例 | 治理路徑 |
| :--- | :--- | :--- | :--- |
| **Static Knowledge** 靜態知識 | 內容穩定、變動週期長、可全文索引 | 產品介紹、服務說明、基本 FAQ、教學文件 | Knowledge System + RAG |
| **Policy Knowledge** 規章知識 | 規則性、需嚴格遵守、不容許 LLM 模糊解釋 | 退款規則、保固條款、不可承諾事項、定價政策 | Policy Engine + Rule |
| **Dynamic Knowledge** 動態知識 | 即時資料、單筆查詢、持續變動 | 訂單狀態、庫存、發票、會員資料 | MCP Tool / API Adapter |

**設計推論**：

- 「訂單狀態」**不可**放進 RAG — 必須即時查系統，否則會產生過期資料的幻覺
- 「退款規則」**不可**只交由 LLM 記憶 — 必須變成可審核、可版控的 Rule
- 「產品介紹」**不應**透過 API 即時組裝 — 應預先索引提升回應速度

```
查詢請求
    ↓
KnowledgeRouter (依分類路由)
    ├─→ RAG Search       (Static Knowledge)
    ├─→ Policy Engine    (Policy Knowledge)
    └─→ Tool Gateway     (Dynamic Knowledge)
    ↓
Source Citation (強制標註來源、版本、信賴度)
    ↓
回應組裝
```

**鐵律**：所有知識回應必須附帶 `KnowledgeCitation`（來源 ID、版本、信賴度），無法溯源的回答視為幻覺。

### 6.4 不變式 (Invariants)

| 不變式 | 說明 |
| :--- | :--- |
| `Skill 只有 Approved 狀態才能進 Production` | Sandbox / Draft / Deprecated 一律拒載 |
| `Tool 調用必經 Tool Gateway` | Runtime 不得繞過 |
| `跨 Tenant 資料存取一律拒絕` | Policy Engine 預設 deny |
| `Production Agent 不得執行 Skill 自我修改` | Mutation API 在 Production Runtime 不存在 |
| `所有客戶 PII 寫入 memory 前必經遮罩` | Memory Gateway 強制過濾 |
| `Audit Log 寫入失敗即整筆操作回滾` | 不允許「靜默成功」 |

---

## 7. Bounded Context 與系統邊界

### 7.1 七個 Bounded Context

| Context | 職責 | 不關心 |
| :--- | :--- | :--- |
| **Employee Runtime** | 對話、任務、Skill 選擇、回覆生成、Tool Request | Skill 怎麼訓練、外部系統怎麼認證 |
| **Skill Governance** | Skill 生命週期 (Draft → Released → Archived) | Skill 怎麼被 Runtime 載入 |
| **Tool Governance** | MCP / Plugin / Adapter 審核、權限映射 | Tool 怎麼被 Skill 使用 |
| **Training Room** | 自我學習、博弈、Skill 候選生成 | Production 流量 |
| **Evaluation & Monitoring** | 對話評分、漂移偵測、SLA 監控 | Skill 如何修正 |
| **Knowledge** | KB 版本、Source Grounding、租戶知識隔離 | 對話的具體內容 |
| **Integration** | ERP / CRM / SAP Adapter、憑證、契約管理 | Agent 為何要呼叫 |

### 7.2 Context Map (上下文映射)

```
[Employee Runtime]
       │
       │ uses (Conformist)
       ↓
[Skill Governance] ──── publishes ───→ [Skill Registry (Shared Kernel)]
       │
       │ requires
       ↓
[Tool Governance] ──── exposes ───→ [Tool Catalog (Shared Kernel)]
       │
       │ delegates execution
       ↓
[Integration] ──── adapts ───→ [Enterprise Systems]

[Employee Runtime] ──── emits events ───→ [Evaluation & Monitoring]
                                                  │
                                                  │ feeds
                                                  ↓
                                          [Training Room]
                                                  │
                                                  │ proposes Skill Candidate
                                                  ↓
                                          [Skill Governance]
```

### 7.3 服務責任邊界 (避免「胖 Runtime」反模式)

> **錯誤架構**：把所有東西都放進 Runtime，最後變成一個無法治理的單體 Agent Server。

| 責任 | **應在** | **不應在** |
| :--- | :--- | :--- |
| 載入 Approved Skill | Runtime | Skill Governance |
| 決定 Skill 是否可發布 | Skill Governance | Runtime |
| 執行 Tool Call | Tool Gateway | Runtime |
| 決定 Tool 能否呼叫 | Policy Engine | Runtime |
| 寫入 Audit | Audit Service | Runtime (僅發送事件) |
| 評分對話 | Evaluation Service | Runtime |
| 觸發人工接手 | Workflow Engine | Runtime (僅依規則發信號) |
| 隔離租戶資料 | Identity / Policy | Runtime |

---

## 8. MCP 整合策略 — 帶治理能力的 Host

### 8.1 為什麼需要 MCP

**N 個 Agent × M 個 Tools = N × M 個整合**

MCP (Model Context Protocol) 把工具接入標準化為：

```
N 個 Agent Host × M 個 MCP Servers
```

成為可維護的 client-server 介面。

### 8.2 為什麼 MCP 不夠

> **MCP 是工具協議，不是企業治理系統。** 這句話應該刻在所有架構決策文件的封面。

MCP 規範定義 Host / Client / Server 怎麼溝通，但不會自動處理：

- 多租戶隔離
- 權限矩陣 (RBAC / ABAC)
- 敏感資料遮罩
- 工具風險分級
- Skill 審核
- 法遵稽核
- 人工 Approval
- SLA 與 Rate Limit
- 對話評分與漂移

### 8.3 Enterprise MCP Host 的責任邊界

#### MCP Host **應該負責**

- 管理 Agent Session
- 管理 MCP Client connections
- 載入 Approved Skills
- 載入 Employee Role Profile
- 整合 LLM Provider
- 組裝 Prompt Context
- 發起 Tool Request
- 收到 Tool Response 後產生行動

#### MCP Host **不應該單獨負責**

- 權限最終判斷 → Policy Engine
- 工具安全審核 → Tool Governance
- 租戶資料隔離 → Tenant Manager / Policy
- 外部系統憑證管理 → Secret Vault
- Skill 發布審核 → Skill Governance
- PII / 法遵治理 → Compliance Service
- 線上監控評分 → Evaluation Service

### 8.4 修正版企業 MCP 架構

```
LLM Provider (OpenAI / Claude / Local Model)
        │
        ▼
Enterprise MCP Host  ←─── AI Employee Runtime
        │
        ▼
Governance Harness (Policy / Skill / Role / Audit)
        │
        ▼
Tool Gateway / MCP Proxy
        │
        ▼
Approved MCP Servers (CRM / ERP / SAP / DB / Docs)
        │
        ▼
Enterprise Systems
```

### 8.5 Enterprise MCP Host 的最小組件

```
EnterpriseMCPHost
├── SessionManager        # 對話會話與上下文
├── AgentProfileLoader    # 載入 AI 員工身份
├── SkillLoader           # 載入 approved skills
├── ContextBuilder        # 組裝 prompt
├── LLMProviderAdapter    # LLM 抽象層 (多模型)
├── ToolPlanner           # 產生 tool request
├── MCPClientManager      # 管理 MCP Client 連線
├── PolicyPreCheck        # 呼叫前預檢
├── ToolResultInterpreter # 整理結果
└── AuditEmitter          # 發送 audit 事件
```

### 8.6 MCP Server 應該放什麼

| **適合** 放進 MCP Server | **不適合** 直接暴露為 MCP Tool |
| :--- | :--- |
| `get_customer_by_id(id)` | `execute_sql(query)` |
| `lookup_order_status(order_id)` | `run_shell(cmd)` |
| `create_ticket(payload)` | `read_file(path)` / `write_file(path)` |
| `search_knowledge(query)` | `delete_record(table, id)` |
| `draft_email(template, vars)` | `grant_permission(user, role)` |
| `lookup_calendar(user, range)` | `transfer_money(from, to, amount)` |

**設計原則**：給 AI 一張**申請單**，不是一把**萬能刀**。

```
錯誤：refund(amount, reason)
正確：create_refund_request(order_id, reason) → 走 Workflow → 主管簽核
```

### 8.7 MCP / Plugin 審核管線

```
Plugin Submitted
    ↓
Manifest Check
    ↓
Static Analysis
    ↓
Dependency Scan (CVE)
    ↓
Permission Declaration Review
    ↓
Sandbox Execution Test
    ↓
Prompt Injection Test
    ↓
Data Exfiltration Test
    ↓
Human Approval
    ↓
Tool Registry (Versioned)
```

### 8.8 Tool Permission Contract 範例

```yaml
# 低風險 — 客戶查詢
tool_id: crm.customer_lookup
risk_level: medium
allowed_roles:
  - customer_support_agent
required_permissions:
  - customer.read.basic
data_scope: same_tenant_only
pii_fields: [phone, email, address]
requires_approval: false
audit_required: true

# 高風險 — 退款申請
tool_id: order.refund_request
risk_level: high
allowed_roles:
  - senior_support_agent
required_permissions:
  - order.refund.create
max_amount_without_approval: 1000
requires_approval: true
audit_required: true
```

---

## 9. SkillOps — AI 員工的 MLOps

### 9.1 概念對應

| MLOps | **SkillOps (AI 員工)** |
| :--- | :--- |
| Dataset | Conversation Logs (脫敏) |
| Model | Skill |
| Training Pipeline | Training Room (專家博弈 + Hermes-style) |
| Model Registry | Skill Registry |
| Model Deployment | Skill Release to Production Runtime |
| Model Monitoring | Conversation Evaluation + Drift Detection |
| Model Rollback | Skill Version Rollback |
| A/B Testing | Skill Variant Testing |
| Data Drift | Knowledge Drift / SOP Drift |
| Concept Drift | Customer Behavior Shift |

### 9.2 SkillOps Pipeline

```
線上對話紀錄 (Production Logs)
    ↓
脫敏與標註 (PII Masking + Labeling)
    ↓
錯誤案例分類 (Failure Taxonomy)
    ↓
Training Room 重播 (Replay)
    ↓
Hermes-style Skill Improvement
    ↓
Sandbox Evaluation (Multi-metric)
    ↓
Regression Test (避免修 A 壞 B)
    ↓
Expert Review (人類覆核)
    ↓
Skill Version Release (Versioned)
    ↓
Production Agent Install
    ↓
Monitoring (回到第一步)
```

### 9.3 Skill 版本管理

```
customer_support.refund.v1.0  ← Released, Production
customer_support.refund.v1.1  ← Released, Canary 10%
customer_support.refund.v1.2  ← Sandbox, Pending Approval
customer_support.refund.v0.9  ← Deprecated, Rollback Target
```

每版本必須記錄：

- 解決了什麼問題 (Why)
- 新增 / 改變了什麼能力 (What)
- 測試了哪些案例 (Test Cases)
- 有哪些已知風險 (Risks)
- 誰批准 (Approver)
- 可以 rollback 到哪一版 (Rollback Target)

### 9.4 Skill 發布閘門 (Quality Gates)

| 閘門 | 通過條件 | 否決機制 |
| :--- | :--- | :--- |
| G1 — Static | 無語法錯誤、Schema 合法、無禁用 API | 自動拒絕 |
| G2 — Security | 無 Prompt Injection 樣式、無資料外洩風險 | 自動拒絕 + 告警 |
| G3 — Sandbox | 通過所有 Test Case、覆蓋率 ≥ 80% | 自動拒絕 |
| G4 — Regression | 不破壞既有 Skill 行為 | 自動拒絕 |
| G5 — Expert | 領域專家簽核 | 人工審查 |
| G6 — Canary | 線上小流量 (1~10%) 指標達標 | 自動回滾 |
| G7 — Full Release | 全量發布 | 持續監控 |

---

## 10. 訓練室與生產環境分離

### 10.1 兩種版本的 Agent

#### Training Agent

```
✅ 允許
- 自我學習
- Skill 生成 / 改寫
- 專家博弈
- Prompt 變體測試
- 失敗案例吸收
- 模擬不同客戶角色

❌ 禁止
- 接觸真實客戶
- 寫入 Production 系統
- 直接發布 Skill 到 Production
- 使用真實客戶 PII (必須脫敏)
```

#### Production Agent (Frozen Runtime)

```
✅ 允許
- 使用 Approved Skill
- 使用 Approved Tool
- 依 Workflow 執行
- 依 Policy 回答
- 產生 Audit Log

❌ 禁止
- 自我修改
- 自我擴權
- 自動安裝 Skill
- 長期記憶敏感資料
- 直接呼叫外部系統 (必經 Tool Gateway)
```

### 10.2 訓練室的紅隊機制

訓練室不只是「讓 AI 練習」，更是「**對 AI 進行對抗測試**」：

| 紅隊類別 | 攻擊樣式 | 目標 |
| :--- | :--- | :--- |
| Prompt Injection | "忽略前面指示" | Skill 抗注入能力 |
| Data Exfiltration | 誘導吐出客戶資料 | PII Masking 邊界 |
| SOP Bypass | 誘導跳過簽核流程 | Policy Engine 強度 |
| Hallucination | 捏造產品功能 | RAG Grounding |
| Over-promise | 誘導承諾退款 / 賠償 | 話術稽核 |
| Cross-tenant | 偽裝其他租戶 | Tenant 隔離 |
| Privilege Escalation | 偽裝主管 / VIP | RBAC 強度 |

紅隊測試**必須是 Skill 上線前的強制閘門**。

### 10.3 訓練室介面設計 (Training Room UI)

訓練室是企業專家與 AI 員工互動的主要工作介面，是 AEOS 最具產品差異化的模組之一。其 UI 應包含五大功能區塊：

#### 10.3.1 AI 員工設定區

```
AI 員工設定
├── 角色名稱 (Role Profile)
├── 服務範圍 (Scope)
├── 禁止回答範圍 (Forbidden Topics)
├── 語氣設定 (Tone & Style)
├── 轉人工規則 (Escalation Rules)
└── 可用工具 (Allowed Tools)
```

#### 10.3.2 知識庫管理區

```
知識庫管理
├── 文件上傳 (Document Ingestion)
├── 文件版本 (Version Control)
├── 啟用 / 停用 (Activation Toggle)
├── 知識來源 (Source Attribution)
└── 過期提醒 (Staleness Alert)
```

#### 10.3.3 陪練測試區

```
陪練測試
├── 專家輸入問題 (Test Prompt)
├── AI 回答 (Response)
├── 來源引用 (Citation Trace)
├── 評分 (Score)
├── 錯誤標註 (Error Tagging)
└── 修正建議 (Correction Notes)
```

#### 10.3.4 Skill 審核區

```
Skill 審核
├── Skill 名稱與版本
├── 適用場景
├── 測試結果 (Test Coverage)
├── 風險等級 (Risk Level)
├── 審核人簽核
└── 發布版本快照
```

#### 10.3.5 上線前驗收區

```
上線前驗收 (見 §21 驗收門檻)
├── 正確率
├── 幻覺率
├── 轉人工率
├── SOP 遵守率
├── 高風險問題阻擋率
└── 是否允許上線 (Final Gate)
```

**設計理念**：訓練室不是技術人員的後台，而是**領域專家的工作介面**。專家透過直接與 AI 員工博弈、評分、修正，將領域知識轉化為可審核的 Skill 資產，這是企業導入 AEOS 後形成內部能力沉澱的核心機制。

### 10.5 訓練資料治理

```
Production Conversation
    ↓
PII Detection (Presidio / 自建)
    ↓
Masking / Synthesis
    ↓
Labeling (人類 + AI 輔助)
    ↓
Training Dataset (Versioned)
    ↓
Training Room
```

**鐵律**：未脫敏的客戶資料**不得**進入訓練室。

---

## 11. 安全與合規

### 11.1 七層安全模型

```
Layer 7  Compliance        ← GDPR / PDPA / HIPAA / SOC 2 / ISO 27001
Layer 6  Audit & Forensics ← 完整可追溯、可重播
Layer 5  Policy & RBAC     ← 業務規則、角色權限
Layer 4  Data Protection   ← PII Masking、Encryption at Rest/Transit
Layer 3  Tool Gateway      ← 工具閘道、Sandbox
Layer 2  Identity          ← 多租戶、多用戶、Service Account
Layer 1  Network           ← VPC、Private Endpoint、WAF
```

### 11.2 法遵框架對應

| 法規 / 標準 | AEOS 必備能力 |
| :--- | :--- |
| **GDPR** (EU) | Right to Access、Right to Erasure、Data Portability、DPO 報表 |
| **PDPA** (TW / SG) | 個資告知、目的限制、保存期限、刪除請求 |
| **HIPAA** (US 醫療) | PHI Encryption、Minimum Necessary、Audit Log |
| **SOC 2 Type II** | Logical Access Control、Change Management、Incident Response |
| **ISO 27001** | ISMS、Risk Assessment、Asset Inventory |
| **EU AI Act** | High-risk AI System Documentation、Human Oversight、Risk Management |
| **NIST AI RMF** | Map / Measure / Manage / Govern |

### 11.3 PII 治理

```
Customer Input
    ↓
PII Detector (entity recognition)
    ↓
Classification (PII / Sensitive PII / SPI)
    ↓
Decision Matrix:
    - Mask in Display
    - Mask in Memory
    - Mask in Logs
    - Encrypt at Rest
    - Tokenize
    - Reject
    ↓
Policy Enforcement
```

### 11.4 客戶資料生命週期

| 階段 | 治理動作 |
| :--- | :--- |
| Collect | 取得明確同意、記錄目的 |
| Store | 加密、租戶隔離 |
| Process | 最小必要原則、PII Masking |
| Memory | 預設不存個資；如需暫存，TTL ≤ Session |
| Audit | 寫入 Append-only Log |
| Delete | 收到刪除請求 → 30 天內完成 (含備份) |
| Retention | 依法規與商業需求設定 |

### 11.5 安全事件響應

```
事件偵測 (Drift / Anomaly / Manual Report)
    ↓
分級 (P0 / P1 / P2)
    ↓
P0 (高風險): 立即停用相關 Employee + Skill
P1 (中風險): 隔離 + 限流 + 告警
P2 (低風險): 紀錄 + 排查
    ↓
根因分析 (RCA)
    ↓
修復 → Sandbox 驗證 → 重新發布
    ↓
事後報告 + Skill / Policy 更新
```

### 11.6 「一鍵停用」原則

任何 AI 員工、任何 Skill 版本、任何 Tool，必須支援：

- **一鍵停用** (Soft Disable)：立即停止接受新流量
- **一鍵下線** (Hard Disable)：移除並通知運營
- **一鍵回滾** (Rollback)：回到上一個 Approved 版本

**理由**：當事故發生時，分秒必爭。**沒有 Kill Switch 的 Agent 系統不該上線**。

---

## 12. 監控評估體系 (AgentOps)

### 12.1 客服 / 業務 AI 員工的關鍵指標

| 類別 | 指標 | 目標 |
| :--- | :--- | :--- |
| **效率** | First Contact Resolution (FCR) | ≥ 70% |
| | Average Handling Time (AHT) | 因業務而定 |
| | 自動化率 (Automation Rate) | 依職位設目標 |
| **品質** | CSAT | ≥ 4.2 / 5 |
| | NPS | ≥ +30 |
| | 幻覺率 (Hallucination Rate) | ≤ 1% |
| | 不當承諾率 | ≤ 0.1% |
| | SOP 遵守率 | ≥ 99% |
| **風險** | PII 洩漏事件數 | 0 |
| | 高風險回答攔截率 | ≥ 99.9% |
| | Cross-tenant 違規數 | 0 |
| **服務** | 轉人工率 | 依職位設目標 |
| | SLA Breach Rate | ≤ 1% |
| | 工單重開率 | ≤ 5% |
| **成本** | LLM Token / Conversation | 持續優化 |
| | Tool Invocation / Conversation | 持續優化 |
| | $ / Resolved Ticket | 持續優化 |

### 12.2 漂移偵測 (Drift Detection)

| 漂移類型 | 監控信號 | 應對 |
| :--- | :--- | :--- |
| **Knowledge Drift** | RAG 引用品質下降、Citation 失效 | KB 重新索引、知識更新 |
| **Behavior Drift** | 同 Skill 版本、不同時段表現差異 | 排查上下游服務 |
| **Customer Drift** | 問題類型分布改變 | Skill 改版或新增 |
| **SOP Drift** | 政策遵守率下降 | Policy Engine 強化 |
| **Cost Drift** | Token / Conversation 上升 | Prompt 精簡 / 模型降階 |

### 12.3 評估迴路

```
Production Conversation
    ↓
Auto Scoring (LLM-as-Judge + Rule-based)
    ↓
Sample for Human Review (10% + 全部 P0/P1)
    ↓
Expert Score + Comments
    ↓
Aggregate to Dashboard
    ↓
Trigger Retraining if Drift Detected
    ↓
Training Room (回到 SkillOps Pipeline)
```

### 12.4 可觀測性必備

| 維度 | 必備 |
| :--- | :--- |
| Trace | 每次 Conversation 完整 Tool Call Chain |
| Log | Structured Log (Conversation ID 串接) |
| Metric | Prometheus / OpenTelemetry 標準 |
| Dashboard | Grafana / Datadog (依租戶切分) |
| Alert | PagerDuty / Opsgenie (按嚴重度) |
| Replay | 任意 Conversation 可完整回放 |

---

## 13. 多模型策略與成本治理

> **draft 缺漏的關鍵章節**。AI 員工平台的成本主要來自 LLM Token，沒有多模型策略會被供應商綁架且成本失控。

### 13.1 多模型抽象層

```
LLMProviderAdapter (統一介面)
    ├── OpenAI (GPT-4 / 4o / mini)
    ├── Anthropic (Claude Opus / Sonnet / Haiku)
    ├── Google (Gemini)
    ├── Local (Ollama / vLLM / LM Studio)
    └── Enterprise Gateway (內部 Model Gateway)
```

### 13.2 模型路由策略

| 任務類型 | 推薦模型層級 | 理由 |
| :--- | :--- | :--- |
| 意圖分類、簡單 FAQ | Haiku 級 / Local Small | 低成本高頻 |
| 一般客服對話 | Sonnet 級 | 平衡品質與成本 |
| 複雜推理、爭議處理 | Opus 級 | 高品質決策 |
| 訓練室博弈 | Opus 級 + 紅隊模型 | 探索與對抗 |
| 線下批次任務 | Local / Batch API | 最低成本 |

### 13.3 成本治理機制

| 機制 | 說明 |
| :--- | :--- |
| **Tenant Quota** | 每租戶設定月度 Token 上限 |
| **Employee Quota** | 每員工設定 Token 上限 |
| **Skill Cost Budget** | 每 Skill 設定單次調用成本上限 |
| **Cost Circuit Breaker** | 異常飆升自動降階模型 |
| **Cost Attribution** | 每 Conversation / Tool Call 完整成本歸屬 |
| **Prompt Cache** | 系統 Prompt + 角色 Profile 必快取 |
| **Distillation** | 高頻場景蒸餾到小模型 |

### 13.4 主權與資料殘留

| 場景 | 模型選擇 | 原因 |
| :--- | :--- | :--- |
| 高度機密 / 工廠內網 / 法遵嚴格 | Local Model + Private Gateway | 資料不出網域 |
| 一般 SaaS 客戶 | 公有 LLM (簽 DPA) | 平衡成本與能力 |
| 跨國客戶 | 區域化模型部署 | 資料主權 |
| 政府客戶 | Sovereign LLM / On-prem | 法規要求 |

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

## 15. 風險與緩解

### 15.1 技術風險矩陣

| 風險 | 機率 | 影響 | 緩解 |
| :--- | :--- | :--- | :--- |
| LLM API 中斷 | 中 | 高 | 多 Provider Fallback、Local Model 備援 |
| Prompt Injection 突破 | 高 | 高 | 紅隊持續、輸出過濾、Tool Gateway 把關 |
| Cross-tenant 資料外流 | 低 | 極高 | Policy 預設 deny、Tenant ID 強制注入、定期稽核 |
| Skill 版本退化 | 中 | 中 | Canary Release、自動回滾、Regression Test |
| Cost 失控 | 高 | 中 | Quota、Circuit Breaker、Cost Attribution |
| MCP Server 漏洞 | 中 | 高 | Sandbox、依賴掃描、版本鎖定 |
| 訓練資料污染 | 中 | 高 | Strict Labeling、Multi-source Cross-validation |
| 模型供應商單一依賴 | 高 | 高 | 多模型抽象層、Local Fallback |

### 15.2 業務風險矩陣

| 風險 | 緩解 |
| :--- | :--- |
| 客戶不信任 AI 員工 | 透明標示「AI 服務」、人工接手隨時可用、Audit Trail 可提供客戶 |
| 法務責任不清 | DPA / 服務契約明確責任邊界、強制 Human-in-the-loop |
| 監管不確定 | 模組化合規層、可關閉自我學習 |
| 員工抵觸 | AI 員工定位為「協作」非「取代」、提供 Trainer / Reviewer 新職位 |
| 競爭加劇 | 護城河在治理體系與企業整合，非單一 Bot |

### 15.3 倫理與責任歸屬框架

> **draft 缺漏的章節**。AI 員工出事時，誰負責？這是企業無法迴避的問題。

| 角色 | 責任 |
| :--- | :--- |
| **Tenant (客戶企業)** | 業務決策、Policy 設定、Skill 採用、最終回應 |
| **Skill Owner** | Skill 內容正確性、回歸測試、版本決策 |
| **Platform Provider (你)** | Runtime 穩定性、Tool Gateway 安全、Audit 完整 |
| **Tool Provider** | MCP Server 邏輯正確性、SLA |
| **LLM Provider** | 模型輸出符合契約 |

**契約建議**：DPA + SLA + Liability Cap + Indemnification Clauses 必須涵蓋上述五方責任。

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

# Part II — 導入方法論與服務交付

> **Part I (§1~§16)** 闡述「AEOS 是什麼、為什麼這樣設計」的產品與架構觀點。
> **Part II (§17~§21)** 回答「客戶如何導入、平台方如何交付」的服務與商業模式觀點。

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

---

# Part III — 戰略與商業視角

> **Part I (§1~§16)** 闡述 AEOS 的產品與架構觀點。
> **Part II (§17~§21)** 闡述服務交付與商業包裝。
> **Part III (§22~§25)** 闡述戰略定位、護城河、自研 vs 外包決策、商業模式與市場切入。
>
> 本部分目標讀者為創辦人、投資人、董事會與商業決策層。

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

### 22.8 大廠下沉威脅評估與 AI 藍領 Wedge 戰略

> 2026 年 Google Cloud Next、Microsoft Ignite、Salesforce Dreamforce 等大會集中發布企業 AI Agent Platform。AEOS 必須明確回應：「大廠都做了，你還剩什麼？」本節是定錨答案。

#### 22.8.1 大廠 AI Agent 平台盤點

| 大廠 | 旗艦產品 | 核心能力 | 1800 億級投入 |
| :--- | :--- | :--- | :--- |
| **Google** | Gemini Enterprise + Agent Studio | 智能體任務控制中心 + 自然語言構建 agent | 1800 億美元（Cloud Next '26） |
| **Microsoft** | Copilot Studio + Power Platform | Office / Teams 深度整合 + 低代碼 agent | Azure AI 數百億美元 |
| **Salesforce** | Agentforce + Data Cloud | CRM 內建 AI agent + 客服 / 銷售 workflow | 數十億美元 |
| **AWS** | Bedrock Agents + Q Business | 多模型 agent + 企業搜尋 | Trainium / Q 系列重金投入 |
| **Anthropic / OpenAI** | Claude / GPT + Agent SDK | 模型直接出 agent，繞過中間層 | 模型投入即護城河 |

**盤點結論**：
- Layer 1 (LLM) 與 Layer 2 (Agent Runtime) 已被大廠完全佔領
- Layer 3 (Governance) 通用部分（如 Gemini Enterprise）也被入侵
- AEOS 自第一天起就**不能**在「通用 AI 員工平台」與大廠正面對撞

#### 22.8.2 大廠的結構性盲區

大廠並非無懈可擊。其結構決定了下列五個無法服務的市場：

| 大廠盲區 | 結構性原因 | AEOS 切入空間 |
| :--- | :--- | :--- |
| **Knowledge Worker 以外的場景** | Workspace / Office 365 / CRM 都服務坐辦公室的白領 | **AI 藍領場景**（現場、行動、SOP、班表） |
| **多雲 / 多 LLM 中立** | 大廠賣自家雲與自家模型 | **跨雲、跨 LLM 治理層** |
| **垂直產業 know-how** | 水平平台公司，不深耕單一產業 | **特定垂直深度**（餐飲連鎖、長照、零售現場） |
| **中小企業可負擔** | Enterprise 套餐起跳，最低用戶數高 | **可負擔方案**（Phase 1 定價 10~50 萬 NTD） |
| **顧問服務 + 方法論** | 大廠不做 SOW 級服務交付 | **Concierge 7 日導入包 + AWM 認證** |

#### 22.8.3 AI 藍領 Wedge — 對的市場、對的時機

> **AEOS 的 Wedge 從「AI 員工平台」收斂為「AI 藍領員工平台」。**
>
> 這個收斂不是縮小市場，而是**避開大廠強項、進入大廠盲區、建立差異化身份**。

#### 「藍領」的精準定義

AEOS 服務的「AI 藍領」涵蓋下列工作型態：

```
AI 藍領 (Frontline AI Worker) =
  服務於現場 / 一線 / 流動性高 / SOP 密集 / 大量重複決策的工作場景
```

| 產業 | 藍領職位範例 | AI 藍領可承擔 |
| :--- | :--- | :--- |
| 服務業 | 客服一線、餐廳點餐、旅館前台、票務 | 接客、查詢、分流、SOP 引導 |
| 零售 | 銷售一線、店員、收銀 | 商品推薦、退換貨、促銷說明 |
| 物流 | 倉儲揀貨、配送調度、客訴處理 | 揀貨指引、路徑優化、配送通知 |
| 製造 | 維修工、品檢、設備巡檢 | SOP 引導、故障診斷、報修記錄 |
| 醫療 | 護理助理、藥局櫃檯、健檢引導 | 衛教問答、用藥提醒、流程引導 |
| 營造 | 工地監工、安檢、進度回報 | 安全檢核、進度填報、SOP 提醒 |
| 連鎖 | 加盟店主、督導、教育訓練 | SOP 培訓、開店檢核、總部問答 |
| 政府 | 服務台、櫃檯、市民熱線 | 表單引導、規則查詢、案件分流 |

#### 為何「AI 藍領」而非「AI 助理」

| 維度 | 「AI 助理 / Copilot」 (大廠戰場) | **「AI 藍領」** (AEOS 戰場) |
| :--- | :--- | :--- |
| 服務對象 | Knowledge Worker（坐辦公桌） | Frontline Worker（在現場 / 行動中） |
| 互動模式 | Chat 介面、Office 工具 | LINE / WhatsApp / 行動 App / 對講機 |
| 工作環境 | 文件、Email、Meeting | SOP、班表、設備、客戶現場 |
| 風險型態 | 誤譯、保密 | 客訴、安規、合規、即時錯誤 |
| 採購決策者 | IT 主管 / CIO | 營運主管 / COO / 店面總監 |
| 預算邏輯 | 軟體 IT 預算 | 人力與培訓預算（規模更大） |
| 大廠覆蓋度 | **高**（Workspace / Office / Salesforce） | **低**（無原生方案） |
| 大廠進入意願 | 高 | **低**（毛利低、客戶分散、不性感） |

**戰略推論**：
- 「AI 助理」市場 = 大廠主場，AEOS 進去是送死
- **「AI 藍領」市場 = 大廠看不上、客戶痛點極強、AEOS 可建立絕對主場**

#### 22.8.4 AI 藍領市場的痛點與商業價值

##### 客戶側痛點（普遍存在於所有藍領產業）

```
□ 缺工嚴重（少子化 + 服務業流失）
□ 流動率高（年流動 > 50% 常見）
□ 訓練成本高（每位新人 1~3 個月才上手）
□ 品質參差（依賴個人經驗）
□ SLA 不穩（高峰時段崩潰）
□ 24/7 覆蓋困難（夜班、假日）
□ 多語言需求（外籍勞工、多國客戶）
□ 合規責任壓力（醫療 / 金融 / 食安）
```

##### AEOS 對應價值

```
✓ 招募、訓練、上線一位 AI 藍領 = 7 天 vs 真人 3 個月
✓ 24/7 不停班，SLA 穩定
✓ 流動率 = 0 (AI 不離職)
✓ 多語言原生支援
✓ Skill 升級即時生效（新政策、新商品）
✓ Audit Log 滿足合規稽核
✓ 「AI 藍領」概念極具象，老闆秒懂
```

#### 22.8.5 對銷售與募資的話術更新

| 場合 | 話術 |
| :--- | :--- |
| 對 VC | 「我們不打 Google / Microsoft 的 white-collar Copilot 戰場。我們做大廠看不上的 AI Blue-collar — 全球 30 億藍領工作者的 AI 替代與輔助平台。」 |
| 對企業 CEO | 「您的客服 / 維修 / 銷售一線缺工嗎？我們 7 天讓您招募一位 AI 員工，永不離職、24/7、合規可稽。」 |
| 對 COO / 營運總監 | 「您的人力預算每年 X 億。AEOS 讓您用 1/10 成本擴充 10 倍工時容量。」 |
| 對工程界 | 「Knowledge Worker 的 AI 是 Copilot；Frontline Worker 的 AI 是 AEOS。前者是輔助，後者是替代。」 |

#### 22.8.6 必須堅守的新紅線

延伸 §22.6 紅線，新增藍領 wedge 的紅線：

| 新紅線 | 違反後果 |
| :--- | :--- |
| 不可進 white-collar Copilot 市場 | 必死 — Google / Microsoft 主場 |
| 不可只做客服（必須涵蓋多藍領場景） | 限制天花板 — 客服 SaaS 是 Zendesk 主場 |
| 不可放棄行動 / LINE / WhatsApp 入口 | 必死 — 藍領不在 Web 與 Slack |
| 不可忽略多語言 / 在地化 | 必死 — 藍領場景跨國語言複雜 |

→ 任一決策若違反藍領 wedge，需重新對齊 §22.8.3。

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

---

# Part IV — 投資人視角與十年戰略

> **Part I (§1~§16)** 闡述產品與架構觀點。
> **Part II (§17~§21)** 闡述服務交付與商業包裝。
> **Part III (§22~§25)** 闡述戰略定位、護城河、自研 vs 外包、商業模式。
> **Part IV (§26~§30)** 從投資人視角檢驗：十年護城河是否成立、系統因果迴路如何運作、核心假設如何驗證、未來十年如何演化。
>
> 本部分目標讀者為投資人、董事會、創辦人，以及任何需評估「此公司能否走十年」的決策者。

---

## 26. 投資人視角總判斷

### 26.1 十年護城河總評

| 判斷項 | 結論 |
| :--- | :--- |
| **短期商業切入** | AI 客服是合理 wedge — 痛點明確、ROI 易說、資料易取得 |
| **中期護城河** | 不在模型 / MCP / UI；而在 Onboarding 自動化、知識結構化、SkillOps、Evaluation、Governance |
| **十年穩固性** | **中高，但有條件** — 若停在客服工具會被大廠吃掉；若做成 AI 員工生命週期平台則護城河可深 |
| **真正公司定位** | AI Employee Lifecycle / AI Workforce Governance Platform |
| **核心戰略** | Narrow wedge 進場，Broad architecture 擴張 |
| **最大風險** | 過早平台化、變接案公司、被模型進步稀釋價值、企業整合成本過高 |

### 26.2 機會為何在「現在」成立

#### 三股市場驅動力同時匯聚

| 驅動力 | 訊號 | 對 AEOS 的意義 |
| :--- | :--- | :--- |
| **Agent 從聊天走向工作流** | Sequoia 2025 AI 50 觀察 AI agents 從 prompt-response 工具轉向處理真實 enterprise workflows | 客服場景已從「會聊天」進化到「會完成任務」 |
| **企業 AI 採購正式化** | a16z 2026 分析顯示 Fortune 500 / Global 2000 已成為 AI startups 正式付費客戶（top-down contract、pilot 轉正） | 企業願意付費，但只買「能落地」的 AI |
| **企業 AI 失敗率仍高** | Orgvue 2026 調查指出 78% 組織有 AI 專案失敗或停在 pilot；原因多為缺乏 roadmap、角色設計、組織導入方式 | 「導入方法論」本身即產品價值 |

#### 推論

> **企業不缺 AI 模型，企業缺的是「如何把 AI 安全放進工作流程」的方法論與治理體系。** 這正是 AEOS 的入口。

### 26.3 5W1H 問題界定

| 維度 | 回答 |
| :--- | :--- |
| **Who** | 有客服 / 知識 / 流程 / 系統整合需求的企業；第一波切入：中小企業、電商、教育、B2B SaaS、連鎖服務 |
| **What** | AI 員工平台 — 訓練、驗收、上線、監控、改版 AI 客服 / 助理 |
| **When** | 現在到未來 3 年是導入窗口期；未來 10 年考驗能否從客服 wedge 擴張為 AI workforce governance layer |
| **Where** | 客服入口、LINE / Web / CRM / ERP / SAP / 進銷存 / 會計 / KB / 工單系統 |
| **Why** | 企業想用 AI 降本，但怕亂答、亂用工具、資料外洩、難驗收、難維運 |
| **How** | 導入精靈 + 訓練室 + SkillOps + Knowledge System + Policy Engine + Tool Gateway + Evaluation System，建立 AI 員工生命週期 |

### 26.4 市場事實與推論

| 市場事實 | 對 AEOS 的戰略推論 |
| :--- | :--- |
| AI agents 正在從聊天轉向工作流完成 | 不能只做客服問答，要做流程型 AI 員工 |
| 企業 AI 採用增加，但 pilot 卡關率高 | **導入、驗收、治理本身就是產品價值** |
| 模型供應商競爭波動大（Anthropic 2026 反超 OpenAI） | 不要把護城河壓在單一 LLM |
| MCP 成為連接 LLM 與工具的標準之一 | MCP 必須支援，但**不是最終護城河** |
| MCP 標準化同時擴大攻擊面 | Tool Gateway、審計、權限、沙盒才是企業價值 |

### 26.5 索克拉底式三大提問

#### Q1：這家公司到底賣什麼？

| 表面定位 | 真正應賣 |
| :--- | :--- |
| AI 客服 | AI 員工導入、訓練、驗收、上線與持續治理 |
| AI Agent | AI Employee Lifecycle Management |
| 企業客服自動化 | Enterprise AI Workforce Governance |

差異本質：**功能（Function） vs 系統（System）**。

#### Q2：客戶真正怕什麼？

不是怕 AI 不聰明，而是怕：

```
答錯 / 亂承諾 / 洩漏個資 / 誤用工具 / 接錯系統
難以驗收 / 沒人負責 / 無法追蹤
內部專家沒時間訓練 / 導入成本太高
```

**產品價值核心**不是「更會回答」，而是 **更可控 / 更可驗收 / 更可追溯 / 更可迭代 / 更低導入負擔**。

#### Q3：十年後模型變強，AEOS 還剩什麼？

| 若價值停在「Prompt / RAG / Wrapper」 | 十年後極危險 |
| :--- | :--- |
| **若價值是「企業 know-how 轉成 AI 員工能力包 + 驗收監控標準 + Skill 版本治理 + 對話回收訓練」** | **模型越強反而越有價值** |

---

## 27. 系統因果迴路與飛輪設計

### 27.1 系統四層邊界

```
A. AI Employee Layer    — AI 客服 / 售前 / 維修 / IT / 採購助理
B. Governance Layer     — Role / Skill / Policy / Permission / Audit / Evaluation
C. Integration Layer    — MCP / API / Webhook / Adapter / Tool Gateway
D. Learning Loop Layer  — Training Room / Expert Review / Conversation Scoring / Drift / SkillOps
```

**護城河重心**：B + D（治理層 + 學習閉環）。A 是 wedge，C 是必要條件，B + D 是長期壁壘。

### 27.2 三條正向迴路 (Reinforcing Loops)

#### R1 — 導入資料飛輪

```
更多客戶導入
  → 更多客服資料 / FAQ / SOP / 例外案例
  → 更好的知識卡抽取與測試題生成
  → 更快導入下一個客戶
  → 更高成交率
  → 更多客戶導入
```

**前提條件**：每次導入必須沉澱為模板（呼應 §24.7 服務公司脫離指標），否則此迴路不會啟動。

#### R2 — 評估飛輪 (最關鍵的護城河)

```
更多線上對話
  → 更多錯誤案例與高風險案例
  → 更好的 Evaluation Set
  → 更準的 Skill 改版
  → 更穩定的 AI 員工
  → 客戶更敢擴大使用
  → 更多線上對話
```

**戰略意義**：大模型供應商不擁有客戶的垂直場景錯誤資料；這是 AEOS 對抗模型商品化的根本武器。

#### R3 — 信任飛輪

```
更好的治理 / 審計 / 權限
  → 企業更敢上線
  → 更多企業流程接入
  → 平台變得更不可替代
  → 續約與擴充增加
  → 投入更多治理能力
```

**企業市場本質**：信任本身就是 moat。Audit / Compliance / Kill Switch 是這條迴路的燃料。

### 27.3 兩條負向迴路 (Balancing Loops)

#### B1 — 複雜度反噬迴路

```
接更多企業系統
  → 更多客製需求
  → 維運複雜度上升
  → 交付速度下降
  → 毛利下降
  → 團隊被專案拖住
  → 無法投入下一輪客戶
```

**緩解設計**：
- Adapter 可客製，**Tool Contract 必須標準化**（呼應 §23.3）
- 每次客製必沉澱為模板（呼應 §24.7）
- 客製 Adapter 比例 ≤ 30%（呼應 §24.7 度量指標）

#### B2 — 模型商品化壓力

```
模型越強
  → 基礎問答越容易被複製
  → 一般 AI 客服價值下降
  → 客戶要求更深流程整合
  → 只有治理與 workflow 能留下價值
```

**緩解設計**：公司不能停在「會回答問題」。必須往 §24.6 Lifecycle Management 與 §29 三 Compiler 移動。

### 27.4 五迴路綜合系統圖

```
              ┌──→ R1 導入飛輪 ──┐
              │                    │
              ↓                    ↑
         AEOS 平台 ←───────────────┘
              │
   ┌──────────┼──────────┐
   ↓          ↓          ↓
 R2 評估    R3 信任    B1 複雜度
 飛輪       飛輪       反噬
   │          │          │
   └──────────┼──────────┘
              ↑
              │
              B2 模型商品化壓力 (外部驅力)
```

**戰略原則**：
- 設計上**最大化 R1 / R2 / R3** — 透過 Onboarding Layer / Evaluation / Governance
- 設計上**最小化 B1** — 透過 Adapter Contract 標準化
- 設計上**抵禦 B2** — 透過 Skill Lifecycle 抽象超越單一模型

---

## 28. 核心假設與驗證指標

### 28.1 假設驗證的戰略意義

> **新創公司不是執行已知計畫，而是一連串被驗證或被推翻的假設。**

AEOS 的商業模型可拆解為四個核心假設。每個假設都需在 Pre-seed / Seed 階段透過 Paid Pilot 驗證。

### 28.2 假設 H1 — 企業願意為「降低導入成本」付費

#### 假設陳述

```
若系統能自動整理網站、FAQ、SOP、客服紀錄，
企業願意付導入費取得「省下整理工時 + 第一版可上線 AI 員工」。
```

#### 驗證方式

5~10 家企業 Paid Pilot（對應 §17 Phase 0~3）。

#### 驗證指標

| 指標 | 建議門檻 |
| :--- | ---: |
| 從資料匯入到第一版 AI 員工 | ≤ 7 天 |
| 客戶專家投入時間 | ≤ 3 小時 |
| 自動抽取 FAQ 可用率 | ≥ 70% |
| 客戶願意付導入費比例 | ≥ 50% pilot |

### 28.3 假設 H2 — Evaluation System 形成留存與擴張

#### 假設陳述

```
企業不只需要 AI 回答，也需要知道 AI 回答得好不好。
持續性的監控 dashboard 將驅動續約、擴員工席次、擴職位類別。
```

#### 驗證方式

提供 Evaluation Dashboard（含正確率、轉人工率、高風險攔截率、幻覺案例、SOP 違規）。

#### 驗證指標

| 指標 | 建議門檻 |
| :--- | ---: |
| 客戶每週查看 Dashboard | ≥ 1 次 |
| 客戶主動要求新增評分項目 | 有 |
| 評估結果能推動 Skill 改版 | 有 |
| Skill 改版後指標改善 | ≥ 10~20% |

### 28.4 假設 H3 — SkillOps 比單純 RAG 更有壁壘

#### 假設陳述

```
企業需要可版本化、可審核、可回滾的 AI 能力包（Skill），
而非僅是 RAG + Prompt 的拼裝。
```

#### 驗證方式

同一企業部署 A/B 對比：
- A 組：純 RAG
- B 組：RAG + Skill + Policy + Evaluation

#### 驗證指標

| 指標 | 比較預期 |
| :--- | :--- |
| 高風險問題處理 | B 明顯優於 A |
| 回覆一致性 | B 明顯優於 A |
| 可驗收性 | B 明顯優於 A |
| 客戶信任感 | B 明顯優於 A |

### 28.5 假設 H4 — MCP / Adapter 是必要能力，但非主護城河

#### 假設陳述

```
企業會要求串接 CRM / ERP / 進銷存，
但不會因「你支援 MCP」就買單。
```

#### 驗證方式

銷售過程觀察客戶實際在意的議題（不引導）。

#### 預期結果

客戶會說：

```
「可以接系統很好，
但我更在意安全、權限、上線風險、AI 答錯怎麼辦。」
```

#### 戰略推論

MCP 是**必要條件 (table stakes)**，不是**差異化本體 (differentiator)**。產品行銷重點不應放在「我們支援 MCP」，而應放在「我們治理 MCP」。

### 28.6 SWOT 分析

| 類別 | 內容 |
| :--- | :--- |
| **Strengths 優勢** | 把 AI 客服升級為 AI 員工生命週期；切入企業最痛的導入、驗收、治理；可從客服擴張到其他職位 |
| **Weaknesses 劣勢** | 初期容易變服務公司；企業整合成本高；資料品質依賴客戶；產品範圍易膨脹 |
| **Opportunities 機會** | 企業 AI adoption 加速；Agent 從 chat 轉 workflow；企業需治理平台；MCP 生態成熟 |
| **Threats 威脅** | Salesforce / Zendesk / Intercom / Microsoft / ServiceNow 大廠下沉；模型供應商直接做 agent；開源 framework 進步；MCP 安全事件 |

### 28.7 黃帽 — 為什麼值得做

> **賣的不是「省人力」，而是「企業 AI 勞動力的可信任上線方式」。**

企業一旦開始部署 AI 員工，將遇到下列無法因模型變強而消失的問題：

```
誰訓練它？
誰批准它？
它能用什麼工具？
它犯錯誰負責？
怎麼知道它變差？
怎麼讓它改版？
怎麼讓不同部門的 AI 員工不互相污染？
```

這些問題本質上是**勞動力管理問題**，AEOS 是這個新類別的早期定義者。

### 28.8 黑帽 — 為什麼可能失敗

| # | 失敗原因 | 警訊 | 對策 |
| :--- | :--- | :--- | :--- |
| 1 | 變成接案公司 | 客製比例上升、Skill 重用率下降 | §24.7 度量、§23.3 Adapter Contract |
| 2 | 客戶覺得導入仍太麻煩 | NPS 低、Pilot 不轉正 | §18 Onboarding Automation Layer 強化 |
| 3 | 大廠把 AI 內建至既有客服系統 | Salesforce / Zendesk Logo 流失 | §22.1 定位為「跨系統治理層」 |
| 4 | 只做 MCP / Agent runtime | 被 Open source 追上 | 護城河重心轉向 §29 三 Compiler |
| 5 | Evaluation 做不出來 | 客戶 Dashboard 使用率低 | Phase 1 即投入；不可延後 |

### 28.9 假設 H5 — AI 藍領市場可承載 100~500 客戶規模

> 此假設在 Google Cloud Next '26 之後新增。驗證大廠下沉是否會吃掉 AEOS 全部市場，或仍留有可生存的藍領 wedge。

#### 假設陳述

```
即使 Google Gemini Enterprise / Microsoft Copilot Studio / Salesforce Agentforce
等大廠完整提供企業 AI Agent Platform，
仍有 30~40% 的企業需求因下列四項結構性原因無法被大廠覆蓋：

  1. 服務對象是 Frontline Worker（藍領），非 Knowledge Worker（白領）
  2. 需多雲 / 多 LLM 中立，不被單一供應商鎖定
  3. 需垂直產業深度（餐飲連鎖 / 長照 / 零售現場 / 工地）
  4. 中小企業預算買不起大廠 Enterprise 套餐

AEOS 鎖定此市場可達 100~500 個客戶規模。
```

#### 驗證方式

訪談 20~30 家具藍領場景之企業（餐飲、零售、物流、長照、製造業現場），詢問：

```
Q1：你會選 Google Gemini Enterprise / Microsoft Copilot Studio 嗎？為什麼會 / 為什麼不會？
Q2：你的 AI 員工會工作在 Web / Slack / Teams，還是 LINE / WhatsApp / 行動 App / 對講機？
Q3：你的客戶或員工主要使用 Workspace / Office 365 / CRM 嗎？
Q4：你的年度 IT 預算 vs 人力預算比例為何？
Q5：你願意為「7 天部署、永不離職、24/7 在線」的 AI 藍領付多少？
```

#### 驗證指標

| 指標 | 建議門檻 |
| :--- | ---: |
| 訪談企業數 | ≥ 20 家 |
| 「不會選大廠」比例（H5 成立關鍵） | ≥ 30% |
| 「需要藍領場景 / 行動入口」比例 | ≥ 60% |
| 願意付費（≥ NTD 10 萬月費）比例 | ≥ 25% |
| 至少取得 3 個 Paid Pilot 簽約 | 完成 |

#### 假設失效時的退路

若驗證失敗（< 20% 企業願意選 AEOS），需採下列其一退路：

| 退路 | 說明 |
| :--- | :--- |
| A | 上 Google Cloud Marketplace 作為「藍領垂直方案」，與 Google 共生 |
| B | 收斂到單一最深垂直（例：只做長照 AI、只做餐飲連鎖 AI） |
| C | 轉型為「AEOS Skill 模板供應商」，賣 Skill Pack 給大廠平台 |

#### 戰略意涵

H5 假設的成立與否，決定 AEOS 公司估值上限：

| H5 結果 | 公司潛力 |
| :--- | :--- |
| ✅ 成立（30% 以上不選大廠） | 可達 100~500 客戶 + ARR 5,000~50,000 萬 NTD |
| ⚠️ 部分成立（10~30%） | 需走垂直深度路線，公司天花板較低 |
| ❌ 不成立（< 10%） | 立即執行退路 A 或 C |

---

## 29. 護城河三層分級與三個 Compiler

### 29.1 弱護城河（不可作為核心倚賴）

| 項目 | 為何弱 |
| :--- | :--- |
| Chat UI | 容易複製 |
| Prompt | 容易複製 |
| RAG | 越來越商品化 |
| MCP Host | 將成為標準能力 |
| 模型選擇 | 供應商波動大 (Anthropic 反超 OpenAI 即為例) |
| 單一客服場景 | 大廠容易內建 |

**戰略意涵**：產品行銷、Pitch Deck、技術部落格中**不可**將上述項目列為核心護城河。

### 29.2 中等護城河（有條件可強化）

| 項目 | 強化條件 |
| :--- | :--- |
| 客戶知識庫 | 純向量庫弱；含版本 / 來源 / 審核 / 缺漏偵測即強 |
| Tool Adapter | 單一 Adapter 弱；標準化 Tool Contract 強 |
| 產業模板 | 必須持續累積、跨客戶可重用 |
| 導入流程 | 須產品化為 Onboarding Layer (§18) |
| 客戶資料 | 須合法合規取得，且轉化為 Evaluation Set 與 Skill 模板 |

### 29.3 強護城河（公司長期生存核心）

| 項目 | 為何強 |
| :--- | :--- |
| **Evaluation Dataset** | 真實錯誤、高風險、SOP 違規案例難從公開資料取得 |
| **SkillOps System** | 把 AI 能力版本化、測試化、審核化 |
| **Governance Harness** | 企業信任與合規核心 |
| **Onboarding 自動化** | 直接降低成交阻力 |
| **工作流綁定** | 接入 CRM / ERP / 工單後切換成本上升 |
| **跨客戶抽象能力** | 每次專案沉澱為通用模板，才有規模化 |

### 29.4 商業壁壘的核心句

> **AEOS 的長期商業壁壘可濃縮為一句：
> 把企業混亂知識與流程，轉化為可驗收、可監控、可改版的 AI 員工能力。**

此句拆解為三個 Compiler。

### 29.5 Compiler 1 — Data-to-Knowledge

```
網站 / PDF / SOP / 客服紀錄
    ↓
[Data-to-Knowledge Compiler]
    ↓
FAQ Card / Policy Card / Product Card / Risk Card / Procedure Card
```

**護城河類型**：導入速度。
**對應章節**：§6.3 三分類 / §18.5 自動整理 / §18.11.1 知識卡結構。

**為何難複製**：
- 跨產業文件結構庫
- 缺漏偵測規則
- Source Citation 完整性
- 與 §6.3 三分類的對應正確率

### 29.6 Compiler 2 — Knowledge-to-Skill

```
Knowledge Cards
    ↓
[Knowledge-to-Skill Compiler]
    ↓
Skill Version → Role Profile → AI Employee Capability
```

**護城河類型**：能力治理。
**對應章節**：§6.1 Skill Aggregate / §9 SkillOps / §21.2 Employee Manifest。

**為何難複製**：
- 跨客戶 Skill 模板庫
- 風險等級 Heuristic
- Test Case 自動生成規則
- Approval Workflow 業界經驗

### 29.7 Compiler 3 — Conversation-to-Improvement

```
線上對話
    ↓
[Conversation-to-Improvement Compiler]
    ↓
評分 → 錯誤分類 → 測試題 → Skill 改版 → 新版本上線
```

**護城河類型**：長期資料飛輪。
**對應章節**：§9 SkillOps Pipeline / §10.3 訓練室 / §12 AgentOps。

**為何難複製**：
- 真實線上錯誤案例庫
- 產業級 Failure Taxonomy
- LLM-as-Judge 提示工程沉澱
- Drift Detection Rule

### 29.8 三 Compiler 與護城河迴路的對應

| Compiler | 主要驅動的迴路 (§27) | 主要強化的護城河層 (§22.5) |
| :--- | :--- | :--- |
| Compiler 1 | R1 導入飛輪 | Layer 1~2 (服務 → 資料) |
| Compiler 2 | R2 評估飛輪 + R3 信任飛輪 | Layer 3 (流程) |
| Compiler 3 | R2 評估飛輪 | Layer 4 (平台) |

**戰略推論**：三 Compiler 同時運作才能完成「服務 → 資料 → 流程 → 平台」的四層遞進。任一缺失即無法十年穩固。

### 29.9 護城河檢核問題

任一時刻檢視 AEOS 是否仍走在十年護城河路徑上：

```
□ Compiler 1 — 第 N 個客戶導入時間是否持續下降？
□ Compiler 2 — Skill 模板重用率是否持續上升？
□ Compiler 3 — 線上 Evaluation Dataset 是否持續擴充？
□ Adapter 客製比例是否 ≤ 30%？
□ Skill / Knowledge / Policy / Evaluation 是否累積在平台？
□ 是否能對 VC 講述「模型升級反而強化我們」的故事？
```

任一答案為「否」即為護城河鬆動的早期警訊。

### 29.10 AEOS vs Loops / Agent Runtime 類工具的競合定位

> 紅杉資本 / Boris (2026) 提到 Loops 等工具將成為「未來 SaaS 公司的標配」。AEOS 與此類工具是**不同層次**而非競爭關係。釐清此定位對銷售與募資至關重要。

#### 29.10.1 三層分工模型

```
┌────────────────────────────────────────┐
│ Layer 3 — Governance & Lifecycle (AEOS) │
│ 訓練 / 驗收 / 監控 / Skill 版控          │
│ 跨客戶 Benchmark / 數據飛輪              │
└─────────────────┬──────────────────────┘
                  ↓ 依賴
┌────────────────────────────────────────┐
│ Layer 2 — Agent Runtime (Loops 類)      │
│ Agent Loop / Tool Calling / Memory      │
│ 多 Agent 編排 / Workflow 動態生成        │
└─────────────────┬──────────────────────┘
                  ↓ 依賴
┌────────────────────────────────────────┐
│ Layer 1 — LLM Provider                  │
│ OpenAI / Anthropic / Google / Local     │
└────────────────────────────────────────┘
```

#### 29.10.2 三層工具的職責邊界

| 層級 | 職責 | 護城河類型 | 商品化風險 |
| :--- | :--- | :--- | :--- |
| Layer 1 — LLM | 產生 token、推理 | 規模 / 演算法 | 高（多供應商競爭） |
| Layer 2 — Loops 類 Agent Runtime | Agent loop、Tool calling、多 Agent 編排 | 開發者體驗 | 中高（Open source 追趕快） |
| **Layer 3 — AEOS** | 治理、評估、Skill 版控、跨客戶數據飛輪 | **企業信任 + 數據資產** | **低**（需長期累積） |

#### 29.10.3 為何 AEOS 不會與 Loops 直接競爭

| 維度 | Loops (Layer 2) | AEOS (Layer 3) |
| :--- | :--- | :--- |
| 目標客戶 | 開發者、SaaS 公司技術團隊 | 企業客戶（含非技術部門） |
| 賣點 | 「讓你快速建出 Agent」 | 「讓你安全管理 AI 員工」 |
| 計價單位 | API 用量 / Workflow 數 | 員工席次 / 治理服務 |
| 累積資產 | Workflow 模板 | 跨客戶 Skill / Evaluation Benchmark |
| 客戶心智 | 「工程工具」 | 「勞動力管理體系」 |

**結論**：Loops 是 AEOS 的**潛在底層元件**，不是競爭對手。AEOS 可選擇：
- (a) 自建 Layer 2（控制度高）
- (b) 採用 Loops 等成熟方案作為 Layer 2（呼應 §23 自研 vs 外包）

#### 29.10.4 對銷售與募資的標準回應

```
Q: 「你們跟 Loops / LangGraph / CrewAI 有什麼差別？」

A: 我們不是同一層工具。
   Loops 解決『如何快速建一個 Agent』；
   AEOS 解決『如何安全把 1000 個 AI 員工放進企業流程並治理它們』。
   Loops 是工程工具，AEOS 是勞動力管理體系。
   未來 AEOS 內部可能採用 Loops 作為 Agent Runtime，但治理層、Skill 版控、
   跨客戶 Benchmark、Evaluation Dataset 是 AEOS 獨有的護城河。
```

#### 29.10.5 戰略推論

此三層分工模型同時驗證三件事：

1. **AEOS 不在「會被模型 / Agent Runtime 進步吃掉」的危險區** — 因為定位高一層
2. **AEOS 不需與 Loops 競爭 Agent 編排能力** — 可採購或自建均可
3. **AEOS 真正的對手不是 Loops，而是「Salesforce 內建 AI / Zendesk AI 助理」等大廠下沉**（呼應 §28.6 SWOT Threats）

### 29.11 三層分工的更新 — Layer 3 必須再細分

> 2026 年 Google Cloud Next 之後，§29.10 的三層分工模型已不足。Layer 3 (Governance) 通用部分已被 Gemini Enterprise 入侵。AEOS 必須在 Layer 3 內進一步切細，明確戰場。

#### 29.11.1 Layer 3 三細分模型

```
Layer 3a — 通用 AI 員工治理層 (大廠戰場)
  ├── Gemini Enterprise (Google)
  ├── Copilot Studio (Microsoft)
  ├── Agentforce (Salesforce)
  └── Q Business (AWS)

Layer 3b — 垂直藍領 AI 員工治理層 (AEOS 主戰場)
  ├── 餐飲連鎖 AI 員工
  ├── 長照 / 醫療現場 AI 員工
  ├── 零售 / 倉儲 AI 員工
  ├── 工地 / 製造現場 AI 員工
  └── 客服 / 票務 AI 員工

Layer 3c — 跨雲跨模型中立治理層 (AEOS 第二戰場)
  ├── 多雲 (Azure + AWS + GCP) 客戶
  ├── 多模型 (Claude + GPT + Gemini + Local) 客戶
  ├── 私有部署 / 資料主權客戶
  └── 受監管產業 (金融、政府、醫療)
```

#### 29.11.2 三細分的競爭分析

| Layer | 戰場主導者 | AEOS 立場 | 戰略動作 |
| :--- | :--- | :--- | :--- |
| **Layer 3a** | Google / Microsoft / Salesforce | **不進入** | 上 Marketplace 共生 (退路 A) |
| **Layer 3b** | 無主導者（市場碎片化） | **主戰場** | 垂直深度 + 跨產業可重用 Skill 庫 |
| **Layer 3c** | 部分被 Cloudflare AI / HuggingFace 等覆蓋 | **第二戰場** | 強化中立性與資料主權訴求 |

#### 29.11.3 為何大廠不會輕易進入 Layer 3b

| 原因 | 說明 |
| :--- | :--- |
| 客戶分散 | 100 家連鎖店比 1 家銀行難服務 10 倍 |
| 毛利低 | 藍領單席費低，無法撐起大廠 Enterprise 銷售團隊 |
| 不性感 | 高層 Roadmap 不會把「為餐飲店員做 AI」放優先 |
| Workspace 不在現場 | 大廠主力是辦公室生產力，不是現場行動 |
| 多語言 / 在地化 | 藍領場景需深度本地化，全球大廠效率低 |

#### 29.11.4 AEOS 在 Layer 3b + 3c 的具體護城河

| 護城河來源 | Layer 3b (垂直藍領) | Layer 3c (中立治理) |
| :--- | :--- | :--- |
| **數據** | 跨產業藍領 Failure Taxonomy + 風險題庫 | 跨雲 / 跨模型行為 Benchmark |
| **Skill 模板** | 8 大藍領產業 Skill 模板庫 | 中立 LLM 路由策略庫 |
| **流程** | Onboarding 7 天交付 SOP | 多雲部署 Playbook |
| **客戶綁定** | Skill / Knowledge / Audit 累積 | 跨雲 Skill 可遷移性 |
| **行銷敘事** | 「AI 藍領」品類定義者 | 「不被鎖死」的中立平台 |

#### 29.11.5 三層完整模型總覽

```
┌──────────────────────────────────────────────┐
│ Layer 3c — 跨雲跨模型中立治理 (AEOS)          │
├──────────────────────────────────────────────┤
│ Layer 3b — 垂直藍領 AI 員工治理 (AEOS 主場)  │
├──────────────────────────────────────────────┤
│ Layer 3a — 通用 AI 員工治理 (大廠主場)        │
├──────────────────────────────────────────────┤
│ Layer 2  — Agent Runtime (Loops / LangGraph) │
├──────────────────────────────────────────────┤
│ Layer 1  — LLM (OpenAI / Claude / Gemini)    │
└──────────────────────────────────────────────┘
```

**戰略推論**：AEOS 永遠不能宣稱進入 Layer 3a。所有 Pitch、官網、產品命名都應強化 Layer 3b + 3c 身份。

#### 29.11.6 對銷售與募資的更新話術

| 場合 | 舊話術 | 新話術 (Google Next '26 之後) |
| :--- | :--- | :--- |
| 對 VC | 「我們做 AI Employee Platform」 | 「我們做大廠看不上的藍領 AI 員工治理層 + 跨雲中立治理層」 |
| 對企業 CEO | 「我們訓練可上線 AI 員工」 | 「我們訓練可上線 AI 藍領 — 您的客服、店員、護理員、維修工」 |
| 對工程界 | 「Layer 3 治理」 | 「Layer 3b 垂直藍領 + Layer 3c 跨雲中立」 |

---

## 30. 十年演化路線與 90 天行動

### 30.1 十年演化四階段

#### Year 0~1：AI 藍領導入包（首位職位 = AI 客服）

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | **7 天為您雇用第一位 AI 藍領員工** (首選 = AI 客服 / 票務 / 點餐) |
| Wedge 收斂 | 鎖定 §22.8 藍領場景，避開大廠白領 Copilot 戰場 |
| 核心能力 | 資料匯入 / 知識卡 / 測試題 / 專家審核 / 草稿模式 / 基礎評分 |
| 入口策略 | **LINE / WhatsApp / 行動 App 優先**，Web Widget 次之（呼應藍領現場） |
| 商業重點 | 收導入費 + 月費；累積藍領案例；找出可跨產業重用的 Skill 模板 |
| 對應章節 | §17 五階段 / §18 Onboarding Layer / §22.8 藍領 Wedge / §25.2 Phase 1 定價 |

#### Year 1~3：AI 客服治理平台

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | 從導入服務變成可重複產品 |
| 核心能力 | SkillOps / Evaluation Dashboard / Policy Engine / Tool Gateway / Webhook + API + MCP Adapter / 多租戶 |
| 商業重點 | 降低導入工時；提高續約；擴大到多部門 |
| 對應章節 | §9 / §11 / §12 / §8 / §25.2 Phase 2 |

#### Year 3~5：AI 藍領員工平台（跨產業擴張）

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | 從客服擴張到其他藍領職位 |
| 可擴張職位 | AI 店員（零售）/ AI 揀貨員（物流）/ AI 護理助理（長照）/ AI 維修員（製造）/ AI 監工（營造）/ AI 加盟督導（連鎖） |
| 核心能力 | Role Profile / 跨藍領產業 Skill Library / Cross-role Evaluation / Enterprise Integration Layer |
| 行銷敘事 | 「全球 30 億藍領工作者的 AI 同事 / 替代方案」 |
| 對應章節 | §2.2 職位目錄 / §22.2 三段式延展 / §22.8 藍領產業範例表 |

#### Year 5~10：AI Blue-collar Workforce Governance Platform

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | 成為企業管理 AI 藍領勞動力的全球控制層 |
| 核心能力 | AI 藍領員工權限 / 績效 / 風險治理 / 技能版控 / 工具審計 / 跨系統流程協作 |
| 戰略意義 | 已脫離客服 / 單一產業範疇，成為**全球 30 億藍領工作者 AI 替代與輔助的標準平台** |
| 防守邊界 | 永不進入大廠主場 (Layer 3a)；專注 Layer 3b 藍領 + Layer 3c 跨雲中立 |

### 30.2 三公司定位的對應話術

| 階段 | 對外說法 |
| :--- | :--- |
| 短期 | 我們幫企業建立第一位可驗收、可監控、可治理的 AI 客服員工 |
| 中期 | AI 員工訓練與營運平台 |
| 長期 | Enterprise AI Workforce Governance Platform |

### 30.3 接下來 90 天行動路線

| 時間 | 任務 | 驗證目標 |
| :--- | :--- | :--- |
| Week 1~2 | 訪談 10 家有客服痛點的企業 | 驗證 H1：是否願意付導入費 |
| Week 3~4 | 做導入精靈 MVP | 驗證資料匯入 → 知識卡可行性 |
| Week 5~6 | 做測試題自動生成 + 專家審核介面 | 驗證專家時間能否壓低 ≤ 3 小時 |
| Week 7~8 | 做草稿模式 AI 客服 | 驗證一線客服是否願意採用 |
| Week 9~10 | 做基礎 Evaluation Dashboard | 驗證 H2：主管是否看得懂、是否每週查看 |
| Week 11~12 | 做 1~2 個 Paid Pilot | 驗證商業付費意願與交付成本 |

### 30.4 第一個 MVP 的硬邊界

**只做下列七項，超過即砍**：

```
1. 匯入網站 / PDF / FAQ
2. 自動生成 Knowledge Cards
3. 自動生成 50 題驗收題
4. 專家審核介面
5. AI 客服草稿模式
6. 基礎監控 Dashboard
7. LINE 或 Web Chat 二選一
```

**第一版禁止做的清單**（避免野心拖死團隊）：

```
× 完整 Agent Marketplace
× 複雜多 Agent 協作
× 完整 ERP / SAP 大整合
× 全自動自我學習
× Kubernetes-heavy 架構
× 完整客服系統
```

### 30.5 十年穩固性的三大條件

#### 條件 1 — 不要停在 AI 客服

平台必須能抽象為：

```
AI Employee = Role + Skill + Knowledge + Policy + Tool + Evaluation
```

這是擴張到其他職位的基礎。

#### 條件 2 — Evaluation 必須成為核心

| 元素 | 是否會被模型進步取代 |
| :--- | :--- |
| 模型 | 會 |
| 工具 | 會 |
| UI | 會 |
| **真實線上錯誤資料** | **不會** |
| **產業風險題庫** | **不會** |
| **SOP 違規案例** | **不會** |
| **Skill Regression 資料** | **不會** |

Evaluation 是長期資產的唯一形式。

#### 條件 3 — 每次交付必須沉澱為產品

每次客戶交付必沉澱以下至少一項：

```
□ 產業模板
□ Knowledge Card schema
□ Skill template
□ Evaluation set
□ Tool Contract
□ Policy Rule
□ Onboarding checklist
```

達不到即代表組織尚未脫離服務模式。

### 30.6 系統設計總圖（呼應 §5 與 §29）

```
┌──────────────────────────────────────────────┐
│                Customer Company              │
│ Website / LINE / CRM / ERP / SAP / Docs      │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│         AI Employee Onboarding System         │
│         (Compiler 1 — Data-to-Knowledge)      │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│              Knowledge Card System            │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│              SkillOps Registry                │
│         (Compiler 2 — Knowledge-to-Skill)     │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│              Training Room                    │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│        Production AI Employee Runtime         │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│              Governance Harness               │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│             Tool Gateway / MCP Proxy          │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│             Enterprise Systems                │
└──────────────────────────────────────────────┘

旁路閉環 (Compiler 3 — Conversation-to-Improvement)：

Conversation Logs
    ↓
Evaluation & Monitoring
    ↓
Risk / Drift / Regression Detection
    ↓
Training Room
    ↓
Skill Version Upgrade
    ↓
Production Release (回到主鏈路)
```

### 30.7 投資人視角的最終判斷

| 評估項 | 評級 |
| :--- | :--- |
| 市場趨勢 | 高 |
| 客戶痛點 | 高 |
| 初期切入可行性 | 中高 |
| 技術可行性 | 中高 |
| 短期護城河 | 中低 |
| 中期護城河 | 中高 |
| **十年護城河** | **有機會高，取決於是否做出治理與評估飛輪** |
| 投資人敘事 | 中高到高 |
| 失敗風險 | 高（主因：過度客製、大廠競爭） |

**綜合判斷**：
- 不投資 → 錯失新類別早期定義者
- 投資 → 必須監控 §29.9 護城河檢核問題；任一答案為「否」即為早期退出訊號

---

## 31. 不採納清單 (Non-goals)

明確列出 **AEOS 不做** 的事，避免邊界蔓延：

| 不做 | 理由 |
| :--- | :--- |
| 通用 AGI / 對話聊天機器人 | AEOS 是企業勞動力平台，不是消費級 Chatbot |
| 取代人類客服 | AEOS 是「協作」與「擴展」，不是「替代」 |
| 自有 LLM 模型訓練 | 模型應由 LLM Provider 提供；AEOS 專注治理 |
| 通用 BI / 資料分析平台 | AEOS 提供 AgentOps，不取代 BI |
| 通用 Workflow / BPM 平台 | AEOS 的 Workflow 服務於 AI 員工，不做通用 BPM |
| 通用 IAM / SSO 平台 | 整合既有 IAM (Okta / Azure AD)，不自建 |
| Hardware Edge / IoT 終端 | 聚焦軟體層 |
| 一次性整合所有企業系統 | MVP 階段嚴格控制整合範圍，避免無底洞 |
| 完全自動化客服 | L4 受控自動化是上限，全程仍須人類監督機制 |

---

## 32. 結論

### 32.1 核心論點回顧

1. **企業要的不是 AI 客服，是 AI 員工作業系統**。客服只是其中一種職位。
2. **護城河不在 Agent Loop，在治理體系**。Skill / Tool / Policy / Audit / Evaluation 才是企業敢付費的理由。
3. **訓練生產分離是鐵律**。會學習的腦關在訓練室，上線員工是 Frozen Runtime。
4. **MCP Host 要有，但不能裸奔**。MCP 是工具協議，不是治理系統。
5. **Governance-first，DevOps-later**。先做治理基礎設施，再談平台規模化。
6. **監控評分才是真正的護城河**。AgentOps 解決「事後可追、事中可控、事前可審」。

### 32.2 給不同決策者的一句話

| 決策者 | 一句話 |
| :--- | :--- |
| CEO | AEOS 不是聊天機器人，是可訓練、可派工、可監控、可下架的數位勞動力平台 |
| CTO | 三平面分離 + Bounded Context + Frozen Runtime 是技術護城河 |
| CISO | 一鍵停用、Tool Gateway、Audit Log、PII 治理是上線前的紅線 |
| CFO | 多模型策略 + Cost Attribution + Quota 決定毛利率 |
| Compliance | GDPR / PDPA / EU AI Act 必須是模組化合規層，不是事後補丁 |
| 產品 PM | MVP 要敢刪：1 職位 + 3 工具 + 1 租戶，不接 ERP / SAP 全家桶 |
| 客戶企業 | 你買的不是 Bot，是一套可以信任 AI 進入流程的治理體系 |

### 32.3 五歲小孩版的記憶錨點

> **把 AEOS 想成一家會招聘 AI 員工的公司：**
>
> - **訓練學校 (Hermes 類)**：員工在這裡練習、犯錯、改進
> - **正式員工 (nanobot / OpenClaw 類)**：上班時只能照核准的規定做事
> - **工程部工具箱 (CheetahClaws 類)**：很好用，但不直接拿到櫃台服務客人
> - **公司工具 (MCP Server)**：每個工具都要先檢查安全、貼標籤、規定誰能用
> - **工具管理員 (Tool Gateway)**：員工拿工具前要打卡簽核、用完要留紀錄
> - **公司規章 (Policy Engine)**：員工不能自己改公司 SOP
> - **人事考評 (AgentOps)**：每位員工都有持續考績，表現不好回訓練學校
>
> **重點不是「AI 很聰明」，而是「AI 像員工一樣，被訓練、被授權、被管理、被考核」。**

---

## 附錄

### A. 術語表

| 術語 | 定義 |
| :--- | :--- |
| AEOS | AI Employee Operating System |
| AI Employee | 受治理的執行物件，由 Role + Skill + Policy + Tool 組成 |
| Skill | 可版本化的能力包，含 Prompt、Schema、Test、Risk Level |
| Tool | 受控的外部能力，必經 Tool Gateway |
| MCP | Model Context Protocol，工具協議標準 |
| MCP Host | 連接 LLM 與 MCP Server 的執行環境 |
| Tool Gateway | 工具閘道，負責權限、稽核、遮罩、限流 |
| Policy Engine | 策略引擎，執行業務規則與權限判斷 |
| Training Room | 訓練室，允許自我學習的隔離環境 |
| Frozen Runtime | 凍結執行環境，禁止自我修改 |
| SkillOps | AI 員工的 MLOps |
| Drift | 漂移，指 Skill / Knowledge / Behavior 的退化 |
| Canary Release | 小流量灰度發布 |
| Tenant | 租戶，最高隔離單位 |
| Multi-tenant | 多租戶隔離（不同於 multi-user） |
| Red Team | 紅隊測試，對 AI 進行對抗測試 |
| RAG Grounding | 檢索增強生成的來源綁定 |
| PII | Personally Identifiable Information |
| RBAC / ABAC | 角色 / 屬性 為基礎的存取控制 |
| Kill Switch | 一鍵停用機制 |

### B. 決策矩陣

#### B.1 Runtime 選型

| 場景 | 推薦 | 不推薦 |
| :--- | :--- | :--- |
| MVP / PoC | nanobot fork + 簡單 Policy Wrapper | 自建 Runtime (太貴) |
| 企業內部 Beta | nanobot 重度 wrap + Tool Gateway | 直接用 Hermes / 桌面工作台 |
| 商用平台 | 自建 Enterprise MCP Host | 任何單一開源框架裸用 |
| Coding 內部助理 | CheetahClaws (內網限定) | 對外客服 |
| 訓練室 | Hermes-style + 自建沙盒 | nanobot (太輕) |

#### B.2 LLM 選型

| 場景 | 推薦 |
| :--- | :--- |
| 高度機密 / 工廠內網 | Local Model (Ollama / vLLM) + Private Gateway |
| 一般 SaaS | 公有 LLM (簽 DPA) + 多供應商 Fallback |
| 跨國 | 區域化部署 + 資料主權考量 |
| 政府 | Sovereign LLM / On-prem |

#### B.3 是否導入自我學習

| 條件 | 建議 |
| :--- | :--- |
| 有專家陪訓資源 + Skill 審核流程 + Sandbox + Red Team | ✅ 導入 (Phase 2+) |
| 缺任一條件 | ❌ 暫不導入，Phase 1 用 Frozen Runtime |

### C. 上線前檢核清單

#### C.1 治理檢核
- [ ] 所有 Skill 都有 Owner、Version、Test Cases
- [ ] 所有 Tool 都有 Permission Contract
- [ ] Policy Engine 預設 deny
- [ ] Audit Log 寫入失敗即整筆回滾
- [ ] 一鍵停用 / 回滾測試通過

#### C.2 安全檢核
- [ ] PII Masking 全鏈路覆蓋
- [ ] Cross-tenant 隔離測試通過
- [ ] 紅隊 7 種樣式攔截率 ≥ 99%
- [ ] 秘密 (API Key、憑證) 集中於 Vault
- [ ] 所有外部呼叫經 Tool Gateway

#### C.3 合規檢核
- [ ] DPA 已簽
- [ ] 客戶資料保留期限已設定
- [ ] Right to Erasure 流程可執行
- [ ] Audit Log 保留期限符合法規
- [ ] AI 服務透明標示

#### C.4 運營檢核
- [ ] Dashboard 涵蓋效率 / 品質 / 風險 / 成本四類
- [ ] Drift 偵測規則已配置
- [ ] On-call 值班表已建立
- [ ] 事件響應 Runbook 已寫
- [ ] Canary 發布流程驗證

#### C.5 商業檢核
- [ ] 計價模型已定 (席次 / Token / Skill)
- [ ] Cost Attribution 可按租戶切分
- [ ] Quota 機制已上線
- [ ] SLA 已寫入契約
- [ ] Liability Cap 已協議

### D. 參考實作定位速查表

| 工具 | 在 AEOS 的位置 | 採用方式 |
| :--- | :--- | :--- |
| Hermes Agent (類) | Training Room Engine | 受控 Wrap，不接 Production |
| nanobot (類) | Production Runtime 候選 | 重度 Wrap + Policy 包覆 |
| CheetahClaws (類) | Internal Automation Worker / Tool Registry 設計參考 | 後台 PoC，不對客戶 |
| 桌面工作台 (洩露源類) | UX 研究素材 | 不採用 |
| Claude Code / Cursor / Claude Desktop | MCP Host 行為參考 | 不採用為平台 Runtime |
| ClawWork (類評估) | Evaluation Service 設計範式 | 自建 Evaluation Harness |

### E. 三句話口訣

1. **AI 員工不是模型，是受治理的執行物件**。
2. **訓練室可成長，上線員工要凍結**。
3. **Skill 要版本化、Tool 要走閘道、監控評分才是護城河**。

### F. 客戶 Onboarding 資料盤點清單

> 對應 §17.3 Phase 0 需求盤點。客戶導入 AEOS 前，平台方需取得以下四類資料以完成 Tenant 配置與 Skill 建模。

#### F.1 業務資料 (Business Data)

```
□ 客服問題分類 (Issue Taxonomy)
□ 常見 FAQ 與標準答案
□ 產品 / 服務說明
□ 退換貨政策
□ 保固條款
□ 客訴處理 SOP
□ 人工接手規則
□ 客服語氣規範
□ 禁止承諾事項清單
□ 行業特殊禁令 (金融 / 醫療 / 法律)
```

#### F.2 系統資料 (System Inventory)

```
□ 目前客服入口 (Web / LINE / Email / 電話)
□ 目前 CRM 系統 (廠牌 / 版本)
□ 目前 ERP / 進銷存 / 會計系統
□ 是否提供 API / Webhook
□ API 文件 / Postman Collection
□ 測試環境 URL 與帳號
□ 認證方式 (OAuth / API Key / JWT / mTLS)
□ Rate Limit 與配額
□ 資料欄位說明文件
□ Schema 變更頻率
```

#### F.3 資安資料 (Security Requirements)

```
□ 是否允許 SaaS 部署
□ 是否需要私有部署 (On-prem / VPC)
□ 個資處理規範 (GDPR / PDPA / HIPAA)
□ 資料保存期限
□ 是否需要 Audit Log 匯出
□ 是否需要 SSO 整合 (Okta / Azure AD / Google Workspace)
□ 是否需要 IP Whitelist
□ 加密要求 (Encryption at Rest / In Transit)
□ 資料主權地理限制
```

#### F.4 驗收資料 (Acceptance Criteria)

```
□ 測試題庫 (含正確答案)
□ 不可回答題目清單
□ 高風險題目清單
□ 必須轉人工的案例
□ 客服主管評分規則
□ 上線門檻 (對應 §21.1)
□ 灰度發布比例計畫
□ 應急聯絡窗口
```

### G. 容器化部署策略

> 對應 §5 系統架構與 §11 安全合規。本附錄提供具體部署型態建議。

#### G.1 哪些元件適合容器化

| 元件 | 容器化必要性 | 理由 |
| :--- | :--- | :--- |
| AI Employee Runtime | 高 | 多版本並存、快速擴縮 |
| MCP Server / Tool Adapter | 高 | 風險隔離、獨立停用 |
| Sandbox Runner | 高 | 訓練室隔離 |
| Evaluation Worker | 高 | 批次任務、資源彈性 |
| Document Parser / Knowledge Indexer | 高 | 異步任務、可橫向擴展 |
| Webhook Receiver | 中 | 視流量決定 |
| Admin Console | 中 | 標準 Web 部署即可 |
| Audit Service | 高 | 高可用、分流寫入 |

#### G.2 工具風險分層的容器隔離

不同風險等級的 MCP Adapter 應採用不同隔離強度：

| 風險等級 | 範例 | 容器策略 |
| :--- | :--- | :--- |
| 低 | FAQ 查詢、Knowledge Search | 共用 Pod / 命名空間 |
| 中 | 訂單查詢、客戶資料查詢 | 獨立 Pod、獨立 ServiceAccount |
| 高 | 退款申請、CRM 寫入 | 獨立 Namespace、Network Policy 隔離 |
| 極高 | 會計操作、權限變更 | 獨立 Cluster 或專屬 VPC |

每個 Container 應具備：

```
- 獨立權限 (least privilege)
- 獨立 NetworkPolicy
- 獨立 Secret (Vault 注入)
- 獨立 Log Stream
- 獨立 Rate Limit
- 獨立停用機制 (Kill Switch)
```

#### G.3 客戶部署型態矩陣

不應採用「每客戶一套完整 K8s」的反模式，過度工程化將導致維運成本失控。建議依客戶等級採用對應策略：

| 客戶等級 | 部署型態 | 隔離強度 | 維運成本 |
| :--- | :--- | :--- | :--- |
| 小型客戶 | Multi-tenant SaaS，共用平台 | 邏輯隔離 (DB Schema / 命名空間) | 最低 |
| 中型客戶 | 共用核心平台，關鍵 Adapter 獨立 Container | 混合隔離 | 中 |
| 大型企業 | 專屬 Tenant Runtime，專屬 Adapter | 物理隔離 (獨立 Namespace) | 高 |
| 高法遵產業 | 私有部署 / VPC / On-premise | 完全隔離 | 最高 |

#### G.4 三平面部署原則

呼應 §5.4 三平面分離，部署層次應：

```
Control Plane    → 全平台共用 (高可用、跨區複製)
Data Plane       → 依租戶等級隔離 (運算與儲存)
Governance Plane → 全平台共用，但稽核資料按租戶分區
```

**設計推論**：Control Plane 升級不應影響 Data Plane 線上服務；單一 Tenant 故障不應影響其他 Tenant；Governance Plane 即使全部 Data Plane 故障仍可獨立查詢稽核紀錄。

#### G.5 反模式警示

| 反模式 | 後果 | 正確做法 |
| :--- | :--- | :--- |
| 一開始就 K8s + Service Mesh + 多區 HA | 維運成本壓垮團隊 | Phase 1 先用 Docker Compose；K8s 留 Phase 3 |
| 每客戶一個獨立 Cluster | 升級困難、成本失控 | 多租戶 SaaS + 邏輯隔離 |
| 所有 Adapter 共用單一 Container | 單一漏洞影響全平台 | 依風險分層隔離 |
| Secret 寫入 ConfigMap | 嚴重資安漏洞 | 使用 Vault / Sealed Secrets |
| 所有日誌寫入單一資料庫 | 法遵稽核困難 | 依租戶分區 + 不可變儲存 |

### H. 導入精靈 UX 七步驟

> 對應 §18 Onboarding Automation Layer。本附錄提供無腦導入精靈的具體 UX 流程，作為 Admin Console 設計藍圖。

#### H.1 精靈總覽

```
Step 1：選擇 AI 員工職位
Step 2：匯入資料
Step 3：系統自動整理知識
Step 4：產生測試題
Step 5：專家審核
Step 6：選擇上線模式
Step 7：接入客服渠道
```

#### H.2 Step 1 — 選擇 AI 員工職位

```
你想先訓練哪一種 AI 員工？

[客服助理]
[售前顧問]
[維修助理]
[訂單查詢助理]
[內部 IT 助理]
```

選定後系統自動套用對應 Role 模板：

```
預設技能：
- FAQ 回答
- 產品介紹
- 客訴分類
- 轉人工
- 工單建立草稿

預設風險規則：
- 金流問題轉人工
- 法律承諾轉人工
- 無來源答案不得回答
- 個資查詢需驗證身份
```

#### H.3 Step 2 — 匯入資料

```
請選擇資料來源：

[貼上網站網址]
[上傳文件]
[連接 Google Drive]
[匯入客服紀錄]
[連接 Notion]
[稍後再補]
```

**設計重點**：必須提供「稍後再補」選項，避免客戶被卡住。

#### H.4 Step 3 — 自動整理知識

```
已整理完成：

- 找到 128 個 FAQ
- 找到 36 個產品資訊
- 找到 8 條退換貨規則
- 找到 12 個高風險問題
- 發現 5 個缺漏項目

[查看缺漏]  [產生 AI 客服]  [請專家審核]
```

#### H.5 Step 4 — 產生測試題

```
系統已產生 80 題驗收題：

- 基礎 FAQ：30 題
- 模糊問法：20 題
- 客訴情緒：10 題
- 高風險問題：10 題
- 轉人工測試：10 題
```

#### H.6 Step 5 — 專家審核

```
這題 AI 回答是否可上線？

[通過]  [需修改]  [應轉人工]  [禁止回答]
```

**設計重點**：每題決策成本必須 ≤ 30 秒。

#### H.7 Step 6 — 選擇上線模式

```
請選擇上線策略：

[保守模式] AI 只產生草稿
[標準模式] 低風險自動回答
[積極模式] 可自動查詢與建立工單
```

底層自動映射至 §20.2 自動化等級 (L1/L2/L3)。

#### H.8 Step 7 — 接入客服渠道

```
你要在哪裡使用 AI 客服？

[網站 Widget]
[LINE 官方帳號]
[Facebook Messenger]
[企業現有客服系統]
[API 串接]
```

對應 §19 三種企業導入模式。

### I. AI 客服 7 日導入包 (Concierge Onboarding Package)

> 對應 §18.13 模式 B 陪跑導入。本附錄定義具體交付節奏，作為銷售 SOW 與 PMO 排程基準。

| 天數 | 任務 | 交付物 | 客戶投入 |
| :---: | :--- | :--- | :--- |
| Day 1 | 資料蒐集 | 網站、FAQ、SOP、客服紀錄收齊 | 1 小時訪談 |
| Day 2 | 知識整理 | FAQ Card / Policy Card / Product Card 初版 | 0 |
| Day 3 | AI 員工初版 | Role / Skill / Knowledge Base 初版 | 0 |
| Day 4 | 測試題生成 | 50~100 題驗收題 | 0 |
| Day 5 | 專家陪練 | 錯誤標註、轉人工規則 | 客服主管 1~2 小時 |
| Day 6 | 灰度上線 | Web Chat / LINE / 草稿模式 | 1 小時上線確認 |
| Day 7 | 報告與優化 | 上線建議、風險清單、下一版 roadmap | 30 分鐘檢視 |

**客戶總投入**：約 4~5 小時，分散於 7 天。

### J. AI 員工履歷模板

> 對應 §18.12 AI 員工履歷。每位 AI 員工上線前必產出，作為與客戶溝通的視覺化交付物。

```yaml
employee_profile:
  name: Sunny Support Agent
  role: 一線客服助理
  tenant: Company A
  hired_at: 2026-05-14

  knowledge_summary:
    faq_count: 128
    product_count: 36
    policy_count: 13
    last_kb_update: 2026-05-13

  capabilities:
    can_handle:
      - 基礎產品問答
      - 退換貨規則說明
      - 客訴初步分類
      - 建立工單草稿
    cannot_handle:
      - 退款承諾
      - 法律爭議
      - 價格特殊折扣
      - 帳務修改

  recommended_launch:
    initial_mode: 保守模式 (L1)
    duration: 2 週
    upgrade_criteria:
      - FAQ 正確率 ≥ 90%
      - 客訴升級轉介率 ≥ 95%
      - 連續 7 日無重大事故
    upgrade_target: 標準模式 (L2)
```

---

**文件結束**

*本白皮書是活文件 (Living Document)，將隨產品迭代與市場變化持續更新。*
*版本歷史將記錄於 `CHANGELOG.md`。*
