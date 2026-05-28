---
id: NFR-001
title: Non-Functional Requirements — Phase 1
status: active
type: nfr
created: 2026-05-14
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 2
related: [SAD-v0.1, ADR-0004, ADR-0005]
---

# NFR-001 — Phase 1 Non-Functional Requirements

> 對 Phase 1 的所有 NFR 一次定義；任何 PR 違反 → 必須在 PR 描述說明 trade-off。

## 1. Performance / Latency

| 指標 | p50 | p95 | p99 | 量測點 |
|---|---|---|---|---|
| **LINE webhook ACK** | ≤ 200ms | ≤ 800ms | ≤ 1.5s | nginx access log |
| **LLM draft generation**（含 RAG） | ≤ 2.5s | ≤ 5s | ≤ 10s | Worker emit metric |
| **Auto reply 端到端**（user 收到回覆） | ≤ 4s | ≤ 8s | ≤ 15s | timestamp diff |
| **KC 列表分頁查詢** | ≤ 80ms | ≤ 250ms | ≤ 500ms | API log |
| **Test set 50 題 run 完** | ≤ 3min | ≤ 5min | ≤ 8min | run_done timestamp |
| **KB ingest 100 頁 PDF** | ≤ 2min | ≤ 5min | ≤ 10min | ingest_job timestamps |

不達標 → 在 PR description 加 `latency-regression` label，CTO review。

## 2. Availability

| 元件 | Phase 1 目標 | 量測 |
|---|---|---|
| Web SPA | 99% | uptime monitor（外部 ping） |
| API webhook endpoint | **99.5%** | 同上（webhook 失效 = 客戶端訊息漏掉，痛點高） |
| Worker | 99%（可短暫離線，queue 會堆） | self health check + redis queue depth |
| PostgreSQL | 99.5% | docker compose health |
| Redis | 99%（重啟丟 queue 可接受） | 同上 |

- **不寫進客戶合約**（Phase 1 SLA agreement only after Phase 2）
- 計劃內維護視窗：每月一次，凌晨 02:00–04:00，事前通知客戶

## 3. Scalability（Phase 1 上限）

| 維度 | 設計上限 | 觸發升級 |
|---|---|---|
| 並發 webhook | 10 / sec / VM | > 5/sec → scale worker |
| 對話 / 日 / tenant | 1,000 | > 700 → 監控 |
| Knowledge Cards / tenant | 1,000 | > 500 → 評估 vector index 升級 |
| Test set 題目 / tenant | 200 | 不會超過（合約限制） |
| Skill versions（global） | 50 | > 30 → 評估 DB index |
| Tenant 數 | 1（單租戶部署） | > 1 即違反 ADR-0004 |

Phase 2 才談 horizontal scaling。

## 4. Security

### 4.1 Transport
- 全 endpoint HTTPS only（Cloudflare + nginx）
- HSTS preload
- TLS 1.2+；禁用 1.0/1.1

### 4.2 Authentication
- API Key：bcrypt cost 12；存 hash never plaintext
- Session cookie：httpOnly + Secure + SameSite=Lax；30 天 expiry
- CSRF token: required for state-changing requests

### 4.3 Authorization
- RBAC scopes：`expert`, `cto`, `super_admin`
- `cto` 才能呼叫 `/admin/*`
- 跨 tenant 操作禁止（即便 super_admin 也須切 tenant context）

### 4.4 Secrets
- 一律走 env（不入 git）
- LINE secret / Anthropic key / PII vault key 用 SOPS+age 加密存 repo（per-tenant）
- 部署時用 GitHub Actions secret 解密注入

### 4.5 Audit
- 所有 state transition → AuditEvent（trigger 強制 append-only）
- 100% endpoint 寫 access log（IP, actor, request_id）

### 4.6 Webhook signature
- LINE webhook：必驗 X-Line-Signature（HMAC-SHA256），錯則 403 + audit

### 4.7 Input validation
- Pydantic schema at API boundary；過長 / 過大 payload reject
- 上傳檔案 magic byte 驗證；防 polyglot

### 4.8 SQL injection / XSS
- ORM only（SQLAlchemy）；禁止 raw SQL string concat
- 前端 React 預設 escape；禁用 `dangerouslySetInnerHTML`

### 4.9 Rate limiting
- 60 req/min/api_key 預設；逐 endpoint 可調
- 失敗 401/403 後 10 次 → soft block 5 min

### 4.10 Vulnerability management
- `npm audit` / `pip-audit` 每週 CI 跑
- CVE high+ 7 天內處理；critical 24h 內

## 5. Compliance / Privacy

| 項目 | Phase 1 |
|---|---|
| 台灣個資法（PDPA） | ✅ 完全遵守（資料留台、可刪、可查、目的揭露） |
| GDPR-like 習慣 | ✅ pseudonymize + 保留期限 + 可攜性（CSV export） |
| SOC 2 | ❌ Phase 1 不認證；客戶 ≥ 10 才啟動 |
| ISO 27001 | ❌ Phase 1 不認證 |
| HIPAA / PCI-DSS | ❌ 客戶若觸及醫療 / 信用卡 = 拒接 |

詳見 ADR-0005。

## 6. Reliability

- **Backup**：PG 每日 `pg_dump` → encrypted → S3-compatible storage；保留 30 天
- **Recovery**：RPO ≤ 24h、RTO ≤ 4h；每季演練一次
- **Idempotency**：所有 POST 接受 `Idempotency-Key`；webhook 用 `webhookEventId` dedup
- **Retry**：Worker job 3 次 exp backoff；外部 API call 同政策
- **Dead Letter Queue**：失敗 job 進 DLQ + alert；不靜默丟

## 7. Observability

| 訊號 | Phase 1 工具 | Phase 2 升級 |
|---|---|---|
| Logs | docker logs (JSON stdout) | Loki + Grafana |
| Metrics | `/metrics` Prometheus endpoint（不開外網） | Prometheus + Grafana |
| Errors | Sentry SaaS free tier | Sentry self-host |
| Tracing | 無（Phase 2 加 OpenTelemetry） | OpenTelemetry + Tempo |
| Alerts | Email / Slack webhook | PagerDuty |

**必設 Alert（Phase 1）**：
1. API error rate > 5% (5min window)
2. Webhook 5xx > 1% (5min window)
3. Worker queue depth > 100 lasting > 10min
4. LLM cost / day > 2x 平均
5. DB disk usage > 80%
6. Anomaly detected (UF-004 §A1)
7. Emergency disable triggered (UF-005)

## 8. Maintainability

- 程式碼覆蓋率 ≥ 80%（unit + integration）
- 函式 ≤ 50 行；檔案 ≤ 800 行
- 縮排 ≤ 3 層（Linus 規）
- 不可變優先；錯誤邊界處理
- 每 PR ≤ 400 行 diff（超過拆 PR）
- Lint 強制過（pre-commit hook）

## 9. Cost

| 項目 | 目標 | 上限 |
|---|---|---|
| 單 tenant VM 月成本 | < NT$ 1500 | < NT$ 3000 |
| LLM 月成本 / tenant | < NT$ 2000 | < NT$ 5000 |
| 工具 / SaaS 月固定 | < NT$ 1500（Sentry, S3, etc.） | < NT$ 3000 |
| **總月成本 / tenant** | **< NT$ 5000** | **< NT$ 11000**（= 月費下限的 30%） |

每月 cost report 給 CEO。

## 10. Portability / Deployability

- 部署 = `docker compose up`；無 IaaS 鎖入（任一雲皆可跑）
- DB migration = Alembic（Python）或 node-pg-migrate；單一指令 forward / rollback
- Rollback：保留 N-2 版本的 docker image；rollback 指令 ≤ 30 秒生效

## 11. 不做的 NFR（明文）

- Multi-region failover（Phase 3）
- Sub-second LLM 回應（不可能）
- 99.99% SLA（Phase 3）
- 零 downtime deploy（Phase 2 加 blue-green）
- Active-active replication（Phase 3）

## 12. 連結
- 架構：`SAD-v0.1.md`
- 部署：`ADR-0004`
- PII / 資料政策：`ADR-0005`
- LLM 成本：`ADR-0001`
