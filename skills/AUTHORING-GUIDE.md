# AEOS Skill 建構與維護指南

> 本指南是 AEOS skill monorepo（`skills/<vertical>/<slug>/<semver>/`）的設計心法。
> 適用對象：新增 / 編輯 / 版本升級任何 AEOS skill（如 `customer-service/faq-respond`）的人。

## 適用範圍與 AEOS 對映

本指南內容源自通用 Claude agentic skill 設計手冊，但**已對映到 AEOS skill registry 的具體實作**（ADR-0003 / MC-005）。閱讀時請對照下表，避免直接套用不適用的章節：

| 原文章節 | AEOS 對映 | 適用度 |
|---|---|---|
| §1 漸進披露三層（100 Token 啟動成本）| ❌ 不適用 — AEOS SkillLoader 每 turn 載 `system.md` 全文（Frozen Runtime per turn）| ⚠️ 概念保留，機制不同 |
| §1 Front Matter (name/description) | `manifest.yaml` 的 `slug` / `name` / `description` 欄位 | ✅ |
| §1 Scripts 解耦確定性操作 | `tools.yaml` 註冊工具 + `ToolExecutor` dispatch | ✅ |
| §2 需求識別三訊號（高頻 / 領域知識 / 高錯誤成本）| 何時 bump 版本 / 何時新增 vertical 或 slug | ✅ |
| §3 雙路徑開發（逆向工程 + 主動發起）+ EDD | TestSet baseline + KeywordJudge / LLMJudge 已內建支援 | ✅ 完美對接 |
| §4 Description 三鐵律 | `manifest.description` 影響 audit / catalogue / 未來 skill 選擇器 | ✅ |
| §5 心法 vs SOP（寬窄原則）| `system.md` 撰寫核心哲學 | ✅ 核心 |
| §5 200-500 行限制 | `system.md` 同此原則；超出考慮拆 skill 或 tool | ✅ |
| §5 Sub-agent 裁判 | LLMJudge 已具備（Haiku 4.5 語意比對 + keyword fallback）| ✅ |
| §6 模型升級清債務 | v1.0 → v1.1 bump 時重審 `system.md`，刪舊補丁 | ✅ |
| §6 人類監督 | expert approve gate（MC-005 5 態 quality gate）| ✅ 強對接 |

**相關規格**：
- `skills/README.md` — 目錄結構與上線流程
- `docs/1-decisions/ADR-0003-skill-registry.md` — git monorepo 是 source of truth
- `docs/2-contracts/MC-005-skill-registry.md` — 5 態 lifecycle + Quality Gate

---

# 通用心法（6 章原文）

在現代 AI 代理（Agentic）工作流的開發體系中，將特定邏輯封裝為「Skill」已非單純的提示詞工程（Prompt Engineering），而是一種旨在最小化隨機行為（Stochastic Behavior）並確保確定性輸出（Deterministic Outputs）的系統化架構策略。透過 Skill 化的管理，開發者能有效處理大語言模型（LLM）的自主不確定性，並在可擴展性與 Token 負載管理之間達成最優平衡。

## 1. Skill 核心架構：最小化系統開銷的層次化設計

Skill 的本質是具備結構化資訊的資料夾，其設計核心在於透過「解耦」讓 Agent 僅在任務必要時讀取關鍵資訊，避免 Context Window 的無謂浪費。

### 核心組成元素

1. **Skill Markdown (`.md`)**：
   - **Front Matter**：定義 Skill 的元數據（名稱與描述），作為觸發判斷的基準。
   - **方法論（Methodology）**：傳授給 Agent 的執行心法與決策邏輯。
2. **References（參考資料）**：存放非高頻使用的長篇規範、術語表或極端案例（Corner Cases）。
3. **Scripts（腳本）**：這是確保穩定性的核心資產。腳本負責處理排序、API 調用與格式驗證等「確定性操作」。
   - **策略性意義**：腳本代碼本身不會進入 Context Window，僅有執行結果會回傳給 Agent，這能確保 Context 的「純淨度」與執行效率。

### 漸進式披露（Progressive Disclosure）機制

> ⚠️ **AEOS 警示**：AEOS SkillLoader **不採此三層機制** — 每 turn 直接載入 `system.md` 全文（Frozen Runtime per turn 原則，見 engineering-charter §1）。
> 本章節作為通用 Claude agentic 架構知識保留供讀者建立心智模型；AEOS 自身的 context 控制由 `tools.yaml` 的 tool 拆分與 `ToolExecutor` 的 dispatch 機制擔當。

為優化 Context Window 並降低 Token 成本，系統執行三層加載邏輯：

- **第一層：系統啟動階段**：當 Claude 啟動時（甚至在請求前），會先行載入所有 Skill 的「名稱」與「描述」。此階段僅需約 100 Tokens 負載，讓 Agent 知悉現有工具集。
- **第二層：需求觸發階段**：當用戶意圖與特定描述匹配時，系統才載入該 Skill 的完整 Markdown 文件。
- **第三層：資源調度階段**：僅在具體執行步驟中，視需求載入 References 或調用 Scripts。

## 2. 需求識別：防止過度工程的開發訊號

過度開發 Skill 會導致維護成本急劇上升。身為架構師，必須精準識別何時該從「提示詞對話」轉向「系統化 Skill」。

### 三大關鍵開發訊號

1. **高頻重複性**：當特定流程在不同 Session 中反覆出現，且需重啟提示詞引導時，即應封裝以減少手動引導負擔。
2. **獨有領域知識 (Domain Knowledge)**：AI 缺乏專案內部的私有路徑、特定文件格式或組織內部的做事「眉角」。Skill 作為橋樑，填補模型訓練數據外的知識缺口。
3. **高錯誤成本**：當任務產出需對外交付或具備嚴格標準時，需透過 Skill 強制規範流程，抑制模型「自由發揮」帶來的品質風險。

⚠️ **警示**：避免為低頻且低風險的任務開發 Skill。若維護 Skill 的成本高於手動調優，即屬於「過度工程（Over-engineering）」。

### 快速檢核表（以「周會報告」為例）

- [ ] 頻率：任務是否每週/每日固定執行？
- [ ] 知識：是否涉及 GitHub 提交紀錄、特定專案路徑或內部 Wiki？
- [ ] 品質：報告是否直接交付主管，且格式不容許偏差？

若任二為「是」，則具備極高的 Skill 化價值。

## 3. 實戰製作：捕捉成功路徑與主動設計

高品質的 Skill 邏輯不應憑空想像，而應來自對「成功執行路徑」的提取。

### 雙路徑開發模式

1. **逆向工程 (Reverse Engineering)：捕捉成功路徑**
   - 在一次成功的對話 Session 後，切記不要關閉對話。這份 Session 是提取邏輯的最珍貴資產。
   - 使用 Anthropic 官方 Marketplace 的 `skill-creator` 工具，或利用指令要求 Agent：「將剛才成功的對話邏輯與步驟提取出來，轉化為可重複使用的 Skill。」
2. **主動發起 (Proactive Design)：AI 作為 Thinking Partner**
   - 以 PM 的視角，向 AI 釐清意圖、約束條件與最終目標。要求 AI 在理解不完整時先行詢問，而非直接生成規則。

### 評估驅動開發 (Evaluation Driven Development, EDD)

在正式定稿 Skill 前，先讓 AI 在「零引導」狀態下嘗試任務。觀察其在哪裡產生幻覺、在哪裡卡住，這些「系統缺口」才是真正需要人為撰寫方法論的空白。

> ✅ **AEOS 對接**：EDD 在 AEOS 已落地為 `TestSet` + `Judge` 機制 — 先用 baseline `system.md` 跑 50 題 test_set.yaml，看 KeywordJudge / LLMJudge 給出的 pass rate 與 failure pattern，再針對性補強 `system.md`。

## 4. 觸發機制優化：精準引導的心理學

由於「漸進式披露」機制，Skill 的「描述 (Description)」是 Agent 在啟動時判斷是否啟用的唯一依據。

### Description 撰寫三鐵律

- **動作與時機並存**：必須明確交代「做什麼」以及「何時使用」。
- **第三人稱視角**：避免使用「我」以減少系統視角衝突，確保與 Agent 的操作視角一致。
- **自然語言觸發詞**：使用使用者口語中的關鍵詞（如：週報、進度更新），而非單純的技術編碼名詞。

### Front Matter 標準範例

```yaml
---
name: weekly-report-drafting
description: |
  Drafts weekly status updates for managers by aggregating data from Google Drive and GitHub commits.
  Use when user mentions "weekly reports", "team updates", "status summaries", "Friday review", or "what have I done this week".
---
```

## 5. 撰寫策略：心法優先於 SOP 的設計哲學

針對 Claude 3.5/4 等高推理模型，過於窄化的 SOP 會限制其應變能力。架構師應優先給予「執行心法」。

### 「寬窄原則」的實踐

- **心法 (Philosophy/Mindset)**：適用於具備判斷空間的任務。例如週報撰寫，應賦予「管理者中心視角 (Manager-centric perspective)」。原則為：「思考主管是否真的需要知道這項細節？優先呈現卡點與下一步，而非瑣事流水帳。」
- **規則 (Rules)**：適用於客觀標準。如「日期格式必須為 `YYYY-MM-DD`」，此時應給予嚴格的窄化步驟。

### 進階架構控制

- **系統穩定性守則**：單份 Skill 建議保持在 **200-500 行**內。超過此限度會導致資訊召回（Recall）精度下降，應考慮拆分。
- **權責分離 (Separation of Concerns)**：利用 **子代理 (Sub-agent) 機制**進行品質控管。由主代理執行任務，另開獨立 Context 的 Sub-agent 擔任「裁判」，按 Checklist 進行最終驗收，避免「球員兼裁判」的情形。

> ✅ **AEOS 對接**：Sub-agent 裁判模式在 AEOS 已落地為 `LLMJudge`（Haiku 4.5 跑語意比對），帶 keyword fallback 防 LLM outage 炸 test run；可注入 `TestSetRunner` 作為品質守門。

## 6. 長期維護與複利效應：減少技術債

Skill 是團隊的知識資產，但若不持續維護，則會演變為產出不穩的「技術債」。

### 維護清單與策略

1. **模型升級時：清除「指令債務」**
   - 當模型從 3.5 升級至 4 時，許多針對舊模型弱點設計的「補丁（Patches）」可能已無必要。刪除這些冗餘規則能讓 Context 更乾淨，讓新模型發揮原生實力。
2. **工作流覆盤時：自動化迭代**
   - 任務結束後，要求 Agent 自行檢討出錯原因，並詢問：「是否需將此避坑邏輯融入 Skill 以防再犯？」

### 風險管理：人類監督原則

- **禁止無監督覆寫**：在 Agent 將新邏輯寫入 Skill 文件前，必須經過人類 Double-check。這能防止 AI 將新資訊散亂插入，導致原有結構崩壞。
- **結構重整**：若 Skill 結構已混亂到人類難以快速閱讀，則必須進行重構。無法維護的 Skill 終將導致系統崩潰。

> ✅ **AEOS 對接**：人類監督在 AEOS 已強制落地為 MC-005 的 5 態 lifecycle — 新版本 `system.md` 必須走 `draft → testing → approved → production`，每態切換需 expert approve（DB CHECK 守門 + audit log）。`AEOS_AUTH_REQUIRED` 模式下，approve 動作的 `actor_id` 與時間戳全進 audit_log。

**核心目標**：Skill 的建構是為了將人類的思考方式、判斷標準與專業直覺轉移給 Agent。透過不斷的迭代與維護，實現個人與團隊能力的複利增長。
