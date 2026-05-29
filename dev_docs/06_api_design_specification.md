# API 設計規範 - Care Copilot（最薄切片 / AEOS core + pack #1）

> **版本:** v0.1.0 | **更新:** 2026-05-29 | **狀態:** 草稿（W1 eval-only；寫入 API W2 design）
> **負責人:** TL | **審核:** ARCH + SEC | **追蹤:** US-0001~0011 / UC-1~5 / ADR-0001, ADR-0003
> **OpenAPI 定義:** [`docs/api/openapi-care-copilot.yaml`](../docs/api/openapi-care-copilot.yaml)（openapi 3.1.0）

---

## 1. 設計約定

| 項目 | 規範 |
| :--- | :--- |
| **風格** | RESTful |
| **Base URL** | `/api/v1` |
| **格式** | `application/json` (UTF-8) |
| **資源路徑** | 小寫、複數（`/contacts`、`/drafts`） |
| **欄位命名** | `snake_case` |
| **日期格式** | ISO 8601 UTC |
| **認證** | `tenantBearer`（HTTP bearer）；每請求帶 tenant context，**RLS 強制隔離**（ADR-0001 / legacy ADR-0007） |
| **版本控制** | URL 路徑（`/api/v1`） |

> **所有路徑經 AEOS Tenant scope(RLS) + Policy + Audit**。API 僅傳輸，不裁決合規（合規判定 = Policy Engine；needs_human = 知識/grounding 層；system-spec C4）。

---

## 2. 通用行為

### 冪等性

- **W2 design（defer，owner = SD）**：非 GET 請求支援 `Idempotency-Key` header + 24h 去重窗。W1 無寫入 API（eval-only），故未啟用。

### 分頁 / 排序 / 過濾

- 切片資源量小（1 tenant / ~100 contacts），W1 不實作游標分頁；W2 審核台列表頁如需要再加 `limit` + `starting_after`。

---

## 3. 錯誤處理

統一 error model（OpenAPI `Error` schema，所有 4xx/5xx 引用）：

```json
{
  "code": "string",       // e.g. cross_tenant_denied / knowledge_insufficient / llm_unavailable
  "message": "string",
  "details": {}
}
```

| 錯誤碼 | HTTP | 描述 | 來源 |
| :--- | :--- | :--- | :--- |
| `cross_tenant_denied` | 403 | 跨租戶拒絕（deny by default） | 鐵律 BR-3 / TC-SEC-01 |
| `knowledge_insufficient` | 422 | 知識缺依據 → `needs_human=true`（不幻覺） | BR-1 / UC-2 |
| `compliance_red_blocked` | 422 | edit 後重跑合規為 red → 阻擋送出 | BR-2 / C2 |
| `llm_unavailable` | 503 | LLM 失敗（fallback 仍失敗 → needs_human） | NFR Reliability |
| `audit_write_failed` | 500 | audit 寫入失敗 → 整筆操作回滾 | BR-5 / threat-model T-T-02 |

> **業務 gate 非 error**：合規紅燈在 `/drafts` 回 `200 + compliance=red`（送出鈕禁用，business gate）；只有 `/drafts/{id}/decision` 的 edit 後重跑 red 才回 422 阻擋（ERD Error Model）。

---

## 4. 安全性（契約層面）

> 📎 **與 `13` §C 的邊界**：本檔聚焦 **API 契約層面**（認證機制、錯誤碼、tenant scope）；**實作層面**（RLS 是否真生效、Tool Gateway 白名單、輸入驗證實作、CVE）見 `13_security_and_readiness_checklists.md §C`。

- **TLS**: 強制 HTTPS（runtime ↔ Anthropic、W2 expert ↔ runtime）。
- **Tenant scope**: 每請求帶 tenant context；RLS `current_tenant()` 讀 GUC，缺值 deny。
- **W2 LINE webhook**: HMAC 驗簽，失敗則拒絕（FR-003 / NFR Security）。
- **Tool Gateway**: 不暴露「自動發送 / 改 policy / 跨租戶查詢」工具給 LLM（OWASP LLM07/08）。
- **不傳超量 PII** 給 LLM provider；Anthropic zero-retention + 不訓練條款（threat-model §邊界 4）。

---

## 5. API 端點定義

### 資源: Contacts（活檔案，UC-1）

#### `POST /contacts` — 建立/補充活檔案（結構化 contact）

- **授權**: tenantBearer（RLS scope）
- **請求體**: `ContactUpsert`（活檔案 7 欄位，可空、慢慢補）
- **回應**: `201 Created` → `Contact` ｜ `403 cross_tenant_denied`
- **追蹤**: US-0002 / ADR-0003

#### `POST /contacts/{id}/ingest` — 貼上 markdown/截圖文字 → 抽取補欄位 + 知識索引

- **請求體**: `{ text: string (required) }`
- **回應**: `200 OK`（已索引 + 抽取欄位；W2 design 綁 `IngestResult`）
- **追蹤**: US-0001 / FR-001 / UC-1

### 資源: Drafts（草稿，UC-2/3）

#### `POST /drafts` — 生成草稿（grounded + 過合規 + 多語氣）

- **請求體**: `{ contact_id (required), inbound_message (required), tone: care|casual|business (default care) }`
- **回應**:
  - `200 OK` → `Draft`（含 `needs_human` / `compliance` 徽章）
  - `422 knowledge_insufficient` → `needs_human=true`（不幻覺）
  - `503 llm_unavailable` → fallback 仍失敗 → needs_human
- **追蹤**: US-0003/US-0004/US-0005 / UC-2 / BR-1/BR-2

#### `POST /drafts/{id}/decision` — expert 審核 approve/edit/reject（Draft Mode，AI 不自動發）

- **請求體**: `{ decision: approve|edit|reject (required), edited_text?, reason?, decided_by (required) }`
- **回應**:
  - `200 OK` → `Draft`（已記錄 + 全稽核 used_chunks/model/decision/decided_by）
  - `403 cross_tenant_denied`
  - `422 compliance_red_blocked`（edit 後重跑合規為 red）
  - `500 audit_write_failed`（整筆回滾）
- **追蹤**: US-0006 / UC-3 / C2（edit 必重跑 gate）

### 資源: Eval（離線 B1，UC-5）

#### `POST /eval` — 離線對測試集打 B1（draft→judge→採用率）

- **請求體**: `{ knowledge_ref?, testset_ref? }`
- **回應**: `200 OK`（採用率 + GO/PIVOT/KILL 裁決；W2 design 綁 `EvalResult`）
- **追蹤**: US-0011 / FR-007 / UC-5

---

## 6. 資料模型

### `ContactUpsert`（活檔案 7 欄位，ADR-0003）

```json
{
  "display_name": "string (required)",
  "health_focus": "string (特種個資，明示同意)",
  "family": "string",
  "work": "string",
  "interests": "string",
  "comm_pref": "string",
  "tags": ["string"]
}
```

### `Contact`

```json
{
  "id": "string",
  "tenant_id": "string",
  "...ContactUpsert 全欄位": "...",
  "timeline": [{ "at": "ISO8601", "kind": "string", "summary": "string" }]
}
```

### `Draft`（對應 ERD `message` 一表多用：草稿 + 審核決定 + 送達狀態）

```json
{
  "id": "string",
  "text": "string",
  "needs_human": "boolean",
  "compliance": "green | yellow | red",
  "compliance_note": "string (red 時改寫建議)",
  "used_chunks": ["string"],
  "model": "string",
  "decision": "approve | edit | reject | needs_human | manual_override",
  "decided_by": "string (NULL = 未審)",
  "sent_at": "ISO8601 | null"
}
```

> **`sent_at` 與 `decision` 正交**：W1 恆 null，W2 回發後填。鐵律掃描 TC-SEC-03：`message WHERE sent_at IS NOT NULL AND decided_by IS NULL` 必為 0。

### `Error` / `IngestResult` / `EvalResult`

```json
// Error（§3）
{ "code": "string", "message": "string", "details": {} }
// IngestResult
{ "indexed_chunks": "integer", "extracted_fields": ["string"] }
// EvalResult
{ "approve_rate": "number", "adopt_rate": "number", "verdict": "go | pivot | kill" }
```

---

## 7. 明確 defer 至 W2 design（非 limbo TODO，owner = SD）

- `Idempotency-Key` header + 24h 去重窗（W1 無寫入 API，eval-only）。
- `/contacts/{id}/ingest`、`/eval` response 綁 `IngestResult` / `EvalResult` schema。
- telemetry `x-telemetry` span = `draft.generate` / `policy.scan` / `audit.write`。
- W2 LINE webhook 入口（HMAC 驗簽）+ approve 後回發路徑。

---

## 變更紀錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v0.1.0 | 2026-05-29 | 依模板 06 從 `docs/api/openapi-care-copilot.yaml` 實例化；含 R2 統一 Error model（B-5） |
