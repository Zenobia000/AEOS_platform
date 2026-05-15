---
name: domain-model
description: AEOS DDD 領域模型 v0 — aggregates, entities, value objects, invariants
status: active
type: contract
created: 2026-05-14
last-synced-with: efb63b3efff9a280e178f46124f39db8d0141b54
owner: CTO
tier: 2
---

# AEOS Domain Model v0

> Phase 1 對應的最小可用 domain model。完整架構見 `02-product-architecture.md`；此處為**契約層**抽取，給工程實作直接對應。

## 1. Bounded Contexts（與 Phase 1 範圍）

| Bounded Context | Phase 1 | 主要 aggregates |
|---|---|---|
| **Employee Runtime** | ✅ 必建 | Employee, Conversation, Message |
| **Skill Governance** | ✅ 必建（最小版） | Skill, SkillVersion |
| **Knowledge** | ✅ 必建（最小版） | KnowledgeCard |
| **Tool Governance** | ⚠️ 半建（直接呼叫 + audit，無 policy engine） | Tool, ToolInvocation |
| **Tenant & Identity** | ✅ 必建 | Tenant, ApiKey |
| **Audit** | ✅ 必建 | AuditEvent（append-only） |
| **Training Room** | ❌ Phase 2 | — |
| **Evaluation** | ❌ Phase 2 | — |

---

## 2. Aggregates

### 2.1 Tenant（root）
**用途**：代表一個付費客戶（企業）。Phase 1 = 1 tenant per VM。

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| name | string | 顯示名稱 |
| slug | string | URL-safe 識別符 |
| status | enum(`active`, `suspended`, `churned`) | |
| contract_start | date | |
| data_retention_days | int | 預設 90（見 ADR-0005） |
| created_at | timestamp | |

**Invariants**：
- 一個 tenant 至少一個 ApiKey
- slug 全局唯一

### 2.2 Employee（root）
**用途**：一個可部署的 AI 員工實例（屬於某個 tenant）。

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK Tenant |
| name | string | e.g. "小美客服" |
| role | enum(`customer_service`, `order_taker`, ...) | Phase 1 只支援 `customer_service` |
| status | enum(`draft`, `live`, `paused`, `retired`) | |
| version | string | 此 Employee 的快照版本（semver） |
| persona_config | jsonb | tone, style, language |
| created_at, updated_at | timestamp | |

**Child entities**：
- `SkillBinding[]` — 此 Employee 綁定哪些 Skill 的哪個版本
- `ChannelBinding[]` — 此 Employee 接哪些 channel（LINE, web chat）

**Invariants**：
- `status=live` 時，所有綁定的 Skill 必須 `status=production`
- `draft` 員工不能接 production 流量；只能在 Training Room 內測試
- 一旦 `live`，persona_config 不可改（要改就建新版本，走 canary）

### 2.3 Conversation（root）
**用途**：一個 end-user 與 Employee 的對話 session。

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| employee_id | UUID | FK |
| employee_version | string | snapshot at session start |
| end_user_pseudo_id | string | 已 pseudonymized 的 end user 識別符 |
| channel | enum(`line`, `web_chat`, `whatsapp`) | |
| started_at, ended_at | timestamp | |
| outcome | enum(`resolved`, `handoff_human`, `abandoned`, `error`) | |
| metadata | jsonb | |

**Child entities**：
- `Message[]` — append-only conversation log

**Invariants**：
- ended_at 一旦設定不可改
- 一旦結束，messages 不可追加
- end_user PII 永不直接存 Conversation（只存 pseudo_id）

### 2.4 Message（child of Conversation）

| Field | Type | 備註 |
|---|---|---|
| id | UUID | |
| conversation_id | UUID | FK |
| seq | int | 序號 |
| role | enum(`user`, `assistant`, `tool`, `system`) | |
| content | text | 已 pseudonymized |
| content_raw_ref | UUID? | 指向 EncryptedPII 表（若有 PII） |
| skill_invocation_id | UUID? | 若此回應由特定 Skill 產生 |
| tool_invocations | jsonb[] | 此回應觸發的 tool calls |
| created_at | timestamp | |

**Invariants**：
- 同一 conversation 的 seq 嚴格遞增
- `content` 永不含 raw PII

### 2.5 Skill（root）+ SkillVersion
**用途**：一個 AI 能力的可版本化資產。對應 `skills/<vertical>/<skill-name>/` git 目錄（見 ADR-0003）。

**Skill**：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| slug | string | e.g. `customer-service/faq-respond` |
| vertical | string | e.g. `customer-service` |
| owner | string | |
| description | text | |
| current_production_version | string? | semver |
| created_at | timestamp | |

**SkillVersion**：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| skill_id | UUID | FK |
| version | string | semver |
| status | enum(`draft`, `approved`, `production`, `deprecated`) | |
| prompt_template_ref | string | git path |
| io_contract | jsonb | input/output schema |
| policy_refs | string[] | 引用的 policy IDs |
| test_set_ref | string | git path |
| test_pass_rate | float | 0–1, last CI run |
| approved_by | string? | |
| approved_at | timestamp? | |
| created_at | timestamp | |

**Invariants**：
- 同一 skill_id 的 version 唯一
- `status=production` 必須有 `approved_by` 與 `approved_at`
- `status=production` 必須 `test_pass_rate >= 0.80`（Phase 1 門檻；Phase 2 可上調）
- Skill `current_production_version` 只能指向 status=`production` 的版本
- Production 版本不可改（immutable）；只能新增版本

### 2.6 KnowledgeCard（root）
**用途**：客戶的單元知識，例如「退貨流程」「營業時間」「商品 X 的規格」。

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| title | string | |
| body_markdown | text | |
| tags | string[] | |
| source_url | string? | 原始出處 |
| version | int | 每次編輯 +1 |
| status | enum(`draft`, `approved`, `archived`) | |
| approved_by | string? | |
| approved_at | timestamp? | |
| valid_from, valid_until | timestamp? | 時效性 |
| created_at, updated_at | timestamp | |

**Invariants**：
- `status=approved` 才會被 retrieval 拿到
- 編輯後 status 自動回 `draft`，需重新 approve
- 跨 tenant 不可互讀（Phase 1 反正是單租戶）

### 2.7 Tool（root）+ ToolInvocation
**用途**：AI 員工可呼叫的外部能力（API、function、knowledge search）。

**Tool**：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID? | null = 系統內建 tool |
| name | string | e.g. `search_knowledge`, `lookup_order` |
| description | text | LLM 看的描述 |
| input_schema | jsonb | JSON Schema |
| risk_tier | enum(`safe`, `caution`, `restricted`) | |
| enabled | bool | |

**ToolInvocation**（記錄每次呼叫）：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| conversation_id | UUID | FK |
| message_id | UUID | FK（觸發此 invocation 的 message） |
| tool_id | UUID | FK |
| input | jsonb | |
| output | jsonb | |
| status | enum(`success`, `error`, `rejected_by_policy`) | |
| latency_ms | int | |
| cost_token | int? | |
| created_at | timestamp | |

**Invariants**：
- `risk_tier=restricted` 的 tool 呼叫必須有 policy approval audit
- 一旦記錄，input/output 不可改

### 2.8 AuditEvent（append-only，無 aggregate root）

| Field | Type | 備註 |
|---|---|---|
| id | UUID | |
| tenant_id | UUID | |
| actor_type | enum(`employee`, `user`, `system`, `policy_engine`) | |
| actor_id | string | |
| event_type | string | e.g. `llm.call`, `tool.invoke`, `policy.deny`, `skill.deploy` |
| entity_type | string | e.g. `conversation`, `skill_version` |
| entity_id | UUID | |
| payload | jsonb | |
| created_at | timestamp | |

**Invariants**：
- **Append-only**：永不 UPDATE、永不 DELETE
- 保留期限：**永久**（見 ADR-0005）

---

## 3. Domain Events（Phase 1 必發）

| Event | When | Subscribers |
|---|---|---|
| `ConversationStarted` | Conversation 建立 | Audit |
| `MessagePosted` | 任何 Message append | Audit, Eval (Phase 2) |
| `ToolInvoked` | Tool 被呼叫 | Audit, Cost Tracker (Phase 2) |
| `SkillVersionApproved` | Skill 過 Quality Gate | Audit, Deploy Pipeline |
| `EmployeeStatusChanged` | draft → live 等 | Audit |
| `KnowledgeCardApproved` | KC 過 review | Audit, Retrieval Index Rebuild |
| `PolicyDenied` | Policy 拒絕某個動作 | Audit, Alerting |

---

## 4. Phase 1 不做的事（明文 out of scope）

- ❌ Multi-tenant aggregate sharing（每 tenant 一個 PG，邏輯隔離簡單）
- ❌ Skill 之間的 dependency graph（只有平面 Skill）
- ❌ Training Room 領域（Phase 2）
- ❌ Evaluation aggregate（Phase 2）
- ❌ Policy Engine 領域（Phase 1 = 一份 YAML + 人工 review）
- ❌ Cost attribution aggregate（Phase 2）

---

## 5. 參考

- `02-product-architecture.md` §22.x — 三平面分離、bounded contexts 完整版
- `ADR-0003` — Skill Registry git/yaml 實作細節
- `ADR-0005` — PII 處理與保留政策
- `docs/2-contracts/db-schema.md` — 對應 PostgreSQL schema
