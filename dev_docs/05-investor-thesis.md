# 投資人視角與十年戰略

> **本檔對應原 whitepaper.md 的 §26~§30 (Part IV)**
> 主題定位：投資 + 擴張
> 最後同步：2026-05-14

## 相關章節速查

**本檔被外部引用的高頻章節**：
- §26.1 十年護城河總評 — 短期/中期/十年三段評級
- §26.5 索克拉底三大提問 — 公司本質、客戶恐懼、十年後價值
- §27.2 三條正向迴路 (R1 導入飛輪 / R2 評估飛輪 / R3 信任飛輪)
- §27.3 兩條負向迴路 (B1 複雜度反噬 / B2 模型商品化壓力)
- §28 H1~H4 核心假設與驗證指標
- **§28.9 H5 假設 — AI 藍領市場可承載 100~500 客戶 + 訪談指標 + 三條退路** (R7 新增)
- §29.5~29.7 三個 Compiler (Data-to-Knowledge / Knowledge-to-Skill / Conversation-to-Improvement)
- §29.9 護城河檢核問題 (六題自檢清單)
- **§29.10 AEOS vs Loops 三層分工模型 (LLM / Agent Runtime / Governance)** (R6 新增)
- **§29.11 Layer 3 細分 3a/3b/3c — AEOS 永不進 3a 大廠主場** (R7 新增)
- §30.1 Year 0~10 四階段演化路線（**R7 全面收斂為 AI 藍領平台**）
- §30.4 第一個 MVP 硬邊界 (七做 + 六禁)
- §30.5 十年穩固性三大條件

**本檔對外引用的章節**：
- §2.2 職位目錄 (見 `01-vision-positioning.md`)
- §5 系統架構藍圖 (見 `02-product-architecture.md`)
- §6.3 知識三分類 (見 `02-product-architecture.md`)
- §8 MCP 整合 (見 `02-product-architecture.md`)
- §9 SkillOps (見 `02-product-architecture.md`)
- §10.3 訓練室 UI (見 `02-product-architecture.md`)
- §11 安全合規 (見 `06-risk-boundaries.md`)
- §12 監控評估 (見 `02-product-architecture.md`)
- §13 多模型 (見 `02-product-architecture.md`)
- §17 五階段方法論 (見 `03-execution-onboarding.md`)
- §18 Onboarding Layer (見 `03-execution-onboarding.md`)
- §22.5 護城河四層遞進 (見 `01-vision-positioning.md`)
- §23.3 Adapter Contract (見 `04-strategy-business.md`)
- §24.6 Lifecycle Core Domain (見 `04-strategy-business.md`)
- §24.7 服務公司脫離指標 (見 `04-strategy-business.md`)
- §25.2 Phase 1 定價 (見 `04-strategy-business.md`)
- §29.9 護城河檢核問題 (本檔)

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
