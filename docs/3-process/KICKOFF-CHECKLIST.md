---
id: KICKOFF-CHECKLIST
title: Phase 1 開發 Day 1 開工 Checklist
status: active
date: 2026-05-17
owner: CTO
tier: 3
related: [DEV-PLAN-PHASE1-2026-05, PROJ-001, ADR-0011, SEC-001, OBS-001, TEST-001, RUNBOOK-001]
---

# Phase 1 Day 1 開工 Checklist

> S2 (KB & KC) sprint 啟動的第一天，照本檔逐項確認。
> 目的：避免「人來了但環境沒備好」、「環境備好但 spec 沒讀」、「spec 讀了但 secret 沒給」這三種延遲。
>
> **使用方式**：新成員（含 CTO 自己）入場時，從上到下勾完。受阻一項立即記錄並 escalate。

---

## A. 帳號與權限（入場第一小時）

- [ ] GitHub repo `aeos-platform` 加 collaborator（write 權限）
- [ ] 新人公鑰加入 deploy VM 的 `authorized_keys`
- [ ] Slack workspace 邀請 + 加入 `#engineering` / `#oncall` / `#alerts`
- [ ] PagerDuty oncall schedule 加入（rotation 從 W2 開始）
- [ ] 1Password / Bitwarden vault 邀請（共用 secret 在這裡）
- [ ] Google Workspace（內部 SSO，依 ADR-0006）
- [ ] Grafana / Prometheus URL + 帳號（Hetzner self-host）
- [ ] Hetzner Cloud console 帳號（read-only 起步）

## B. Secrets / API Key（必須在入場前準備好）

由 CTO 或 CEO 在 1Password 內備齊，新人 day 1 取用：

- [ ] **Anthropic API Key**（Sonnet 4.6 + Haiku 4.5 access）
- [ ] **LINE Developers Console** 一個 sandbox channel（Channel ID + Secret + Access Token）
- [ ] **S3-compatible object storage**（Cloudflare R2 或 Hetzner Object Storage）endpoint + access key
- [ ] **PostgreSQL** 本地 dev 用 docker volume；prod 用 VM 內 volume
- [ ] **Grafana Cloud** 或 self-host Grafana admin credentials
- [ ] **GitHub Actions** secrets 已注入：`ANTHROPIC_API_KEY`、`LINE_*`、`POSTGRES_TEST_DSN`
- [ ] **Cloudflare API token**（DNS + TLS 自動續期）
- [ ] **gitleaks** pre-commit hook 安裝 + 已掃過一次無誤

## C. 本地開發環境

- [ ] Python 3.12 安裝（pyenv 或 system）
- [ ] `uv` 或 `poetry` 安裝（S2 第一週確定後統一）
- [ ] Docker Desktop / Docker Engine + Compose v2
- [ ] PostgreSQL 15 client + `psql` CLI
- [ ] `redis-cli`
- [ ] Node.js 20 LTS + pnpm（前端用）
- [ ] VS Code（或同等）安裝以下擴充：`Python`, `Pylance`, `Ruff`, `Docker`, `GitLens`, `ESLint`
- [ ] Git config 設好 `user.name` / `user.email`
- [ ] SSH key 已加入 GitHub
- [ ] `claude` CLI 安裝（本 repo `.claude/` 設定生效）

## D. 必讀文件（按順序 — 預估 4 小時）

從淺到深，邊讀邊在團隊頻道筆記疑問。

### D.1 速讀（20 分鐘）

- [ ] `CLAUDE.md` — repo 大圖
- [ ] `docs/LAUNCH-DASHBOARD.md` — 當前 sprint 狀態
- [ ] `docs/00-executive-summary.md` — 產品速讀

### D.2 產品與業務（60 分鐘）

- [ ] `docs/4-exploration/PRD-001-7day-ai-cs-onboarding.md` — Phase 1 唯一 PRD
- [ ] `docs/2-contracts/BF-001-customer-onboarding.md` — 客戶 Day 0~7 業務流程
- [ ] `docs/3-process/PILOT-001-success-criteria.md` — 成功/失敗標準

### D.3 工程（120 分鐘）

- [ ] `docs/0-principles/engineering-charter.md` — 5 大工程原則（Governance-first、Frozen Runtime…）
- [ ] `docs/2-contracts/SAD-v0.1.md` — 系統架構
- [ ] `docs/2-contracts/domain-model.md` — DDD aggregate
- [ ] `docs/2-contracts/db-schema.md` — 25 張表
- [ ] `docs/2-contracts/MC-008-knowledge-rag.md` — S2 主要依循
- [ ] `docs/1-decisions/ADR-0001` ~ `ADR-0011` — 全部讀過一次（重點 ADR-0006 auth、ADR-0007 隔離、ADR-0011 backend 語言）

### D.4 上線就緒（60 分鐘）

- [ ] `docs/2-contracts/NFR-001-non-functional-requirements.md`
- [ ] `docs/2-contracts/OBS-001-observability-spec.md`（重點 §10 W1~W8 交付）
- [ ] `docs/2-contracts/SEC-001-threat-model.md`（重點 §6.1 Go/No-Go 13 項）
- [ ] `docs/2-contracts/TEST-001-test-plan.md`（80% coverage、quality gates）
- [ ] `docs/3-process/RUNBOOK-001-incident-response.md`（oncall 規則）

### D.5 工作流（20 分鐘）

- [ ] `.claude/CLAUDE.md` — harness 規則
- [ ] `.claude/rules/git-workflow.md` — Conventional Commits + PR
- [ ] `.claude/rules/change-governance.md` — CIA 硬 gate
- [ ] `.claude/WORKFLOW.md` — 常用 skill / command

## E. CI / CD 環境

- [ ] `.github/workflows/ci.yml` 存在且通過：lint + mypy + pytest + coverage gate
- [ ] gitleaks pre-commit hook 在本地 + CI
- [ ] Trivy container image scan 在 CI
- [ ] Dependabot 已啟用（Python + Node）
- [ ] PR template 設好（WHY/WHAT/IMPACT + Test Plan）
- [ ] main 分支保護：要求 PR、要求 CI 綠、禁止 force push
- [ ] `sunnydata-doc-freshness` skill 在本地可跑

## F. Infra（OBS-001 W1 交付）

- [ ] Hetzner VM 開機（2 vCPU / 8 GB / 100 GB SSD）
- [ ] Cloudflare DNS A record 指向 VM
- [ ] nginx 安裝 + Let's Encrypt 自動續期 + HSTS
- [ ] Docker Compose stack 起 stack：Prometheus + Grafana + Loki + Tempo
- [ ] FastAPI app expose `/metrics`（即使沒功能也要有 health + golden signals）
- [ ] Loki 接收 stdout log（JSON 結構）
- [ ] Grafana dashboards：D1 (golden signals) 與 D2 (KPI metrics) 框架就緒

## G. Pilot 客戶資訊（CEO 提供）

S2 開工前必須齊備（無此資訊則 S2 不啟動）：

- [ ] 客戶簽約完成（含 setup fee 50% 已收）
- [ ] 客戶 LINE Official Account：Channel ID + Channel Secret + Access Token
- [ ] 客戶 KB 來源：FAQ Excel / PDF / 既有客服紀錄 / 網站 URL 清單
- [ ] 客戶 Expert 聯絡方式 + 4 次 session 排程（總 3h 投入）
- [ ] DPA 已簽（依 LEGAL-001 範本）
- [ ] 客戶 webhook 接收 IP / 域名（若客戶端有防火牆）

## H. 跑通「冒煙」流程（環境驗證 — 預估 30 分鐘）

確認所有元件互通：

- [ ] `git clone` repo 成功
- [ ] `make dev`（或同等）起本地 stack：PG / Redis / API / Worker
- [ ] `curl http://localhost:8000/health` 回 200
- [ ] `pytest` 跑空套件通過（即使沒測試也應綠）
- [ ] 直接呼叫 Anthropic API 成功（用 `curl` 或一個 hello script）
- [ ] 直接 push 一則 LINE 訊息到 sandbox channel 成功
- [ ] `psql` 連本地 PG 成功
- [ ] 寫一筆假資料進本地 PG，從另一連線讀出來

## I. 第一週節奏（W3 Day 1~5）

| Day | 重點 | 產出 |
|---|---|---|
| Day 1 | 本 checklist A~H 全綠 | 本 checklist 全勾 |
| Day 2 | FastAPI app 骨架 + Alembic 初始化 + Dockerfile | `feat/s2-scaffold` PR |
| Day 3 | DB migration：先建 5 張核心表（Tenant, ApiKey, KnowledgeCard, AuditLog, Conversation） | migration PR |
| Day 4 | Auth middleware + RLS context | auth PR |
| Day 5 | KB ingest pipeline (PDF) 跑通最簡單版 | `feat/s2-kb-ingest-pdf` 起 |

## J. 退出條件（本 checklist 何時完成？）

達成以下全部即可宣告 kickoff 完成：

- [ ] A~F 全勾（基礎設施）
- [ ] D 必讀全勾（spec 已內化）
- [ ] G 若 S2 已啟動則必勾（pilot 簽下）
- [ ] H 冒煙流程跑通
- [ ] I Day 1 任務完成

完成後通知 CTO 在 `docs/LAUNCH-DASHBOARD.md` 更新 S2 為 IN PROGRESS。

## K. 受阻處理

任何項目 > 2 小時無法解開：
1. Slack `#engineering` 開 thread 描述「卡在哪 / 試過什麼 / 需要什麼」
2. 同時在本 checklist 旁邊註記 `🚫 blocked: <reason>`
3. CTO 1 小時內回應或指派 unblock
4. 超過 24h 仍阻塞 → 升級為 P1（依 RUNBOOK-001）

---

## 變更紀錄

| 日期 | 變更 | Owner |
|---|---|---|
| 2026-05-17 | 初版發布 | CTO |
