---
id: ADR-0012
title: Runtime 策略修正 — nanobot 是 Python 框架，採「借鑑 + 自寫」而非「fork + wrap 整套」
status: accepted
date: 2026-05-18
deciders: CTO
tier: 1
amends: ADR-0002
related: [ADR-0001, ADR-0002, ADR-0011, NANOBOT-EVALUATION-2026-05-18]
---

# ADR-0012 — Runtime 策略修正

## Context

ADR-0002（2026-05-14，accepted）做了兩件事：
1. **選擇 nanobot 作為 Employee Runtime 來源**（與 Hermes-Agent / CheetahClaws 比較後）
2. **策略：fork + wrap nanobot**，vendor 進 `runtime/nanobot/`，自寫 `EmployeeRuntime` 包住

2026-05-18 實際讀 nanobot 倉庫（local: `/Users/imding1211/project/AEOS_platform/nanobot/`、GitHub: `HKUDS/nanobot`、PyPI: `nanobot-ai` v0.2.0）後，發現兩個需要修正的問題。詳細評估見 [`docs/report/NANOBOT-EVALUATION-2026-05-18.md`](../report/NANOBOT-EVALUATION-2026-05-18.md)。

依 `.claude/rules/context-stability.md` 規定，tier-1 ADR 為 append-only，不可編輯 accepted ADR。故開本 ADR 對 ADR-0002 補正。

## Decision

**修正 ADR-0002 兩處**：

### 1. Erratum — nanobot 的語言事實

| 項目 | ADR-0002 原文 | 實際情況 |
|---|---|---|
| 語言 | 「TypeScript/Node 輕量 runtime」 | **Python ≥ 3.11** |
| 開發組織 | （未提）| HKUDS（HKU Data Science Lab）|
| 作者 | （未提）| Xubin Ren + nanobot contributors |
| License | （未提）| MIT |
| 發布管道 | （未提）| PyPI `nanobot-ai`，當前 v0.2.0（2026-05-15）|
| WebUI | （未提）| React/TS WebUI bundle 進 Python wheel |
| 主要 deps | （未提）| `anthropic`, `openai`, `pydantic v2`, `httpx`, `asyncio`, `loguru`, `mcp>=1.26.0` |

**此修正不改變 ADR-0002 選 nanobot 的結論**。實際上，nanobot 是 Python 的事實**強化**了 ADR-0002 的選擇——與 ADR-0011（Python 3.12 + FastAPI）完美吻合，無語言衝突。

### 2. 策略修正 — Fork + Wrap → 借鑑 + 自寫

| 項目 | ADR-0002 原策略 | 本 ADR 修正策略 |
|---|---|---|
| 來源處理 | Vendor nanobot 原始碼進 `runtime/nanobot/`（pinned commit）| 不 vendor codebase；不 `pip install nanobot-ai` |
| AEOS 入口 | `EmployeeRuntime` class 包住 nanobot `Session` | **自寫 AEOS 精簡版 `EmployeeRuntime`**（~200-300 行 Python）|
| 借鑑方式 | （無；用 import 整套）| 讀 `nanobot/nanobot/agent/{loop,runner,hook}.py` 三檔，移植**設計觀念**到 AEOS |
| Governance Layer | 攔截 nanobot 內部 LLM/tool call | 寫成 AEOS `AgentHook` 子類（`AuditHook`/`PolicyHook`/`QuotaHook`），註冊進自寫的 `CompositeHook` |
| MCP 整合 | （未明示）| AEOS Tool Registry 未來可採 nanobot 的 MCP client 模式作為延伸 |

**借鑑的具體三個設計觀念**：

1. **AgentLoop / AgentRunner 切分**（`nanobot/agent/loop.py:122`、`runner.py:112`）
   - AgentLoop 管狀態機（RESTORE→COMPACT→COMMAND→BUILD→RUN→SAVE→RESPOND→DONE）與 hook 協調
   - AgentRunner 純執行 LLM 對話迴圈 + tool execution + streaming
   - 對 AEOS：AgentLoop = MC-009 「Frozen Runtime snapshot」；AgentRunner = 「單次 LLM call per turn」

2. **Hook 機制**（`nanobot/agent/hook.py`）
   - `AgentHook` ABC + `CompositeHook` 串接
   - `before_iteration` / `after_iteration` / `on_stream` / `emit_reasoning`
   - 對 AEOS：MC-001 audit + MC-006 policy + QUOTA-001 cost 三個 governance 全部寫成 hook

3. **Provider 抽象 + 結構化錯誤**（`nanobot/providers/base.py:92`）
   - `LLMProvider` ABC + `chat()` + `chat_stream_with_retry()`
   - 結構化錯誤元資料：`error_status_code` / `error_kind` / `error_type` + 瞬態 vs 永久錯誤分類
   - 對 AEOS：ADR-0001 `LLMClient` interface 設計參考

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| **A. Fork + Wrap 整個 nanobot**（ADR-0002 原策略）| nanobot v0.2.0 仍 alpha；從 README News 看 daily 改動（v0.1.5.post1 → v0.2.0 一個月內 60+ commits）。Vendor 後 upstream merge cost 高於自寫 cost；且引入 17 channels + Dream + cron + WebUI 大量未用 code，需 disable 工作量等同部分重寫 |
| **B. `pip install nanobot-ai` 當 lib 用** | dep bloat 巨大（17 channel 全拉進來）；nanobot 並非設計為 library 引用，breaking change 風險高；alpha 狀態不適合作為 prod 依賴 |
| **C. 完全自建不參考 nanobot** | 浪費 nanobot 已驗證的 AgentLoop 狀態機切分 + Hook 模式設計；6 個月起跳工程 |

## Consequences

**Positive**：
- 語言/stack 對齊度從「未知衝突風險」（ADR-0002 寫錯）變成「完全吻合」
- 避開 nanobot v0.2.0 alpha 上游 merge 風險
- AEOS Employee Runtime 完全可控；版本鎖死
- 借鑑成本低（30 分鐘讀 3 個檔案）
- 不被 nanobot 未用 17 channel + Dream + cron + WebUI 拖累
- Dream skill discovery 不會誤入 prod（自寫精簡版自然排除）

**Negative**：
- 不直接 import nanobot 也意味著未來如 nanobot 出新功能想用，要再次借鑑/移植
- 自寫 `EmployeeRuntime` 200-300 行 Python 是新工作量（vs vendor 後 wrap）
- 不在 nanobot v0.x 升級時自動受惠

**Tracking**：
- S4 開工前（W7）讀 `nanobot/nanobot/agent/{loop,runner,hook}.py` 三檔並完成「借鑑筆記」進 `docs/4-exploration/`
- 自寫的 `app/agent/employee_runtime.py` 行數預估 ≤ 300 行；超過時觸發 review

## Operational Updates

### Phase 1 工程資料更新

需同步更新以下檔案：

1. **`docs/4-exploration/DEV-PLAN-PHASE1-2026-05.md` §2「鎖定的工程決策」表**：
   - 「Runtime」一行從「fork nanobot」改為「借鑑 nanobot 設計（ADR-0002 + ADR-0012）+ 自寫 AEOS 精簡版 EmployeeRuntime」

2. **`docs/3-process/KICKOFF-CHECKLIST.md` §D.3 工程必讀**：
   - 補一條「ADR-0012 — Runtime 策略修正」進閱讀清單

3. **`docs/LAUNCH-DASHBOARD.md`**：
   - 不需直接更動（Runtime 策略不在 dashboard 指標範圍）

### Week 4 評估點（沿用 ADR-0002 原條件，文字微調）

ADR-0002 寫「若 nanobot 在 production tool-calling 穩定性 < 95%，啟動 ADR-0002-supersede，評估改包 Hermes 的工具層」。

本 ADR 修正：因不再 vendor nanobot，「穩定性 < 95%」應改為衡量 AEOS **自寫** `EmployeeRuntime` 的 tool-calling 穩定性。若 < 95%，supersede 路徑為：

- 路徑 a：再次借鑑 nanobot v0.x 新版的改進（差異重新借鑑）
- 路徑 b：借鑑 Hermes 工具層設計（但不含 self-improvement）

不再有「直接換 vendor」的選項。

## Status

Accepted。本 ADR amends ADR-0002 §Decision 的兩個面向（語言事實 + 包裝策略）；ADR-0002 的核心結論（採 nanobot 作為設計來源）維持不變。

不設 review 時點；若未來 nanobot 或 Hermes 出現 breaking 變化、或自寫 `EmployeeRuntime` 不夠用，再寫 ADR-0013 supersede。
