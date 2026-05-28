# 01 — Role Responsibilities & RACI

DevTeam 區分 **driver skill**（主動產文件的角色）與 **critique persona**（freeze review 時的視角）。Driver = 「能力容器」，Persona = 「眼鏡」。同一個 RACI 角色可同時是 driver owner 與 critique persona。

---

## 12 Personas Cheat Sheet

| Persona | 最該盯的一件事 | 最重要交付物 | 最晚不能錯過 | Critique 視角 |
|:--------|:--------------|:-------------|:------------|:--------------|
| **PM** | 問題值不值得做 | PRD / KPI | 進入 delivery planning 前 | scope 對不對齊商業目標、KPI 是否可量測 |
| **PO** | 優先順序是否一致 | Ordered Backlog | Sprint planning 前 | 是否值得排進這個迭代、與其他 item 互斥嗎 |
| **BA** | Stakeholder 與規則是否漏掉 | Stakeholder Map / Rule Catalog | System analysis 前半段 | 規則完整性、stakeholder 覆蓋、合規 |
| **SA** | 系統行為是否可驗收 | System Spec | Architecture/System design 前 | use case 完整性、acceptance 可驗、edge case 覆蓋 |
| **UX** | 核心任務是否走得通 | User Flow / Prototype | UI handoff 前 | task success、error/empty/loading state、a11y |
| **UI** | 開發規格是否足夠精準 | Hi-fi / Component Spec | FE/Mobile build 前 | state coverage、token、responsive、handoff 完整 |
| **Architect** | 重要決策是否可追溯 | C4 / ADR / NFR | API/DB freeze 前 | bounded context、failure mode、operability、演進路徑 |
| **SD** | 模組設計是否可平行實作 | Module Design / API Spec | Implementation 前 | 模組責任清晰、API 穩定、平行可實作性 |
| **DBA** | migration 是否可演練 | DDL / Migration / Data Dict | Integration 前 | schema 變更可回滾、retention、PII、index |
| **QA** | 品質證據是否成立 | Test Plan / Completion Report | Go/No-Go 前 | 可測、exit criteria 明確、自動化覆蓋 |
| **DevOps** | 是否可重複部署 | Pipeline / Runbook | Release 前 | pipeline gate、rollback、env 自動化 |
| **SRE** | 是否可觀測、可回滾 | SLO / Alerts / Postmortem | Release 前與後 | observability、SLO、error budget、incident path |

> **圖級交付物（單一權威 = KB-07 §3 By Role × Phase）**：上表交付物欄為**文件級**；各 driver **必畫 / 按需** 的圖（State Machine / Sequence / C4 / ERD / Deployment / Activity / Class）以 **`07_diagram_picker.md` §3** 為唯一歸屬權威，本檔不複製清單（避免漂移）。**圖是 conditional 交付物**（非每模組都畫，依 KB-07 §1/§2 觸發條件）：analyst 必畫 State Machine（核心聚合根）、design 必畫 Sequence（關鍵 endpoint）、ops 必畫 Deployment + Activity（rollout / runbook 流程）、Class 僅 domain model 複雜時補。freeze 時由 KB-04 各 gate evidence 強制。

---

## RACI 表（交付物 × 角色）

R = Responsible（執行），A = Accountable（最終負責），C = Consulted（諮詢），I = Informed（被告知）

| 交付物 / 決策 | PM/PO | BA/SA | UX/UI | Architect | Dev Lead | DBA | QA | DevOps/SRE | Stakeholders |
|:--------------|:------|:------|:------|:----------|:---------|:----|:---|:-----------|:-------------|
| Problem Statement / KPI | A | C | C | I | I | I | I | I | C |
| PRD | A | R | C | C | C | I | C | I | C |
| User Flow / Wireframe | C | C | A/R | I | C | I | C | I | C |
| System Spec | C | A/R | C | C | C | C | C | I | I |
| ADR / C4 / NFR | I | C | I | A/R | C | C | C | C | I |
| API Spec | I | C | C | C | A/R | I | C | I | I |
| DB Schema / Migration | I | C | I | C | C | A/R | C | C | I |
| Test Plan / Exit Criteria | I | C | C | I | C | I | A/R | C | I |
| Runbook / Rollback | I | I | I | C | C | I | C | A/R | I |
| Release Go/No-Go | C | I | I | C | R | C | R | R | I |

---

## Driver Skill 與 Persona 的對應

| Driver Skill | 涵蓋的 RACI 角色 | Owner critique persona | 邊界提醒 |
|:-------------|:-----------------|:----------------------|:---------|
| devteam-pm | PM, PO | pm + po | PM 偏商業/scope；PO 偏 backlog priority。同人可兼。 |
| devteam-analyst | BA, SA | ba + sa | BA 管 stakeholder/rules；SA 管 system spec。overlap 大但仍可區辨。 |
| devteam-ux | UX, UI | ux + ui | UX 流程；UI 視覺與 handoff。 |
| devteam-arch | Architect | arch | C4/ADR/NFR 都這裡。 |
| devteam-design | SD, DBA | sd + dba | SD 管 API/Module；DBA 管 schema/migration。 |
| devteam-qa | QA | qa | Test plan + exit criteria。 |
| devteam-ops | DevOps, SRE | devops + sre | DevOps 管 pipeline；SRE 管 SLO/observability/incident。 |

---

## 產品角色 ↔ Persona ↔ Driver Crosswalk（單一真相對照表）

> **為什麼需要這張表**：系統裡有三套角色枚舉 —— 產品門面 `product_to_launch/lib/taxonomy.ts` 的 **10 角色**、本檔的 **12 critique persona**、driver skill 的 **7 條合併主線**。三者不是 1:1，缺對照會漂移。任何角色/交付物的新增異動，**先改這張表**再改其他地方。
>
> **機械單一真相 = `devteam_knowledge_base/_registry.json` 的 `roles` 段**（persona ↔ driver ↔ product_role）。本表為人類可讀版；linter C13d 驗每個 persona 有對應 `.claude/agents/devteam-<persona>-persona.md`（防 role 枚舉漂移 HB-1）。

| 產品角色 (slug) | Critique persona | Driver skill | 產品招牌交付物 | Harness 範本 / 輸出 |
|:----------------|:-----------------|:-------------|:---------------|:--------------------|
| pm | pm | devteam-pm | PRD / Roadmap / KPI | `prd.md` (+ `governance/stakeholders.md`) |
| po | po | devteam-pm（兼） | Ordered Backlog / Acceptance Criteria | `prd.md` §Prioritized Scope Slice（MoSCoW，**取代** sprint Ordered Backlog —— harness 為 feature-spec 導向）；AC 單一真相源在 `system-spec.md`（UC priority 欄） |
| ba | ba | devteam-analyst | Stakeholder Map / Business Rules Catalog | `system-spec.md` + `governance/rule-catalog.md` |
| sa | sa | devteam-analyst | System Spec / SRS / State Machine | `system-spec.md` |
| ux | ux | devteam-ux | User Journey / Flow / Wireframe | `user-flow.md` (+ `wireframe-*.md`) |
| ui | ui | devteam-ux（兼） | Hi-fi / Component Spec / Design System | ⚠ 描述落在 `user-flow.md` state coverage，無獨立 UI spec 範本 |
| architect | arch | devteam-arch | C4 / ADR / NFR Matrix / Threat Model | `c4-l1/l2/l3.md` + `adr.md` + `threat-model.md`（條件式，資料分級觸發掛 Gate 4）；NFR 為 arch 內一段 |
| **dev** | **— 無 —** | **— 無 —** | Code / Tests / Migrations / Telemetry | **外部 coding agent 實作**；接手契約 = `specs/<feature>/handoff.md`（見「Scope 邊界」） |
| qa | qa | devteam-qa | Test Plan / Completion Report | `test-plan.md` |
| devops（·SRE） | devops + sre | devteam-ops | Pipeline / SLO / Runbook / Postmortem / **Deployment + Activity 圖**（KB-07 必畫） | `runbook.md`（含 Deployment topology + incident Activity 圖）+ `slo.md` + `release-readiness.md` + `postmortem-template.md` |

**Harness-only persona（產品把它們折進 architect/dev，harness 拆出獨立視角）：**

| Persona | Driver skill | 負責 | 對應產品角色 |
|:--------|:-------------|:-----|:-------------|
| sd（System Designer） | devteam-design | API contract / Module Design / Error Model / **Sequence（關鍵 endpoint，KB-07 必畫）** / Class（按需）→ `openapi.yaml` + sequence/class（落 c4 或 design 文件） | 折進產品 `architect`（RACI 欄稱 **Dev Lead**，三者同指實作設計責任） |
| dba | devteam-design | ERD / DDL / Migration → `erd.md` + `data/migrations/*.sql` | 折進產品 `architect` + `dev` |

**交付物命名 rosetta（產品名 → harness 範本名）：** `srs`/`frd`→`system-spec.md`、`api-spec`→`openapi.yaml`、`data-model`→`erd.md`、`journey-map`→`user-flow.md`、`non-functional-reqs`→ NFR matrix（arch 內一段）、`threat-model`→`threat-model.md`（條件式）、`jtbd`/`value-hypothesis`→`prd.md` 必填段、`ordered-backlog`→`prd.md` §Prioritized Scope Slice（不產 sprint backlog）。

> **2026-05-28 Roundtable B 決議落地**（D1/D2/D3）：JTBD + Value Hypothesis 升 PRD 必填段；Ordered Backlog 降級為 PRD Prioritized Scope Slice；新增條件式 STRIDE threat-model（資料分級觸發掛 Gate 4）。詳見 `.claude/context/devteam/meetings/2026-05-28-harness-gap-planning/MoM.md`。

> **Scope 邊界**：`dev`（Build code）、Operate runtime loop 不在 harness 產出範圍 —— harness 是 **spec 產生器**，產規範包後交外部 coding agent + 運維承接。詳見 `.claude/CLAUDE.md` §Scope 邊界。

---

## Critique Persona 的責任邊界

freeze gate 前的 multi-role review，每個 persona 只該關注**自己最該盯的事**（見第一張表「最該盯的一件事」）。

### 標準 critique 輸出格式

每個 persona agent 產出三段：

```markdown
## [persona-name] critique on docs/<path>

### 重大阻礙（必修才能 freeze）
- [B-1] ...
- [B-2] ...

### 建議調整（可接受但建議改）
- [S-1] ...

### 通過項
- 哪些段落符合 persona 視角

### 跨 persona 衝突點
（若有，列出與其他 persona 觀點的潛在衝突）
```

由 `devteam-orchestrator` 合併為單一 review report。
