# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 補充規則見 `.claude/CLAUDE.md`（skill / tier / CIA / git workflow），以及 `.claude/rules/*.md`（自動載入）。本檔僅描述本 repo 特有的大圖。

## Repo 是什麼

**AEOS (AI Employee Operating System)** 的「企業白皮書 + 結構化規格」單一專案。**目前處於 spec-first 階段，repo 內尚無生產程式碼**（沒有 `package.json` / `pyproject.toml` / `src/` / `tests/`）。主要產出是：

| 路徑 | 角色 |
|---|---|
| `whitepaper.md`（根目錄，~4500 行） | **對外快照**。單檔合併版，用於發送 / 列印 / 完整閱讀。 |
| `docs/`（拆檔版） | **內部 reference**。`whitepaper.md` 的主題拆檔 + tier 化規格 + ADR + flow contracts。 |
| `agent_x.md`（根目錄） | Agent X 設計草稿。 |
| `VibeCoding_Workflow_Templates/` | 整個 docs 結構所依循的 6-tier 模板原版（不是空盒子，是 source of templates）。 |
| `.claude/` | Claude Code harness 設定：rules、skills、agents、commands、hooks。 |

## 入口優先序

1. **`docs/LAUNCH-DASHBOARD.md`** — 上線推進的唯一入口。Sprint 狀態、阻塞項、CEO / CTO 本週行動、必讀清單。每週五更新。
2. **`docs/README.md`** — 章節 ↔ 檔案地圖；角色閱讀路徑（VC / CTO / PM / CEO / 合規）。
3. **`docs/2-contracts/flow-index.md`** + **`traceability-matrix.md`** — Flow ID 與 AC ↔ TC ↔ 模組對應（AI-AUTO 生成，是 cache）。

## 文件 6-tier 結構（docs/）

| Tier | 目錄 | 變動頻率 | 信任度 |
|---|---|---|---|
| 0 | `0-principles/` | 年級 | 硬約束 |
| 1 | `1-decisions/` | append-only ADR | 高 |
| 2 | `2-contracts/` | 與 code 同步 | 需檢查 `last-synced-with` frontmatter |
| 3 | `3-process/` | 季度 | 直接照做 checklist |
| 4 | `4-exploration/` | 任務級 | 讀動機，不當前狀態 |
| 5 | `5-views/` | 自動再生 | 當 cache，code 為準 |

**Tier 2 frontmatter 範例**（強制）：

```yaml
---
id: API-001
last-synced-with: <git-commit-sha>
sync-source: code | doc
source-paths: [src/api/users.py]
synced-at: 2026-05-14
---
```

寫入前用 `sunnydata-doc-freshness` skill 檢查鮮度；大規模文件再生用 `sunnydata-auto-regen`。

## 目前的 Sprint 狀態（速看）

- **S0 / S0.5 已完成**：ADR、domain model、DB schema、PRD、SAD、API、BF/UF/NFR 已就緒。
- **S1 (Week 2.5) IN PROGRESS**：PM Layer + 開工準備（PROJ-001 / AC / 開工 checklist）。
- **S2+ 待**：等簽下第一個 pilot 客戶才開 KB 實作（UF-001）。
- **上線就緒燈號全 RED**：治理 / 安全 / 合規 / 運營 / 商業 都還沒落地（見 LAUNCH-DASHBOARD §「上線就緒」）。
- **Engineering Health 大部分 n/a**：因為 code 還沒寫，CI / coverage / latency 全是 baseline。

## 目標技術架構（Phase 1，尚未實作）

來自 `docs/2-contracts/SAD-v0.1.md`：

```
Customer-dedicated VM (Docker Compose)
├── Web SPA       — Next.js or Vite + React + TS + Tailwind + shadcn/ui
├── API           — FastAPI (Python 3.12) 或 Node.js (TS)
├── Worker        — 同 API 程式碼、不同 entrypoint
├── PostgreSQL 15 — + pgvector（KC 檢索）
├── Redis 7       — queue + DLQ + hot cache
└── Skill Git Repo (read-only mount) — skills/ YAML + prompts
```

外部依賴：LINE Messaging API、Anthropic Claude API、S3-compatible object storage。

**Python / Node 抉擇**：待 Week 1 Day 1 決定，依隊員 A 主力語言。後續文件預設 Python；若選 Node 須對應替換。

## Change Governance — 硬 gate

任何變更涉及 **flow / contract / data / architecture / external integration / test plan / boundary**：

1. **先呼叫 `sunnydata-change-impact-analysis` skill** 產出 CIA 寫入 `docs/4-exploration/CR-NNNN-*.md`；不可繞過直接改文件。
2. **CIA §8「Human Decisions Required」未填寫 → 不可動 code / contract**。
3. **文件衝突**或讀到 `status: deprecated / superseded` 文件 → **停下回報**，引用具體 ID（BF-/UF-/SF-/API-/MC-/ADR-/TC-…），**不腦補**。

完整規則：`.claude/rules/change-governance.md`。Rewrite vs Refactor 9 維打分表用來判斷「改文件 vs 重組模組 vs 開新主幹」。

## 雙版維護 SOP

`whitepaper.md`（單檔）與 `docs/`（拆檔）是同一份白皮書的兩種形態：

1. **修改某章節時**：先動 `docs/` 拆檔版（粒度小），再同步回 `whitepaper.md` 單檔版。
2. **新增整個 Part 時**：先在 `docs/` 新增主檔，視情況再合併。
3. **單檔版 = 發布快照**：對外發送前確認與拆檔一致。
4. **章節編號穩定**：`§X.Y` 引用保留原語意，不轉相對連結（跨工具 anchor 處理不一致）。
5. **避免漂移**：每次修改在 `docs/README.md` 的「Part 演進史」追加紀錄。

## Repo 內常用的 Skills / Commands

完整列表見 `.claude/WORKFLOW.md`。針對本 repo 性質（spec-first，文件為主）最常用：

| 入口 | 用在 |
|---|---|
| `sunnydata-doc-freshness` skill | 寫 tier-2 文件前；週度檢查 stale doc |
| `sunnydata-change-impact-analysis` skill | 任何 contract / flow / schema 變動前（hard gate） |
| `sunnydata-auto-regen` skill | flow-index / traceability-matrix / project-structure 等 AI-AUTO 視圖再生 |
| `sunnydata-flow-audit` skill | 稽核 BF/UF/SF/API/TC 一致性（讀-only） |
| `vibecoding-write-prd` / `vibecoding-write-api-contract` / `vibecoding-write-tdd` | 起新文件時 |
| `/release <version>` | Tag + CHANGELOG + GitHub Release（暫無 code 變動，少用） |

無建置 / lint / test 指令 — 因為還沒有 code。當 code 進來後，新增 build / test 章節到本檔。

## 分支與 Commit

- `main` 為保護分支：禁止直接 commit；功能用 `<type>/<short-desc>` 分支 → PR 合入。
- Commit message 強制 Conventional Commits（feat/fix/refactor/docs/test/chore/perf/ci）+ WHY/WHAT/IMPACT body。
- 詳細格式與 AI 讀取深度分層見 `.claude/rules/git-workflow.md`。

## 給未來 Claude 的提醒

1. **這個 repo 沒有 code**，所以「跑測試 / build」「修 lint」「裝依賴」這類請求都應該停下來確認，使用者可能誤把 repo 當成 code 專案。
2. **動 tier-2 文件之前**先 `sunnydata-doc-freshness` 確認你不是在改一份 stale 的文件。
3. **跨檔引用使用 `§X.Y` 文字**（不是 Markdown anchor），因為章節編號穩定且跨工具兼容。
4. **`whitepaper.md` 通常不該手動編輯**——先動 `docs/` 拆檔，再從拆檔合併回單檔。
