---
id: ADR-0008
title: Observability Stack Choice
status: accepted
date: 2026-05-15
deciders: CTO
tier: 1
---

# ADR-0008 — 可觀測性技術棧選擇

## Context

OBS-001 定義了「該量測什麼」，本 ADR 決定「用什麼工具量測」。

需求：
- 三大支柱（metrics / logs / traces）都要
- Phase 1 預算 ≤ US$ 100/月（含基礎設施）
- 單人可運維
- 不鎖死 vendor（後續可遷移）
- 支援 OpenTelemetry 標準（避免 instrumentation 重寫）

主流選項：

| 方案 | 月成本（est） | 優 | 劣 |
|---|---|---|---|
| **Datadog** | $1,000+（5 host） | 一站式、UX 好 | 貴；data lock-in |
| **New Relic** | $500+ | 同上 | 同上 |
| **Grafana Cloud Free** | $0 + 超量 $ | 標準棧、可遷移 | 量超就貴 |
| **Self-host Grafana stack（LGTM）** | $30~50（infra） | 完全自主、無 lock | 自己維運 |
| **AWS CloudWatch** | $20~80 | 與 AWS 整合好 | 我們不在 AWS（Hetzner） |
| **Better Stack / Highlight / 等新品** | $50~150 | UX 好 | Vendor 風險、small player |

## Decision

**Phase 1：Self-host Grafana LGTM stack on Hetzner**
- **L**oki — logs
- **G**rafana — visualization
- **T**empo — traces
- **M**imir / **P**rometheus — metrics

**Phase 2 評估遷移路徑**：負載超過自管能力時，遷至 Grafana Cloud（同 stack，零 instrumentation 改動）。

### 1. 元件清單

| 元件 | 角色 | 部署 |
|---|---|---|
| Prometheus | Metric scraping + 短期儲存（15d） | Docker on Hetzner（與 app 同機 Phase 1） |
| Loki | Log aggregation | Docker；後端 S3 cold |
| Tempo | Trace storage | Docker；後端 S3 |
| Grafana | UI / dashboard / alert | Docker |
| OpenTelemetry Collector | 接 OTLP，分流 metric/log/trace | Sidecar pattern |
| Alertmanager | Alert routing（Slack / PagerDuty） | Docker |
| Pushgateway | Batch job metrics | Docker |
| Promtail / OTel Collector | Log shipping | DaemonSet 模式 |

### 2. Instrumentation 標準

- **強制 OpenTelemetry SDK**（Python: `opentelemetry-instrumentation-*`；TS: `@opentelemetry/api`）
- Metric naming：Prometheus 慣例 `aeos_<noun>_<unit>_<aggregation>`
- Log：JSON structured（OBS-001 §4.1）
- Trace：W3C trace-context propagation

### 3. 部署架構

```
┌─────────────────────────────────────┐
│ App services（agent-worker, api,    │
│ webhook-handler, ingest-worker）    │
│  └─ OTel SDK → OTLP HTTP            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ OTel Collector（sidecar）            │
│  ├─ metrics → Prometheus            │
│  ├─ logs → Loki                     │
│  └─ traces → Tempo                  │
└─────────────────────────────────────┘
       │           │           │
       ▼           ▼           ▼
   Prometheus   Loki        Tempo
       │           │           │
       └───────────┴───────────┘
                   │
                   ▼
              Grafana ◄─── (browser)
                   │
                   ▼
              Alertmanager → Slack / PagerDuty
```

### 4. 資源與成本

| 項目 | Spec | 月成本估 |
|---|---|---|
| Hetzner CX31（4 vCPU, 8GB） | 監控專用 VM | €15 |
| S3（B2 cheaper）冷資料 | 200GB | $10 |
| Better Stack（uptime + status page） | Free tier → starter | $0 ~ $25 |
| PagerDuty / OnCall（Phase 1 用 Grafana OnCall self-host）| - | $0 |
| **合計** | | **~$30~50/月** |

對比 Datadog（$1000+）= **節省 95%**，代價是運維時間（預估 4 hr/月 maintenance）。

### 5. 保留期

| 資料 | Hot（高解析） | Cold（downsampled / S3） |
|---|---|---|
| Metrics | 15 天 1m 解析 | 13 個月 1h 解析 |
| Logs | 30 天 | 90 天 S3（grep 用 `logcli`）|
| Traces | 7 天 | 不長期保留 |
| Audit log | 13 個月（合規） | 同 |

## Consequences

### 正向

- 月成本可控（< $50）
- 完全 vendor-neutral（遷 Grafana Cloud 零成本）
- OTel 標準確保 instrumentation 不被鎖
- 同事熟悉度高（Grafana 業界普及）

### 負向

- 需要自己維運（升級、磁碟、TLS cert）
- 預估 4 小時/月 維運時間 + 偶發故障
- 高負載時 self-host 可能成為瓶頸（→ §Phase 2 遷雲）

### 風險與緩解

| 風險 | 緩解 |
|---|---|
| 監控系統本身掛掉 = 看不見其他系統 | 用 Better Stack 做外部 uptime check 作為 last-resort |
| 磁碟爆滿 → log lost | Cron + alert 監控磁碟；自動 lifecycle 到 S3 |
| Grafana 升級爆 | Pin version；staging 環境先試 |
| 流量爆增成本失控 | Loki / Tempo 設 ingestion limit；超過降採樣 |
| 我們離職 / 無人懂 | 用標準 OSS，找接班人成本低 |

## Alternatives Considered

| 方案 | 為何不選（Phase 1） |
|---|---|
| **Datadog** | 月費 $1000+ 在 Pilot 期不可接受；後續 lock-in |
| **CloudWatch** | 不在 AWS；遷移成本 |
| **ELK stack** | Elasticsearch 資源吃重；Loki 對 log 更省 |
| **Sentry only** | 只覆蓋 error tracking，三支柱不全 |
| **Honeycomb** | 強在 tracing，但 metric/log 弱；總成本不低 |
| **Native Postgres + cron + dashboard 拼裝** | 不可擴展；無 alert；over-DIY |

## Migration Plan to Grafana Cloud（Phase 2 觸發條件）

觸發任一即啟動評估：

- Self-host instance CPU > 70% 持續 1 週
- 磁碟管理時間 > 8 hr/月
- Tenant 數 > 30
- 收入 > $50K/月（可負擔 $300/月 grafana cloud）

遷移實際操作：

- Grafana Cloud 支援 OTLP；改 OTel Collector remote-write endpoint 即可
- Dashboard / Alert / Trace 可 export-import（兼容格式）
- 預估遷移時間：< 1 day

## Implementation Notes

- 主要 IaC：`infra/observability/docker-compose.yml`
- Provisioning：`infra/observability/grafana/provisioning/`（dashboards as code）
- Alert rules：`infra/observability/alertmanager/rules/`
- Runbook 連結：每個 alert 在 annotation 帶 `runbook_url`

## Related

- OBS-001 — 規範（本 ADR 是 stack 實作）
- RUNBOOK-001 — 告警對應 playbook
- ADR-0004 — Deployment model
- NFR-001 §2 §6 — 量化目標
