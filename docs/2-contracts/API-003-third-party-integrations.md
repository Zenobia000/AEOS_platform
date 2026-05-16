---
id: API-003
title: Third-Party Integration Contracts
status: active
type: integration-contract
created: 2026-05-15
last-synced-with: a5d7a75bd822b8cf7d2b6d8c3157060f50848e86
owner: CTO
tier: 2
related: [SAD-v0.1, ADR-0001, QUOTA-001, SEC-001, OBS-001, LEGAL-001]
---

# API-003 — 第三方整合契約

> 「**每個第三方都是潛在故障點。**」本文件為每個外部依賴定義：用途、契約、認證、配額、失敗策略、退場方案。

## 1. 整合清單總覽

| 編號 | 服務 | 用途 | 關鍵性 | Provider |
|---|---|---|---|---|
| INT-001 | LLM Provider 主 | 對話生成 / 摘要 / 分類 | P0 — 沒它服務全停 | OpenAI / Anthropic（ADR-0001） |
| INT-002 | LLM Provider 副 | Fallback | P1 — 沒它降級不可用 | 另一家（ADR-0001） |
| INT-003 | Embedding Provider | RAG vector 生成 | P1 | OpenAI text-embedding-3-small |
| INT-004 | LINE Messaging API | Channel 訊息收發 | P0 — 主 channel | LINE Corporation |
| INT-005 | Object Storage | 檔案 / backup | P0 — 沒它資料丟失 | Hetzner Storage Box + S3 (B2) |
| INT-006 | Email Provider | 通知 / magic link / report | P1 | Postmark / Resend |
| INT-007 | Payment Provider | 訂閱收費 | P2（Pilot 期手收）| Stripe（Phase 2） |
| INT-008 | DNS / CDN | 域名 / 邊緣安全 | P0 | Cloudflare |
| INT-009 | SMS Provider | MFA 備援 / 緊急通知 | P2 | Twilio（Phase 2） |
| INT-010 | Error Tracking | 例外通報 | P2 | Sentry（self-host） |

詳細契約見下方分節。

---

## 2. INT-001 / INT-002 — LLM Provider

### 2.1 用途
- 對話回覆生成（Tier 1 / 2 / 3 模型，QUOTA-001 §2）
- KB ingest 標籤化
- 50 題 test set 評分
- 摘要 / 分類

### 2.2 認證
- API Key（per-tenant 或共用，依 LLM provider DPA）
- Key 存 KMS / env var；不進 git
- 月度 rotate

### 2.3 端點與模型
| Provider | 主模型 | 副模型 | 端點 |
|---|---|---|---|
| OpenAI | gpt-4o-mini (T1), gpt-4o (T2) | - | api.openai.com/v1/chat/completions |
| Anthropic | claude-haiku-4-5 (T1), claude-sonnet-4-6 (T2), claude-opus-4-7 (T3) | - | api.anthropic.com/v1/messages |

### 2.4 配額
- 每 tenant 月度預算上限（QUOTA-001 §1.1）
- 每呼叫 max_tokens 上限（QUOTA-001 §4.1）
- 每 user 每小時 60 messages（QUOTA-001 §3 L1）

### 2.5 超時與重試
- HTTP timeout: 15s（hard）
- 重試: 1 次 + exponential backoff (1s)
- 429 / 5xx → circuit breaker（QUOTA-001 §3 L4）

### 2.6 失敗策略
- Primary failed → fallback to secondary（ADR-0001）
- Both failed > 1 分鐘 → 對話 escalate to human + status page 標 degraded
- 即使無 LLM，webhook 必須 ACK（不可讓 LINE 重試造成 duplicate）

### 2.7 安全與隱私
- LLM provider 必須有「我方資料不訓練」合約條款（ADR-0001 §contract requirement）
- 不傳 raw PII（Phase 2 token 化；Phase 1 依 LEGAL-001 §5.2 揭露 sub-processor）
- HTTPS strict cert validation

### 2.8 監控（OBS-001）
- `aeos_llm_tokens_total` per provider/model
- `aeos_llm_latency_seconds`
- `aeos_llm_errors_total` per error_code
- Provider availability check（每分鐘 ping `/models`）

### 2.9 退場
- 統一 LLM client interface（`services/llm-client/`）
- 切換 provider 只需改 config + key
- 退場時間估：< 1 工作日

---

## 3. INT-003 — Embedding Provider

### 3.1 用途
- RAG vector 生成（KB chunk → embedding）
- 對話 query embedding（即時）

### 3.2 模型選擇
- 主：OpenAI `text-embedding-3-small`（1536 dim, $0.02/M tokens）
- 評估替代：Voyage AI, Cohere（Phase 2 才考慮）

### 3.3 一致性原則
- KB embeddings 與 query embeddings **必須**用同一個模型版本
- 模型升級 → 全 reindex（大工程）
- Vector DB 需存 `embedding_model_version`

### 3.4 失敗策略
- 同步呼叫（query 時）失敗 → 降級為 keyword search（BM25）
- 異步呼叫（KB ingest）失敗 → 重試 3 次 → 進 dead letter queue

### 3.5 監控
- `aeos_embedding_calls_total`
- `aeos_embedding_latency_seconds`
- Index health：每 tenant `embedded_chunks / total_chunks` ratio

---

## 4. INT-004 — LINE Messaging API

### 4.1 用途
- 接收終端使用者訊息（webhook，API-002）
- 傳送 AI 回覆 / Tenant CS 訊息

### 4.2 認證
- Channel access token（per LINE Official Account）
- Channel secret（用於 HMAC 驗章）
- Token 存 KMS；每 tenant 獨立

### 4.3 端點
- 接收：webhook to our endpoint（API-002 定義）
- 送出：`https://api.line.me/v2/bot/message/push` / `reply`

### 4.4 配額（LINE 規則 2026）
- Push messages：依方案（Free / Pro Plus）
- Pilot 期假設客戶用 Pro Plus（每月 30,000 free push）
- 超出 → 計費 per push；我方需提供使用量 dashboard

### 4.5 失敗策略
- Webhook 接收失敗 → LINE 自動重試 3 次（10s 間隔）
- 我方必須在 1 秒內回 200（即使非同步處理）
- Push 失敗 → 重試 3 次 + log；連續失敗 → tenant alert（token 可能過期）

### 4.6 安全
- HMAC SHA-256 驗章每個 webhook（SEC-001 T-T-01）
- IP allowlist：LINE 公告 IP 範圍
- 拒絕無簽章請求

### 4.7 監控
- `aeos_line_webhook_received_total`
- `aeos_line_push_total` per status
- `aeos_line_webhook_signature_failures` → SEC alert

### 4.8 退場 / 多 channel
Phase 2 加 Messenger / WhatsApp：
- Channel-agnostic message envelope（abstract layer）
- LINE-specific 邏輯隔離在 `adapters/line/`

---

## 5. INT-005 — Object Storage

### 5.1 用途
- KB 原始檔案（PDF, docx, txt 等）
- 對話附件（圖片、語音）
- DB backup（RUNBOOK-003）
- Log cold storage（OBS-001 §1）

### 5.2 Provider
| Provider | 用途 | 月成本（est） |
|---|---|---|
| Hetzner Storage Box | Hot tier（KB, 對話附件） | €4 / TB |
| Backblaze B2 / AWS S3 | Cold tier + cross-region backup | $5~10 / TB |

### 5.3 認證
- IAM access key per role（read-only / write / admin）
- Pre-signed URL for tenant direct upload（避免流量過我方 server）

### 5.4 目錄結構
```
aeos-prod/
├── tenants/<tenant_id>/
│   ├── kb/<doc_id>/raw.pdf
│   ├── kb/<doc_id>/parsed.json
│   └── attachments/<conversation_id>/<msg_id>.jpg
├── backups/postgres/<YYYY-MM-DD>.tar.gz.age
├── backups/audit/<YYYY-MM>.jsonl.gz.age
└── logs-cold/<YYYY-MM-DD>/
```

### 5.5 配額
- Tenant 上傳：50MB/file, 500MB/day, 5GB total（Pilot 期）
- 超出 → 加購 or 拒絕

### 5.6 安全
- Bucket policy：default deny；無 public ACL（SEC-001 T-I-04）
- Server-side encryption AES-256
- Versioning：on（防誤刪 SEC-001 T-T-05）
- Object lock for backup：on
- 監控：每日 audit bucket policy（防意外開放）

### 5.7 失敗策略
- KB upload 失敗 → 重試 2 次 → 提示 tenant 重傳
- Backup upload 失敗 → P0 alert（RUNBOOK-003 §7）
- Storage provider 故障 → 暫停寫入；讀取從 cross-region replica

---

## 6. INT-006 — Email Provider

### 6.1 用途
- Tenant admin magic link / password reset
- Onboarding 通知
- Weekly health report
- Incident notification

### 6.2 Provider
- 主：Postmark（transactional 高送達率）
- 副：Resend（評估中）

### 6.3 認證
- API key
- DKIM / SPF / DMARC 設定（防 spoofing）

### 6.4 配額
- 月度 transactional 量：~10K（Pilot 期）
- 超出 → 加購

### 6.5 失敗策略
- 重要 email（magic link）失敗 → 即時提示 user 嘗試備援（SMS Phase 2）
- 報表類失敗 → backlog 隔日重試

### 6.6 隱私
- Email 內容 minimal PII
- Unsubscribe link 強制（行銷類 email；Pilot 期幾乎無）

---

## 7. INT-007 — Payment Provider（Phase 2）

Pilot 期手動收款（invoice + 銀行轉帳 / 信用卡刷單）。
Phase 2 評估 Stripe / Lemon Squeezy / 綠界。
本節為 placeholder：

- 訂閱模型 / usage-based
- Webhook 處理（subscription created / failed payment）
- PCI compliance（**永遠不存信用卡號**）

---

## 8. INT-008 — DNS / CDN（Cloudflare）

### 8.1 用途
- 域名管理（aeos.<tld>）
- TLS termination + auto-renew
- DDoS 防護（free tier）
- WAF（rate-limit only on free tier）

### 8.2 配置
- DNSSEC: on
- Always Use HTTPS: on
- TLS 1.2+
- HSTS: max-age 6 months
- Universal SSL（Let's Encrypt via Cloudflare）

### 8.3 失敗策略
- Cloudflare 故障 → 直連 origin（DNS bypass via /etc/hosts in emergency）
- 真實 IP 不對外公開

---

## 9. 通用契約規則

### 9.1 所有第三方整合必須

- [ ] 有 retry policy（最少 1 次）
- [ ] 有 timeout（最多 15s synchronous / 60s async）
- [ ] 有 circuit breaker（連續失敗 → 短期不打）
- [ ] 有 metric（call count, latency, error rate）
- [ ] 有 fallback / degradation path
- [ ] API key 存 KMS / env，**不進 git**
- [ ] DPA / sub-processor 在 LEGAL-001 §5.2 揭露（如處理 PII）
- [ ] 退場估時 < 1 工作日（避免硬鎖定）

### 9.2 新增第三方檢查清單

- [ ] 走 ADR 流程（新關鍵依賴 = 架構決策）
- [ ] 更新本文件 §1 清單
- [ ] 更新 LEGAL-001 §5.2 sub-processor list
- [ ] 更新 SEC-001（攻擊面評估）
- [ ] 整合 client 走統一抽象層
- [ ] 加入 OBS-001 監控

### 9.3 第三方故障 = RUNBOOK-001 處理

依關鍵性分級：
- P0 service（LLM, LINE, Storage, DNS）故障 → P0/P1 incident
- P1 service（Email, Sentry）故障 → P2 incident
- 故障 > 30 分鐘 → 通報受影響客戶

## 10. Vendor 評估每季 review

每季最後一週：
- 各 vendor 上季可用性 / 故障次數
- 成本對比預算
- 替代方案是否成熟
- 合約續約條件

特別關注：
- LLM provider 定價變動（直接影響 QUOTA-001）
- LINE 政策變動（影響核心 channel）

---

**See also**:
- `ADR-0001-llm-provider-strategy.md` — LLM provider 選擇
- `ADR-0004-deployment-model.md` — Hetzner / Cloudflare 選擇
- `API-002-line-webhook.md` — LINE webhook 詳細契約
- `QUOTA-001-llm-budget.md` — LLM provider 配額
- `SEC-001-threat-model.md` — 第三方攻擊面
- `OBS-001-observability-spec.md` — 第三方監控
- `LEGAL-001-DPA-template.md` §5 — Sub-processor 揭露
- `RUNBOOK-001-incident-response.md` §4.1 — Provider 故障處理
- `RUNBOOK-003-backup-dr.md` — Storage 故障處理
