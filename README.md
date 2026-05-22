# AEOS Platform

AI Employee Operating System — Phase 1 MVP（7-Day AI 客服 Onboarding）。

> Repo 大圖請讀 [`CLAUDE.md`](./CLAUDE.md)。
> Phase 1 開發路線圖請讀 [`docs/4-exploration/DEV-PLAN-PHASE1-2026-05.md`](./docs/4-exploration/DEV-PLAN-PHASE1-2026-05.md)。
> 入場 checklist 請讀 [`docs/3-process/KICKOFF-CHECKLIST.md`](./docs/3-process/KICKOFF-CHECKLIST.md)。

## Tech Stack

| 層 | 選擇 | 依據 |
|---|---|---|
| 語言 | Python 3.12 | ADR-0011 |
| Web framework | FastAPI | ADR-0011 |
| Dep manager | [uv](https://docs.astral.sh/uv/) | ADR-0011 |
| Lint / format | ruff | ADR-0011 |
| Type check | mypy (strict) | ADR-0011 |
| Test | pytest + pytest-asyncio + pytest-cov | TEST-001 |
| DB（S2 起）| PostgreSQL 15 + pgvector + RLS | ADR-0007 |
| Cache / Queue（S2 起）| Redis 7 list + DLQ | ADR-0008 |
| Frontend（Expert UI）| Vite 6 + React 19 + TypeScript + Tailwind 3 | S2.5 |

## 本機開發起手式

### 1. 安裝 uv

```bash
brew install uv
# 或
pipx install uv
```

### 2. 同步依賴

```bash
uv sync
```

`uv` 會自動建立 `.venv/`、解析 `pyproject.toml`、產生 `uv.lock`。

### 3. 跑測試

```bash
uv run pytest
```

預期：所有測試綠 + coverage ≥ 80%（依 TEST-001 §4）。

### 4. 啟動 API server

```bash
uv run uvicorn app.main:app --reload
```

驗證：

```bash
curl http://localhost:8000/health
# {"status":"ok","env":"dev","version":"0.0.1"}
```

OpenAPI docs：`http://localhost:8000/docs`

### 4.1 啟動 Expert Console UI（Draft Mode 審查介面）

```bash
cd web/expert
npm install            # 首次
npm run dev            # http://localhost:5173 → proxy /api → :8000
```

詳見 [`web/expert/README.md`](./web/expert/README.md)。CI 已涵蓋 typecheck + vitest + build。

### 5. Lint / Format / Type check

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy app              # type check
```

### 6. Pre-commit（secret scanning + lint）

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Repo 結構

```
AEOS_platform/
├── app/                          # FastAPI source（API / agent / worker / services）
├── tests/                        # pytest（80% coverage gate）
├── web/expert/                   # Expert Console UI（Vite + React + Tailwind）
├── docs/                         # 6-tier 文件結構
│   ├── 0-principles/            # 工程原則（年級變動）
│   ├── 1-decisions/             # ADR（append-only）
│   ├── 2-contracts/             # 模組契約、API、Schema（與 code 同步）
│   ├── 3-process/               # 流程、Runbook、Checklist
│   ├── 4-exploration/           # PRD、Dev Plan、CIA
│   └── report/                  # 一次性報告（blocker 等）
├── VibeCoding_Workflow_Templates/  # 6-tier 文件模板源
├── .claude/                      # Claude Code harness 設定
├── .github/                      # CI/CD workflows + dependabot
├── whitepaper.md                 # 對外快照（單檔合併版）
├── pyproject.toml                # uv + ruff + mypy + pytest 統一設定
└── CLAUDE.md                     # repo 大圖（給未來 Claude）
```

## Sprint 狀態

當前：**S1 (Week 2.5) IN PROGRESS** — PM Layer + 開工準備。

詳見 [`docs/LAUNCH-DASHBOARD.md`](./docs/LAUNCH-DASHBOARD.md)（每週五更新）。

## 開發規範

- **Conventional Commits**（`feat:`, `fix:`, `refactor:`...）+ WHY/WHAT/IMPACT body — 見 `.claude/rules/git-workflow.md`
- **Change Governance**：觸 flow / contract / data / architecture 之變更必先跑 `sunnydata-change-impact-analysis` skill — 見 `.claude/rules/change-governance.md`
- **Test coverage**：≥ 80% — CI 自動阻擋
- **Type check**：mypy strict — CI 自動阻擋
- **PR 規範**：見 `.github/pull_request_template.md`

## 授權

Proprietary. © AEOS Team.
