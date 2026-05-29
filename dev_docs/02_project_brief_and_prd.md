# 專案簡報與產品需求文件 (PRD) - care-copilot（AI 客服 MVG / Draft Mode）

> **版本:** v1.0 | **更新:** 2026-05-29 | **狀態:** 已批准（Gate 1 PRD frozen，變更走 DR）
> **負責人:** PM | **審核:** PO + TL | **追蹤:** 本檔產生 E-/US-/Q-/D- 為下游
> **來源:** `docs/prd/ai-cs-mvg.md`（frozen v1）+ `docs/foundation/00~03` + `docs/governance/stakeholders.md`

---

## 1. 專案總覽

| 項目 | 內容 |
| :--- | :--- |
| **專案名稱** | care-copilot（AEOS 核心切片代號 `ai-cs-mvg`；對外垂直產品名 care-copilot，pack #1） |
| **狀態** | 規劃中（PRD frozen，刻意停在 PRD，直接進寫切片模式） |
| **目標發布日期** | Pilot：簽 pilot 後 W6 Go/Kill 決策點 |
| **核心團隊** | PM: CEO 戴帽 / Lead Engineer: coding agent（依 `foundation/02` handoff）/ UX: W2 才需審核台 |

> **命名 source-of-truth**：`ai-cs-mvg` = 本 PRD 代號 = AEOS 核心 B1 賭注（freeze scope）；`care-copilot` = 對外垂直產品名（下游 spec/ux/arch/api/data/qa/ops 一律用此名）；`foundation/pilot_run.md` = 垂直商品全集（11 工具 superset，**非本次 freeze scope**）。三者同一賭注、同一 B1，scope 大小不同。

---

## 2. 商業目標

| 項目 | 內容 |
| :--- | :--- |
| **背景與痛點** | 一線客服缺工、流動率高、新人 1~3 個月才上手；企業 FAQ/SOP 散亂，沒人能快速把它變成可用的客服回答。 |
| **策略契合度** | 整個 AI 員工工廠願景（`foundation/00-the-bet`）的第一塊基石。若「混亂知識 → 可用客服草稿」轉換成立，企業能用 1/10 成本擴充工時容量、24/7 不停班。 |
| **不解的成本** | 賭注無法被證明 → 整個工廠願景停在 PPT；pilot 客戶缺工與訓練成本持續燒。 |
| **成功指標** | **主要（北極星 K1）**: 草稿原樣 approve 率 ≥ 50% / **次要**: 總採用率 ≥ 70%（K2）、測試集 pass rate ≥ 70% W1（K3）、單租戶毛利 ≥ 50%（K4） |

### KPI 與反向指標（量化）

| 類別 | 指標 | 目標 | 觀測週期 |
| :--- | :--- | :--- | :--- |
| Business Goal | 8 週內 ≥ 1 家 pilot 真實跑通；pilot 末願付費簽約 ≥ 1（B-2） | 一次性 | — |
| User Goal（expert） | 每則省時 ≥ 50%（審比自己寫快） | weekly |
| **K1 北極星** | 草稿原樣 approve 率 | ≥ 50% | weekly（pilot ≥ 2 週穩定讀數） |
| K2 | 草稿總採用率（approve + edit-and-send） | ≥ 70% | weekly |
| K3 | 知識可用性（測試集 50 題 pass rate） | ≥ 70% W1 / ≥ 80% pilot 末 | W1 起 |
| K4 | 單租戶毛利 | ≥ 50% | monthly |
| C1 反向 | expert reject 率（超過代表治理在救火） | ≤ 30% | weekly |
| C2 鐵律 | 未經人類 approve 的自動發訊 | = 0（Draft Mode 保證） | 持續 |
| B-2 baseline | W0 量「無 AI 時 expert 自寫」approve 對照與每則耗時（避免 50% 其實是退步） | 對照組 | W0 |
| B-3 客戶側 | 終端客戶側 counter-metric（重問率 / 投訴；approve ≠ 客戶滿意） | 監控趨勢 | weekly |

> **只盯一個北極星數字 K1**，其餘是它的輔助診斷。不要被多個數字分心。

---

## 3. 使用者故事與允收標準

> Persona：**Primary** = pilot 客戶的客服專家／主管（Amy，審草稿）；**Secondary** = 真實終端客戶（透過 LINE 發問，不知背後是 AI 草稿，個資權利主體）。
> UC↔FR 對映為 **5 UC ↔ 7 FR，非 1:1**（見 system-spec §7）。

### Epic: E-0001 知識攝取與活檔案（原料端）

| ID | 描述 (As a / I want to / So that) | 允收標準 | BDD 連結 |
| :--- | :--- | :--- | :--- |
| US-0001 | As an expert, I want to 貼上一份真實 FAQ/SOP（markdown）, so that 系統建立可檢索索引。（FR-001 / UC-1） | 1. 貼一份真知識後對相關問題能檢索回正確片段 2. 不同租戶 0 串 | `ingest.feature` |
| US-0002 | As an expert, I want to 建立/補充客戶活檔案（7 欄位 + 互動時間軸）, so that 草稿能 grounded 在結構化關係資料。（UC-1 / ADR-0003） | 1. 抽取欄位正確率 ≥ 80%（對標註集） 2. append-only 時間軸 3. health_focus 特種個資需明示同意 | `contact.feature` |
| US-0012 | As an expert, I want to W1 手動貼上/截圖真實客戶訊息（W2+ 改 LINE webhook 自動收訊）, so that 訊息能入庫產草稿。（FR-003 / R2 S-1） | W1：貼上/截圖即入庫；W2+：webhook 接收並驗簽，失敗則拒絕 | `message-intake.feature` |

### Epic: E-0002 草稿生成與合規把關（核心鏈路）

| ID | 描述 | 允收標準 | BDD 連結 |
| :--- | :--- | :--- | :--- |
| US-0003 | As the system, I want to 檢索活檔案+知識 → Claude 產生 3 語氣草稿回覆, so that expert 有可審的草稿。（FR-002 / UC-2） | 1. 測試集 50 題 pass ≥ 70%（W1） 2. grounded（有 citation 且 judge 不判幻覺） 3. p95 < 5s | `draft.feature` |
| US-0004 | As the system, I want to 草稿過合規低語（綠過/黃提醒/紅強制改寫）, so that 不外送踩 FTC/FDA 線。（UC-4 / BR-2） | 1. 高風險詞召回 100% 2. 誤擋率 ≤ 5% 3. red = 送出鈕禁用，100% 紀錄 | `compliance-gate.feature` |
| US-0005 | As the system, I want to 缺依據時草稿標 `[需人工]`, so that 不硬掰幻覺。（BR-1 / UC-2） | 缺依據 → `needs_human=true`，不回幻覺草稿 | `grounding.feature` |

### Epic: E-0003 Draft Mode 人類審核與回發（治理閘門）

| ID | 描述 | 允收標準 | BDD 連結 |
| :--- | :--- | :--- | :--- |
| US-0006 | As an expert, I want to approve / edit / reject 草稿，approve 後回發 LINE, so that 我審每一則、AI 永不自動發。（FR-004 / UC-3，W2） | 1. 三種決定皆可操作 2. approve 後客戶收到回覆 3. edit 後**必重跑合規 gate**（不可繞紅燈，C2） | `review-decision.feature` |

### Epic: E-0004 稽核與治理鐵律（橫切）

| ID | 描述 | 允收標準 | BDD 連結 |
| :--- | :--- | :--- | :--- |
| US-0007 | As an operator, I want to 每則訊息記錄知識來源 + model + 人類決定 + 決定者, so that 任一對話可完整還原。（FR-005 / BR-5） | 任一對話可完整還原 used_chunks + model + decision + decided_by（100%） | `audit.feature` |
| US-0008 | As an operator, I want to 單一 kill switch 全停, so that 出事 30 秒內全面停止。（FR-006 / NFR Operability） | 實測 30 秒內全面停止產草稿與回發；`killswitch_active` 心跳可驗 | `killswitch.feature` |
| US-0009 | As an operator, I want to 上線配置凍結（prompt + 知識快照）, so that AI 不線上即時學習改行為（學習/生產分離）。（BR-6 / ADR-0001） | 生產 runtime 嘗試自改 prompt → 被 Frozen 包覆拒絕 | `frozen-runtime.feature` |
| US-0010 | As an operator, I want to 跨 tenant 存取一律 deny（RLS + app 層）, so that 不同租戶資料 0 串。（BR-3 / 鐵律） | tenant A 查 tenant B 的 contact/message/knowledge_chunk → 全 403/空集（**1 次都不能破**） | `tenant-isolation.feature` |

### Epic: E-0005 離線 B1 驗證（最致命賭注最早驗）

| ID | 描述 | 允收標準 | BDD 連結 |
| :--- | :--- | :--- | :--- |
| US-0011 | As an operator, I want to 對測試集跑 draft→judge → 採用率裁決, so that W1 不等 LINE 即可打 B1。（FR-007 / UC-5） | 一個指令對 testset 印出 pass rate；達 GO/PIVOT/KILL 門檻（foundation/03） | `eval.feature` |

---

## 4. 範圍與限制

| 項目 | 內容 |
| :--- | :--- |
| **功能範圍（In Scope）** | - LINE 單一通道（W1 手動貼，W2 webhook + approve 後回發） - 知識 ingest（貼上 markdown/純文字 → 建索引） - 檢索 + Claude 產生草稿 - Draft Mode 人類審核 - 全鏈路稽核 - Kill switch（30s 全停） - Eval pass rate - 單一 pilot 租戶 |
| **非功能需求** | 性能: 草稿 p95 < 5s / 合規 regex < 50ms ｜ 安全: 來源驗簽 + secrets 不進 git + 傳輸加密 + tenant_id 強制 RLS scope ｜ 可用性: pilot best-effort，無正式 SLO，killswitch 保底 ｜ 成本: ≤ $0.30/直銷商/日（≤ $300/月毛利護欄） ｜ 學習/生產分離: Frozen Runtime（ADR-0001） |
| **不做什麼（Out of Scope）** | - 自動發訊 / canary 流量分配 / 信心閾值自動 fallback（切片永遠停在 Draft Mode） - Web chat / 多通道 / 多語言 - 多租戶 / 跨租戶 - 訂單寫入（只查不寫；動態查詢本切片不接，OQ-004） - Skill registry / 多 skill / 版本化 UI - Email digest / Dashboard / 主動推送 - 微服務拆分 / agent framework / K8s / 完整 observability stack - PDF/DOCX/URL 自動解析（只收貼上的 markdown/純文字） - OpenAPI 全集 / 完整 ERD / domain-model 全集 |
| **假設與依賴** | **假設**: pilot 客戶能提供真實 FAQ/SOP + 真實 LINE 官方帳號 ｜ **Upstream 依賴**: 一位真實簽下的 Synergy 教練（OQ-002 硬閘門） ｜ **External**: Claude API（草稿生成）、LINE Messaging API（通道，W2） ｜ **Stack**: Python 單體（FastAPI + nanobot）+ Postgres/pgvector + 單台 VM |

> **Out of Scope 不可空**：以上做了就是 scope creep，違反最薄切片原則（`foundation/02-mvg-build-sheet` §7）。

---

## 5. 待辦問題與決策

| ID | 描述 | 狀態 | 負責人 |
| :--- | :--- | :--- | :--- |
| D-0001 | OQ-001：K1 = 草稿原樣 approve ≥ 50%、總採用 ≥ 70%；W1 前簽字鎖死（門檻是事前承諾，防事後合理化） | 已決定（Elon-lens 2026-05-28） | CEO |
| D-0002 | OQ-003：W1 不做審核 UI（eval-only 即可打 B1）；W2 真流量才做「最笨一張 web 列表頁」 | 已決定 | CEO |
| D-0003 | OQ-004：不碰動態查詢（訂單/庫存）；草稿需要時標「需人工查詢」（B1 賭的是知識非動態資料） | 已決定 | CEO |
| D-0004 | OQ-002：驗證載具 = Care Copilot 的 Synergy 教練 design-partner pilot；`ai-cs-mvg` = AEOS 核心，care-copilot = 第一個垂直 pack | 已決定 | CEO |
| Q-0001 | OQ-002 剩餘硬閘門：需**一位真實簽下的 Synergy 教練**提供真知識 + 真對話樣本（8 週內簽到 ≥ 1 pilot）。屬市場賭注非技術。 | 待裁決（市場閘門） | CEO / GTM owner |
| Q-0002 | OQ-NFR-1：expert 審核台 WCAG 等級（pilot 內部工具是否需 AA？）→ 暫釘 WCAG 2.1 AA，GA 前確認 | 待裁決 | UX + CEO |

### 已升級為 ADR 的決策（Decision Log）

| ID | Type | Topic | Status |
| :--- | :--- | :--- | :--- |
| ADR-0001 | ADR | nanobot Frozen Runtime（學習/生產分離 + 治理包覆） | Proposed |
| ADR-0002 | ADR | Vertical Pack 可插拔抽象 | Proposed |
| ADR-0003 | ADR | 結構化 contact（活檔案）納知識模型 | Proposed |
| ADR-0004 | ADR | 知識 ingestion 治理管線（8 階段） | Proposed |
| — | — | 單體 vs 微服務（切片明確選單體） | 見 feasibility §4 / ADR-0001 anti-scope |

---

## 6. 風險登記（Risks）

| ID | Risk | Severity | Mitigation |
| :--- | :--- | :--- | :--- |
| RISK-001 | B1 死：草稿採用率 < 40%，調 3 輪仍上不去 | 🔴 high | W1 先用 eval 對測試集早驗；採用率崩即 Kill，不續寫 |
| RISK-002 | 8 週簽不到任何願給真知識的 pilot | 🔴 high | 依 PILOT-ICP 名單，W0 先簽 + 簽 DPA |
| RISK-003 | 知識品質差導致草稿幻覺 | 🟡 medium | ingest 品質檢查 + 缺依據標 `[需人工]` + expert 回流標註 |
| RISK-004 | 客戶個資外洩 | 🟡 medium | 驗簽 / 傳輸加密 / secrets 不進 git / tenant scope / 先簽 DPA |

> 殺死條件完整定義見 `docs/foundation/03-validation-and-kill.md`；W6 Go/Kill 預先承諾現在簽、W6 不准賴。

---

## 7. Release Plan

| 項目 | 說明 |
| :--- | :--- |
| **Rollout strategy** | 對 1 個 pilot 直接上 Draft Mode（人類審每一則 = human-in-loop，無需 canary，單 pilot 規模） |
| **Timeline** | W0 簽 pilot+DPA · W1 eval 打 B1 · W2–3 全鏈路跑通 · W4–6 量採用率 · W6 Go/Kill |
| **Observability** | stdout log + 草稿採用率（簡單列表，不上完整 stack） |
| **Rollback trigger / owner** | 採用率崩 / 出事 → Kill switch 30 秒全停；owner = CEO（唯一 oncall） |

---

## 8. Sign-off

> Gate 1 PRD Freeze 需業主明確簽核。

- [ ] **PM** (owner): ____________ / Date: ____________
- [ ] **Stakeholder**: ____________ / Date: ____________
- [ ] **Review verdict**: ✅ ready / ⚠️ revise / ❌ blocked

---

## 變更紀錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v1.0 | 2026-05-29 | 依 VibeCoding 模板 02 從 `docs/prd/ai-cs-mvg.md`（frozen v1，含 R2/R3 修正）實例化；Epic/US 編號為下游 BDD/WBS 追蹤基準 |
