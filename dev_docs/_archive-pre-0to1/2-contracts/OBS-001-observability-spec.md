---
id: OBS-001
title: Observability Specification — Phase 1
status: active
type: observability-spec
created: 2026-05-15
last-synced-with: abbd2b83fd1ec10383cb68850fff218c1ad57923
owner: CTO
tier: 2
related: [SAD-v0.1, NFR-001, RUNBOOK-001, ADR-0008, PILOT-001]
---

# OBS-001 — 可觀測性規範 (Phase 1)

> 「**沒被量測的就沒被管理。**」本文定義 Pilot 期需要的 metrics / logs / traces / alerts。違反此規範的 PR 在 review 時拒絕。

## 1. 三大支柱原則

| 支柱 | Phase 1 工具 | 保留期 |
|---|---|---|
| **Metrics**（時序聚合數據） | Prometheus + Grafana（self-host on Hetzner） | 30 天高解析 + 13 個月 downsampled |
| **Logs**（結構化事件） | Loki + Grafana | 30 天 hot + 90 天 cold S3 |
| **Traces**（請求追蹤） | OpenTelemetry → Tempo | 7 天 |

正式 stack 決策見 ADR-0008。本文先定**規範**，stack 可替換。

## 2. Golden Signals（每服務必出 4 指標）

依 Google SRE Golden Signals：

| Signal | 定義 | Phase 1 量測 |
|---|---|---|
| **Latency** | 請求耗時 p50/p95/p99 | histogram metric per endpoint |
| **Traffic** | RPS / msg/s | counter |
| **Errors** | 5xx + 業務錯誤率 | counter + breakdown by error_code |
| **Saturation** | CPU / memory / queue depth / DB conn pool | gauge |

每個 service（agent-worker / api-gateway / webhook-handler / ingest-worker）必須暴露這 4 個指標。

## 3. 業務 KPI Metrics（對應 PILOT-001 §2）

| Metric 名稱 | 類型 | Label | 目的 |
|---|---|---|---|
| `aeos_conversations_total` | counter | tenant_id, status (auto_resolved / escalated / abandoned) | auto-reply rate |
| `aeos_test_set_pass_rate` | gauge | tenant_id | 對應 AC-002 |
| `aeos_escalation_correctness` | gauge | tenant_id | 對應 AC-003 |
| `aeos_e2e_latency_seconds` | histogram | step (webhook / llm / reply) | NFR-001 §1 |
| `aeos_llm_tokens_total` | counter | tenant_id, model, type (prompt / completion) | QUOTA-001 |
| `aeos_llm_cost_usd_total` | counter | tenant_id, model | 成本追蹤 |
| `aeos_active_tenants` | gauge | - | 商業健康 |
| `aeos_kb_ingest_jobs_total` | counter | tenant_id, status | KB 健康 |

實作位置：每 service 內 `metrics.py`（Python）/ `metrics.go`（Go）centralized。

## 4. Logging 規範

### 4.1 結構化 JSON（強制）

每行 log 必須是合法 JSON，包含：

```json
{
  "ts": "2026-05-15T10:23:45.123Z",
  "level": "info | warn | error | debug",
  "service": "agent-worker | api-gateway | webhook-handler | ingest-worker",
  "trace_id": "<otel trace id>",
  "span_id": "<otel span id>",
  "tenant_id": "<uuid>",
  "user_id": "<hashed; never raw PII>",
  "event": "<snake_case_event_name>",
  "msg": "<human readable>",
  "...": "<event-specific fields>"
}
```

### 4.2 必記事件（Audit Log）

以下事件 **必須** 記錄，且寫入獨立 audit log channel（不可僅 stdout）：

| Event | 觸發 | 必含欄位 |
|---|---|---|
| `llm.call` | 每次 LLM 呼叫 | model, prompt_tokens, completion_tokens, latency_ms, cost_usd |
| `tool.invoke` | 每次 agent 工具呼叫 | tool_name, args_hash, result_status |
| `policy.decision` | guardrail / escalation 決策 | rule_id, action, reason |
| `auth.login` | 使用者登入 | user_id, ip, ua, mfa_used |
| `data.access` | 存取 PII / 知識卡片 | resource, action (read/write), justification |
| `data.export` | 任何資料匯出 | resource, dest, requester |
| `config.change` | 系統設定變更 | actor, key, old_value_hash, new_value_hash |

對應 ADR-0005 §audit 要求。

### 4.3 禁止項

- ❌ **絕不**記錄完整 PII（姓名、電話、地址、訂單）— 必須 hash 或 mask
- ❌ **絕不**記錄 prompt/completion 原文 to public log — 只記 token 數與 hash；原文進 audit-only encrypted store
- ❌ **絕不**記錄 secrets（API key、token、密碼）— 即使 hash 也不行
- ❌ **絕不**使用 `console.log` / `print` — 必須走 structured logger

## 5. Tracing 規範

### 5.1 採樣率

| 環境 | 採樣率 |
|---|---|
| dev | 100% |
| pilot prod | 10%（一般）+ 100%（error） |
| 未來 GA | 1%（一般）+ 100%（error / slow > p99） |

### 5.2 必有 Span

關鍵路徑必須有 span，並 propagate trace_id：

```
http.request
  └─ webhook.verify_signature
  └─ session.lookup
  └─ agent.run
       ├─ rag.retrieve
       ├─ llm.call
       └─ tool.invoke
  └─ reply.send_line
```

## 6. Dashboards（Grafana）

Pilot 期最少 4 個 dashboard，定義於 `infra/grafana/dashboards/`：

| Dashboard | 受眾 | 核心 panel |
|---|---|---|
| **D1 — Product Health** | CEO + CTO | auto-reply rate, test set pass rate, e2e latency p95, active tenants |
| **D2 — Tech Health** | CTO + Eng | RPS, error rate, latency p95/p99, saturation per service |
| **D3 — LLM Cost & Usage** | CTO + Finance | tokens/min, USD/day, top tenant by cost, model split |
| **D4 — Per-Tenant Drill-down** | Customer Success | 單 tenant 的所有 KPI（用 tenant_id filter） |

## 7. Alerts

### 7.1 告警分級對應 RUNBOOK-001 severity

| Alert | 條件 | Severity | 通知管道 |
|---|---|---|---|
| `service_down` | `up == 0` for 1m | P0 | PagerDuty + Slack #alerts |
| `error_rate_high` | 5xx rate > 5% for 5m | P1 | PagerDuty + Slack |
| `latency_p95_breach` | e2e p95 > 10s for 10m | P1 | Slack |
| `llm_provider_down` | LLM error rate > 50% for 2m | P1 | PagerDuty |
| `llm_cost_spike` | tenant 1h cost > 平均 * 5 | P1 | Slack |
| `disk_usage_high` | > 85% | P2 | Slack |
| `cert_expiry` | TLS cert < 14 days | P2 | Slack（每日 digest） |
| `backup_failed` | RUNBOOK-003 daily snapshot 失敗 | P0 | PagerDuty |
| `pii_audit_anomaly` | data.access 數量 > 平均 * 10 | P1 | Slack + email CTO |

### 7.2 告警設計原則

- **可動作（Actionable）**：告警必須對應 RUNBOOK-001 §4 一個 playbook；無 playbook 的告警禁止上線
- **無雜訊（Low noise）**：每週 review 觸發次數；> 5 次/週且非真實事故 → 調整閾值或刪除
- **聚合（Group）**：同類告警 5 分鐘內合併，避免 alert storm

## 8. SLO（Service Level Objectives）

| SLO | 目標 | Error Budget（月） |
|---|---|---|
| **可用性**（webhook 接收） | 99.5% | 3.6 小時 |
| **可用性**（管理後台） | 99.0% | 7.2 小時 |
| **延遲**（e2e p95 ≤ 8s） | 95% 時間達標 | 36 小時違反 |
| **回答正確率**（test set） | ≥ 85% | 每月不可低於 80% > 7 天 |

**Error budget burn rate alerts**：
- 1 小時內燒掉 14% budget → P1 告警
- 6 小時內燒掉 5% budget → P1 告警

## 9. PII / Compliance

- Log / metric / trace **任一支柱都不可** 含 raw PII（對應 ADR-0005）
- Tenant 必須能下載屬於自己 tenant_id 的 audit log（PII shadow 已 mask）
- Audit log 保留至少 13 個月（法遵基線）

## 10. 實作優先序（Pilot 13 週）

| Week | 交付 |
|---|---|
| W1 | Prometheus + Grafana + Loki on Hetzner；service 出 Golden Signals |
| W2 | §3 業務 KPI metrics；D1 + D2 dashboard 上線 |
| W3 | OTel tracing；§4.2 audit log 寫入獨立 store |
| W4 | Alerts §7.1 全部接入 PagerDuty/Slack |
| W6 | D3 cost dashboard；§8 SLO 監控上線 |
| W8 | D4 per-tenant dashboard；error budget burn alert |

## 11. PR Review Checklist（與本規範相關）

- [ ] 新 endpoint 是否暴露 Golden Signals？
- [ ] 新業務事件是否加入 §3 metric？
- [ ] 新 log 是否符合 §4.1 JSON 結構？
- [ ] 是否有意外 log raw PII / secrets？
- [ ] 新 alert 是否對應 RUNBOOK-001 playbook？

---

**See also**:
- `NFR-001-non-functional-requirements.md` §2 §3 — 量化目標基線
- `RUNBOOK-001-incident-response.md` §4 — 告警對應 playbook
- `PILOT-001-success-criteria.md` §2 — 業務 KPI 來源
- `ADR-0005-data-retention-pii.md` — PII 在 log 中的處理
- `ADR-0008-observability-stack.md` — stack 選型決策
