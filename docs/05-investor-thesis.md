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
- §29.5~29.7 三個 Compiler (Data-to-Knowledge / Knowledge-to-Skill / Conversation-to-Improvement)
- §29.9 護城河檢核問題 (六題自檢清單)
- §30.1 Year 0~10 四階段演化路線
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

---

## 30. 十年演化路線與 90 天行動

### 30.1 十年演化四階段

#### Year 0~1：AI 客服導入包

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | **7 天建立你的第一位 AI 客服員工** |
| 核心能力 | 資料匯入 / 知識卡 / 測試題 / 專家審核 / 草稿模式 / 基礎評分 |
| 商業重點 | 收導入費 + 月費；累積案例；找出重複模板 |
| 對應章節 | §17 五階段 / §18 Onboarding Layer / §25.2 Phase 1 定價 |

#### Year 1~3：AI 客服治理平台

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | 從導入服務變成可重複產品 |
| 核心能力 | SkillOps / Evaluation Dashboard / Policy Engine / Tool Gateway / Webhook + API + MCP Adapter / 多租戶 |
| 商業重點 | 降低導入工時；提高續約；擴大到多部門 |
| 對應章節 | §9 / §11 / §12 / §8 / §25.2 Phase 2 |

#### Year 3~5：AI 員工平台

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | 從客服擴張到其他 AI 員工 |
| 可擴張職位 | AI 售前 / 維修 / 內部 IT / 採購 / 業務 / 文件助理 |
| 核心能力 | Role Profile / 受控企業內部 Skill Library / Cross-role Evaluation / Enterprise Integration Layer |
| 對應章節 | §2.2 職位目錄 / §22.2 三段式延展 |

#### Year 5~10：AI Workforce Governance Platform

| 維度 | 內容 |
| :--- | :--- |
| 對外定位 | 成為企業管理 AI 勞動力的控制層 |
| 核心能力 | AI 員工權限管理 / 績效管理 / 風險治理 / 技能版本管理 / 工具審計 / 跨系統流程協作 |
| 戰略意義 | 已脫離客服公司範疇，成為**企業 AI workforce 的管理平台** |

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
