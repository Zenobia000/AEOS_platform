---
id: MC-007
title: "Module Contract — Admin Console"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
sync-source: doc
source-paths:
  - src/frontend/admin-console/
related: [SAD-v0.1, ADR-0006, MC-001, MC-004, MC-005, MC-006, API-001]
---

# Admin Console — One-Page Module Contract

> **Plane**: Control | **Priority**: #5 (消費所有其他模組的 API；最後設計) | **Phase 1 必做（最小版）**

## Purpose

提供 CTO / Tenant Admin / Expert 的 Web 管理介面，讓非工程師能操作 AEOS 平台 -- 建立 tenant、上傳知識庫、部署 Skill、監控對話品質、緊急停機。Admin Console 本身不擁有業務邏輯，純粹是其他模組 REST API 的 UI 消費者。Phase 1 的設計目標：CTO 能在 30 分鐘內完成一個 pilot 客戶的 AI 員工上線流程。

## Responsibilities

| 做 | 不做 |
|---|---|
| 呈現 dashboard（對話量、自動回覆率、handoff 率） | 計算 metrics（→ Evaluation Service MC-003） |
| Tenant 設定表單（LLM model、branding、channel） | Tenant 業務邏輯（→ Tenant Manager / MC-004） |
| Skill 版本列表、approve / deploy 按鈕 | Skill 測試執行（→ CI pipeline / Training Room） |
| Knowledge Card 列表、編輯、審核 | KC embedding / RAG 檢索（→ Knowledge Service） |
| Audit log 瀏覽器（filter + 分頁） | Audit log 寫入（→ Audit Service / MC-001） |
| 對話記錄瀏覽 + Draft Inbox | LLM 呼叫 / 對話處理（→ Employee Runtime） |
| 緊急停機按鈕 (kill switch) | 實際停機邏輯（→ Employee API `pause`） |
| API Key 管理 UI | Key hash / 驗證邏輯（→ Tenant Manager / MC-004） |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | React 18 + Vite + Tailwind + shadcn/ui（SAD-v0.1） | :green_circle: | 團隊熟悉；shadcn/ui 提供 accessible 元件；無 license 費 | 需 SSR / SEO → :yellow_circle: Next.js |
| D2 | SPA 純前端；所有資料從 REST API 取 | :green_circle: | 後端已有完整 API（API-001）；前後分離 | 需即時通知 → :yellow_circle: 加 WebSocket |
| D3 | Session cookie + CSRF token 認證（ADR-0006） | :green_circle: | 安全性高於 localStorage JWT；HttpOnly 防 XSS | 需 SSO → :yellow_circle: OIDC adapter |
| D4 | Phase 1 不做 i18n（僅繁中） | :green_circle: | Pilot 客戶全台灣；減少前端複雜度 | 海外客戶 → :yellow_circle: react-intl |
| D5 | 不做即時 dashboard（polling 30s 或手動重整） | :green_circle: | Phase 1 對話量低（< 100/天）；避免 WebSocket 複雜度 | 對話量 > 1000/天且需即時 → :yellow_circle: WebSocket + live chart |

## Data Model

Admin Console 是純 UI 層，不擁有獨立 table。它消費以下模組的資料：

| 資料來源 | Table / API | 用途 |
|---|---|---|
| Tenant Manager (MC-004) | `tenant`, `api_key` | Tenant 設定、Key 管理 |
| Skill Registry (MC-005) | `skill`, `skill_version` | Skill 列表、版本管理 |
| Tool Registry (MC-006) | `tool`, `tool_invocation` | Tool 列表、呼叫記錄 |
| Audit Service (MC-001) | `audit_log` | 審計日誌瀏覽 |
| Knowledge Service | `knowledge_card`, `ingest_job` | KC 管理 |
| Employee Runtime | `employee`, `conversation`, `message` | 員工管理、對話瀏覽 |

### 前端唯一的本地狀態

```typescript
// 前端 local state（不落 DB）
interface AdminUIState {
  // Auth session
  currentUser: { id: string; email: string; role: string; tenantId: string };
  csrfToken: string;

  // UI preferences (localStorage)
  sidebarCollapsed: boolean;
  tablePageSize: number;        // 預設 20
  dashboardAutoRefresh: boolean; // 預設 true, 30s interval
  theme: 'light' | 'dark';      // Phase 1 只做 light
}
```

## Interface

### Screen Map（Phase 1）

```
┌─────────────────────────────────────────────────────────┐
│  Admin Console                                          │
│                                                         │
│  ┌─── Sidebar ───┐  ┌─── Main Content ───────────────┐ │
│  │                │  │                                 │ │
│  │  Dashboard     │  │  (depends on selected page)     │ │
│  │  Employees     │  │                                 │ │
│  │  Skills        │  │                                 │ │
│  │  Knowledge     │  │                                 │ │
│  │  Conversations │  │                                 │ │
│  │  Draft Inbox   │  │                                 │ │
│  │  Audit Log     │  │                                 │ │
│  │  Tools         │  │                                 │ │
│  │  ─────────     │  │                                 │ │
│  │  Settings      │  │                                 │ │
│  │  API Keys      │  │                                 │ │
│  │                │  │                                 │ │
│  └────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Screen Detail

#### 1. Dashboard (`/`)
- **KPI Cards**: 今日對話數、自動回覆率、handoff 率、平均 response time
- **趨勢圖**: 過去 7 天對話量折線圖（from MC-003 `GET /api/v1/evaluation/dashboard/{tenant_id}`）
- **近期 Audit Events**: 最新 10 筆（from `GET /api/v1/audit?limit=10`）
- **AI 員工狀態**: 所有 Employee 的 status badge（live/paused/draft）
- **Refresh**: 30 秒自動 polling 或手動按鈕

#### 2. Employees (`/employees`)
- **列表**: name, role, status, version, skill count, channel count
- **建立**: 表單 → `POST /api/v1/employees`
- **詳情**: persona config 編輯（draft 時）、skill bindings、channel bindings
- **上線**: "Deploy to Live" 按鈕 → `POST /api/v1/employees/{id}/deploy`（顯示 pre-flight checklist）
- **緊急停機**: 紅色 "Emergency Pause" 按鈕 → `POST /api/v1/employees/{id}/pause`（需輸入 reason + 二次確認）

#### 3. Skills (`/skills`)
- **列表**: slug, vertical, current production version, test pass rate badge
- **版本歷史**: 每個 Skill 展開 → 所有 SkillVersion 的 timeline
- **Approve**: "Approve" 按鈕（testing -> approved）→ `POST /api/v1/admin/skill-versions/{id}/approve`
- **Deploy**: "Deploy to Production" 按鈕（approved -> production）→ `POST /api/v1/admin/skill-versions/{id}/deploy`
- **Rollback**: "Rollback" 按鈕 → 選擇歷史版本 → `POST /api/v1/admin/skill-versions/{id}/rollback`
- **Sync**: "Sync from Git" 按鈕 → `POST /api/v1/admin/skills/sync`

#### 4. Knowledge (`/knowledge`)
- **上傳**: drag-and-drop 或 URL 輸入 → `POST /api/v1/knowledge/ingest`
- **Ingest 進度**: progress bar（polling `GET /api/v1/knowledge/ingest/{job_id}`）
- **KC 列表**: title, status badge, tags, version, updated_at
- **KC 編輯**: Markdown editor → `PATCH /api/v1/knowledge/cards/{id}`
- **審核**: "Approve" / "Archive" 按鈕 → `POST /api/v1/knowledge/cards/{id}/approve`

#### 5. Conversations (`/conversations`)
- **列表**: date, employee, channel, outcome badge, message count
- **Filter**: date range, outcome, employee
- **詳情**: 完整對話 thread（user/assistant 氣泡）+ tool invocations inline

#### 6. Draft Inbox (`/drafts`)
- **待審列表**: AI 生成但未送出的訊息（from `GET /api/v1/conversations/messages?status=draft_pending`）
- **審核**: "Approve & Send" / "Edit & Send" / "Reject" 按鈕 → `POST /api/v1/conversations/messages/{id}/approve`
- **統計**: 待審數量 badge 在 sidebar

#### 7. Audit Log (`/audit`)
- **列表**: timestamp, actor, event_type, resource, outcome
- **Filter**: date range, event_type (dropdown), actor_type, outcome
- **詳情**: 展開 payload JSONB（pretty-printed）
- **匯出**: "Export CSV" / "Export JSONL" 按鈕 (Phase 2 -- MC-001 export endpoint not yet defined)

#### 8. Tools (`/tools`)
- **列表**: name, type, risk_tier badge, rate_limit, enabled toggle
- **呼叫記錄**: 展開 → 最近 invocations（status, latency, timestamp）
- **統計**: per-tool success rate, avg latency（from `GET /api/v1/tool-invocations/stats`）

#### 9. Settings (`/settings`)
- **Tenant Config**: LLM model 選擇、branding 設定、greeting/farewell message
- **Channel Config**: LINE channel 連結設定
- **Data Retention**: 天數設定（需 admin 確認）

#### 10. API Keys (`/api-keys`)
- **列表**: name, prefix, scopes, last_used_at, created_at
- **建立**: "Generate New Key" → 顯示明文 key（僅一次，含 copy 按鈕 + 警告）
- **輪換**: "Rotate" 按鈕 → 確認 → 舊 key 立即失效 + 顯示新 key
- **撤銷**: "Revoke" 按鈕 → 二次確認

### Critical Day-1 Admin Flows

#### Flow 1: Onboard a Pilot Customer (CTO)

```
1. Login → Dashboard
2. Settings → 設定 tenant config（LLM model, branding）
3. Knowledge → 上傳客戶 FAQ PDF → 等 ingest → 審核 KC
4. Skills → Sync from Git → 確認 faq-respond skill 可用
5. Employees → 建立 AI 員工 → 綁 Skill + Channel
6. Employees → Deploy to Live
7. Dashboard → 監控第一批對話
```

#### Flow 2: Monitor & Intervene (Expert)

```
1. Login → Dashboard（看 KPI）
2. Draft Inbox → 審核 AI 草稿 → Approve / Edit / Reject
3. Conversations → 檢視完整對話 → 確認 AI 回答品質
4. Audit Log → 查看異常事件
```

#### Flow 3: Emergency Stop (CTO/Expert)

```
1. Dashboard → 發現異常（handoff 率飆升 / 錯誤回答）
2. Employees → 選擇 AI 員工 → "Emergency Pause"
3. 輸入 reason → 二次確認 → 立即停機
4. Audit Log → 確認停機事件已記錄
5. 事後：修復 → Re-enable
```

### API 依賴一覽

| Screen | 依賴 API Endpoint |
|---|---|
| Dashboard | `GET /api/v1/evaluation/dashboard/{tenant_id}`, `GET /api/v1/audit`, `GET /api/v1/employees` |
| Employees | `GET/POST/PATCH /api/v1/employees`, `POST /api/v1/employees/{id}/deploy`, `POST /api/v1/employees/{id}/pause` |
| Skills | `GET /api/v1/skills`, `GET /api/v1/skills/{id}/versions`, `POST /api/v1/admin/skills/sync`, `POST /api/v1/admin/skill-versions/{id}/approve`, `POST /api/v1/admin/skill-versions/{id}/deploy` |
| Knowledge | `POST /api/v1/knowledge/ingest`, `GET /api/v1/knowledge/ingest/{job_id}`, `GET/PATCH /api/v1/knowledge/cards/{id}`, `POST /api/v1/knowledge/cards/{id}/approve` |
| Conversations | `GET /api/v1/conversations`, `GET /api/v1/conversations/{id}/messages` |
| Draft Inbox | `GET /api/v1/conversations/messages?status=draft_pending`, `POST /api/v1/conversations/messages/{id}/approve` |
| Audit Log | `GET /api/v1/audit` (Phase 2: `GET /api/v1/audit/export`) |
| Tools | `GET /api/v1/tools`, `GET /api/v1/tool-invocations`, `GET /api/v1/tool-invocations/stats` |
| Settings | `GET/PATCH /api/v1/tenants/{id}` |
| API Keys | `GET/POST /api/v1/tenants/{id}/api-keys`, `POST /api/v1/tenants/{id}/api-keys/{key_id}/rotate`, `POST /api/v1/tenants/{id}/api-keys/{key_id}/revoke` |

### Event Types

```
admin.login
admin.config_changed
admin.emergency_stop
admin.employee_deployed
```

## Dependencies

```
 ┌─────────────────────────────────────────────────────┐
 │                  Admin Console (SPA)                 │
 │         React 18 + Vite + Tailwind + shadcn/ui      │
 └────────┬────────┬────────┬────────┬────────┬────────┘
          │        │        │        │        │
          ▼        ▼        ▼        ▼        ▼
   ┌──────────┐┌──────┐┌───────┐┌──────┐┌────────┐
   │ Tenant   ││Skill ││ Tool  ││Audit ││Employee│
   │ Manager  ││Regist││Regist ││Svc   ││Runtime │
   │ MC-004   ││MC-005││MC-006 ││MC-001││        │
   └──────────┘└──────┘└───────┘└──────┘└────────┘
          │        │        │        │        │
          └────────┴────────┴────────┴────────┘
                           │
                    FastAPI REST API
                    (API-001 contract)
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| 10 個 screens（上述列表） | 即時 WebSocket dashboard |
| Session cookie auth（ADR-0006） | SSO / OIDC 登入 |
| 繁中 UI | i18n 多語系 |
| Light theme only | Dark theme |
| 30s polling dashboard | Real-time event stream |
| 基本 filter + 分頁 | 全文搜尋 / 進階篩選 |
| shadcn/ui 元件庫 | 自訂 design system |
| 靜態部署（nginx serve dist/） | SSR / ISR |
| Desktop-first responsive | 手機版完整支援 |
| 每個操作前二次確認（destructive actions） | Undo 機制 |

### Frontend Tech Stack

| 層 | 選擇 | 理由 |
|---|---|---|
| Framework | React 18 | 團隊熟悉；生態最大 |
| Build | Vite 6 | 快；HMR 好 |
| Styling | Tailwind CSS 4 | utility-first；與 shadcn/ui 配合 |
| Components | shadcn/ui | accessible、可 copy-paste、無 runtime dependency |
| State | React Query (TanStack) | server state 管理；自帶 cache + refetch |
| Routing | React Router 7 | SPA routing |
| Forms | React Hook Form + Zod | 表單驗證 |
| Charts | Recharts | 簡單、React-native、輕量 |
| HTTP | ky (or axios) | 內建 retry + interceptor |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
1 tenant admin           5-15 tenant admins            50+ users + RBAC
──────────────────────────────────────────────────────────────────
10 screens              → 20+ screens (eval, billing) → white-label per tenant
polling 30s             → WebSocket live updates      → event-driven reactive UI
cookie auth             → OIDC SSO                    → RBAC + fine-grained permissions
繁中 only               → i18n (en/zh/ja)            → per-tenant localization
Recharts                → Grafana embedded            → custom analytics dashboard
nginx static            → CDN + edge cache            → micro-frontend per plane
desktop-first           → mobile responsive           → native mobile app (Phase 3+)
```
