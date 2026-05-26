---
id: CR-0001
title: "Multi-Vertical Skill Framework Hardening"
status: approved-implementation-in-progress
tier: 4-exploration
owner: CTO + CEO
created: 2026-05-26
last-updated: 2026-05-26
approved: 2026-05-26
related: [MC-005, MC-009, MC-010, ADR-0003, ADR-0007, PRD-001, SAD-v0.1, db-schema §3.3, AUTHORING-GUIDE]
---

# CR-0001 — Multi-Vertical Skill Framework Hardening

## 1. Change Statement

**As-is**：AEOS Phase 1 framework 雖然 schema 抽象到 `<vertical>/<slug>/<semver>/`，但只有 1 個 skill instance（`customer-service/faq-respond/v1.0.0`）；DraftProcessor hardcode 接 skill_slug 參數，無 routing logic；skill_binding 沒 routing_rule 欄；Expert Console 5 tabs 不分 skill。

**To-be**：framework 升級為「Multi-Expert Platform」— 支援 3-5 vertical 平行運作；skill_binding 帶 `routing_rule` JSONB；新增 SkillRouter service 決定每則 inbound message 走哪個 skill；Expert Console 加 skill selector（top-level）；提供 `new_skill` CLI 與 3-5 個 stub vertical skill 證明 framework 通用；各 skill 配 50 題 stub test_set。

**Driver**：CEO 要展示 framework 不只能跑 customer-service，期望可給 HR / IT-helpdesk / sales / finance / legal 等不同 expert 使用 → 強化 pitch 故事 + 降低 pilot 期客戶議價阻力（「我們不是給你做 demo，是 framework 已具備」）。

## 2. Affected Flow

| ID | Status | Modified / New / Deleted | 變動內容 |
|---|---|---|---|
| `BF-001` 客戶 Onboarding | active | Modified | Step 「指派 skill」由「綁定 1 個 skill」改為「綁定 N 個 skill + 設 routing_rule」 |
| `UF-001` Pilot KB 建立 | active | Modified | KB 改 per-vertical 區隔（hr KB 不混 sales KB） |
| `UF-NEW-006` Multi-Skill Routing | — | **New** | 新 UF：inbound message → SkillRouter → 選 skill → DraftProcessor |
| `SF-NEW-006` Skill Selection Pipeline | — | **New** | 新 SF：routing_rule evaluator（keyword path + LLM intent classify fallback）|

## 3. Affected Spec (FR / NFR)

| ID | 影響 |
|---|---|
| `PRD-001 §5.4 Draft Mode` | Draft 訊息要顯示「由哪個 skill 產生」（Expert UI 加標籤） |
| `NFR-001 §1 P95 ≤5s` | Routing 加 ≤200ms budget（不超 budget 才不影響整體 SLO） |
| `SEC-001 §6.1 #4 RLS` | skill_binding.routing_rule 內可能含 PII（避免在 rule 寫真實電話 / email）→ 文件規範 + 驗證 |

## 4. Affected API

| Endpoint | Verb | Status | Breaking? | 變動 |
|---|---|---|---|---|
| `/api/v1/expert/reviews` | GET | Existing | ⚠️ Soft-breaking | 新增 `?skill_slug=` filter；不傳則保留現行行為（回全 skill） |
| `/api/v1/kc/drafts` | GET | Existing | ⚠️ Soft-breaking | 同上 |
| `/api/v1/testset/cases` | GET | Existing | ⚠️ Soft-breaking | 同上 |
| `/api/v1/admin/skills` | GET | **New** | — | 列 tenant 已綁定 skills + status |
| `/api/v1/admin/skills/bindings` | POST | **New** | — | 建/改 skill_binding + routing_rule |
| `/api/v1/admin/skills/bindings/{id}` | DELETE | **New** | — | 解綁 skill |
| `/api/v1/admin/skills/route-preview` | POST | **New** | — | Dev 用：給訊息預覽 routing 結果（不實際送）|

## 5. Affected Data

### 5.1 Schema 變動

| 表 | 變動 | Migration |
|---|---|---|
| `skill_binding` | **+1 column**：`routing_rule JSONB NOT NULL DEFAULT '{}'` | `alembic/versions/0011_skill_binding_routing_rule.py` |
| `skill_binding` | **+1 column**：`is_default BOOLEAN NOT NULL DEFAULT false`（fallback skill）| 同上 |
| `skill_binding` | **+1 partial unique idx**：`UNIQUE (employee_id) WHERE is_default = true`（每 employee 至多 1 個 default）| 同上 |
| `message` | **+1 column**：`skill_version_id UUID NULL REFERENCES skill_version(id)`（記錄哪個 skill 處理了此 turn，Audit + 統計用）| `alembic/versions/0012_message_skill_version_id.py` |
| `tool_invocation` | 無變動（已可關聯到 message → 反向找 skill）| — |

### 5.2 routing_rule JSONB schema 範例

```json
{
  "type": "keyword | llm_intent | channel_match | explicit",
  "params": {
    "keywords": ["請假", "leave", "請休"],          // type=keyword
    "intents": ["leave_request"],                  // type=llm_intent
    "channel_id": "U1234..."                       // type=channel_match
  },
  "priority": 10  // 數字小者先評估
}
```

### 5.3 既有資料影響

- 現存 1 個 skill_binding（customer-service/faq-respond）：migration `routing_rule = {}` + `is_default = true` → 行為等同今日（fallback skill catch-all）
- 既存 message 沒 skill_version_id → migration 填 NULL；新 message 開始填

## 6. Affected Test

### 6.1 既有 TC 須改

| 測試類別 | 數量 | 變動 |
|---|---|---|
| `tests/test_skill_*.py` | ~20 | 加 routing_rule 維度 |
| `tests/test_draft_processor.py` | ~12 | DraftProcessor 改吃 routing 結果而非 hardcode skill_slug |
| `tests/test_expert_api.py` | ~14 | 加 `?skill_slug=` filter 測試 |
| `tests/api/test_admin.py` | ~10 | 加 skill binding CRUD 測試 |
| `web/expert/src/**/*.test.tsx` | ~5 | UI multi-skill selector |

### 6.2 新 TC

| 類別 | 估計題數 |
|---|---|
| SkillRouter 單元測試（keyword / llm_intent / channel_match / fallback / priority）| ~15 |
| 整合測試（inbound → router → draft → outbound）per skill | ~5 |
| Stub vertical skill 各 50 題 test_set.yaml × N skill | ~250 |
| Frontend skill selector + filter | ~6 |

**估 +280 個自動化測試**（多數是 test_set 內容；單元/整合約 +40）

## 7. Affected Architecture

### 7.1 新模組

| 模組 | 角色 |
|---|---|
| `app/skill/router.py` | **SkillRouter** — 給 message + tenant_id → 回 SkillVersion；evaluator 支援 4 種 rule type；priority sort |
| `app/cli/new_skill.py` | **new_skill CLI** — `python -m scripts.new_skill <vertical> <slug>` 產目錄 + 範本 manifest/system/tools/test_set |
| `skills/_template/v0.0.0/` | Skill scaffolding template — CLI copy 來源 |

### 7.2 既有模組需改

| 模組 | 變動 |
|---|---|
| `app/worker/draft_processor.py` | `process_message()` 不再吃 skill_slug 參數；改向 SkillRouter 拿 |
| `app/skill/loader.py` | 加 cache（multi-skill 載入頻繁，避免每 turn IO）|
| `app/skill/registry_service.py` | 加 `list_bindings(tenant_id)` / `set_binding(tenant_id, skill_v_id, routing_rule)` |
| `web/expert/src/App.tsx` | 加 `<SkillSelector />` 頂層元件 |
| `web/expert/src/pages/*.tsx` | 5 tab 加 skill_slug context（URL query param 同步）|

### 7.3 ADR 影響

| ADR | 是否需新 ADR / amendment |
|---|---|
| `ADR-0003 Skill Registry` | **需 amendment** — routing_rule 是 v1 沒考慮的新語意 |
| `ADR-0007 Tenant Isolation` | 不變 — multi-skill 仍在同 tenant RLS 內 |
| 其他 ADR | 不變 |

→ **建議產出 `ADR-0013-skill-routing-rule.md`** 紀錄 routing rule 設計決策。

## 8. Human Decisions Required

**✅ 全部決策已採納（2026-05-26 approved）。**

| # | 決策點 | 決定 | 理由 |
|---|---|---|---|
| 1 | **要做哪些 vertical？** | **4 個**：`customer-service`(已有) + `hr/leave-request` + `it-helpdesk/password-reset` + `sales/quote-request` | 涵蓋四象限：對外 FAQ / 內部員工 / 內部 IT / 對外業務。`finance` / `legal` 留下次（policy + 法務沒真實資料容易生 slop）|
| 2 | **Routing 策略** | **hybrid**（keyword fast path + llm_intent fallback + default skill）| keyword 命中 ~80% 流量 <10ms；未命中 ~20% 走 Haiku 4.5 ~300-500ms；整體 routing p95 < 500ms，仍在 NFR-001 §1 P95 ≤5s 預算內 |
| 3 | **每 tenant 1 skill 或 N skill** | **允許多 skill**，每 tenant 必有 1 個 `is_default=true` 作 fallback | 不寫死才叫「framework」；小客戶綁 1 個，大客戶綁多個。partial unique idx 已在 §5 規範 |
| 4 | **Stub tool 設計** | **in-mem dict 模擬**，標 `# STUB: replace before production` | demo 時可演「查員工 → 該員工有 3 天年假」互動，比 fake fn 真實、比 NotImpl 體驗好。每 vertical ~50 行 stub data |
| 5 | **Expert Console UI** | **Top-level skill selector**（URL `?skill_slug=...` 同步）| 心智模型清楚；可 deep link；用 React Context 全頁共享，vitest 改動較小 |
| 6 | **Test set 50 題誰編** | **AI 生成 + 標 `quality: stub`** | 4 vertical × 50 = 200 題，AI 生半天 vs 手寫 3-4 天；明確標 stub 不裝高品質；pilot 真實對話進來後覆寫 |
| 7 | **ADR-0013 timing** | **CIA 通過後立刻寫**（在 #2 SkillRouter branch 開工前）| Routing 設計 tradeoff 值得記，retrospective 寫容易忘 |

**關鍵守則（從建議副作用提取）**：

1. AI 生成 test_set 後**務必跑 KeywordJudge baseline** — 任何 vertical pass rate < 0.5 不算 framework demo-ready
2. hybrid routing 的 fallback default skill **必須是** `customer-service/faq-respond`（最寬泛）— 不然「不知道客戶在問啥」會卡住
3. 4 vertical 全部 stub data + tool 都標 `# STUB`，避免 pilot 期混入正式 code 路徑

## 9. Suggested Implementation Order

依依賴鏈，建議拆 7 個 feat branch：

| # | Branch | 內容 | 預估 | 阻塞 |
|---|---|---|---|---|
| 1 | `feat/cr-0001-skill-binding-schema` | DB migration 加 routing_rule + is_default + message.skill_version_id；models 更新 | 1 天 | — |
| 2 | `feat/cr-0001-skill-router-service` | `app/skill/router.py` SkillRouter + 4 種 rule evaluator + 單元測試 | 2 天 | #1 |
| 3 | `feat/cr-0001-draft-processor-routing` | DraftProcessor 改吃 router；DraftPoll 不再傳 skill_slug | 1 天 | #2 |
| 4 | `feat/cr-0001-new-skill-cli` | `scripts/new_skill.py` + `skills/_template/v0.0.0/` | 半天 | — (可平行) |
| 5 | `feat/cr-0001-stub-verticals` | 用 CLI 產 N 個 stub skill（依 §8 決策 #1 + #4）+ 50 題 test_set | 2-3 天 | #4, #6 決策 |
| 6 | `feat/cr-0001-admin-skill-api` | `/api/v1/admin/skills/*` 4 endpoint + 測試 | 1-2 天 | #1 |
| 7 | `feat/cr-0001-expert-console-skill-ui` | App.tsx skill selector + 5 tab 加 `?skill_slug` filter + vitest | 2 天 | #6 |
| 8 | `feat/cr-0001-adr-0013` | ADR-0013-skill-routing-rule.md（依 §8 #7 決策 timing）| 半天 | #2 |
| 9 | `chore/cr-0001-doc-sync` | 更新 MC-005 / db-schema / flow-index 加 UF-006/SF-006 / traceability-matrix | 半天 | 全部 |

**整體預估**：8-12 工作天（依 §8 決策複雜度浮動）。

## 10. Rollback Strategy

若實作後決定回滾 multi-vertical：

1. Revert #7 #6 #5（UI / API / stub skills）— 純加減操作，無破壞性
2. Revert #3（DraftProcessor 改回吃 skill_slug 參數）
3. Revert #2（移除 SkillRouter）
4. Revert #1（DB schema：可選擇 keep columns 不刪，因 routing_rule 有 default `{}` 不影響舊行為）
5. 既存 1 個 skill_binding 仍 `is_default=true` → 行為等同今日

**Rollback 安全度高**：所有 schema 變動有 `DEFAULT` + `NULL`，不破壞既存資料。

---

✅ **CIA approved 2026-05-26 — 全部建議採納，依 §9 順序開工**
