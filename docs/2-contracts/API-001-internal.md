---
id: API-001
title: Internal API — Onboarding, Knowledge, Employee, Skill, TestSet, Admin
status: active
type: api-contract
created: 2026-05-14
last-synced-with: efb63b3efff9a280e178f46124f39db8d0141b54
owner: CTO
tier: 2
related: [SAD-v0.1, UF-001, UF-002, UF-003, UF-004, UF-005, SF-001, SF-002, SF-005, domain-model, db-schema]
---

# API-001 — Internal API Contract（OpenAPI 3 風格摘要）

> Phase 1 後台 / Web SPA 與 API 之間的 REST contract。
> 完整 OpenAPI YAML 在 `openapi/api-001.yaml`（Phase 1 Week 2 出檔）；本文件為 human-readable 摘要。

## 0. 共通

### 0.1 Base URL
`https://{tenant-slug}.aeos.app/api/v1`

### 0.2 Auth
- Web SPA：session cookie + CSRF token (header `X-CSRF-Token`)
- 內部呼叫 / API client：`X-API-Key: <key>` (bcrypt match against `api_key.key_hash`)
- 失敗：`401 Unauthorized`

### 0.3 Tenancy
- API Key / session 綁定 tenant；URL path 不含 tenant_id
- 跨 tenant 操作禁止（即便 super admin 也須切換 tenant context）

### 0.4 Response Envelope
所有 endpoint 統一回傳：
```json
{
  "ok": true,
  "data": { ... },
  "error": null,
  "meta": { "request_id": "uuid", "page": 1, "total": 42 }
}
```
錯誤：
```json
{
  "ok": false,
  "data": null,
  "error": { "code": "VALIDATION_FAILED", "message": "...", "fields": {...} },
  "meta": { "request_id": "..." }
}
```

### 0.5 Idempotency
- 所有 POST / PATCH / DELETE 接受 `Idempotency-Key` header (UUID)
- 24h 內同 key 重送 → 回上次結果

### 0.6 Pagination
- Query: `?page=1&limit=20`
- Response `meta.total`, `meta.page`, `meta.limit`
- limit max 100

### 0.7 Standard Errors
| HTTP | code | 用途 |
|---|---|---|
| 400 | VALIDATION_FAILED | request body / params 不對 |
| 401 | UNAUTHENTICATED | 缺/錯 auth |
| 403 | FORBIDDEN | 已驗 auth 但 scope 不足 |
| 404 | NOT_FOUND | 資源不存在 |
| 409 | CONFLICT | 狀態衝突（e.g. approve 已 archived 的 KC） |
| 422 | UNPROCESSABLE | 語義錯（e.g. 上線未過 Quality Gate 的 Skill） |
| 429 | RATE_LIMITED | 速率限制 |
| 500 | INTERNAL | 系統錯（自動 audit） |

### 0.8 Rate Limiting
- 預設 60 req/min/api_key；逐 endpoint 可調
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 1. Knowledge

### POST `/knowledge/ingest`
上傳 KB 來源 → 異步切片 → 產 KC draft。對應 **UF-001 / SF-001**。

**Request**（multipart 或 JSON）：
```json
{ "source_type": "pdf|docx|md|url", "url": "https://..." }
```
或 multipart `file=@<binary>`。

**Response 202**：
```json
{ "ok": true, "data": { "ingest_job_id": "uuid", "status": "queued" } }
```

### GET `/ingest-jobs/{id}`
**Response 200**：
```json
{ "ok": true, "data": {
    "id": "uuid", "status": "queued|running|done|failed",
    "progress": 0.42, "kc_ids": ["uuid",...], "error": null
}}
```

### GET `/knowledge-cards?status=draft&page=1`
列表（含 pagination）

### GET `/knowledge-cards/{id}`
單張詳情，含 embedding 預覽（前 64 dim）+ source 段落

### PATCH `/knowledge-cards/{id}`
**Body**：`{ "title": "...", "body_markdown": "...", "tags": [...] }`
- 編輯後 status 自動回 `draft`
- 需 audit `KC_EDITED` (含 diff)

### POST `/knowledge-cards/{id}/approve`
**Body**：`{ "approved_by": "<expert_username>" }`
- 422 若 status != draft
- audit `KC_APPROVED`

### POST `/knowledge-cards/{id}/archive`
soft delete；不可再被檢索

### POST `/knowledge-cards/{id}/merge`
**Body**：`{ "merge_with_id": "uuid" }`

### POST `/knowledge-cards/{id}/split`
**Body**：`{ "split_at_offset": 234 }`

---

## 2. Employee

### POST `/employees`
**Body**：
```json
{ "name": "小美客服", "role": "customer_service",
  "persona_config": { "tone": "polite_zh_tw", "language": "zh-TW" } }
```
status 預設 `draft`。

### GET `/employees`, GET `/employees/{id}`, PATCH `/employees/{id}`
- PATCH：只在 status=`draft` 可改 persona_config / name
- live 後改 → 422，需走 new version flow（Phase 2）

### POST `/employees/{id}/skills`
綁定 Skill。
**Body**：`{ "skill_id": "uuid", "skill_version": "1.0.0" }`
- 422 若 SkillVersion.status != `production`

### DELETE `/employees/{id}/skills/{skill_id}`
解綁

### POST `/employees/{id}/channels`
綁 channel。Phase 1 = LINE。
**Body**：
```json
{ "channel": "line",
  "config": { "channel_id": "...", "channel_access_token": "...",
              "channel_secret": "..." } }
```
- channel_secret 用於 webhook 簽章驗證（見 API-002）
- config 落地前用 KMS / age 加密

### POST `/employees/{id}/promote`
draft → live。Pre-condition：
- 至少 1 個 SkillBinding（status=production）
- 至少 1 個 ChannelBinding
- 過 Quality Gate（最近一次 test pass rate ≥ 0.80）
- 否則 422 含具體缺項

### POST `/admin/employees/{id}/emergency-disable`
**Body**：`{ "reason": "..." }`
- 立即 status → `paused`
- 觸發 alert（Slack/email/SMS）
- audit `EMERGENCY_DISABLE`
- 對應 **UF-005 / SF-005**

### POST `/admin/employees/{id}/re-enable`
status: `paused` → `live`
audit `EMERGENCY_REENABLED`

### POST `/admin/employees/{id}/auto-reply-pct`
**Body**：`{ "pct": 10 }`（0 / 10 / 50 / 100）
對應 **UF-004 canary**

---

## 3. Skill (DB mirror; Git 是 source of truth)

### GET `/skills?vertical=customer-service`
列出 Phase 1 可用 Skill

### GET `/skills/{id}/versions`
某 Skill 的所有版本

### POST `/admin/skills/sync`
從 git 重新掃 `skills/` → upsert DB（CI 部署時自動呼叫，手動可用）

### POST `/admin/skill-versions/{id}/approve`
status: `approved` → `production`
- 422 若 test_pass_rate < 0.80
- audit `SKILL_PRODUCTION`

---

## 4. TestSet

### POST `/test-sets`
**Body**：`{ "employee_id": "uuid", "name": "v1 baseline" }`

### PUT `/test-sets/{id}/cases`
整批 upsert 50 題。
**Body**：
```json
{ "cases": [
  { "question": "你們營業時間？", "expected_outcome": "accept",
    "expected_keywords": ["09:00", "21:00"] }, ...
]}
```

### POST `/test-sets/{id}/runs`
**Body**：`{ "employee_version": "..." }`（雪照當下 Employee 配置）
**Response**：`{ "run_id": "uuid" }`

### GET `/test-runs/{id}`
**Response**：含 pass_rate, per-case detail（AI 回答 + retrieved KCs + judgment）

### POST `/test-runs/{id}/cases/{case_id}/override`
**Body**：`{ "actual_pass": true, "note": "..." }`
人工 mark 「實際上是對的」；下次 re-run 沿用

---

## 5. Conversation & Message（後台讀取）

### GET `/conversations?from=...&to=...`
列表，含 outcome / channel / employee_version / message_count

### GET `/conversations/{id}/messages`
完整訊息序列（已 pseudonymized）

### GET `/messages?status=draft_pending`
Draft Inbox 用，對應 **UF-003 / SF-003**

### POST `/messages/{id}/approve`
**Body**：`{ "edited_content": null | "..." }`
- 若 edited_content 為 null → 直接送 LINE Push
- 否則 → 送 edited_content + audit 含 diff

### POST `/messages/{id}/reject`
**Body**：`{ "reason": "..." }`
- status → `expert_takeover`
- 不會自動回；Expert 在另一個介面手動回（Phase 2 才做）

---

## 6. Audit

### GET `/audit-events?actor_type=&event_type=&from=&to=`
全部 event 可查；不可刪、不可改

### GET `/audit-events/export?format=csv|jsonl`
匯出給客戶（Phase 1 限 admin scope）

---

## 7. Admin / Health

### GET `/healthz`
liveness（無 DB 依賴）

### GET `/readyz`
readiness（PG / Redis / LINE / Anthropic 可達）

### GET `/admin/stats/daily`
每日對話數、handoff、auto rate、cost（從 audit 聚合）

---

## 8. 不在 Phase 1 的 endpoint（明文不做）

- Skill 編輯 API（Phase 1 用 git PR）
- 多 tenant 切換 API
- 訂閱 / 計費 API
- Marketplace API
- 主動推送 API
- 自動爬蟲 API

---

## 9. OpenAPI 檔產出

Week 2 出檔 `openapi/api-001.yaml`，從本文件衍生。Worker / SDK / web spa client 從 OpenAPI 自動 codegen。

## 10. 連結
- LINE webhook 入口：`API-002-line-webhook.md`
- 對應系統時序：`SF-001` ~ `SF-005`
- 對應 data model：`domain-model.md` / `db-schema.md`
- 對應 NFR（延遲、可用性）：`NFR-001`
