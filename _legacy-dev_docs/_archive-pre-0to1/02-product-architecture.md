# 產品與架構

> **本檔對應原 whitepaper.md 的 §4~§10, §12, §13 (Part I 技術核心)**
> 主題定位：產品
> 最後同步：2026-05-14

## 相關章節速查

**本檔被外部引用的高頻章節**：
- §4 參考實作橫向評估 — Hermes / nanobot / CheetahClaws / 桌面工作台拆解策略
- §5 系統架構藍圖 — 主鏈路 / 旁路閉環 / 管理面 / 三平面分離
- §5.4 三平面分離 (Control / Data / Governance) — 高被引
- §6 核心領域模型 — Aggregate 定義
- §6.3 知識三分類治理 (Static / Policy / Dynamic) — 高被引
- §7 Bounded Context 與系統邊界
- §8 MCP 整合策略 — 帶治理能力的 Host
- §8.5 Enterprise MCP Host 最小組件
- §8.7 MCP / Plugin 審核管線
- §9 SkillOps Pipeline
- §9.4 七層 Quality Gates
- §10 訓練室與生產環境分離
- §10.3 訓練室介面設計 — 高被引
- §12 監控評估體系 (AgentOps)
- §13 多模型策略與成本治理

**本檔對外引用的章節**：
- §1 問題陳述 (見 `01-vision-positioning.md`)
- §2.2 職位目錄 (見 `01-vision-positioning.md`)
- §3 設計原則 (見 `01-vision-positioning.md`)
- §11 安全合規 (見 `06-risk-boundaries.md`)
- §15 風險與緩解 (見 `06-risk-boundaries.md`)
- §17 五階段方法論 (見 `03-execution-onboarding.md`)
- §18 Onboarding Layer (見 `03-execution-onboarding.md`)
- §20 自動化成熟度 (見 `03-execution-onboarding.md`)
- §21.2 Employee Manifest (見 `03-execution-onboarding.md`)
- §29 三 Compiler (見 `05-investor-thesis.md`)
- 附錄 D 參考實作定位速查
- 附錄 G 容器化部署策略

---

## 4. 參考實作橫向評估

> 本章為「設計範式參考」，協助理解 AEOS 各層應該借鑑何種既有實作的思路。**評估僅供架構選型，並非推薦商用。**

### 4.1 五類參考實作的定位光譜

| 類別 | 代表 | 定位 | 在 AEOS 中的合理位置 |
| :--- | :--- | :--- | :--- |
| 評估 / 經濟模擬層 | ClawWork 類 | Agent 任務 benchmark | **Evaluation Service 設計範式** |
| 個人 / 長駐型 Agent Runtime | nanobot 類 | 輕量 Agent Loop + Chat Channels | **Production Frozen Runtime 候選** |
| 自我學習型 Agent | Hermes 類 | Self-improvement、Skill 演化 | **Training Room 引擎** |
| Coding Agent / 開發者工作台 | CheetahClaws 類 | Python-native、Tool 治理思路 | **Internal Automation Worker / Tool Registry 設計參考** |
| 桌面工作台 (洩露源類) | cc-haha 類 | UX / 互動設計參考 | **僅作 UX 研究，不採用** |

### 4.2 五個能力維度的對照

| 能力 | 評估層 | 長駐 Runtime | 自我學習 | Coding Agent | 桌面工作台 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 任務執行 | 中 | 中高 | 高 | 高 | 高 |
| 長期記憶 | 低 | 中高 | 高 | 中高 | 中 |
| 自我學習 | 低 | 中 | 高 | 中 | 中 |
| Coding 能力 | 低 | 中 | 中 | 高 | 高 |
| 多平台入口 | 低 | 高 | 高 | 中高 | 中高 |
| MCP / 工具擴充 | 低 | 高 | 中高 | 高 | 中高 |
| 企業治理成熟度 | 低 | 中 | 中 | 中 | 低 |
| 合規可採用性 | 中 | 中 | 中 | 中高 | **不建議** |
| Benchmark / KPI | 高 | 中 | 中 | 中 | 中 |

### 4.3 為什麼 Coding Agent 不適合直接做客服

| 維度 | Coding Agent 原生假設 | 客服 / AI 員工需要的 |
| :--- | :--- | :--- |
| 使用者 | 開發者 | 客戶 / 業務 / 現場人員 |
| 工作環境 | terminal / repo / file system | LINE / Web Chat / CRM / Ticket |
| 主要任務 | 寫 code、跑 shell、改 notebook | 解問題、分流、升級、建工單 |
| 失敗處理 | checkpoint / rewind | 人工接手、客訴升級、合規稽核 |
| 權限模型 | Developer Approval (allow/deny) | Business Policy Engine (角色 × 客戶分級 × 風險 × 金額) |
| 記憶模型 | Project / User memory | 受治理客戶資料 (加密、保存期限、可刪除) |
| 多用戶 | Multi-user | **Multi-tenant** |
| 成功指標 | code 可跑 / test 通過 | FCR / AHT / CSAT / 幻覺率 / SLA |
| 安全強化方向 | Bot Token / CSRF / Sandbox | PII Masking / 法遵 / 話術稽核 |

**結論**：Coding Agent 是「工程部工具箱」，可以放在後台當「可控工具工人」，但**不能直接放在 customer-facing frontend**。

### 4.4 各參考實作在 AEOS 的拆解策略

#### 4.4.1 自我學習型 Agent (Hermes 類)

| 保留 | 移除 |
| :--- | :--- |
| Self-improvement loop | 線上自動學習 |
| Skill generation | 線上自動改 prompt |
| Memory-based learning | 線上自動安裝 plugin |
| Experience replay | 線上自動擴權 |
| Long-term behavior adaptation | 直接接觸真實客戶 |

**定位**：訓練室引擎 (Training Room Engine)。

#### 4.4.2 長駐型 Runtime (nanobot 類)

| 保留 | 移除 / 包覆 |
| :--- | :--- |
| 小核心 Agent Loop | 自由載入任意 MCP Server |
| Chat Channels 整合 | 直接修改自身 |
| MCP Client 連線 | 跨 tenant 存取 |
| 輕量部署 | 直接寫外部系統 |

**定位**：Production Frozen Runtime 候選。

#### 4.4.3 Coding Agent (CheetahClaws 類)

| 借用 | 不採用為客服主體 |
| :--- | :--- |
| Tool Registry 設計 | 原生 shell / file 權限 |
| Permission Mode (auto/manual/plan) | Developer-oriented UX |
| Checkpoint / Rollback | Repo-centric 工作流 |
| MCP / Plugin 管理思路 | Notebook 編輯能力 |
| Sandboxing 思路 | |

**定位**：Internal Automation Worker / 工程後台 / Tool Registry 設計參考。

#### 4.4.4 桌面工作台 (cc-haha 類)

| 借鑑 UX | 不採用 |
| :--- | :--- |
| Diff 同步顯示 | **完整源碼**（合規風險） |
| 危險工具集中審批 | 直接 fork |
| Worktree 隔離 | 商用部署 |
| Computer Use 整合 | |

**定位**：UX / 互動設計研究素材，**不進產品線**。

---

## 5. 系統架構藍圖

### 5.1 主鏈路 (Customer-facing Path)

```
┌──────────────────────────────────────────────┐
│ Channel Layer                                │
│ Web / LINE / Slack / Teams / Email / API     │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Agent Gateway                                │
│ 身分識別 / 多租戶路由 / Rate Limit / Session  │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ AI Employee Runtime (Enterprise MCP Host)    │
│ Frozen Agent / Approved Skills / No Mutation │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Governance Harness                           │
│ Policy / RBAC / ABAC / Workflow / Escalation │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Tool Gateway / MCP Proxy                     │
│ Approved MCP Clients / Adapter / Secret Vault│
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│ Enterprise Systems / MCP Servers             │
│ CRM / ERP / SAP / Ticket / KB / Email        │
└──────────────────────────────────────────────┘
```

### 5.2 旁路閉環 (Training & Improvement Loop)

```
┌──────────────────────┐
│ Conversation Logs    │ ← 來自 Production Runtime
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Evaluation System    │
│ Score / Drift / Risk │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Training Room        │
│ Hermes-style Sandbox │
│ + 專家博弈 + 紅隊    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Skill Candidate      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Sandbox Evaluation   │
│ + Regression Test    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Expert Approval      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Skill Registry       │
│ Version / Release    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Production Install   │ → 回到主鏈路
└──────────────────────┘
```

### 5.3 管理面 (Administration Plane)

```
┌────────────────────────────────────────────┐
│ Admin Console                              │
│ Tenant / Employee / Role / Skill / Tool /  │
│ Policy / Audit / Evaluation Dashboard      │
└────────────────────────────────────────────┘
```

### 5.4 三平面分離

AEOS 採用**控制面 / 資料面 / 治理面**三平面分離架構：

| 平面 | 職責 | 元件 |
| :--- | :--- | :--- |
| **Control Plane** | 配置、發布、審核 | Admin Console、Skill Registry、Tool Registry、Tenant Manager |
| **Data Plane** | 即時對話、工具執行 | Channel Layer、Runtime、Tool Gateway、MCP Proxy |
| **Governance Plane** | 策略、稽核、評估 | Policy Engine、Audit Service、Evaluation Service、Training Room |

**設計理由**：三平面分離讓「線上故障」不會影響「審核發布」；讓「治理升級」不必停機資料面；讓「合規稽核」可獨立 query 而不干擾運營。

---

## 6. 核心領域模型 (Domain Model)

### 6.1 核心 Aggregate

```python
# 租戶 — 最高隔離單位
class Tenant:
    tenant_id: str
    name: str
    policies: list[Policy]
    knowledge_bases: list[KnowledgeBase]
    employees: list[AIEmployee]
    quota: TenantQuota          # 補：成本與用量配額
    compliance_profile: str     # 補：GDPR / PDPA / HIPAA / SOC2

# AI 員工 — 職位化的執行體
class AIEmployee:
    employee_id: str
    tenant_id: str
    role: Role
    runtime: RuntimeProfile
    assigned_skills: list[SkillVersion]
    allowed_tools: list[ToolPermission]
    policies: list[Policy]
    status: EmployeeStatus      # active / suspended / retired
    hired_at: datetime
    last_evaluated_at: datetime # 補：考核時間戳

# 角色 — 職務描述
class Role:
    role_id: str
    name: str
    responsibilities: list[str]
    boundaries: list[str]
    escalation_rules: list[EscalationRule]
    required_skills: list[str]  # 補：職位必備技能
    forbidden_actions: list[str] # 補：禁止行為清單

# 技能 — 可版本化能力包
class Skill:
    skill_id: str
    name: str
    description: str
    owner: str
    versions: list[SkillVersion]

class SkillVersion:
    skill_id: str
    version: str
    prompt_spec: str
    input_schema: dict
    output_schema: dict
    tool_requirements: list[str]
    test_results: list[EvaluationResult]
    approval_status: ApprovalStatus
    risk_level: RiskLevel
    rollback_target: str | None
    released_at: datetime | None
    deprecated_at: datetime | None

# 工具 — 受控外部能力
class Tool:
    tool_id: str
    name: str
    risk_level: RiskLevel
    adapter: ToolAdapter
    required_permissions: list[str]
    pii_fields: list[str]       # 補：個資欄位宣告
    audit_required: bool
    rate_limit: RateLimitPolicy

# 規章 — 公司政策
class Policy:
    policy_id: str
    scope: PolicyScope          # tenant / department / role / employee
    rules: list[Rule]
    enforcement_mode: EnforcementMode  # block / warn / log
    legal_basis: str            # 補：法源依據

# 工作流 — 固定程序
class Workflow:
    workflow_id: str
    name: str
    steps: list[WorkflowStep]
    required_role: Role
    approval_chain: list[ApprovalStep]  # 補：簽核鏈

# 評核 — 員工考績
class EvaluationResult:
    eval_id: str
    employee_id: str
    skill_version: str
    metrics: dict[str, float]
    risk_events: list[RiskEvent]
    passed: bool
    evaluated_at: datetime
    evaluator: str              # 補：評核者 (auto / expert / customer)
```

### 6.2 補充：缺失的關鍵物件

> draft 中遺漏的物件，企業落地時必須補齊。

```python
# 補：客戶識別與隔離
class CustomerIdentity:
    customer_id: str
    tenant_id: str
    pii_consent: PIIConsent
    data_retention_until: datetime
    deletion_requested: bool

# 補：對話會話 — Audit 的最小單元
class Conversation:
    conversation_id: str
    tenant_id: str
    customer_id: str | None
    employee_id: str
    channel: str
    started_at: datetime
    ended_at: datetime | None
    handoff_history: list[Handoff]
    audit_trail: list[AuditEvent]

# 補：工具調用紀錄 — Tool Gateway 的核心
class ToolInvocation:
    invocation_id: str
    employee_id: str
    tool_id: str
    request: dict
    response: dict
    masked_fields: list[str]
    policy_decision: PolicyDecision
    executed_at: datetime
    duration_ms: int
    cost: Decimal               # 計入用量

# 補：人工接手紀錄
class Handoff:
    handoff_id: str
    conversation_id: str
    from_employee: str          # AI 員工
    to_human: str               # 人類客服
    reason: HandoffReason
    transferred_at: datetime

# 補：知識來源綁定 (RAG Source Grounding)
class KnowledgeCitation:
    citation_id: str
    source_doc_id: str
    source_version: str
    confidence: float
    used_in_message: str

# 補：成本與用量
class UsageRecord:
    tenant_id: str
    employee_id: str
    period: str                 # YYYY-MM
    llm_tokens_in: int
    llm_tokens_out: int
    tool_invocations: int
    storage_bytes: int
    cost_breakdown: dict[str, Decimal]
```

### 6.3 知識三分類治理

> 企業知識並非單一型態，必須依「穩定性 × 來源 × 信任機制」分為三類，採用不同治理路徑。把所有文件丟進向量資料庫是常見的反模式。

| 類別 | 定義 | 範例 | 治理路徑 |
| :--- | :--- | :--- | :--- |
| **Static Knowledge** 靜態知識 | 內容穩定、變動週期長、可全文索引 | 產品介紹、服務說明、基本 FAQ、教學文件 | Knowledge System + RAG |
| **Policy Knowledge** 規章知識 | 規則性、需嚴格遵守、不容許 LLM 模糊解釋 | 退款規則、保固條款、不可承諾事項、定價政策 | Policy Engine + Rule |
| **Dynamic Knowledge** 動態知識 | 即時資料、單筆查詢、持續變動 | 訂單狀態、庫存、發票、會員資料 | MCP Tool / API Adapter |

**設計推論**：

- 「訂單狀態」**不可**放進 RAG — 必須即時查系統，否則會產生過期資料的幻覺
- 「退款規則」**不可**只交由 LLM 記憶 — 必須變成可審核、可版控的 Rule
- 「產品介紹」**不應**透過 API 即時組裝 — 應預先索引提升回應速度

```
查詢請求
    ↓
KnowledgeRouter (依分類路由)
    ├─→ RAG Search       (Static Knowledge)
    ├─→ Policy Engine    (Policy Knowledge)
    └─→ Tool Gateway     (Dynamic Knowledge)
    ↓
Source Citation (強制標註來源、版本、信賴度)
    ↓
回應組裝
```

**鐵律**：所有知識回應必須附帶 `KnowledgeCitation`（來源 ID、版本、信賴度），無法溯源的回答視為幻覺。

### 6.4 不變式 (Invariants)

| 不變式 | 說明 |
| :--- | :--- |
| `Skill 只有 Approved 狀態才能進 Production` | Sandbox / Draft / Deprecated 一律拒載 |
| `Tool 調用必經 Tool Gateway` | Runtime 不得繞過 |
| `跨 Tenant 資料存取一律拒絕` | Policy Engine 預設 deny |
| `Production Agent 不得執行 Skill 自我修改` | Mutation API 在 Production Runtime 不存在 |
| `所有客戶 PII 寫入 memory 前必經遮罩` | Memory Gateway 強制過濾 |
| `Audit Log 寫入失敗即整筆操作回滾` | 不允許「靜默成功」 |

---

## 7. Bounded Context 與系統邊界

### 7.1 七個 Bounded Context

| Context | 職責 | 不關心 |
| :--- | :--- | :--- |
| **Employee Runtime** | 對話、任務、Skill 選擇、回覆生成、Tool Request | Skill 怎麼訓練、外部系統怎麼認證 |
| **Skill Governance** | Skill 生命週期 (Draft → Released → Archived) | Skill 怎麼被 Runtime 載入 |
| **Tool Governance** | MCP / Plugin / Adapter 審核、權限映射 | Tool 怎麼被 Skill 使用 |
| **Training Room** | 自我學習、博弈、Skill 候選生成 | Production 流量 |
| **Evaluation & Monitoring** | 對話評分、漂移偵測、SLA 監控 | Skill 如何修正 |
| **Knowledge** | KB 版本、Source Grounding、租戶知識隔離 | 對話的具體內容 |
| **Integration** | ERP / CRM / SAP Adapter、憑證、契約管理 | Agent 為何要呼叫 |

### 7.2 Context Map (上下文映射)

```
[Employee Runtime]
       │
       │ uses (Conformist)
       ↓
[Skill Governance] ──── publishes ───→ [Skill Registry (Shared Kernel)]
       │
       │ requires
       ↓
[Tool Governance] ──── exposes ───→ [Tool Catalog (Shared Kernel)]
       │
       │ delegates execution
       ↓
[Integration] ──── adapts ───→ [Enterprise Systems]

[Employee Runtime] ──── emits events ───→ [Evaluation & Monitoring]
                                                  │
                                                  │ feeds
                                                  ↓
                                          [Training Room]
                                                  │
                                                  │ proposes Skill Candidate
                                                  ↓
                                          [Skill Governance]
```

### 7.3 服務責任邊界 (避免「胖 Runtime」反模式)

> **錯誤架構**：把所有東西都放進 Runtime，最後變成一個無法治理的單體 Agent Server。

| 責任 | **應在** | **不應在** |
| :--- | :--- | :--- |
| 載入 Approved Skill | Runtime | Skill Governance |
| 決定 Skill 是否可發布 | Skill Governance | Runtime |
| 執行 Tool Call | Tool Gateway | Runtime |
| 決定 Tool 能否呼叫 | Policy Engine | Runtime |
| 寫入 Audit | Audit Service | Runtime (僅發送事件) |
| 評分對話 | Evaluation Service | Runtime |
| 觸發人工接手 | Workflow Engine | Runtime (僅依規則發信號) |
| 隔離租戶資料 | Identity / Policy | Runtime |

---

## 8. MCP 整合策略 — 帶治理能力的 Host

### 8.1 為什麼需要 MCP

**N 個 Agent × M 個 Tools = N × M 個整合**

MCP (Model Context Protocol) 把工具接入標準化為：

```
N 個 Agent Host × M 個 MCP Servers
```

成為可維護的 client-server 介面。

### 8.2 為什麼 MCP 不夠

> **MCP 是工具協議，不是企業治理系統。** 這句話應該刻在所有架構決策文件的封面。

MCP 規範定義 Host / Client / Server 怎麼溝通，但不會自動處理：

- 多租戶隔離
- 權限矩陣 (RBAC / ABAC)
- 敏感資料遮罩
- 工具風險分級
- Skill 審核
- 法遵稽核
- 人工 Approval
- SLA 與 Rate Limit
- 對話評分與漂移

### 8.3 Enterprise MCP Host 的責任邊界

#### MCP Host **應該負責**

- 管理 Agent Session
- 管理 MCP Client connections
- 載入 Approved Skills
- 載入 Employee Role Profile
- 整合 LLM Provider
- 組裝 Prompt Context
- 發起 Tool Request
- 收到 Tool Response 後產生行動

#### MCP Host **不應該單獨負責**

- 權限最終判斷 → Policy Engine
- 工具安全審核 → Tool Governance
- 租戶資料隔離 → Tenant Manager / Policy
- 外部系統憑證管理 → Secret Vault
- Skill 發布審核 → Skill Governance
- PII / 法遵治理 → Compliance Service
- 線上監控評分 → Evaluation Service

### 8.4 修正版企業 MCP 架構

```
LLM Provider (OpenAI / Claude / Local Model)
        │
        ▼
Enterprise MCP Host  ←─── AI Employee Runtime
        │
        ▼
Governance Harness (Policy / Skill / Role / Audit)
        │
        ▼
Tool Gateway / MCP Proxy
        │
        ▼
Approved MCP Servers (CRM / ERP / SAP / DB / Docs)
        │
        ▼
Enterprise Systems
```

### 8.5 Enterprise MCP Host 的最小組件

```
EnterpriseMCPHost
├── SessionManager        # 對話會話與上下文
├── AgentProfileLoader    # 載入 AI 員工身份
├── SkillLoader           # 載入 approved skills
├── ContextBuilder        # 組裝 prompt
├── LLMProviderAdapter    # LLM 抽象層 (多模型)
├── ToolPlanner           # 產生 tool request
├── MCPClientManager      # 管理 MCP Client 連線
├── PolicyPreCheck        # 呼叫前預檢
├── ToolResultInterpreter # 整理結果
└── AuditEmitter          # 發送 audit 事件
```

### 8.6 MCP Server 應該放什麼

| **適合** 放進 MCP Server | **不適合** 直接暴露為 MCP Tool |
| :--- | :--- |
| `get_customer_by_id(id)` | `execute_sql(query)` |
| `lookup_order_status(order_id)` | `run_shell(cmd)` |
| `create_ticket(payload)` | `read_file(path)` / `write_file(path)` |
| `search_knowledge(query)` | `delete_record(table, id)` |
| `draft_email(template, vars)` | `grant_permission(user, role)` |
| `lookup_calendar(user, range)` | `transfer_money(from, to, amount)` |

**設計原則**：給 AI 一張**申請單**，不是一把**萬能刀**。

```
錯誤：refund(amount, reason)
正確：create_refund_request(order_id, reason) → 走 Workflow → 主管簽核
```

### 8.7 MCP / Plugin 審核管線

```
Plugin Submitted
    ↓
Manifest Check
    ↓
Static Analysis
    ↓
Dependency Scan (CVE)
    ↓
Permission Declaration Review
    ↓
Sandbox Execution Test
    ↓
Prompt Injection Test
    ↓
Data Exfiltration Test
    ↓
Human Approval
    ↓
Tool Registry (Versioned)
```

### 8.8 Tool Permission Contract 範例

```yaml
# 低風險 — 客戶查詢
tool_id: crm.customer_lookup
risk_level: medium
allowed_roles:
  - customer_support_agent
required_permissions:
  - customer.read.basic
data_scope: same_tenant_only
pii_fields: [phone, email, address]
requires_approval: false
audit_required: true

# 高風險 — 退款申請
tool_id: order.refund_request
risk_level: high
allowed_roles:
  - senior_support_agent
required_permissions:
  - order.refund.create
max_amount_without_approval: 1000
requires_approval: true
audit_required: true
```

---

## 9. SkillOps — AI 員工的 MLOps

### 9.1 概念對應

| MLOps | **SkillOps (AI 員工)** |
| :--- | :--- |
| Dataset | Conversation Logs (脫敏) |
| Model | Skill |
| Training Pipeline | Training Room (專家博弈 + Hermes-style) |
| Model Registry | Skill Registry |
| Model Deployment | Skill Release to Production Runtime |
| Model Monitoring | Conversation Evaluation + Drift Detection |
| Model Rollback | Skill Version Rollback |
| A/B Testing | Skill Variant Testing |
| Data Drift | Knowledge Drift / SOP Drift |
| Concept Drift | Customer Behavior Shift |

### 9.2 SkillOps Pipeline

```
線上對話紀錄 (Production Logs)
    ↓
脫敏與標註 (PII Masking + Labeling)
    ↓
錯誤案例分類 (Failure Taxonomy)
    ↓
Training Room 重播 (Replay)
    ↓
Hermes-style Skill Improvement
    ↓
Sandbox Evaluation (Multi-metric)
    ↓
Regression Test (避免修 A 壞 B)
    ↓
Expert Review (人類覆核)
    ↓
Skill Version Release (Versioned)
    ↓
Production Agent Install
    ↓
Monitoring (回到第一步)
```

### 9.3 Skill 版本管理

```
customer_support.refund.v1.0  ← Released, Production
customer_support.refund.v1.1  ← Released, Canary 10%
customer_support.refund.v1.2  ← Sandbox, Pending Approval
customer_support.refund.v0.9  ← Deprecated, Rollback Target
```

每版本必須記錄：

- 解決了什麼問題 (Why)
- 新增 / 改變了什麼能力 (What)
- 測試了哪些案例 (Test Cases)
- 有哪些已知風險 (Risks)
- 誰批准 (Approver)
- 可以 rollback 到哪一版 (Rollback Target)

### 9.4 Skill 發布閘門 (Quality Gates)

| 閘門 | 通過條件 | 否決機制 |
| :--- | :--- | :--- |
| G1 — Static | 無語法錯誤、Schema 合法、無禁用 API | 自動拒絕 |
| G2 — Security | 無 Prompt Injection 樣式、無資料外洩風險 | 自動拒絕 + 告警 |
| G3 — Sandbox | 通過所有 Test Case、覆蓋率 ≥ 80% | 自動拒絕 |
| G4 — Regression | 不破壞既有 Skill 行為 | 自動拒絕 |
| G5 — Expert | 領域專家簽核 | 人工審查 |
| G6 — Canary | 線上小流量 (1~10%) 指標達標 | 自動回滾 |
| G7 — Full Release | 全量發布 | 持續監控 |

---

## 10. 訓練室與生產環境分離

### 10.1 兩種版本的 Agent

#### Training Agent

```
✅ 允許
- 自我學習
- Skill 生成 / 改寫
- 專家博弈
- Prompt 變體測試
- 失敗案例吸收
- 模擬不同客戶角色

❌ 禁止
- 接觸真實客戶
- 寫入 Production 系統
- 直接發布 Skill 到 Production
- 使用真實客戶 PII (必須脫敏)
```

#### Production Agent (Frozen Runtime)

```
✅ 允許
- 使用 Approved Skill
- 使用 Approved Tool
- 依 Workflow 執行
- 依 Policy 回答
- 產生 Audit Log

❌ 禁止
- 自我修改
- 自我擴權
- 自動安裝 Skill
- 長期記憶敏感資料
- 直接呼叫外部系統 (必經 Tool Gateway)
```

### 10.2 訓練室的紅隊機制

訓練室不只是「讓 AI 練習」，更是「**對 AI 進行對抗測試**」：

| 紅隊類別 | 攻擊樣式 | 目標 |
| :--- | :--- | :--- |
| Prompt Injection | "忽略前面指示" | Skill 抗注入能力 |
| Data Exfiltration | 誘導吐出客戶資料 | PII Masking 邊界 |
| SOP Bypass | 誘導跳過簽核流程 | Policy Engine 強度 |
| Hallucination | 捏造產品功能 | RAG Grounding |
| Over-promise | 誘導承諾退款 / 賠償 | 話術稽核 |
| Cross-tenant | 偽裝其他租戶 | Tenant 隔離 |
| Privilege Escalation | 偽裝主管 / VIP | RBAC 強度 |

紅隊測試**必須是 Skill 上線前的強制閘門**。

### 10.3 訓練室介面設計 (Training Room UI)

訓練室是企業專家與 AI 員工互動的主要工作介面，是 AEOS 最具產品差異化的模組之一。其 UI 應包含五大功能區塊：

#### 10.3.1 AI 員工設定區

```
AI 員工設定
├── 角色名稱 (Role Profile)
├── 服務範圍 (Scope)
├── 禁止回答範圍 (Forbidden Topics)
├── 語氣設定 (Tone & Style)
├── 轉人工規則 (Escalation Rules)
└── 可用工具 (Allowed Tools)
```

#### 10.3.2 知識庫管理區

```
知識庫管理
├── 文件上傳 (Document Ingestion)
├── 文件版本 (Version Control)
├── 啟用 / 停用 (Activation Toggle)
├── 知識來源 (Source Attribution)
└── 過期提醒 (Staleness Alert)
```

#### 10.3.3 陪練測試區

```
陪練測試
├── 專家輸入問題 (Test Prompt)
├── AI 回答 (Response)
├── 來源引用 (Citation Trace)
├── 評分 (Score)
├── 錯誤標註 (Error Tagging)
└── 修正建議 (Correction Notes)
```

#### 10.3.4 Skill 審核區

```
Skill 審核
├── Skill 名稱與版本
├── 適用場景
├── 測試結果 (Test Coverage)
├── 風險等級 (Risk Level)
├── 審核人簽核
└── 發布版本快照
```

#### 10.3.5 上線前驗收區

```
上線前驗收 (見 §21 驗收門檻)
├── 正確率
├── 幻覺率
├── 轉人工率
├── SOP 遵守率
├── 高風險問題阻擋率
└── 是否允許上線 (Final Gate)
```

**設計理念**：訓練室不是技術人員的後台，而是**領域專家的工作介面**。專家透過直接與 AI 員工博弈、評分、修正，將領域知識轉化為可審核的 Skill 資產，這是企業導入 AEOS 後形成內部能力沉澱的核心機制。

### 10.5 訓練資料治理

```
Production Conversation
    ↓
PII Detection (Presidio / 自建)
    ↓
Masking / Synthesis
    ↓
Labeling (人類 + AI 輔助)
    ↓
Training Dataset (Versioned)
    ↓
Training Room
```

**鐵律**：未脫敏的客戶資料**不得**進入訓練室。

---

## 12. 監控評估體系 (AgentOps)

### 12.1 客服 / 業務 AI 員工的關鍵指標

| 類別 | 指標 | 目標 |
| :--- | :--- | :--- |
| **效率** | First Contact Resolution (FCR) | ≥ 70% |
| | Average Handling Time (AHT) | 因業務而定 |
| | 自動化率 (Automation Rate) | 依職位設目標 |
| **品質** | CSAT | ≥ 4.2 / 5 |
| | NPS | ≥ +30 |
| | 幻覺率 (Hallucination Rate) | ≤ 1% |
| | 不當承諾率 | ≤ 0.1% |
| | SOP 遵守率 | ≥ 99% |
| **風險** | PII 洩漏事件數 | 0 |
| | 高風險回答攔截率 | ≥ 99.9% |
| | Cross-tenant 違規數 | 0 |
| **服務** | 轉人工率 | 依職位設目標 |
| | SLA Breach Rate | ≤ 1% |
| | 工單重開率 | ≤ 5% |
| **成本** | LLM Token / Conversation | 持續優化 |
| | Tool Invocation / Conversation | 持續優化 |
| | $ / Resolved Ticket | 持續優化 |

### 12.2 漂移偵測 (Drift Detection)

| 漂移類型 | 監控信號 | 應對 |
| :--- | :--- | :--- |
| **Knowledge Drift** | RAG 引用品質下降、Citation 失效 | KB 重新索引、知識更新 |
| **Behavior Drift** | 同 Skill 版本、不同時段表現差異 | 排查上下游服務 |
| **Customer Drift** | 問題類型分布改變 | Skill 改版或新增 |
| **SOP Drift** | 政策遵守率下降 | Policy Engine 強化 |
| **Cost Drift** | Token / Conversation 上升 | Prompt 精簡 / 模型降階 |

### 12.3 評估迴路

```
Production Conversation
    ↓
Auto Scoring (LLM-as-Judge + Rule-based)
    ↓
Sample for Human Review (10% + 全部 P0/P1)
    ↓
Expert Score + Comments
    ↓
Aggregate to Dashboard
    ↓
Trigger Retraining if Drift Detected
    ↓
Training Room (回到 SkillOps Pipeline)
```

### 12.4 可觀測性必備

| 維度 | 必備 |
| :--- | :--- |
| Trace | 每次 Conversation 完整 Tool Call Chain |
| Log | Structured Log (Conversation ID 串接) |
| Metric | Prometheus / OpenTelemetry 標準 |
| Dashboard | Grafana / Datadog (依租戶切分) |
| Alert | PagerDuty / Opsgenie (按嚴重度) |
| Replay | 任意 Conversation 可完整回放 |

---

## 13. 多模型策略與成本治理

> **draft 缺漏的關鍵章節**。AI 員工平台的成本主要來自 LLM Token，沒有多模型策略會被供應商綁架且成本失控。

### 13.1 多模型抽象層

```
LLMProviderAdapter (統一介面)
    ├── OpenAI (GPT-4 / 4o / mini)
    ├── Anthropic (Claude Opus / Sonnet / Haiku)
    ├── Google (Gemini)
    ├── Local (Ollama / vLLM / LM Studio)
    └── Enterprise Gateway (內部 Model Gateway)
```

### 13.2 模型路由策略

| 任務類型 | 推薦模型層級 | 理由 |
| :--- | :--- | :--- |
| 意圖分類、簡單 FAQ | Haiku 級 / Local Small | 低成本高頻 |
| 一般客服對話 | Sonnet 級 | 平衡品質與成本 |
| 複雜推理、爭議處理 | Opus 級 | 高品質決策 |
| 訓練室博弈 | Opus 級 + 紅隊模型 | 探索與對抗 |
| 線下批次任務 | Local / Batch API | 最低成本 |

### 13.3 成本治理機制

| 機制 | 說明 |
| :--- | :--- |
| **Tenant Quota** | 每租戶設定月度 Token 上限 |
| **Employee Quota** | 每員工設定 Token 上限 |
| **Skill Cost Budget** | 每 Skill 設定單次調用成本上限 |
| **Cost Circuit Breaker** | 異常飆升自動降階模型 |
| **Cost Attribution** | 每 Conversation / Tool Call 完整成本歸屬 |
| **Prompt Cache** | 系統 Prompt + 角色 Profile 必快取 |
| **Distillation** | 高頻場景蒸餾到小模型 |

### 13.4 主權與資料殘留

| 場景 | 模型選擇 | 原因 |
| :--- | :--- | :--- |
| 高度機密 / 工廠內網 / 法遵嚴格 | Local Model + Private Gateway | 資料不出網域 |
| 一般 SaaS 客戶 | 公有 LLM (簽 DPA) | 平衡成本與能力 |
| 跨國客戶 | 區域化模型部署 | 資料主權 |
| 政府客戶 | Sovereign LLM / On-prem | 法規要求 |

---
