---
name: domain-model
description: AEOS DDD 領域模型 v0 — aggregates, entities, value objects, invariants
status: active
type: contract
created: 2026-05-14
last-reviewed: 2026-05-15
last-synced-with: ec2eac3528daaa3e0ee9a5674309f90ec726d3e3
owner: CTO
tier: 2
related: [MC-001, MC-002, MC-003, MC-004, MC-005, MC-006, MC-008, MC-009, MC-010, MC-011, db-schema]
---

# AEOS Domain Model v0

> Phase 1 對應的最小可用 domain model。完整架構見 `02-product-architecture.md`；此處為**契約層**抽取，給工程實作直接對應。

## 1. Bounded Contexts（與 Phase 1 範圍）

| Bounded Context | Phase 1 | 主要 aggregates |
|---|---|---|
| **Employee Runtime** | ✅ 必建 | Employee, Conversation, Message, ConversationHandoff |
| **Skill Governance** | ✅ 必建 | Skill, SkillVersion, SkillBinding |
| **Knowledge** | ✅ 必建 | KnowledgeCard, IngestionJob |
| **Tool Governance** | ✅ 必建（最小版：直接呼叫 + audit + YAML policy） | Tool, ToolInvocation, ToolPolicy |
| **Tenant & Identity** | ✅ 必建 | Tenant, ApiKey |
| **Audit** | ✅ 必建 | AuditLog（append-only） |
| **Channel** | ✅ 必建 | ChannelBinding, WebhookEvent, OutboundMessage |
| **Training Room** | ✅ 必建（Phase 1 最小版） | TrainingSession, TestCase, TestRun, TestResult, SkillApproval |
| **Evaluation** | ✅ 必建（Phase 1 基本指標） | EvaluationMetric, FailureRecord |

---

## 2. Aggregates

### 2.1 Tenant（root）
**用途**：代表一個付費客戶（企業）。Phase 1 = 1 tenant per VM。
**MC 來源**：MC-004

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| name | string | 顯示名稱 |
| slug | string | URL-safe 識別符，全局唯一 |
| status | enum(`active`, `suspended`, `terminated`, `purged`) | 4 態生命週期（MC-004） |
| plan | string | `pilot`, `standard`, `premium`；預設 `pilot` |
| config | jsonb | LLM model, branding, channel 設定（見 MC-004 §Tenant Config） |
| contact_email | string | 主要聯繫 email |
| contract_start | date | |
| contract_end | date? | null = 無期限 |
| data_retention_days | int | 預設 90（見 ADR-0005） |
| suspended_at | timestamptz? | |
| terminated_at | timestamptz? | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**Invariants**：
- 一個 tenant 至少一個 ApiKey
- slug 全局唯一
- 狀態轉換：active -> suspended -> terminated -> purged（見 MC-004 狀態機）

### 2.2 ApiKey（child of Tenant）
**用途**：租戶的 API 認證金鑰。
**MC 來源**：MC-004

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK Tenant |
| name | string | e.g. `admin-key`, `ci-deploy` |
| key_prefix | string | 前 8 字元，用於識別（不是秘密） |
| key_hash | string | bcrypt hash，唯一 |
| scopes | string[] | `admin`, `read`, `deploy`, `webhook` |
| status | enum(`active`, `revoked`) | |
| last_used_at | timestamptz? | |
| expires_at | timestamptz? | null = 不過期（手動輪換） |
| created_at | timestamptz | |
| revoked_at | timestamptz? | |

**Invariants**：
- 每 tenant 最多 5 個 active API Key
- key_hash 全局唯一
- 明文金鑰只在生成時顯示一次

### 2.3 Employee（root）
**用途**：一個可部署的 AI 員工實例（屬於某個 tenant）。
**MC 來源**：MC-009

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK Tenant |
| name | string | e.g. "小美客服" |
| role | string | Phase 1 只支援 `customer_service` |
| status | enum(`draft`, `live`, `paused`, `retired`) | |
| version | string | 此 Employee 的快照版本（semver） |
| persona_config | jsonb | tone, style, language, greeting |
| runtime_snapshot | jsonb | Frozen Runtime 機制（MC-009）：包含 skill_bindings, tool_bindings, knowledge_config, llm_config, validation_rules, handoff_config, frozen_at。deploy 時凍結，live 期間不可變。 |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**Child entities**：
- `SkillBinding[]` — 此 Employee 綁定哪些 Skill 的哪個版本
- `ChannelBinding[]` — 此 Employee 接哪些 channel（LINE, web chat）

**Invariants**：
- `status=live` 時，所有綁定的 Skill 必須 `status=production`
- `draft` 員工不能接 production 流量；只能在 Training Room 內測試
- 一旦 `live`，persona_config 不可改（要改就建新版本，走 canary）
- `runtime_snapshot` 在 deploy 時凍結：即使 Skill Registry 的 prompt 被修改，live Employee 讀的是 snapshot

### 2.4 Conversation（root）
**用途**：一個 end-user 與 Employee 的對話 session。
**MC 來源**：MC-010

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| employee_id | UUID | FK |
| employee_version | string | snapshot at session start |
| end_user_pseudo_id | string | 已 pseudonymized 的 end user 識別符 |
| channel | string | `line`, `web_chat`, `whatsapp` |
| channel_user_id | string | channel-specific user ID（hashed） |
| status | enum(`open`, `active`, `waiting_human`, `resolved`, `closed`, `archived`) | 6 態生命週期（MC-010） |
| started_at | timestamptz | |
| last_message_at | timestamptz? | for idle timeout detection |
| ended_at | timestamptz? | |
| outcome | enum(`resolved`, `handoff_human`, `abandoned`, `error`) | |
| summary | text? | L2.5 session summary（conversation close 時由 Haiku 4.5 生成，<= 200 token，已過 PII 遮罩）。見 ADR-0010 |
| message_count | int | denormalized counter，預設 0 |
| metadata | jsonb | |

**Child entities**：
- `Message[]` — append-only conversation log

**Invariants**：
- ended_at 一旦設定不可改
- 一旦結束，messages 不可追加
- end_user PII 永不直接存 Conversation（只存 pseudo_id）
- idle > 30 分鐘自動 resolve（MC-010 D4）
- 狀態轉換：open -> active -> waiting_human/resolved -> closed -> archived

### 2.5 Message（child of Conversation）
**MC 來源**：MC-010

| Field | Type | 備註 |
|---|---|---|
| id | UUID | |
| conversation_id | UUID | FK |
| seq | int | 序號 |
| role | enum(`user`, `assistant`, `tool`, `system`) | |
| status | enum(`sent`, `draft_pending`, `approved`, `rejected`) | Draft Inbox 機制（MC-010）：低信心度回覆先存 `draft_pending`，Expert 審核後 approve/reject |
| content | text | 已 pseudonymized |
| content_raw_ref | UUID? | 指向 EncryptedPII 表（若有 PII） |
| skill_invocation_id | UUID? | 若此回應由特定 Skill 產生 |
| tool_invocations | jsonb[] | 此回應觸發的 tool calls |
| token_count | int? | for context window budget tracking |
| created_at | timestamptz | |

**Invariants**：
- 同一 conversation 的 seq 嚴格遞增
- `content` 永不含 raw PII
- Message table partition by month（append-only）

### 2.6 ConversationHandoff（child of Conversation）
**用途**：追蹤 AI -> Expert 的轉接記錄。
**MC 來源**：MC-010

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| from_conversation_id | UUID | FK Conversation |
| to_conversation_id | UUID? | null until Expert picks up |
| reason | string | `low_confidence`, `restricted_tool`, `user_request`, `policy_deny` |
| handoff_message | text? | context for Expert |
| expert_id | string? | who picked up |
| picked_up_at | timestamptz? | |
| resolved_at | timestamptz? | |
| created_at | timestamptz | |

### 2.7 Skill（root）+ SkillVersion
**用途**：一個 AI 能力的可版本化資產。對應 `skills/<vertical>/<skill-name>/` git 目錄（見 ADR-0003）。
**MC 來源**：MC-005

**Skill**：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID? | NULLABLE：NULL = platform-level skill。Phase 1 所有 skill 為 tenant-scoped（app layer 強制 NOT NULL）；Phase 2 支援 platform-level skills（tenant_id = NULL） |
| slug | string | e.g. `customer-service/faq-respond`，tenant 內唯一 |
| vertical | string | e.g. `customer-service` |
| name | string | 人類可讀名稱 |
| owner | string? | 負責人 |
| description | text? | |
| current_production_version | string? | semver |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**SkillVersion**：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| skill_id | UUID | FK |
| tenant_id | UUID | FK（冗餘，加速查詢） |
| version | string | semver |
| status | enum(`draft`, `testing`, `approved`, `production`, `deprecated`) | 5 態生命週期（MC-005）：draft -> testing -> approved -> production -> deprecated |
| prompt_template_ref | string | git path，e.g. `skills/cs/faq/v1.0.0/prompt.md` |
| io_contract | jsonb? | input/output JSON Schema |
| tool_bindings | string[] | tool slugs this skill can use |
| policy_refs | string[] | 引用的 policy IDs |
| test_set_ref | string? | git path to test cases |
| test_pass_rate | numeric(5,4)? | 0.0000-1.0000, last CI run |
| quality_gate_scores | jsonb? | e.g. `{ "pass_rate": 0.85, "latency_p95_ms": 1200, "cost_per_turn_usd": 0.003 }` |
| approved_by | string? | |
| approved_at | timestamptz? | |
| deployed_at | timestamptz? | |
| deprecated_at | timestamptz? | |
| git_commit_sha | string? | 對應 git commit (40 chars) |
| created_at | timestamptz | |

**Invariants**：
- 同一 skill_id 的 version 唯一
- `status=production` 必須有 `approved_by` 與 `approved_at`
- `status=production` 必須 `test_pass_rate >= 0.80`（Phase 1 門檻；Phase 2 可上調）
- Skill `current_production_version` 只能指向 status=`production` 的版本
- Production 版本不可改（immutable）；只能新增版本
- `testing` 狀態由 CI trigger test run 進入；通過後由 CTO/Expert approve

**SkillBinding**（CR-0001 / ADR-0013 升級為 multi-vertical routing 的核心表）：

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| employee_id | UUID | FK |
| skill_version_id | UUID | FK |
| priority | int | router 評估順序（小者先）|
| routing_rule | jsonb | `{ type: keyword \| llm_intent \| channel_match \| explicit, params, priority }`（CR-0001） |
| is_default | bool | 每 employee 至多 1 個 default（partial unique idx 守門） |
| created_at | timestamptz | |

**Invariants**（CR-0001 新增）：
- (employee_id, skill_version_id) 唯一
- 每 employee 至多 1 個 `is_default = true` binding（partial unique idx `uq_skill_binding_default_per_emp`）
- routing_rule.type 未知時視為 miss（router 不炸；只警告）
- 沒 default 且所有 rule 都 miss → `NoSkillBoundError`（admin UI 應阻止此狀態）

### 2.8 KnowledgeCard（root）
**用途**：客戶的單元知識，例如「退貨流程」「營業時間」「商品 X 的規格」。
**MC 來源**：MC-008

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| card_type | string | `faq`, `policy`, `product`, `procedure`, `risk`（MC-008 5 種類型） |
| title | string | |
| body_markdown | text | |
| tags | string[] | |
| source_url | string? | 原始出處 |
| source_file_ref | string? | S3 path to original uploaded file |
| version | int | 每次編輯 +1 |
| status | enum(`draft`, `approved`, `archived`) | |
| approved_by | string? | |
| approved_at | timestamptz? | |
| valid_from | timestamptz? | 時效性 |
| valid_until | timestamptz? | |
| embedding | vector(1024) | pgvector，Phase 1 用 small embedding model |
| embedding_model | string? | e.g. `voyage-3-lite`，for traceability |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**Invariants**：
- `status=approved` 才會被 retrieval 拿到
- 編輯後 status 自動回 `draft`，需重新 approve
- 跨 tenant 不可互讀（Phase 1 反正是單租戶）
- 整張 card body 做單一 embedding（Phase 1）

### 2.9 IngestionJob（Knowledge bounded context）
**用途**：追蹤文件上傳轉化為 Knowledge Cards 的進度。
**MC 來源**：MC-008

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| source_file_ref | string | S3 path |
| source_filename | string | original filename |
| status | enum(`pending`, `processing`, `completed`, `failed`) | |
| cards_created | int | 預設 0 |
| error_message | text? | |
| created_at | timestamptz | |
| completed_at | timestamptz? | |

### 2.10 Tool（root）+ ToolInvocation
**用途**：AI 員工可呼叫的外部能力（API、function、knowledge search）。
**MC 來源**：MC-006

**Tool**：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID? | null = 系統內建 tool |
| slug | string | e.g. `search_knowledge`, `lookup_order`；tenant 內唯一 |
| name | string | 人類可讀名稱 |
| description | text | LLM 看的描述（function calling） |
| tool_type | enum(`internal`, `http_api`, `db_query`, `function`) | |
| endpoint | string? | HTTP endpoint（tool_type=http_api 時） |
| auth_method | string? | `none`, `api_key`, `bearer`, `basic`, `hmac` |
| auth_config | jsonb? | 加密的 auth 設定（key/token/secret） |
| input_schema | jsonb | JSON Schema for input |
| output_schema | jsonb? | JSON Schema for output |
| risk_tier | enum(`safe`, `caution`, `restricted`) | 預設 `safe` |
| rate_limit_rpm | int | requests per minute per tenant，預設 60 |
| timeout_ms | int | 呼叫逾時，預設 5000 |
| retry_policy | jsonb | 預設 `{"max_retries": 2, "backoff_ms": 500}` |
| enabled | bool | 預設 true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**ToolInvocation**（記錄每次呼叫）：
| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| conversation_id | UUID? | FK Conversation |
| message_id | UUID? | FK Message（觸發此 invocation 的 message） |
| tool_id | UUID | FK Tool |
| employee_id | UUID? | FK Employee |
| skill_version_id | UUID? | 哪個 Skill 觸發的 |
| input | jsonb | 已 PII mask |
| output | jsonb? | 已 PII mask；null if error |
| status | enum(`success`, `error`, `timeout`, `rejected_by_policy`) | |
| error_message | text? | |
| latency_ms | int? | |
| cost_token | int? | LLM token cost (if applicable) |
| policy_decision | jsonb? | e.g. `{ "allowed": true, "rule": "rule-003", "reason": "..." }` |
| created_at | timestamptz | |

**Invariants**：
- `risk_tier=restricted` 的 tool 呼叫必須有 policy approval audit
- 一旦記錄，input/output 不可改
- 所有 tool 呼叫必須透過 Tool Gateway（MC-006）

### 2.11 ToolPolicy（Tool bounded context）
**用途**：YAML-driven 靜態 policy 規則，控制 tool 呼叫權限。
**MC 來源**：MC-006

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID? | null = 全局規則 |
| name | string | |
| description | text? | |
| rule_yaml | text | YAML 規則內容 |
| priority | int | 越高越優先，預設 0 |
| enabled | bool | 預設 true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### 2.12 AuditLog（append-only，無 aggregate root）
**用途**：記錄平台所有有意義的操作事件。
**MC 來源**：MC-001

| Field | Type | 備註 |
|---|---|---|
| id | bigserial | PK |
| tenant_id | UUID | |
| actor_type | enum(`ai_employee`, `admin`, `system`, `policy_engine`) | |
| actor_id | string | 操作者 ID |
| event_type | string | e.g. `conversation.message_sent`, `skill.deployed`, `tool.invoked` |
| resource_type | string? | e.g. `conversation`, `skill`, `tool` |
| resource_id | string? | 被操作對象 ID |
| action | string | `create`, `invoke`, `deploy`, ... |
| outcome | string | `success`, `failure`, `denied` |
| payload | jsonb? | 事件特有資料（含完整對話內容） |
| ip_address | inet? | 來源 IP |
| created_at | timestamptz | |

**Invariants**：
- **Append-only**：永不 UPDATE、永不 DELETE（DB trigger 保護）
- 保留期限：**永久**（見 ADR-0005）
- 90 天後對 payload 中 PII 欄位脫敏

### 2.13 TrainingSession（Governance bounded context）
**用途**：一次專家與 AI 員工共同訓練的 session。
**MC 來源**：MC-002

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| skill_version_id | UUID | FK SkillVersion |
| started_by | string | domain expert user ID |
| status | enum(`active`, `completed`, `abandoned`) | |
| notes | text? | 專家備註 |
| started_at | timestamptz | |
| ended_at | timestamptz? | |
| created_at | timestamptz | |

### 2.14 TestCase（Governance bounded context）
**用途**：Training Room 中的單一測試題。
**MC 來源**：MC-002

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| training_session_id | UUID | FK TrainingSession |
| seq | int | |
| category | string | `happy_path`, `edge_case`, `red_team`, `adversarial` |
| attack_pattern | string? | red team: `prompt_injection`, `pii_extraction`, `jailbreak`, `hallucination_bait`, `scope_escape`, `policy_bypass`, `emotional_manipulation` |
| input_message | text | |
| expected_behavior | text | 預期行為描述（非精確 match） |
| tags | string[]? | |
| created_at | timestamptz | |

**Invariants**：
- (training_session_id, seq) 唯一

### 2.15 TestRun（Governance bounded context）
**用途**：一次測試執行（含 Red Team）。
**MC 來源**：MC-002

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| skill_version_id | UUID | FK SkillVersion |
| training_session_id | UUID | FK TrainingSession |
| run_type | enum(`standard`, `red_team`, `full`) | |
| status | enum(`pending`, `running`, `completed`, `failed`) | |
| total_questions | int | |
| passed | int | 預設 0 |
| failed | int | 預設 0 |
| pass_rate | numeric(5,4)? | 0.0000-1.0000 |
| started_at | timestamptz? | |
| completed_at | timestamptz? | |
| run_by | string | |
| llm_model | string | 記錄用了哪個 model |
| total_tokens | int? | |
| total_cost_usd | numeric(10,4)? | |
| created_at | timestamptz | |

### 2.16 TestResult（Governance bounded context）
**用途**：單題測試結果。
**MC 來源**：MC-002

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| test_run_id | UUID | FK TestRun |
| test_case_id | UUID | FK TestCase |
| actual_response | text | |
| verdict | enum(`pass`, `fail`, `error`) | |
| failure_reason | text? | 失敗原因分類 |
| latency_ms | int? | |
| tokens_used | int? | |
| evaluator | string | `llm_judge`, `rule_based`, `human` |
| created_at | timestamptz | |

### 2.17 SkillApproval（Governance bounded context）
**用途**：專家對 SkillVersion 的最終審核記錄。
**MC 來源**：MC-002

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| skill_version_id | UUID | FK SkillVersion（唯一：一個版本只有一筆 approval） |
| decision | enum(`approved`, `rejected`, `revoked`) | |
| approved_by | string | |
| rejection_reason | text? | |
| gate_results | jsonb | snapshot of all gate results at approval time |
| created_at | timestamptz | |

### 2.18 EvaluationMetric（Governance bounded context）
**用途**：每日聚合的 AI 員工品質指標。
**MC 來源**：MC-003

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| employee_id | UUID | FK Employee |
| skill_id | UUID? | null = employee-level metric |
| skill_version | string? | |
| metric_name | string | Phase 1: `fcr`, `csat`；Phase 2: `aht_seconds`, `hallucination_rate`, `sop_compliance`, `drift_score`, `escalation_rate` |
| metric_value | numeric(10,4) | |
| sample_size | int | 計算此指標的對話數 |
| period_start | timestamptz | |
| period_end | timestamptz | |
| granularity | string | Phase 1: `daily` only；Phase 2: `hourly`, `weekly` |
| created_at | timestamptz | |

### 2.19 FailureRecord（Governance bounded context）
**用途**：單一失敗案例記錄，用於品質回饋與重訓。
**MC 來源**：MC-003

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| conversation_id | UUID | FK Conversation |
| message_id | UUID? | FK Message（指向具體問題回應） |
| employee_id | UUID | FK Employee |
| skill_id | UUID? | |
| skill_version | string? | |
| failure_category | string | 7 類 taxonomy：`hallucination`, `sop_violation`, `scope_escape`, `pii_leak`, `tone_mismatch`, `escalation_failure`, `tool_misuse` |
| severity | enum(`critical`, `high`, `medium`, `low`) | |
| description | text | |
| evidence | jsonb? | 佐證 (e.g. expected vs actual, matched rule) |
| retraining_status | enum(`pending`, `acknowledged`, `retraining`, `resolved`, `wont_fix`) | 預設 `pending` |
| acknowledged_by | string? | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### 2.20 ChannelBinding（child of Employee）
**用途**：Employee 與通訊 channel 的綁定。
**MC 來源**：MC-011

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| employee_id | UUID | FK Employee (ON DELETE CASCADE) |
| channel | enum(`line`, `web_chat`, `whatsapp`) | |
| config | jsonb | encrypted channel credentials (e.g. LINE channel access token) |
| enabled | bool | 預設 true |
| created_at | timestamptz | |

**Invariants**：
- (employee_id, channel) 唯一

### 2.21 WebhookEvent（Channel bounded context）
**用途**：Webhook 去重表，防止重複處理。
**MC 來源**：MC-011

| Field | Type | 備註 |
|---|---|---|
| id | string | LINE: webhookEventId |
| tenant_id | UUID | FK |
| channel | string | |
| received_at | timestamptz | |

**Invariants**：
- PK: (id, channel)
- 自動清除 > 7 天的記錄（dedup window）

### 2.22 OutboundMessage（Channel bounded context）
**用途**：追蹤 outbound 訊息的送出狀態與重試。
**MC 來源**：MC-011

| Field | Type | 備註 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | FK |
| conversation_id | UUID | FK Conversation |
| message_id | UUID | 觸發此 outbound 的 internal message |
| channel | string | |
| channel_user_id | string | target user (hashed) |
| status | enum(`pending`, `sent`, `failed`, `retrying`) | |
| retry_count | int | 預設 0 |
| error_message | text? | |
| sent_at | timestamptz? | |
| created_at | timestamptz | |

---

## 3. Domain Events（Phase 1 必發）

| Event | When | Subscribers |
|---|---|---|
| `ConversationStarted` | Conversation 建立 | Audit |
| `ConversationActivated` | 第一次 AI 回覆（open -> active） | Audit |
| `ConversationHandoffRequested` | 轉接 Expert | Audit |
| `ConversationResolved` | 對話結束 | Audit, Summary Generator |
| `MessagePosted` | 任何 Message append | Audit, Eval |
| `MessageDraftPending` | 低信心度回覆待審 | Audit, Expert Notification |
| `ToolInvoked` | Tool 被呼叫 | Audit, Cost Tracker (Phase 2) |
| `ToolDenied` | Policy 拒絕 tool 呼叫 | Audit, Alerting |
| `SkillVersionApproved` | Skill 過 Quality Gate | Audit, Deploy Pipeline |
| `SkillVersionDeployed` | Skill 進入 production | Audit |
| `EmployeeStatusChanged` | draft -> live 等 | Audit |
| `EmployeeDeployed` | Employee snapshot frozen, status -> live | Audit |
| `KnowledgeCardApproved` | KC 過 review | Audit, Retrieval Index Rebuild |
| `KnowledgeIngested` | 文件上傳完成轉化 | Audit |
| `PolicyDenied` | Policy 拒絕某個動作 | Audit, Alerting |
| `SummaryGenerated` | 對話結束時 L2.5 摘要產生 | Audit |
| `TrainingTestRunCompleted` | Test run 完成 | Audit |
| `TrainingSkillApproved` | 專家審核通過 | Audit, Skill Registry |
| `ChannelMessageReceived` | 收到外部訊息 | Audit |
| `ChannelMessageSent` | 送出外部訊息 | Audit |
| `ChannelSendFailed` | 送出失敗（all retries exhausted） | Audit, Alerting |
| `EvaluationMetricsComputed` | 每日指標計算完成 | Audit |
| `EvaluationFailureDetected` | 偵測到失敗案例 | Audit, Training Room |

---

## 3.5 Memory Layer Mapping（對應 ADR-0010）

AI 員工的記憶分為五層，對應到本文件的 aggregates：

| Layer | 名稱 | 對應 Aggregate | Phase 1 |
|---|---|---|---|
| L1 Working Memory | 當前對話 context | Message buffer（§2.5）-> LLM prompt | ✅ |
| L2 Session Memory | 單次對話歷程 | Conversation + Message（§2.4-2.5）+ Redis session | ✅ |
| L2.5 Session Summary | 對話結束摘要（跨 session 事實記憶） | Conversation.summary 欄位（§2.4） | ✅ |
| L3 Tenant Knowledge | KB + Skill | KnowledgeCard（§2.8）+ Skill/SkillVersion（§2.7） | ✅ |
| L4 Operational Memory | 跨對話累積模式 | 待定（Phase 2，由 Training Room bounded context 負責） | -- |

L2.5 的設計原則：Frozen Runtime 凍結「行為」不凍結「記憶」。記下事實觀察（「客戶問了退貨」）與 append-only Message 本質相同，不屬於自我改進。

詳見 `ADR-0010-memory-architecture.md`。

---

## 4. Phase 1 不做的事（明文 out of scope）

- ❌ Multi-tenant aggregate sharing（每 tenant 一個 PG，邏輯隔離簡單）
- ❌ Skill 之間的 dependency graph（只有平面 Skill）
- ❌ Cost attribution aggregate（Phase 2）
- ❌ Policy Engine 完整領域（Phase 1 = YAML 靜態規則 via ToolPolicy）
- ❌ Drift alert / retraining suggestion 專用 table（Phase 1 用 SQL 查詢 + 人工判斷）
- ❌ Quality Gate Result 專用 table（Phase 1 從 test_run 資料推導）

---

## 5. 參考

- `02-product-architecture.md` §22.x — 三平面分離、bounded contexts 完整版
- `ADR-0003` — Skill Registry git/yaml 實作細節
- `ADR-0005` — PII 處理與保留政策
- `docs/2-contracts/db-schema.md` — 對應 PostgreSQL schema
- `docs/2-contracts/MC-001-audit-service.md` — Audit Service module contract
- `docs/2-contracts/MC-002-training-room.md` — Training Room module contract
- `docs/2-contracts/MC-003-evaluation-service.md` — Evaluation Service module contract
- `docs/2-contracts/MC-004-tenant-manager.md` — Tenant Manager module contract
- `docs/2-contracts/MC-005-skill-registry.md` — Skill Registry module contract
- `docs/2-contracts/MC-006-tool-registry.md` — Tool Registry module contract
- `docs/2-contracts/MC-008-knowledge-rag.md` — Knowledge (RAG) module contract
- `docs/2-contracts/MC-009-employee-runtime.md` — Employee Runtime module contract
- `docs/2-contracts/MC-010-conversation-engine.md` — Conversation Engine module contract
- `docs/2-contracts/MC-011-channel-gateway.md` — Channel Gateway module contract
