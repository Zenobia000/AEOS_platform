# PRD — AI 客服 MVG（Draft Mode 草稿模式）

> **📋 Status**: draft
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: PM
> **🔖 Version**: v1
> **🔗 Related**: docs/foundation/00~03 · ADR-0001(Frozen Runtime) · [[06_quality_attributes_catalog]] · [[11_data_and_stack_catalog]]

---

> [!NOTE]
> **命名與 source-of-truth（收 docs-gap-audit N1/N2）**:
> - **`ai-cs-mvg`** = 本 PRD 代號 = AEOS **核心切片**的 B1 賭注（eval-only 北極星 = 草稿原樣 approve 率）。**這份是 freeze 賭注。**
> - **`care-copilot`** = 對外**垂直產品名**（pack #1）;下游文件（spec/ux/arch/api/data/qa/ops）一律用此名。
> - **`foundation/pilot_run.md`** = 垂直**商品全集**（Phase I 11 工具 superset）= 願景參考,**非本次 freeze scope**。三者同一賭注、同一 B1，scope 大小不同。

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: 把一個 pilot 客戶的混亂 FAQ/SOP，在 7 天內變成一位在 LINE 上產生「草稿回覆」的 AI 客服——人類審每一則、approve 才送出。我們只賭一件事、只盯一個數字：**草稿原樣 approve 率**。最大爭議：採用率夠不夠高到證明「混亂知識能變可用員工」。

| 維度 | 摘要 |
|:---|:---|
| **🎯 目標** | 用最薄切片證明核心賭注 B1：真實混亂知識能在數天內變成可被採用的客服草稿 |
| **👥 主要 persona** | pilot 客戶的客服專家／主管（審草稿），規模：1 租戶、數名 expert |
| **📊 主要 KPI** | 草稿原樣 approve 率 ≥ 50%（且總採用率 ≥ 70%） |
| **🚀 狀態** | 🟢 OQ-001/003/004 已裁決（Elon-lens）；devteam 流水線**刻意停在 PRD**，不跑後續 6 phase（避免重製文件白癡指數），直接進寫切片模式 |
| **🎯 下一步** | ① 機器：依 `foundation/02` 建 `aeos-mvg/` W1 路徑（ingest+draft+eval）② 業主：簽 pilot（OQ-002）取得真知識+真 LINE，機器就緒即打 B1 |

---

## 🎯 Problem Statement

- **現況**: 一線客服缺工、流動率高、新人 1~3 個月才上手；企業的 FAQ/SOP 散亂，沒人能快速把它變成可用的客服回答。
- **為什麼值得解**: 若「混亂知識 → 可用客服草稿」這條轉換成立，企業能用 1/10 成本擴充工時容量、24/7 不停班。這是整個 AI 員工工廠願景的第一塊基石（見 `foundation/00-the-bet`）。
- **不解的成本**: 賭注無法被證明，整個工廠願景停在 PPT；對 pilot 客戶而言，缺工與訓練成本持續燒。

---

## 📊 Goals & Success Metrics

| 類別 | 目標 | 量化指標 | 觀測週期 |
|:---|:---|:---|:---|
| **Business Goal** | 證明 B1（混亂知識可量產為可用客服員工）並簽到第一個付費意願 pilot | 8 週內 ≥ 1 家 pilot 真實跑通 | 一次性 |
| **User Goal**（expert） | 草稿好用到「審比自己寫快」 | 每則省時 ≥ 50% | weekly |
| **KPI K1（北極星）** | 草稿原樣 approve 率 | ≥ 50% | weekly（pilot ≥ 2 週穩定讀數） |
| **KPI K2** | 草稿總採用率（approve + edit-and-send） | ≥ 70% | weekly |
| **KPI K3** | 知識可用性（測試集 50 題 pass rate） | ≥ 70% W1、≥ 80% pilot 末 | W1 起 |
| **KPI K4** | 單租戶毛利 | ≥ 50% | monthly |
| **Counter-metric C1** | expert reject 率（超過代表治理在「救火」不是「審核」） | ≤ 30% | weekly |
| **Counter-metric C2** | 未經人類 approve 的自動發訊 | = 0（Draft Mode 鐵律保證） | 持續 |

> [!IMPORTANT]
> 只盯一個北極星數字 **K1 草稿原樣 approve 率**，其餘是它的輔助診斷。不要被六個數字分心。

---

## 👥 Users & Scenarios

- **Primary Persona**: pilot 客戶的客服專家／主管。脈絡：手上有散亂 FAQ/SOP，每天回大量重複問題；要的是「AI 先擬好、我快速確認」。規模：1 租戶、數名 expert。
- **Secondary Persona**: 真實終端客戶（透過 LINE 發問，不知背後是 AI 草稿）。
- **Key Scenario**（主任務流）:
  1. expert 貼上一份真實 FAQ/SOP（markdown）→ 系統建索引
  2. 客戶在 LINE 問問題 → 系統檢索知識 → 產生草稿回覆 → 通知 expert
  3. expert approve / edit / reject；approve 後回覆送回客戶；全程進稽核
- **Edge Cases**:
  - 知識缺漏（檢索不到相關內容）→ 草稿須標「無足夠依據，建議人工」，不可硬掰
  - 客戶問動態資料（訂單狀態／庫存）→ 切片不接系統，草稿標「需人工查詢」
  - 訊息含敏感個資 / 惡意注入 → 不外洩、不被指令綁架（紅隊邊界，P1 深化）

---

## 🎯 Scope

### ✅ In Scope
- LINE 單一通道（webhook 收訊 + approve 後回發）
- 知識 ingest：貼上 markdown / 純文字 → 建索引
- 檢索 + Claude 產生草稿回覆
- Draft Mode 人類審核（approve / edit / reject）
- 全鏈路稽核（每則記：用了哪些知識 + 哪個 model + 人類決定）
- Kill switch（30 秒內全停）
- Eval：對測試集跑 pass rate
- 單一 pilot 租戶

### ❌ Out of Scope

> [!WARNING]
> Out of Scope 不可空。以下做了就是 scope creep，違反最薄切片原則（見 `foundation/02-mvg-build-sheet` §7）。

- 自動發訊（canary 流量分配、信心閾值自動 fallback）— 切片永遠停在 Draft Mode
- Web chat / 多通道、多語言
- 多租戶 / 跨租戶
- 訂單寫入（只查不寫；動態查詢本切片不接）
- Skill registry / 多 skill / 版本化 UI
- Email digest / Eval Dashboard / 主動推送
- 微服務拆分、agent framework、K8s、完整 observability stack
- PDF / DOCX / URL 自動解析（只收貼上的 markdown/純文字）
- OpenAPI / 完整 ERD / domain-model 全集

---

## 🔗 User Flow Links

| Asset | Location |
|:---|:---|
| Journey | [`docs/ux/user-flow-care-copilot.md`](../ux/user-flow-care-copilot.md)（P1 產出） |
| Wireframe | TBD（expert 審核台，P1） |

---

## 📋 Functional Requirements

| ID | Description | Acceptance Criteria | Priority |
|:---|:---|:---|:---:|
| FR-001 | 知識 ingest：貼上 markdown → 切塊 → 建立可檢索索引 | 貼一份真知識後，對相關問題能檢索回正確片段 | P0 |
| FR-002 | 草稿生成：檢索 + Claude 產生回覆草稿 | 對測試集 50 題產草稿，pass rate ≥ 70%（W1） | P0 |
| FR-003 | LINE 收訊：webhook 接收並驗證來源後存檔 | 真實 LINE 訊息入庫；來源驗簽失敗則拒絕 | P0 |
| FR-004 | Draft Mode 審核：expert approve / edit / reject，approve 後回發 LINE | 三種決定皆可操作；approve 後客戶收到回覆 | P0 |
| FR-005 | 稽核：每則訊息記錄知識來源 + model + 人類決定 + 決定者 | 任一對話可完整還原上述四項 | P0 |
| FR-006 | Kill switch：單一開關全停 | 實測 30 秒內全面停止產草稿與回發 | P0 |
| FR-007 | Eval：對測試集跑 pass rate | 一個指令對 testset 印出 pass rate | P0 |

> [QA 視角] FR-002 / FR-007 的測試集即 Gate 6 的量尺；測試案例與 exit criteria 於 P4 補。

---

## 🛡 Non-Functional Requirements

| Dimension | Requirement | Target | Reference |
|:---|:---|:---|:---|
| **⚡ Performance** | 草稿生成（非即時自動發，人類審） | p95 < 5s | [[06_quality_attributes_catalog]] §1 |
| **🔁 Reliability** | pilot 期單台 VM，best-effort | 無正式 SLO；killswitch 保底 | [[06_quality_attributes_catalog]] §2 |
| **🔒 Security / 資料分級** | 客戶對話含個資（聯絡資訊／對話內容） | 來源驗簽 + secrets 不進 git + 傳輸加密 + tenant_id 強制 scope | [[11_data_and_stack_catalog]] §1 §2 |
| **📜 Auditability** | 每則訊息全稽核、可還原 | 保留期依 DPA（baseline 90 天） | — |
| **🧊 學習/生產分離** | 上線配置（prompt + 知識快照）凍結；回饋資料離線改版 | AI 不得線上即時學習改變行為（Frozen Runtime） | `foundation/01` · ADR-0001 |
| **💰 Cost** | 單租戶 LLM 用量上限 | ≤ $300/月（毛利護欄） | — |

> [Architect 視角] 學習/生產分離與 tenant_id scope 是身份級鐵律，即使單租戶也要寫對，否則多租戶階段需重構。對應未來 ADR（Frozen Runtime）。

---

## 🔌 Dependencies

| Type | Detail |
|:---|:---|
| **Upstream** | pilot 客戶提供真實 FAQ/SOP + 真實 LINE 官方帳號 |
| **Downstream** | 無（切片是端到端單體，下游 phase 才拆） |
| **External systems** | Claude API（草稿生成）、LINE Messaging API（通道） |
| **Data / API** | 輸入：客戶知識文件 + LINE 訊息；輸出：草稿 / 回發訊息 |
| **Stack constraint** | Python 單體服務 + Postgres/pgvector + 單台 VM（見 `foundation/02` §4） |

---

## ⚠️ Risks & Open Questions

> [!IMPORTANT]
> 這是業主主要決策區。殺死條件見 `foundation/03-validation-and-kill`。

### Risks

| ID | Risk | Severity | Mitigation |
|:---|:---|:---:|:---|
| R-001 | B1 死：草稿採用率 < 40%，調 3 輪仍上不去 | 🔴 high | W1 先用 eval 對測試集早驗；採用率崩即 Kill，不續寫 |
| R-002 | 8 週簽不到任何願給真知識的 pilot | 🔴 high | 依 PILOT-ICP 名單，W0 先簽 + 簽 DPA |
| R-003 | 知識品質差導致草稿幻覺 | 🟡 medium | ingest 品質檢查 + 缺依據時草稿標「需人工」 + expert 回流標註 |
| R-004 | 客戶個資外洩 | 🟡 medium | 驗簽 / 傳輸加密 / secrets 不進 git / tenant scope / 先簽 DPA |

### ✅ Resolved Decisions（Elon-lens，2026-05-28）

| ID | 裁決 | 理由（Elon 心智模型） |
|:---|:---|:---|
| **OQ-001** | **確認 K1 = 草稿原樣 approve ≥ 50%、總採用 ≥ 70%；W1 前簽字鎖死** | 門檻的功能是事前承諾防止事後合理化；糾結確切數值是優化不該花時間的東西。重點是「鎖死」不是「最佳化數字」 |
| **OQ-003** | **W1 不做審核 UI（eval-only 即可打 B1）；W2 真流量才做「最笨的一張 web 列表頁」** | best part is no part：W1 用 eval.py + 測試集就能打最致命賭注，UI 是 W2 才需要的零件。LINE 內審看似聰明實則更多工（互動 flow + 長文編輯痛），故選最笨 web |
| **OQ-004** | **不碰動態查詢（訂單/庫存）；草稿需要時標「需人工查詢」** | B1 賭的是「混亂**知識**→可用草稿」，訂單是**動態資料**（API 整合），證明不了 B1 卻要每 pilot 接一套系統。質疑笨需求→刪除 |

### ✅ OQ-002 已裁決（2026-05-28）

**驗證載具 = Care Copilot 的 Synergy 教練 design-partner pilot**（見 `docs/foundation/pilot_run.md`、`docs/architecture/feasibility-AEOS-x-care-copilot.md`）。

- B1（混亂知識 → 可用草稿）透過 Care Copilot **最薄切片**（訊息草稿 + 合規低語 + 活檔案）對一位 Synergy 教練的**真實客戶關係資料**驗證。
- **ai-cs-mvg = 此驗證的 AEOS 核心**；Care Copilot = 第一個垂直（vertical pack）。兩者至此對齊：同一個賭注、同一個 B1、同一個北極星數字（原樣 approve 率）。
- `aeos-mvg/data/` 範例已是精油直銷主題，方向一致。

> **剩餘硬閘門（仍未決，屬市場賭注非技術）**：需**一位真實簽下的 Synergy 教練**提供真知識 + 真對話樣本（foundation/03「8 週內簽到 ≥ 1 pilot」）。拿到真資料前，範例資料只證明產線會轉，證不了 B1。

---

## 🚀 Release Plan

| 項目 | 說明 |
|:---|:---|
| **Rollout strategy** | 對 1 個 pilot 直接上 Draft Mode（人類審每一則，等同 human-in-loop，無需 canary — 見 [[10_resilience_patterns]] §3.1，單 pilot 規模） |
| **Timeline** | W0 簽 pilot+DPA · W1 eval 打 B1 · W2–3 全鏈路跑通 · W4–6 量採用率 · W6 Go/Kill |
| **Observability** | stdout log + 草稿採用率（簡單列表，不上完整 stack） |
| **Rollback trigger** | 採用率崩 / 出事 → Kill switch 30 秒全停 |
| **Rollback owner** | CEO / 唯一 oncall |

---

## 📝 Decision Log

> list ADR / DR，完整內容在 `docs/architecture/`。

| ID | Type | Topic | Status |
|:---|:---|:---|:---:|
| ADR-0001 | ADR | nanobot Frozen Runtime（學習/生產分離 + 治理包覆） | ✅ Proposed |
| ADR-0002 | ADR | Vertical Pack 可插拔抽象 | ✅ Proposed |
| ADR-0003 | ADR | 結構化 contact（活檔案）納知識模型 | ✅ Proposed |
| ADR-0004 | ADR | 知識 ingestion 治理管線 | ✅ Proposed |
| — | — | 單體 vs 微服務（切片明確選單體） | 見 feasibility §4 / ADR-0001 anti-scope |

---

## 🔗 Cross References

- **Foundation（理念地基）**: [`docs/foundation/00-the-bet.md`](../foundation/00-the-bet.md) · [`02-mvg-build-sheet.md`](../foundation/02-mvg-build-sheet.md) · [`03-validation-and-kill.md`](../foundation/03-validation-and-kill.md)
- **Stakeholder map**: [`docs/governance/stakeholders.md`](../governance/stakeholders.md)
- **User flow**（downstream）: [`docs/ux/user-flow-care-copilot.md`](../ux/user-flow-care-copilot.md)
- **KB catalog refs**: [[06_quality_attributes_catalog]] · [[10_resilience_patterns]] · [[11_data_and_stack_catalog]]

---

## ✍️ Sign-off

> [!IMPORTANT]
> Gate 1 PRD Freeze 需業主明確簽核。

- [ ] **PM** (owner): ____________ / Date: ____________
- [ ] **Stakeholder**: ____________ / Date: ____________
- [ ] **Review verdict**（from `reviews/Gate1_PRD-ai-cs-mvg-{date}.md`）: ✅ ready / ⚠️ revise / ❌ blocked

---

**End of PRD**

---

## Review 修正 R2（2026-05-28 multi-role review）

- **B-2 baseline**：W0 量「無 AI 時 expert 自寫」的 approve 對照與每則耗時，作 K1/K3 對照組（避免 50% 其實是退步）。
- **B-2 付費 KPI**：補 business KPI「pilot 末願付費簽約 ≥ 1」（OQ-002 簽 pilot 是入場券，非成功本身）。
- **B-3 客戶側 counter-metric**：補一個終端客戶側指標（重問率 / 投訴）— expert approve ≠ 客戶滿意。
- **S-1 scope 一致化**：FR-003「LINE webhook 自動收訊」與切片「草稿+手動貼 LINE」不一致 → **pilot 切片 FR-003 改為手動入口（貼上/截圖）**，LINE webhook 排 W2+。
- **Decision Log**：ADR-TBD → 已落地 **ADR-0001**（nanobot Frozen Runtime）；單體決策見 feasibility §4 / ADR-0001 anti-scope。

> 給業主：主要看 **Executive Summary + Goals & KPI + Risks & Open Questions + Sign-off** 四段。其餘是給下游 phase（analyst / ux / arch）的輸入。
