# ADR-0001: 採 nanobot 為 Frozen Runtime 底層 + AEOS 治理包覆

> **檔名:** `ADR-0001-adopt-nanobot-frozen-runtime.md`
> **狀態:** 提議中 | **日期:** 2026-05-28 | **決策者:** devteam-arch
> **負責人:** TL | **審核:** ARCH | **追蹤:** feasibility §4（上游觸發者）
> **取代:** — | **被取代:** —
> **來源:** `docs/architecture/adr/ADR-0001-nanobot-frozen-runtime.md`

---

## 1. 背景與問題

- **上下文**: feasibility spike（`docs/architecture/feasibility-AEOS-x-care-copilot.md` §4）確認 MCP/plugin 整合外部系統需要 agentic（tool-calling 編排、多步取數、錯誤重試），且業主硬要求**底層全 Python**。AEOS 設計與 Care Copilot 後端皆 Python(FastAPI)。
- **問題**: 需要一個 Python 的 agent runtime 底層；既有 legacy 決策已規定 Frozen Runtime（學習/生產分離）與多租戶隔離，blast radius 須限縮在單一 tenant，MCP 工具呼叫須過 Policy + Audit。
- **驅動因素/約束**:
  - 與 Python 底層一致（降跨語言 coupling）— high
  - 原生 agentic + MCP（整合外部系統）— high
  - 可被 AEOS 凍結 + 多租戶包覆（blast radius）— high
  - Time-to-market（現成 vs 自建）— high
  - 多模型 + prompt caching（成本）— medium

## 2. 考量的選項

### 選項一: nanobot（Python）+ AEOS 治理包覆

- **描述**: 採 HKUDS/nanobot（Python ≥3.11，MIT）小核心 agent loop + 原生多 MCP，外加 AEOS 三層治理包覆。
- **優點**: Python 同語言零跨語言 coupling；原生多 MCP server/SSE/auth；原生 openai+anthropic+fallback + prompt caching；內建 cron/schedules；即 `02 §4.4.2` 既選「nanobot 類」的具體實作。
- **缺點**: 預設個人單租戶 + 可自我擴展 → 必須包覆凍結；上游活躍開發需釘版本。
- **成本/複雜度**: 中（包覆層）

### 選項二: pi（earendil-works, TypeScript）

- **描述**: 成熟的 coding agent harness。
- **優點**: agentic 強。
- **缺點**: TS 與 Python 底層分裂（跨語言 coupling）；偏 coding agent（對映 `02 §4.3` 反模式）。
- **成本/複雜度**: 中 + 雙語維運負擔

### 選項三: 自建 Python agent runtime

- **優點**: 完全可控。
- **缺點**: 重造 agent loop/MCP/多模型/快取，time-to-market 差；違反 foundation「驗證前不過度建設」。
- **成本/複雜度**: 高

### 選項四: LangGraph（Care Copilot PRD §5 原方案）

- **優點**: 成熟編排。
- **缺點**: 偏 workflow 編排，MCP/channel/memory/排程需另接；與「小核心 Frozen Runtime」定位不貼。
- **成本/複雜度**: 中

## 3. 決策

**選擇**: 選項一 — nanobot（Python）+ AEOS 治理包覆。

**理由**: Python 同語言消除跨語言 coupling（拒選項二）；現成 agentic+MCP+多模型+排程使 time-to-market 遠優於自建（拒選項三）；nanobot「小核心 agent loop」比 LangGraph workflow 編排更貼 Frozen Runtime 定位（拒選項四）。最關鍵：這是既有架構選型的落地，非新賭。接受的 trade-off = 必須自建治理包覆層，這層正是 AEOS 護城河。

**AEOS 必加三層治理包覆（boundary）**：
1. **Frozen Runtime**：生產關閉自我擴展（自裝 skill / 自改 prompt / 自由載入任意 MCP）；配置凍結快照，回饋走離線。
2. **多租戶隔離**：每位直銷商一個受隔離 runtime context + RLS；blast radius 限單一 tenant。
3. **Tool Gateway + Policy 前置**：MCP 工具呼叫前過 Policy Engine + Audit；外部系統憑證不入 nanobot。

- **✅ 適用範圍**: AI 員工 agent runtime 底層（員工執行體、MCP 工具整合）。
- **❌ 不適用**: 裸用 nanobot 跑生產；單次 LLM/規則類工具（情緒/合規）直呼 LLM 即可。

## 4. 後果

- **正面**: 零跨語言 coupling；agentic MCP/多模型/排程/prompt caching 現成 → time-to-market 短；兌現既有架構選型，決策連貫。
- **負面**: nanobot 預設「個人單租戶 + 可自我擴展」與 AEOS「多租戶 + Frozen」相反 → **必須**先建包覆層（mitigation：列為 design driver P0）；上游活躍開發 → 釘版本 + 包覆而非 fork；nanobot 未內建 LINE channel（mitigation：pilot 是「草稿+手動貼 LINE」，不需 LINE API）。
- **影響範圍**: `05 架構與設計`（runtime container = nanobot + 包覆）、`14 部署與運維`（nanobot 部署/版本/凍結流程）。
- **可逆性 / 重新評估觸發**: 半可逆（包覆而非 fork，底層可替換，但牽動 design/ops）；nanobot 上游 breaking change 或 tenant > 5 時重新評估。

## 5. 執行計畫

1. design driver 定義治理包覆介面（凍結 / 租戶 / Policy hook）— P3
2. 釐清哪些工具走 agent loop vs 直呼 LLM — P3（feasibility §4）
3. ops 定 nanobot runtime 部署 + 版本釘選 — P5

> **legacy 依賴內聯**（被依賴的 legacy 決策已退役至 git history，內聯重述視為本 ADR 一部分）：
> - Frozen Runtime（原 legacy ADR-0002）：上線配置（prompt+知識快照）凍結；生產不可自我學習改行為；回饋走離線改版。
> - Tenant Isolation（原 legacy ADR-0007）：RLS + 應用層雙重；跨租戶預設 deny；blast radius 限單 tenant。

---

| 日期 | 審核人 | 備註 |
| :--- | :--- | :--- |
| 2026-05-28 | ARCH | R2 補 legacy 依賴鏈內聯重述（B-6） |
