---
id: S2-PROGRESS-2026-05-22-expert-review
title: S2 — Expert Review + CI + E2E Smoke 完成報告
status: active
type: report
created: 2026-05-22
owner: CTO
tier: 5
---

# S2 進度報告 — 2026-05-22（Draft Mode + CI + E2E）

> 接續 `S2-PROGRESS-2026-05-22-tier4-complete.md`。本檔覆蓋 Tier 4 之後到 Expert Review 端到端完成這段。

## 完成項目（本回合）

| # | 項目 | Branch | 重點 |
|---|---|---|---|
| 1 | Worker polling loop | `feat/s2-worker-loop` | DraftPoll + OutboundPoll + `SELECT FOR UPDATE OF c SKIP LOCKED` + idle/exception backoff |
| 2 | KB ingest pipeline | `feat/s2-kb-ingest` | pdf/docx/md/txt parser + chunk_text + StubEmbeddingClient (1024-dim L2) → KC drafts |
| 3 | Expert review 後端 API | `feat/s2-expert-review-api` | migration `5c56148236b0`（outbound status 4→6 態：+awaiting_review/+rejected）；service `approve / edit_and_approve / reject / list_pending`；FastAPI router `/api/v1/expert/*` 4 endpoint；14 tests |
| 4 | Expert Console UI | `feat/s2-expert-review-ui` | Vite 6 + React 19 + TS strict + Tailwind 3；ReviewCard 三 mode（view/edit/reject）；expert_id localStorage；7 vitest |
| 5 | CI 拆 backend / web-expert | `ci/web-expert` | `dorny/paths-filter@v3` 偵測；3 job（detect-changes + backend + web-expert + ci-gate aggregator） |
| 6 | Draft Mode E2E smoke | `test/draft-mode-e2e` | `tests/e2e/test_draft_mode_pipeline.py` × 2 tests：完整鏈路 + reject 路徑 |

## 量化指標

| 指標 | 上回（tier4-complete） | 本次 | Δ |
|---|---|---|---|
| Tests（Python） | 180 | 238 | +58 |
| Coverage | 93.16% | 93.30% | +0.14% |
| Tests（前端 vitest） | 0 | 7 | +7 |
| LOC（總）| 10607 | 13881 | +3274 |
| - app/ | 4198 | 5233 | +1035 |
| - tests/ | 4636 | 6062 | +1426 |
| - alembic/ | 1537 | 1649 | +112 |
| - skills/ | 236 | 236 | 0 |
| - web/expert/src/ | 0 | 701 | +701 |
| DB 表 | 18 / 25 (72%) | 18 / 25 (72%) | 0 |
| Outbound status 態數 | 4 | 6 | +2 (+awaiting_review/+rejected) |

## 關鍵設計決策

### 1. Draft Mode 走「擴 status」而非「新表」
PRD §5.4 的 Draft Mode 行為是「AI 產 draft 但不立即送」。兩個選項：
- (A) 新建 `outbound_draft` 表 → 一個 conversation 兩條 outbound 流（複雜）
- (B) 擴 `outbound_message.status` CHECK 加 `awaiting_review` / `rejected` → 同一條 row 從 awaiting_review 流向 pending 或 rejected

選 (B)：
- OutboundProcessor 的 partial index `WHERE status IN ('pending', 'retrying')` 自然把 awaiting_review 隔離（rejected 也不會被撿）
- audit / retry / message_id 全部 reuse 既有欄位
- migration 只動 CHECK constraint，無 backfill

成本：DraftProcessor 多 1 個 constructor param `outbound_initial_status`（預設 'pending' 向後相容）。

### 2. Expert UI 用 monorepo lite 結構
`web/expert/` 與 Python 後端共存於同 repo：
- 不獨立 repo 的原因：Phase 1 expert UI 必須跟 backend 同步版本（API 改 = UI 改），分 repo 反而增加同步成本
- node_modules / dist / *.tsbuildinfo 已 ignore
- CI 加 path filter 讓僅改 backend 不跑前端 job，反之亦然
- 上線時兩個 artifact 一起 build（後端 docker image + 前端 dist/ 由 nginx 服務）

### 3. expert_id 暫時走 localStorage
Phase 1 內網試用，沒有 auth gate。UI 內 expert_id 是輸入框，存 localStorage。
- S5 補 MFA + RBAC 時改成 server-side session/JWT
- 不影響 audit trail（service 層的 actor_id 直接從 request body 帶入，會進 audit_log）

### 4. CI ci-gate aggregator
`ci-gate` job 聚合 backend + web-expert 結果，repo 的 required check 設這個就好。
- 純文件 PR：兩個 job 都 skipped → ci-gate 仍 pass（skipped 視為通過）
- 任一 job 失敗 → ci-gate 失敗 → block merge
- 不用每改一支 branch 就到 settings 改 required check 列表

### 5. E2E smoke 不接真 LINE
`tests/e2e/test_draft_mode_pipeline.py` 用 `httpx.MockTransport` 攔 LINE Push。
- 為什麼不接真 LINE：(1) LINE sandbox channel 還沒註冊；(2) E2E 在 CI 跑，不能依賴外網
- 真實 LINE 整合留給 staging 環境 + 手動 smoke（S6 Pilot Hardening 時）

## 剩下的真實 blocker

| Blocker | 性質 | 解鎖人 | 時間估 |
|---|---|---|---|
| Hetzner Cloud 帳號 | 外部（信用卡 + KYC） | CTO | 1 天 |
| Slack workspace + PagerDuty Free | 外部 | CEO + CTO | 半天 |
| LINE Developers Console sandbox channel | 外部 | CTO | 30 分鐘 |
| Pilot 客戶簽約 | 商業 critical path | CEO | unknown |

不再有「可寫 code 但卡架構決策」類的 blocker。

## 下一波可推進（不需外部資源）

| # | 項目 | 估時 | 價值 |
|---|---|---|---|
| 1 | KC review UI（複用 web/expert 結構） | 1-2h | pilot KB ingest 後 expert 審稿介面 |
| 2 | OBS IaC 預備（docker-compose.observability.yml + prometheus/grafana config） | 1h | Hetzner 帳號開好後直接套用 |
| 3 | 合併 6 支 feature branch 到 main | 30min | 統一 main 為單一事實源 |
| 4 | 重新計算 traceability matrix + flow-index（AI-AUTO） | 5min | 視圖 cache 同步 |

## 對應 AC 進度

| AC | 條件 | 狀態 |
|---|---|---|
| AC-003 §1 | webhook ≤1s ACK | ✅ (LINE webhook 設計 + test) |
| AC-003 §2 | draft 生成 p95 ≤5s | 🟡 待真實負載驗證 |
| AC-003 §3 | approve/edit/reject 全進 audit | ✅ (expert_review service + audit hook + E2E 斷言) |

AC-003 三條全部就緒，僅剩真實負載驗證（pilot 上線後量）。
