---
id: REPORT-S2-PROGRESS-TIER4
title: S2 進度報告 — Tier 3 + Tier 4 MC-011 (2026-05-22 下午)
date: 2026-05-22
owner: CTO
type: one-shot progress report
period: 2026-05-22 中午 ~ 下午
related: [LAUNCH-DASHBOARD, DEV-PLAN-PHASE1-2026-05, S2-PROGRESS-2026-05-22, ADR-0012, MC-001, MC-006, MC-009, MC-011, NANOBOT-EVALUATION-2026-05-18]
---

# S2 進度報告 — Tier 3 + Tier 4 (MC-011)

> 接續 `S2-PROGRESS-2026-05-22.md`（Tier 0~2 完成 snapshot）。本檔記
> Tier 3 (EmployeeRuntime + Governance Hooks) 與 Tier 4 第一塊
> (MC-011 Channel Gateway DB schema) 的完成。

---

## 1. 摘要

| 維度 | 期初（05-22 中午）| 期末（05-22 下午）| 變動 |
|---|---|---|---|
| DB 表完成 | 15 / 25 (60%) | **18 / 25 (72%)** | +3 |
| Test 數量 | 71 | **119** | +48 |
| Test coverage | 99.63% | **98.82%** | -0.81%（樣本擴大正常）|
| 程式碼行數 | 5273 | **7400+** | +2127 |
| Migrations | 3 | **4** | +1 |
| Governance Layer 落地 | 0 / 3 | **3 / 3 ✅** | +3 |
| 開啟 feat branch (累計 push) | 5 | **7** | +2 |
| Tier 完成 | 0/4 → Tier 0+1+2 ✅ | **Tier 0+1+2+3 ✅ + Tier 4 部分 🟡** | +1.5 |

**一句話結論**：**Governance Layer 三大支柱（Audit/Policy/Quota）全部落地為 hook**；EmployeeRuntime 借鑑 nanobot 設計自寫 ~150 行 Python；MC-011 Channel Gateway 儲存層完成（webhook dedup + outbound retry 表）。

---

## 2. 已完成（2 個 feat branch 全 push）

### 2.1 ✅ `feat/s2-employee-runtime`（1 commit）— Tier 3

**MC-009 Employee Runtime + Hook 系統**：依 ADR-0012 §11.2 借鑑 nanobot/agent/hook.py 設計，自寫 AEOS 精簡版。

落地檔案：
| 檔 | 角色 |
|---|---|
| `app/agent/context.py` | `AgentContext` (frozen dataclass) + `ToolDecision` (allow/block) |
| `app/agent/hook.py` | `AgentHook` ABC + `CompositeHook` 串接（short-circuit on block） |
| `app/agent/runtime.py` | `EmployeeRuntime.run_turn()` orchestrator + `ToolCallRecord` + `TurnResult` |
| `app/agent/hooks/audit.py` | **AuditHook** — 每個 LLM/tool call 發 `ai.llm_call` / `ai.tool_call` AuditEvent |
| `app/agent/hooks/policy.py` | **PolicyHook** — 從 DB tool_policy 按 priority 評估 YAML rule（block_risk_tier / block_tool）|
| `app/agent/hooks/quota.py` | **QuotaHook** — per-tenant token 累加 + monthly cap raise QuotaError |

Phase 1 簡化決策：
- 單次 LLM call per turn（不做 multi-turn tool loop）— S5 再擴
- in-memory token counter（重啟歸零）— Phase 2 改 Redis token bucket
- YAML evaluator 只認 block_risk_tier / block_tool — 完整 DSL Phase 2

**Tests**：37（hook 9 + runtime 10 + quota 6 + policy 8 + audit 5）

對齊：MC-001 / MC-006 / MC-009 / QUOTA-001 / engineering-charter §1+§2

### 2.2 ✅ `feat/s2-channel-gateway`（1 commit）— Tier 4 第一塊

**MC-011 Channel Gateway 3 表**：

| 表 | 用途 |
|---|---|
| `channel_binding` | Employee ↔ channel 綁定（3 channel CHECK + unique(emp,channel)）|
| `webhook_event` | 複合 PK (id, channel) 用於 webhook dedup；7 天 cron purge |
| `outbound_message` | 出站訊息追蹤（4 態 status + retry_count + partial idx_pending）|

落地細節：
- channel_binding：employee_id FK ON DELETE CASCADE
- webhook_event：同 id 不同 channel 可共存（測試 verified）
- outbound_message：partial index `WHERE status IN ('pending','retrying')` 給 worker 撿活用
- 3 個 RLS policy（cb / webhook_event allow_all；outbound 用 tenant_id 比對）

**Tests**：11（CRUD + check constraints + cascade delete + partial index 存在 + RLS）

對齊：db-schema.md §4.7~§4.9 + MC-011 + API-002

---

## 3. 驗證 snapshot

| 檢查 | 結果 |
|---|---|
| `pytest` | ✅ **119 passed** |
| Coverage | ✅ **98.82%** / 80% gate |
| `ruff check` | ✅ All checks passed |
| `mypy strict` | ✅ no issues in 61 source files |
| `alembic upgrade head` | ✅ 4 migrations → 18 base tables + 8 message partitions = 27 relations |
| Governance Hooks 串接 | ✅ Audit + Policy + Quota 都可在 CompositeHook 內 chain，block 短路測試通過 |
| MC-011 webhook dedup PK | ✅ 同 (id, channel) 二次 INSERT 觸發 IntegrityError |
| outbound partial index | ✅ pg_indexes verified `WHERE status IN ('pending','retrying')` |

---

## 4. Tier 完成度地圖（更新）

```
Tier 0  基礎設施 ✅✅✅
Tier 1  Auth + Data Models ✅✅✅✅ (9 表)
Tier 2  LLM + Tool ✅✅✅ (6 表 + LLMClient + skills/)
Tier 3  Runtime ✅✅✅
  ├── ✅ EmployeeRuntime (MC-009) — 借鑑 nanobot agent loop
  ├── ✅ Hook 系統 (AgentHook + CompositeHook)
  └── ✅ 3 governance hooks (Audit / Policy / Quota)

Tier 4  Channel + UI 🟡 (1.5 / 5)
  ├── ✅ MC-011 Channel Gateway DB schema (3 表) — 本輪
  ├── 🚫 LINE webhook 端點 (HMAC + dedup + 1s ACK)
  ├── 🚫 ToolExecutor (依 MC-006 tool_type 分派)
  ├── 🚫 KB ingest pipeline worker
  └── 🚫 Conversation 6 態狀態機 + L2.5 summary
```

---

## 5. DB 表覆蓋 — 18/25 (72%)

| 已建 | 18 表 |
|---|---|
| MC-001/004/006 系列 (Tier 0+1+2) | tenant / api_key / audit_log / knowledge_card / ingestion_job / employee / conversation / message + 8 partitions / conversation_handoff / skill / skill_version / skill_binding / tool / tool_invocation / tool_policy |
| MC-011 (本輪) | channel_binding / webhook_event / outbound_message |

剩 7 表（Phase 1 範圍內）：
- MC-002 Training Room: `training_session` / `test_case` / `test_run` (S3)
- MC-003 Evaluation: `evaluation_metric` / `failure_record` (S5)
- 其他 2 表（依 db-schema §5 cross-reference）

---

## 6. S4 Critical Path 剩餘工作

依 DEV-PLAN §4.4 + AC-003 (`webhook ≤1s ACK / draft 生成 p95 ≤5s / approve+edit+reject 全進 audit`)，剩 3 大 application 層：

| # | 任務 | 預估 | 解鎖內容 |
|---|---|---|---|
| 1 | **ToolExecutor** | 中（半天）| EmployeeRuntime 接 real tool 執行；http_api 用 httpx、internal 用註冊 callable |
| 2 | **LINE webhook 端點** | 中（1 天）| `app/api/webhooks/line.py` + HMAC-SHA256 驗簽 + webhook_event PK insert (dedup) + 1s ACK + Redis enqueue |
| 3 | **KB ingest worker** | 大（2 天）| `app/worker/kb_ingest.py` + pypdf/python-docx + voyage-3-lite embedding + KC draft create |

3 件全完成 ≈ S4 Exit Gate（AC-003）達標。但仍需 pilot 客戶提供真實 LINE OA credentials + KB 才能跑端到端 BF-001。

---

## 7. 仍受阻（critical path）

- **pilot 客戶簽下** — 仍 hard-gate S2~S8 整段 live；LAUNCH-DASHBOARD line 52「Pilot 客戶簽約數 = 0」
- **S1-4 OBS infra**（Hetzner 帳號）
- **S1-7 Oncall**（Slack + PagerDuty）

不受 pilot 影響的「程式碼可動」工作仍餘豐：本檔 §6 列的 3 大件 + S3 Training Room 表 + LINE sandbox channel 申請（CTO 自己可做 30 分鐘）。

---

## 變更紀錄

| 日期 | 變更 | Owner |
|---|---|---|
| 2026-05-22 下午 | 初版（Tier 3 + MC-011 完成 snapshot；18/25 表 / 119 tests / Governance 三大支柱落地）| CTO |
