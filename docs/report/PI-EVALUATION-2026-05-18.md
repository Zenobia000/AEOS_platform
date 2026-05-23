---
id: REPORT-PI-EVALUATION
title: pi (Pi Agent Harness) 評估 — 是否作為 AEOS 迭代學習 agent 架構
date: 2026-05-18
owner: CTO
type: one-shot evaluation report
related: [ADR-0001, ADR-0002, ADR-0003, ADR-0011, engineering-charter, MC-002, MC-005, MC-009]
subject:
  repo: https://github.com/badlogic/pi-mono
  local_path: pi/
  license: MIT (Copyright 2025 Mario Zechner)
  version_evaluated: working tree as of 2026-05-18
---

# pi 評估報告 — 不適合作為 AEOS 迭代學習 agent 架構基底

> **TL;DR**：pi 是強大的 personal coding agent 框架（MIT，TypeScript，5 packages，23+ LLM provider 抽象），設計目標與 AEOS 完全不同。**5 項硬衝突 + 4 項缺漏 + 3 項可借鑑**。不可作為基底；但 `pi/packages/agent/src/` 的 ReAct loop 與 session JSONL tree 設計值得在 MC-009 / MC-002 開工前讀過，借鑑觀念到 Python 實作。
>
> **對 ADR-0002（nanobot 選擇）的衝擊**：無。pi 與 nanobot 解決不同問題，且 pi 的 self-extensible 哲學與 AEOS Frozen Runtime 原則正面衝突——比 nanobot 更衝突。維持 ADR-0002 accepted。

---

## 1. 摘要結論

### 1.1 5 項硬衝突（pi 不可作為基底的核心理由）

| 維度 | pi | AEOS 需求 | 衝突類型 |
|---|---|---|---|
| 1. **語言** | TypeScript / Node | Python 3.12（ADR-0011 accepted）| 重寫成本高；IPC bridge 是新工程 |
| 2. **設計目標** | personal coding agent CLI（單機） | multi-tenant SaaS for AI 員工 | 目標差太遠 |
| 3. **Skill 機制** | runtime `pi.registerTool()` + hot-reload extension | git monorepo + YAML manifest + atomic symlink swap + 5 態 lifecycle（MC-005）| 哲學衝突 |
| 4. **Frozen Runtime** | self-extensible（核心賣點）| 生產不可變（engineering-charter 原則 2）| 設計理念正面衝突 |
| 5. **Training Room** | 無；session 用於 export 給別人訓練 pi（pi-share-hf）| 隔離 sandbox + 7 層 quality gate + red team + expert review（MC-002）| 缺核心能力 |

### 1.2 4 項缺漏（AEOS 必備但 pi 沒有）

- ❌ **Multi-tenant 隔離**：pi sessions 存單機 `~/.pi/agent/sessions/`；AEOS 要 shared PG + RLS + 應用層雙重檢查（ADR-0007）
- ❌ **Append-only audit service**：pi 用 session JSONL 當 trail，無中央 audit；AEOS MC-001 要求 append-only + 90 天 PII 脫敏 + 3 索引
- ❌ **YAML 風險分級 policy engine**：pi 用 `beforeToolCall` hook 手寫檢查；AEOS MC-006 要求 3 級風險 YAML policy + 同步 gateway
- ❌ **Cost / quota enforcement**：pi 只顯示 token 計數；AEOS QUOTA-001 要求 5 層 rate limit + soft/hard/emergency 降級

### 1.3 3 項可借鑑（移植到 Python 實作）

- ✅ **ReAct agent loop**：`agentLoop()` + `beforeToolCall` / `afterToolCall` hooks 是乾淨範本，可作為 MC-009 Employee Runtime 的設計參考
- ✅ **Session JSONL tree + branching**（`/fork` `/clone` `/tree`）：對 MC-002 Training Room 中「expert 沙盒陪練多分支對話」有啟發
- ✅ **薄層 LLM provider abstraction**：`Model<API>` 泛型 + `Context { systemPrompt, messages, tools }` 是好範本（AEOS 只需薄層 Anthropic 但介面設計可借鑑）

---

## 2. pi 是什麼（架構速覽）

來源：`pi/README.md`、`pi/package.json`、`pi/packages/agent/src/` 主要檔案

### 2.1 5 個 npm packages

| Package | 角色 | 對外 API |
|---|---|---|
| `@earendil-works/pi-agent-core` | Agent runtime + tool calling + state mgmt | `Agent`, `agentLoop()`, `AgentTool`, `AgentMessage`, `AgentEvent` |
| `@earendil-works/pi-ai` | Unified multi-provider LLM API（23+ providers） | `Model<API>`, `stream()`, `complete()`, `Context` |
| `@earendil-works/pi-coding-agent` | Interactive coding agent CLI（self-extensible） | `pi.registerTool()`, `pi.registerCommand()`, `pi install npm:...` |
| `@earendil-works/pi-tui` | Terminal UI 元件 | （內部使用） |
| `@earendil-works/pi-web-ui` | Web 介面 | （內部使用） |

### 2.2 主要設計特徵

- **Agent loop**：ReAct 風格 — 單次 prompt → LLM 決策 → 工具執行迴圈 → 繼續
- **Tool calling**：TypeBox schema + automatic validation；`beforeToolCall` / `afterToolCall` hooks
- **Session**：JSONL tree，存 `~/.pi/agent/sessions/`，支援 `/fork` / `/clone` / `/tree` 分支
- **Memory**：messages stack + custom message types via TypeScript declaration merging + `transformContext()` for pruning
- **LLM provider**：統一 `Model<API>` 泛型介面，支援 OpenAI / Anthropic / Google / Bedrock / Ollama / OpenRouter 等 23+
- **Cost tracking**：自動 token 計數 + provider 定價（input/output/cacheRead/cacheWrite）
- **Self-extension**：使用者寫 TypeScript extension（`.ts` 或 npm package），放 `~/.pi/agent/extensions/`，`/reload` 熱載入；或讓 agent 寫 extension save → `/reload`

### 2.3 設計定位（從 README 與 AGENTS.md 推導）

- **目標使用者**：個人開發者，使用 coding agent CLI 做 OSS / 個人 project 的編碼任務
- **OSS 文化**：強調 session 分享（`pi-share-hf` 上傳到 Hugging Face dataset 蒐集 OSS coding 訓練資料）
- **License**：MIT（Copyright 2025 Mario Zechner / badlogicgames）

---

## 3. AEOS 對「迭代學習 agent 架構」的需求

來源：`docs/0-principles/engineering-charter.md`、`docs/1-decisions/ADR-000{1,2,3,11}`、`docs/2-contracts/MC-00{2,5,9}`

### 3.1 工程原則硬約束

| 原則 | 涵義 |
|---|---|
| **Governance-first** | AI 對外行為先 audit log + policy check；無此路徑禁上線 |
| **Frozen Runtime** | 生產版本不可變；學習/改進在 Training Room；版本號凍結 |
| **Skill as Asset** | git 化、版本化、測試化、可回滾；未過 Quality Gate 禁上線 |
| **Simplicity over Sophistication** | 縮排 ≤ 3 層、命名動詞-名詞 |
| **Pragmatism over Theory** | 不寫「未來可能」的 abstraction |

### 3.2 模組契約硬需求

- **MC-002 Training Room**：sandbox + test case + 50 題自動生成 + 7 層 Quality Gate + Red Team + Expert Review
- **MC-005 Skill Registry**：5 態 lifecycle（Draft → Testing → Staging → Active → Archive）+ 0.80 pass rate gate + atomic symlink swap
- **MC-009 Employee Runtime**：Frozen Runtime snapshot + 單次 LLM call per turn + RAG top-K=5 + output validation
- **ADR-0010 Memory**：L1 工作 + L2 會話 + L2.5 對話摘要（Haiku 產）+ L3 知識 + L4 待定

### 3.3 平台需求

- **多租戶**：ADR-0007 共享 PG + RLS + 應用層雙重檢查
- **語言**：ADR-0011 Python 3.12 + FastAPI（accepted）
- **runtime**：ADR-0002 fork nanobot + AEOS Governance Layer wrap（accepted）
- **LLM**：ADR-0001 Anthropic 主，薄層 LLMClient abstraction
- **Skill 儲存**：ADR-0003 git monorepo + YAML manifest（**不**用 npm install / dynamic registration）

---

## 4. 13 維對照矩陣

| # | 維度 | pi | AEOS | 對齊度 |
|---|---|---|---|---|
| 1 | 語言 | TypeScript / Node | Python 3.12（ADR-0011）| ❌ |
| 2 | License / 商業可用 | MIT | proprietary OK | ✅ |
| 3 | 設計目標 | personal coding CLI | multi-tenant SaaS for AI 員工 | ❌ |
| 4 | LLM provider 抽象 | 23+ via `Model<API>` 泛型 | 薄層（Anthropic 主 + 未來 fallback）| 🟡 過大 |
| 5 | Agent loop | ReAct + tool calling + session | 單次 LLM call + RAG + validation（MC-009） | 🟢 觀念可借鑑 |
| 6 | Tool calling schema | TypeBox（JSON-serializable） | Pydantic v2（JSON Schema） | 🟢 觀念可借鑑 |
| 7 | Skill 機制 | runtime `registerTool()` + hot-reload | git monorepo + YAML + atomic swap + 5 態（MC-005）| ❌ |
| 8 | Frozen Runtime | self-extensible（與此相反） | 生產不可變（charter 原則 2） | ❌ |
| 9 | Training / Quality Gate | 無（227 test files 但都是 pi 自己的單元測試） | sandbox + 7 層 gate + red team（MC-002）| ❌ |
| 10 | Session persistence | JSONL tree 單機本地 | PG monthly partition + L2.5 summary | 🟡 觀念可借鑑 |
| 11 | Multi-tenant | 無 | RLS + 應用層雙重檢查（ADR-0007）| ❌ |
| 12 | Audit log | session JSONL 隱性紀錄 | append-only PG + 90d PII 脫敏（MC-001）| ❌ |
| 13 | Policy engine / Cost quota | hook 手寫 + 顯示 token 數 | YAML 3 級風險（MC-006）+ 5 層 rate limit（QUOTA-001）| ❌ |

**統計**：✅ 1 / 🟢 3 / 🟡 2 / ❌ 7。明顯不對齊。

---

## 5. 5 項硬衝突詳述

### 5.1 語言：TypeScript vs Python 3.12（ADR-0011）

- **pi**：純 TypeScript / Node monorepo；`tsgo --noEmit` + biome 工具鏈；npm workspaces
- **AEOS**：ADR-0011 已 accepted Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2.0
- **為何不可調和**：
  - 直接 import pi packages = 引入第二語言 stack（工程稅 2-3 週起）
  - 走 IPC / subprocess / REST bridge = 新增「Python ↔ Node」整合層，違反「Simplicity over Sophistication」
  - 自動重寫 pi 到 Python = 完全自建，pi 的價值消失
- **同樣的問題在 nanobot 也存在**（ADR-0002 選了 TypeScript runtime）。差別：ADR-0002 已決策接受此複雜度（fork + vendor + wrap）；pi 沒有同等的「值得付這個代價」的論證

### 5.2 設計目標：coding CLI vs SaaS

- **pi**：1 個 user 用 CLI 在自己機器上跑 coding 任務；OSS 分享文化
- **AEOS**：N 個 tenant × M 個 AI 員工 × ∞ 個 conversation，per-tenant VM Docker Compose（ADR-0004），LINE 終端用戶 → Worker → LLM → Audit 全鏈路
- **為何不可調和**：pi 沒有 webhook 入口、沒有非同步 Worker、沒有 LINE 整合、沒有 RAG pipeline、沒有 expert review UI。所有 AEOS 的 critical path 在 pi 都不存在

### 5.3 Skill 機制：dynamic vs git-versioned

- **pi**：`pi.registerTool({ name, schema, execute })` 在 runtime 動態註冊；extension 放 `~/.pi/agent/extensions/`；`/reload` 熱載入；無版本化機制
- **AEOS MC-005**：Skill = `skills/customer-service/faq-respond/v1.0.0/{manifest.yaml, system.md, tools.yaml}`；5 態 lifecycle（Draft → Testing → Staging → Active → Archive）；atomic symlink swap；pass rate ≥ 0.80 才可 promote
- **為何不可調和**：pi 把 skill 當「runtime mutable state」；AEOS 把 skill 當「git-versioned immutable artifact」。這不是兼容問題，是哲學差異

### 5.4 Frozen Runtime vs self-extensible

- **pi**：核心賣點是「self-extensible coding agent」——agent 可寫自己的 extension、save 後 `/reload`
- **AEOS engineering-charter 原則 2**：生產版本**不可變**；學習/改進在 Training Room；版本號凍結；違反 = 工程災難（self-mutating agent in prod 是治理炸彈）
- **為何不可調和**：這正是 ADR-0002 拒絕 **Hermes-Agent** 的同一個理由（「Hermes-Agent 具自我改進能力 — 但 AEOS 明文 Frozen Runtime，self-improvement 是反向能力」）。pi 比 nanobot **更違反** Frozen Runtime（nanobot 無 self-mutation；pi 有）
- 推論：若 ADR-0002 拒絕 Hermes 的 self-improvement 是對的，pi 的 self-extensible 也該拒絕

### 5.5 Training Room：無 vs MC-002

- **pi**：無內建 Training Room、無 quality gate、無 red team、無 expert review workflow。`pi-share-hf` 是 **export** 工具（上傳 OSS session 到 Hugging Face），不是 import 學新 skill
- **AEOS MC-002**：Training Room 是 Phase 1 必交付的子系統，包含 sandbox + 50 題自動生成 + 7 層 Quality Gate + Red Team + Expert Review；後續 Phase 2 接 self-improvement
- **為何不可調和**：pi 的「迭代學習」是「我的 session 變成別人訓練資料」；AEOS 的「迭代學習」是「expert 在 sandbox 裡陪 AI 員工練習 → 過 gate → promote 到 prod」。詞同義不同

---

## 6. 4 項缺漏詳述

### 6.1 Multi-tenant 隔離

- **AEOS 需求**：ADR-0007 共享 PG + RLS + 應用層雙重檢查；SEC-001 §6.1 #4「RLS 啟用 + cross-tenant query 測試」
- **pi 現狀**：sessions 存單機本地 `~/.pi/agent/sessions/`；無 tenant 概念；無 RLS
- **補的成本**：等同重寫一份 multi-tenant 包裝層，pi 提供的價值消失

### 6.2 Append-only audit service

- **AEOS 需求**：MC-001 append-only PG + 3 索引 + 90 天 PII 脫敏 cron + 永久保留稽核軌跡
- **pi 現狀**：session JSONL 隱性記錄所有 message + tool call/result（可當 audit trail 用），但無中央服務、無不可竄改保證、無 PII 脫敏
- **補的成本**：要在 pi 外接 audit service，pi 的 session 機制變成第二份記錄

### 6.3 YAML 風險分級 policy engine

- **AEOS 需求**：MC-006 Tool Registry — YAML 靜態 3 級風險 policy + 同步 gateway，所有工具呼叫經 policy check
- **pi 現狀**：`beforeToolCall` hook 由 extension 作者手寫檢查（e.g., block `rm -rf`）；無 YAML schema、無集中管理
- **補的成本**：自建 policy engine 並把 pi 的 hook 改接 — 等於部分重寫

### 6.4 Cost / quota enforcement

- **AEOS 需求**：QUOTA-001 — 5 層 rate limit（L1 per user 60 msg/hr → L2 daily soft/hard cap → L3 per-endpoint → L4 provider → L5 global > $200/hr auto-downgrade）+ 3 級降級（soft 100-120% → hard 120-150% → emergency 200%）
- **pi 現狀**：session 顯示成本（token 計數 + 定價）；無自動 quota；provider rate limit 被動處理
- **補的成本**：完全自寫 quota orchestrator

---

## 7. 3 項可借鑑設計觀念（移植到 Python）

### 7.1 ReAct agent loop（→ MC-009 Employee Runtime）

- **pi 怎麼做**：`pi/packages/agent/src/agent-loop.ts` 的 `agentLoop()` + `agentLoopContinue()`；`beforeToolCall(name, args) → block?` + `afterToolCall(name, result) → modify? terminate?` hooks
- **移植到 Python**：
  - 用 `asyncio` + `httpx.AsyncClient` 寫類似 loop
  - hooks 用 sync/async callable list（依 SAD-v0.1 §3.1 Worker async）
  - tool schema 用 Pydantic v2 BaseModel（自動 JSON Schema export 給 Anthropic API）
- **借鑑點**：把 `before/afterToolCall` 兩個 hook 設計成 AEOS Governance Layer 的攔截點（audit + policy + cost 三個全部插這裡）

### 7.2 Session JSONL tree + branching（→ MC-002 Training Room）

- **pi 怎麼做**：每筆 message 一行 JSONL，`parentId` 連結，單檔 tree；`/fork` 從某點分支、`/clone` 複製整個 session、`/tree` 視覺化
- **移植到 AEOS Training Room**：Training Room 的 expert sandbox 需要「同一個 KB + 多個對話分支」測試不同 prompt / Skill 版本對相同問題的回應差異。pi 的 tree pattern 直接可用
- **借鑑點**：DB schema 上 `training_sessions` 加 `parent_session_id`；UI 給 expert 一個 tree 視覺化

### 7.3 薄層 LLM provider abstraction（→ ADR-0001 LLMClient）

- **pi 怎麼做**：`pi/packages/ai/src/models.ts` 的 `Model<API>` 泛型 + `Context { systemPrompt, messages, tools }` + streaming events (`'text_delta' | 'toolcall_delta' | 'thinking_delta'`)
- **移植到 AEOS**：ADR-0001 已決定薄層 `LLMClient` interface + 唯一實作 `AnthropicClient`。pi 的 streaming event 設計可作為 Python `AsyncIterator` event type 參考
- **借鑑點**：streaming tool call arguments（partial JSON parsing）— 在 AEOS Draft Mode 中讓 expert 看到 AI 邊想邊出來，UX 更好

---

## 8. 對 ADR-0002（nanobot）的衝擊評估

| 評估面向 | 衝擊 |
|---|---|
| 是否 supersede ADR-0002？ | **否** |
| 是否新增 ADR 評估 pi vs nanobot？ | 否（本報告即為紀錄）|
| Week 4 評估點是否要加入 pi？ | 否（Week 4 評估範圍是「若 nanobot 穩定性 < 95% 則考慮 Hermes 工具層」，pi 不在這 supersede 路徑上）|

**理由**：
- pi 與 nanobot 解決不同問題（pi 是完整 coding agent；nanobot 是輕量 runtime）
- pi 與 ADR-0002 拒絕 Hermes 的核心理由（self-improvement / self-mutation）正面衝突
- 把 pi 拿來和 nanobot 比，等同於把已被 ADR-0002 拒絕的「self-extensible runtime」重新搬上桌
- ADR-0002 維持 accepted

---

## 9. 建議

### 9.1 對 pi/ 目錄的處置

- ✅ **保留 pi/ 作 reference**：`pi/` 有自己的 `.git`，已被 root 的工作樹忽略（不會被 AEOS commit 包進去）
- ❌ **不要 fork pi**：fork 後 maintenance 成本高，且 pi 跟 AEOS 哲學衝突
- ❌ **不要 import pi packages**：語言不對，IPC bridge 是新工程
- ✅ **MC-009 / MC-002 開工前讀 `pi/packages/agent/src/agent-loop.ts` 一次**：30 分鐘，借鑑 ReAct loop 與 hook 設計

### 9.2 後續行動

| 行動 | 對象 | 時程 |
|---|---|---|
| 本報告 commit 進 `chore/phase-1-kickoff` branch | CTO | 立即 |
| 報告 link 加入 `docs/4-exploration/DEV-PLAN-PHASE1-2026-05.md` 「關鍵文件參考」 | CTO | 立即 |
| MC-009 開工時讀 `pi/packages/agent/src/agent-loop.ts`，記錄借鑑到的設計細節 | CTO（S4 開工）| 7 週後 |
| MC-002 設計 Training Room expert sandbox UI 時，參考 pi 的 `/fork` `/clone` `/tree` pattern | CTO（Phase 2）| 6 個月後 |

### 9.3 不採納 pi 的明確理由（給未來再評估時看）

1. pi 是 **TypeScript**（與 ADR-0011 Python 不相容）
2. pi 是 **self-extensible**（與 engineering-charter 原則 2 Frozen Runtime 正面衝突）
3. pi 是 **personal CLI**（與 AEOS multi-tenant SaaS 設計目標差太遠）
4. pi 無 **multi-tenant / audit / policy / quota**（AEOS 4 個必備能力全缺）
5. pi 的「迭代學習」是 **session export 給別人訓練**（與 AEOS Training Room 概念完全不同）
6. ADR-0002 已選 nanobot，pi 不在 ADR-0002 的 supersede 路徑上

---

## 10. 變更紀錄

| 日期 | 變更 | Owner |
|---|---|---|
| 2026-05-18 | 初版發布 | CTO |
