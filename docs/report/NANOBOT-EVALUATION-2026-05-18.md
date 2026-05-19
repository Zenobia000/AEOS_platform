---
id: REPORT-NANOBOT-EVALUATION
title: nanobot (HKUDS) 評估 — 作為 AEOS Employee Runtime 基底
date: 2026-05-18
owner: CTO
type: one-shot evaluation report
related: [ADR-0001, ADR-0002, ADR-0011, ADR-0012, engineering-charter, MC-002, MC-005, MC-009, NANOBOT-EVALUATION, PI-EVALUATION-2026-05-18]
subject:
  repo: https://github.com/HKUDS/nanobot
  local_path: nanobot/
  pypi: nanobot-ai
  version_evaluated: v0.2.0 (2026-05-15)
  license: MIT (Xubin Ren + nanobot contributors)
---

# nanobot 評估報告 — 適合作為設計借鑑，建議「借鑑 + 自寫」而非「fork + wrap 整套」

> **TL;DR**：nanobot 與 AEOS 的對齊度遠高於 pi（✅ 9 / 🟡 2 / ❌ 5）。但發現 ADR-0002 對 nanobot 的事實描述錯誤（寫成 TypeScript，實為 Python），且 v0.2.0 仍 alpha 每週改動巨大。**建議走「借鑑設計觀念 + 自寫精簡版 AEOS Employee Runtime」路線**，不直接 vendor 整套。本報告觸發 **ADR-0012** 對 ADR-0002 補 erratum + 策略修正。

---

## 1. 摘要結論

### 1.1 對齊度評估（與 pi 對照）

| 維度 | nanobot | pi |
|---|---|---|
| ✅ 完全符合 | 9 | 1 |
| 🟢 觀念可借鑑 | (合併到 ✅) | 3 |
| 🟡 部分 / 需自寫 | 2 | 2 |
| ❌ 不符合 | 5 | 7 |

nanobot 是更現實的 Phase 1 Employee Runtime 來源。

### 1.2 推薦走向

**「借鑑 + 自寫」**（B 路徑）：
- 不 fork 整個 nanobot codebase（避免被 v0.2.0 alpha 每週改動拖累）
- 不 `pip install nanobot-ai` 當 dep（避免拉進 17 個 channel + Dream + cron + WebUI 大量未用 code）
- **讀 `nanobot/nanobot/agent/{loop.py, runner.py, hook.py}` 三檔，借鑑設計觀念**，自寫 AEOS 精簡版 `EmployeeRuntime`（預估 200-300 行 Python）

### 1.3 關鍵發現

1. **ADR-0002 事實錯誤**：寫「nanobot：TypeScript/Node 輕量 runtime」與真實情況不符 — 實際是 Python 3.11+
2. **Dream skill discovery 是「半 frozen」**：可動態建立 skill `.md` 檔，但**不會自動熱載入 ToolRegistry**（需重啟）— 對 AEOS 反而是優點
3. **無 LINE channel**（17 個內建 channel 沒有 LINE） — 需自寫，中等工作量（~700 行，參考 Telegram 實作）
4. **MCP 客戶端內建**（`mcp>=1.26.0` dep）— 是 Anthropic 標準工具協議，未來 AEOS Tool Registry 可整合
5. **MIT + 無 GPL 依賴**（THIRD_PARTY_NOTICES 只列 KaTeX fonts SIL OFL）— 商業可用

---

## 2. nanobot 是什麼（架構速覽）

來源：`nanobot/README.md`、`nanobot/pyproject.toml`、`nanobot/CLAUDE.md`、`nanobot/nanobot/agent/`

### 2.1 基本識別

| 項目 | 值 |
|---|---|
| 開發組織 | HKUDS（HKU Data Science Lab） |
| 主作者 | Xubin Ren |
| License | MIT |
| PyPI 套件 | `nanobot-ai` |
| 當前版本 | v0.2.0（2026-05-15） |
| Python 版本 | ≥ 3.11 |
| 倉庫地址 | https://github.com/HKUDS/nanobot |

### 2.2 核心架構（Python 後端）

```
MessageBus (asyncio in-memory)
   ↑↓
Channels (17 個：Telegram/Discord/Slack/Feishu/Matrix/WhatsApp/QQ/WeChat/WeCom/DingTalk/Email/MoChat/MS Teams/WebSocket + 變體)
   ↕
AgentLoop (狀態機: RESTORE→COMPACT→COMMAND→BUILD→RUN→SAVE→RESPOND→DONE)
   ↕
AgentRunner (LLM 對話迴圈 + tool execution + streaming)
   ↕
LLMProvider (Anthropic / OpenAI / Azure / Bedrock / DeepSeek / Kimi / MiMo / GLM / OpenRouter / Ollama / vLLM / GitHub Copilot / Codex)
```

### 2.3 設計特徵

- **狀態機切分清晰**：AgentLoop 管會話狀態與 hook 協調；AgentRunner 純執行 LLM 對話迴圈
- **Hook 機制**：`AgentHook` ABC + `CompositeHook` 串接，支援 `before_iteration`, `after_iteration`, `on_stream`, `emit_reasoning`
- **Tool registry**：**靜態註冊**（啟動時 `register()`），無 hot-reload — 比 pi 接近 Frozen Runtime
- **Session 儲存**：JSONL → `~/.nanobot/sessions/<key>.json`，無 DB
- **Dream skill discovery**：兩階段 LLM 流程（Phase 1 分析、Phase 2 代理執行 `read_file`/`edit_file` 自動建立 `~/.nanobot/skills/<name>/SKILL.md`），但**不會自動熱載入**
- **MCP 內建為 client**：可連接遠端 MCP server，將其工具包裝為 `MCPToolWrapper` 再 register

### 2.4 部署

- 單一 Dockerfile（Python 3.12 uv），含 Node.js 給 WhatsApp bridge
- Gateway 單 asyncio event loop（gateway:18790 + optional api:8900）
- `NANOBOT_MAX_CONCURRENT_REQUESTS` env 限制並行
- WebUI bundle 進 Python wheel（v0.2.0 起）

---

## 3. AEOS 對 Employee Runtime 的需求（對照清單）

來源同 PI 評估報告 §3，重點要點：

- ADR-0001 LLMClient：Anthropic 主，薄層 abstraction
- ADR-0002 Runtime：選 nanobot（事實描述待修，見本報告觸發 ADR-0012）
- ADR-0007 Multi-tenant：共享 PG + RLS + 應用層雙重檢查
- ADR-0011 Backend：Python 3.12 + FastAPI + pydantic v2
- MC-001 Audit：append-only PG + 90d PII 脫敏
- MC-002 Training Room：sandbox + 7 層 quality gate + red team + expert review
- MC-005 Skill Registry：git monorepo + YAML + atomic symlink swap + 5 態 lifecycle + pass rate ≥ 0.80
- MC-006 Tool Registry：YAML 3 級風險 policy + 同步 gateway
- MC-009 Employee Runtime：Frozen Runtime snapshot + 單次 LLM call + RAG top-K=5 + output validation
- QUOTA-001：5 層 rate limit + 3 級降級

---

## 4. 16 維對照矩陣

| # | 維度 | nanobot | AEOS 需求 | 對齊度 |
|---|---|---|---|---|
| 1 | 語言 | Python 3.11+ | Python 3.12（ADR-0011）| ✅ |
| 2 | LLM SDK | `anthropic`, `openai` 內建 dep | Anthropic 主（ADR-0001）| ✅ |
| 3 | Stack | `pydantic v2 + httpx + asyncio + loguru` | 與 AEOS scaffold 同 | ✅ |
| 4 | License | MIT；無 GPL deps（THIRD_PARTY 只 KaTeX fonts）| 商業可用 | ✅ |
| 5 | Agent loop 設計 | AgentLoop（狀態機）+ AgentRunner（LLM 對話）切分 | MC-009 單次 LLM call + RAG + validation | ✅ |
| 6 | Hook 機制 | `before/after_iteration` + `on_stream` + `CompositeHook` | Governance Layer 攔截點 | ✅ |
| 7 | Tool registry | 靜態註冊；無 hot-reload；新 tool 要重啟才生效 | Frozen Runtime（charter 原則 2）| ✅ |
| 8 | Provider 抽象 | `LLMProvider` ABC + `chat()` + `chat_stream_with_retry()` + 結構化錯誤 | ADR-0001 LLMClient | ✅ |
| 9 | MCP 整合 | 內建 client（`mcp>=1.26.0`） | 未來 Tool Registry 可整合 | ✅ |
| 10 | 容器化 | Dockerfile + docker-compose 已就緒 | per-tenant Docker | ✅ |
| 11 | MessageBus + Worker | 內存 asyncio bus | SAD-v0.1 §3 Worker pattern | 🟡 部分 |
| 12 | Channel 抽象 | 17 channel 但無 LINE；繼承 `Channel` 基類自寫 | Phase 1 唯一 channel | 🟡 自寫 |
| 13 | Multi-tenant | 無（per-workspace `~/.nanobot`） | RLS + 應用層雙重檢查（ADR-0007）| ❌ |
| 14 | Audit log | loguru only（含 tool event metadata） | append-only PG（MC-001）| ❌ |
| 15 | Policy engine | `restrict_to_workspace` + SSRF + workspace violation 限流 | YAML 3 級風險（MC-006）| ❌ |
| 16 | Cost / quota | 仰賴 provider 配額；無全域 rate limit | 5 層 rate limit（QUOTA-001）| ❌ |
| 17 | Storage | 檔案系統 JSON；無 DB 介面抽象 | PostgreSQL + pgvector | ❌ |
| 18 | Training Room / Quality Gate | Dream skill discovery 但無熱載；無 quality gate | MC-002 sandbox + 7 層 gate | ❌ |

**統計**：✅ 10 / 🟡 2 / ❌ 6（其中 16-18 是「不缺即可」，AEOS 本來就要自己加上層；對 nanobot 本身評估不算扣分）。

---

## 5. 5 項符合 AEOS 的優勢

### 5.1 語言 + Stack 完美吻合

nanobot 是 Python 3.11+，依賴 `anthropic` / `openai` / `pydantic` / `httpx` / `asyncio` / `loguru` — 與 AEOS S1 scaffold 同 stack。直接借鑑無語言重寫成本。

### 5.2 AgentLoop / AgentRunner 切分清晰

```
AgentLoop（位置：nanobot/agent/loop.py:122）
├── 狀態機: RESTORE → COMPACT → COMMAND → BUILD → RUN → SAVE → RESPOND → DONE
├── 管會話 (Session) 與 hook 協調
└── 不直接呼叫 LLM

AgentRunner（位置：nanobot/agent/runner.py:112）
├── 純執行層，無會話知識
├── LLM 對話迴圈（多輪 tool call）
├── streaming
└── 重試邏輯（瞬態 vs 永久錯誤分類）
```

對 AEOS MC-009 Employee Runtime：這個切分是「Frozen Runtime snapshot + 單次 LLM call」的天然對應。AgentLoop = Runtime snapshot，AgentRunner = 單次 LLM call。

### 5.3 Hook 機制是 Governance Layer 攔截點

`AgentHook` ABC 提供 `before_iteration`, `after_iteration`, `on_stream`, `emit_reasoning`，可串聯 `CompositeHook`。

對 AEOS：把 MC-001 audit + MC-006 policy + QUOTA-001 cost tracking 三個 governance 全部寫成 hook，註冊進 `CompositeHook`。

### 5.4 Tool registry 靜態註冊 = Frozen Runtime 友好

啟動時 `register()` 進 `ToolRegistry`（內存字典）；新 tool 要重啟。

對 AEOS：與 engineering-charter 原則 2 完美吻合。Skill 上線必須走 git → atomic symlink swap → 重啟 worker，本來就符合「重啟才生效」模式。

### 5.5 Provider 抽象 + 結構化錯誤

`LLMProvider.chat()` + `chat_stream_with_retry()` + 結構化 `error_status_code` / `error_kind` / `error_type`。對 AEOS：ADR-0001 LLMClient interface 可直接借鑑這個設計，包含 retry policy 與 error taxonomy。

---

## 6. 5 項 AEOS 必須自寫的上層

### 6.1 Multi-tenant 隔離

- **nanobot 現狀**：per-workspace 設計（`~/.nanobot/sessions/`、`~/.nanobot/skills/`）；無 tenant 概念
- **AEOS 補的方式**：在 `EmployeeRuntime` 外層加 `TenantContext`（SQLAlchemy session-scoped variable 注入 `app.tenant_id`），所有 hook 都 read context 寫進 audit；DB 操作走 RLS
- **成本**：中（依賴 AEOS S2 的 DB schema + RLS migration）

### 6.2 Append-only audit service

- **nanobot 現狀**：loguru 結構化日誌（含 `name`/`status`/`detail` for tool event）；無 audit service
- **AEOS 補的方式**：寫 `AuditHook(AgentHook)`，每個 hook 點 emit `AuditEvent` 進 PG `audit_log` 表（append-only trigger + BIGSERIAL）
- **成本**：低（MC-001 設計已完整，套到 hook 即可）

### 6.3 Policy engine

- **nanobot 現狀**：只有 `restrict_to_workspace` + SSRF + workspace violation 限流（位置：`nanobot/agent/runner.py:953-1034`）
- **AEOS 補的方式**：寫 `PolicyHook(AgentHook)` 在 `before_iteration` 讀 YAML policy（MC-006 3 級風險 schema），對每個 tool call 做 risk_tier 檢查
- **成本**：中（需先寫 YAML schema）

### 6.4 Cost / quota enforcement

- **nanobot 現狀**：累加 `usage.prompt_tokens` / `usage.completion_tokens`；無全域 rate limit
- **AEOS 補的方式**：寫 `QuotaHook(AgentHook)` 在 `after_iteration` 讀 Redis 計數器，超 hard cap 就 raise；emergency cap 切 LLM provider 到 Haiku
- **成本**：中（QUOTA-001 設計已完整）

### 6.5 PostgreSQL session storage

- **nanobot 現狀**：JSONL → JSON 檔案；無 DB 抽象介面
- **AEOS 補的方式**：用 SQLAlchemy 重寫 `Session.save()` / `load()` 邏輯，寫進 `conversations` + `messages`（monthly partition）兩張表
- **成本**：中-高（是 MC-010 Conversation Engine 的核心工作）

---

## 7. 3 條可選路徑（給 ADR-0012 決策）

| 路徑 | 描述 | 工作量 | 風險 | 建議 |
|---|---|---|---|---|
| A | **Fork + Wrap 整個 nanobot** | Vendor 進 `runtime/nanobot/`，pin commit，自寫 `EmployeeRuntime` 包住 `AgentLoop` | 高（1-2 週初始 + 持續 merge）| 高 — v0.2.0 alpha 每週改；17 channels + Dream + cron + WebUI 大量未用 | ❌ |
| B | **借鑑 + 自寫**（推薦）| 讀 `nanobot/nanobot/agent/{loop,runner,hook}.py` 三檔，自寫 AEOS 精簡版 `EmployeeRuntime`（~200-300 行 Python）| 中（1 週）| 低 — 完全可控；版本鎖死 | ✅ |
| C | **PyPI 套件直接 `pip install nanobot-ai`** | 當 lib 用，靠 nanobot API | 低（半週）| 中-高 — dep bloat 巨大；breaking change 風險；nanobot 並非設計為 lib | ❌ |

**推薦 B 的理由**：

1. AEOS 真正需要的是**設計觀念**而非 codebase。讀 3 個檔案 30 分鐘即可學到 AgentLoop/AgentRunner 切分、Hook 模式、Provider 抽象
2. AEOS MC-009 規格已明確（單次 LLM call + RAG + validation）— 自寫只要 200-300 行
3. nanobot v0.2.0 是 alpha，從 README News 看 daily 改動（v0.1.5.post1 ~ v0.2.0 一個月內 60+ commits）— vendor 後 merge cost 高於自寫 cost
4. 引整套進來後還要 disable 16 個未用 channel、disable Dream（不適合 prod）、改 storage 從 file → PG — 工作量等於部分重寫
5. 風險可控：未來若有 nanobot 新功能想用，再個別借鑑（不會被綁定）

---

## 8. Dream Skill Discovery 評估（關鍵釐清）

我原本擔心 Dream 違反 Frozen Runtime，深掘後發現：

### 8.1 Dream 怎麼運作

兩階段 LLM 流程（位置：`nanobot/agent/memory.py:1010-1130`）：
- **Phase 1（分析）**：LLM 讀對話歷史，提取可能值得學習的 pattern
- **Phase 2（代理執行）**：LLM 用 `read_file` / `edit_file` 工具自動建立 `~/.nanobot/skills/<name>/SKILL.md`

### 8.2 為什麼不違反 Frozen Runtime

- 產出是 **`.md` 檔案到磁碟**，**不是 runtime mutable state**
- **不會自動熱載入** ToolRegistry — 需重啟 nanobot 才生效
- 這實際上是「**half-frozen runtime + offline skill draft generator**」模式

### 8.3 對 AEOS 的啟發

Dream 可作為 **MC-002 Training Room 中「Skill Draft Generator」的設計參考**：
- 對話結束後（或 expert 觸發），跑 Dream-like 流程產出 `skill.draft.yaml`
- 走 7 層 quality gate（MC-002）+ pass rate ≥ 0.80（MC-005）
- 過 gate 才 atomic swap 上線

**生產環境關閉 Dream 自動執行**（或限制只跑 read-only 分析）；只在 Training Room 隔離環境用。

---

## 9. LINE Channel 新增評估

### 9.1 17 個內建 channel 但無 LINE

Telegram / Discord / Slack / Feishu / Matrix / WhatsApp / QQ / WeChat / WeCom / DingTalk / Email / MoChat / MS Teams / WebSocket + variants。

### 9.2 新增 LINE channel 工作量

繼承 `Channel` 基類（位置：`nanobot/channels/base.py`），實作 `start()`, `stop()`, 訊息轉換。**參考 Telegram 實作約 700 行**。

但實際上，依 **路徑 B（借鑑 + 自寫）**：
- AEOS 不用 nanobot 的 channel 系統
- LINE webhook 是 FastAPI route（API-002）— 直接寫進 `app/channels/line.py`
- 不需要 nanobot Channel 基類

---

## 10. 對 ADR-0002 的衝擊

### 10.1 兩個必須處理的問題

| 問題 | 嚴重度 | 處理方式 |
|---|---|---|
| 事實描述錯誤（nanobot 是 Python 不是 TypeScript）| 高 | 必須在 ADR 系統中留紀錄 |
| 「fork + wrap」策略應改「借鑑 + 自寫」 | 中 | 策略修正，但結論「選 nanobot」不變 |

### 10.2 處理：開 ADR-0012

依 tier-1 規則（`.claude/rules/context-stability.md`：ADR append-only，不可修改 accepted ADR），不直接改 ADR-0002，而是開新 ADR：

- **`docs/1-decisions/ADR-0012-runtime-strategy-amendment.md`**
  - **erratum**：更正 nanobot = Python 3.11+，不是 TypeScript
  - **strategy shift**：fork + wrap → 借鑑設計 + 自寫精簡版
  - **保留**：依然採用 nanobot 作為 Employee Runtime 設計來源（ADR-0002 結論不變）

### 10.3 不需要 supersede

ADR-0002 的核心結論「採用 nanobot 作為 Employee Runtime 來源 + Governance Layer 自寫」**仍然成立**。ADR-0012 只是修正執行細節。

---

## 11. 建議行動

### 11.1 立即（本 PR 一起）

1. ✅ 本報告 commit 進 `chore/phase-1-kickoff`
2. ✅ 開 `docs/1-decisions/ADR-0012-runtime-strategy-amendment.md`
3. 更新 `docs/4-exploration/DEV-PLAN-PHASE1-2026-05.md`「鎖定的工程決策」表，把 Runtime 那行改為 `nanobot 借鑑設計（ADR-0002 + ADR-0012）`

### 11.2 S4（LINE + Draft Mode）開工前

讀以下 3 個 nanobot 檔案，每個 ~30 分鐘：

| 檔案 | 借鑑點 |
|---|---|
| `nanobot/nanobot/agent/loop.py:122-300` | AgentLoop 狀態機切分（RESTORE→COMPACT→COMMAND→BUILD→RUN→SAVE→RESPOND→DONE）|
| `nanobot/nanobot/agent/runner.py:112-300` | AgentRunner LLM 對話迴圈 + tool execution |
| `nanobot/nanobot/agent/hook.py` | Hook ABC + CompositeHook，AEOS Governance Hook 設計 |

### 11.3 S3（Skill v1.0）開工前

讀 `nanobot/nanobot/agent/memory.py:1010-1130`（Dream 兩階段流程），作為 MC-002 Training Room Skill Draft Generator 設計參考。

### 11.4 保留 nanobot/ 作 reference

- nanobot 有自己的 `.git`，不會被 AEOS root 的 commit 包進去
- 不必加進 `.gitignore`（top-level dir 通常排除 nested .git 自動處理；可選擇明確列）

---

## 12. 變更紀錄

| 日期 | 變更 | Owner |
|---|---|---|
| 2026-05-18 | 初版發布；觸發 ADR-0012 | CTO |
