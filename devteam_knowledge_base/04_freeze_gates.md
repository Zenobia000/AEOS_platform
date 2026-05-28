# 04 — Freeze Gates

7 個 freeze gates 的 owner、必備 evidence、預設 review intensity、必到 personas。

**設計原則：** Freeze 不是鎖死，是讓並行不失控。每個 gate 都允許後續變更（透過寫新 ADR/DR + cascade），但變更要明文留下決策鏈。

---

## 7 個 Freeze Gates 總表

| Gate | 名稱 | Owner driver | 預設 intensity | 必到 review personas |
|:-----|:-----|:-------------|:---------------|:--------------------|
| 1 | PRD Freeze | devteam-pm | **strict** | ba, sa, ux |
| 2 | UX Flow Freeze | devteam-ux | standard | pm, qa |
| 3 | System Spec Freeze | devteam-analyst | standard | arch, qa |
| 4 | NFR + ADR Baseline | devteam-arch | **strict** | pm, sre, dba |
| 5a | API Contract Freeze | devteam-design | **strict** | pm, qa, sre |
| 5b | DB Schema Freeze | devteam-design | **strict** | arch, qa, sre |
| 6 | Test Ready | devteam-qa | standard | arch（as dev-lead lens）, devops |
| 7 | Release Ready | devteam-ops | **strict** | pm, qa, arch |

---

## 共通 evidence（所有 gate 強制，機械驗）

每個 gate freeze 前，除各自 evidence 外，以下兩項由 `scripts/check-doc-consistency.sh` 強制：

- [ ] **`scripts/check-doc-consistency.sh` 全綠**（C1–C12：斷連結 / 命名 / ID / TC-SEC / parity / 鐵律 / orphan / UC / gate↔Status / header / ASCII / 雙向 parity）
- [ ] **gate owner doc 的 `📋 Status` 已同步**：freeze 該 gate ⟹ owner doc Status = `frozen`（ADR 例外 `Proposed`）。C9 驗。

> 設計：一致性不再靠 persona 肉眼或 AI 記得 — Stop hook 每 turn 結束自動跑 linter，drift 寫 `consistency-drift.md` 並於下次 SessionStart 浮現補償。gate 只是再確認一次全綠。

> **gate 枚舉的機械單一真相 = `devteam_knowledge_base/_registry.json`**（owner_driver / personas / intensity / required_diagrams / feature owner_doc）。改 gate 先改 registry，本檔 cross-ref 不複製；linter C9 讀 registry 的 feature_bindings、C13 驗 registry↔本檔↔state↔agents 對齊（防 KB-to-KB 漂移 HB-1）。

---

## Gate 1: PRD Freeze

**Owner**: devteam-pm（PM persona）

**必備 evidence**:
- [ ] Problem Statement 三項都填（現況 / 為什麼解 / 不解的成本）
- [ ] 至少 1 個可量化 KPI
- [ ] Primary persona + Key scenario 已定義
- [ ] **JTBD 段已填**（每個 job ≥ 1 條 success criterion，可被 user-flow anchor 引用）
- [ ] **Value Hypothesis 段已填**（每條含 counter-metric + 成功閾值；樣本 N 可標 `<TBD, gate 前補>`）
- [ ] In-scope 與 Out-of-scope 都列出，且 **Prioritized Scope Slice 已排序**（MoSCoW / P0-P1-P2，取代 sprint backlog）
- [ ] 主要 risks 已揭露
- [ ] Open questions 已標記（不可以「沒問題」帶過）

**Review personas**:
- `ba`: stakeholder 是否齊、商業規則是否合理
- `sa`: 需求是否可翻成系統規格
- `ux`: persona 與 scenario 是否支援設計

**變更規則**: PRD frozen 後再改 → 寫 `DR`（產品決策），影響 scope 升格為 `ADR`。

---

## Gate 2: UX Flow Freeze

**Owner**: devteam-ux

**必備 evidence**:
- [ ] 核心任務 flow 完整（入口 → 成功）
- [ ] Error path、empty state、loading state 都列
- [ ] a11y 檢查項已標
- [ ] 高風險互動已有 prototype 或驗證假設

**Review personas**:
- `pm`: flow 是否支援 PRD scenarios
- `qa`: 可測性 + 測試 hook 是否存在

---

## Gate 3: System Spec Freeze

**Owner**: devteam-analyst

**必備 evidence**:
- [ ] use cases 完整（含 actor / trigger / steps / acceptance）
- [ ] business rules 表（每條有 ID + source + priority）
- [ ] 例外流與 edge case 已列
- [ ] 外部依賴與假設可追溯
- [ ] Acceptance criteria 可被 QA 直接使用
- [ ] **State Machine（核心聚合根生命週期，KB-07 §3 必畫）**：有意義狀態的物件須畫 mermaid `stateDiagram`，含終結態與每邊 event；無狀態物件可免

**Review personas**:
- `arch`: 系統行為是否需要新架構決策
- `qa`: acceptance 是否可測

---

## Gate 4: NFR + ADR Baseline

**Owner**: devteam-arch

**必備 evidence**:
- [ ] NFR matrix（latency / availability / security / a11y / auditability）已 baseline
- [ ] 至少 1 份 ADR 涵蓋主要技術選型
- [ ] C4 Level 1（Context）+ Level 2（Container）已畫
- [ ] Failure modes 初步盤點
- [ ] Observability 需求已前置（不是上線前才補）
- [ ] **（條件式）Threat Model**：觸發規則命中時（見下）→ `templates/threat-model.md` 已產，且每條 STRIDE 閉環（ADR mitigation + API error model + security negative test）；未命中可免；主張豁免須寫 DR（Architect 可簽，業主 informed）

**Review personas**:
- `pm`: NFR 是否回應 KPI 與商業目標
- `sre`: SLO / 可觀測 / rollback 路徑是否可行
- `dba`: 資料相關 NFR（retention / PII / audit）是否被涵蓋

### Gate 4 Threat Model 觸發規則（條件式必備）

> Source: Roundtable B (2026-05-28) D3 + 業主 Q2/Q3/Q4=A。
> 設計：threat model 不靠 architect 自由心證，由**資料分級客觀規則自動觸發**，綁 [[11_data_and_stack_catalog]] §1/§2 既有欄位。

```
threat_model_required =
    (ERD.pii_type ∈ {identifier, sensitive})
    OR (ERD.classification = restricted)
    OR (surface ∈ {auth, payment})
    OR (ERD.pii_type = quasi-identifier AND consent_required = explicit)
```

| 項目 | 規則 |
|:-----|:-----|
| **硬度** | Hard rule。命中卻無 threat-model 且無豁免 DR ⟹ Gate 4 阻擋（與「缺資料分級 → Gate 4 阻擋」同級） |
| **豁免** | 寫 DR：rationale + 殘餘風險 + 到期 review 日。簽核權 = Architect 可簽、業主 informed |
| **閉環** | 觸發時每條 STRIDE 須結到 ADR mitigation + API error model/status code/telemetry + 一條 security negative test（寫進 system-spec acceptance） |
| **合規背書** | GDPR Art.32 / Art.35 DPIA、個資法第 27 條 / 特種個資第 6 條 |
| **與 NFR 關係** | 互補非重複 — NFR matrix 答「達標常數」，threat model 答「誰攻 / 攻哪 / 怎麼防」 |
| **詞彙橋接** | 既有 prose ERD（特種個資 / PII / 脫敏）先經 [[11_data_and_stack_catalog]] §2.1 詞彙橋接正規化為 `pii_type` / `classification` 機械值再評估觸發 |

---

## Gate 5a: API Contract Freeze

**Owner**: devteam-design

**必備 evidence**:
- [ ] OpenAPI 3.x spec 完整（endpoint + schema + auth + error code）
- [ ] Idempotency / rate limit / timeout 政策明示
- [ ] Mock server 可生成
- [ ] FE / BE / QA 能依此 contract 平行工作
- [ ] Breaking change 政策已寫入 `x-governance`
- [ ] **Sequence（關鍵 endpoint flow，KB-07 §3 必畫）**：每個 endpoint 的呼叫鏈畫 mermaid `sequenceDiagram` + `autonumber`，含失敗路徑；步驟對應 OpenAPI endpoint

**Review personas**:
- `pm`: contract 是否支援所有 use cases
- `qa`: error / edge case 是否可測
- `sre`: rate limit / timeout / error code 是否與運維能力對齊

---

## Gate 5b: DB Schema Freeze

**Owner**: devteam-design（DBA persona）

**必備 evidence**:
- [ ] Logical model + Physical model 完整
- [ ] Migration script + Rollback script 都演練過
- [ ] Backfill 策略已定（若需要）
- [ ] Index / retention / PII map 已標
- [ ] 資料一致性與整合測試假設可驗證

**Review personas**:
- `arch`: schema 是否符合 bounded context
- `qa`: 測試資料策略可行
- `sre`: backup / capacity / migration 風險可承受

---

## Gate 6: Test Ready

**Owner**: devteam-qa

**必備 evidence**:
- [ ] Test plan：scope / levels / env / data / cases / automation / exit criteria
- [ ] 測試環境就緒，資料策略可行
- [ ] Non-functional test 覆蓋（perf / security / a11y）已規劃
- [ ] Defect triage 規則清楚

**Review personas**:
- `dev-lead`（合併到 arch persona 觀點）: 測試覆蓋與切片是否對齊
- `devops`: pipeline gate 是否能執行測試

---

## Gate 7: Release Ready

**Owner**: devteam-ops（devops + sre persona；harness 無獨立 dev-lead agent，實作設計視角由 sd/arch 兼）

**必備 evidence**:
- [ ] Build / defect / perf / security 證據齊
- [ ] Runbook + Alerts + Dashboards 已就緒
- [ ] Rollback plan 可執行（不只是寫「rollback」）
- [ ] Go / No-go 標準明文，依 evidence 決策非氣氛
- [ ] Canary / staged rollout 策略已定
- [ ] **Deployment topology 圖**（KB-07 §3 必畫）：部署拓樸 mermaid（節點 / DB / 對外 egress），與 C4 L2 + threat-model 信任邊界一致
- [ ] **Activity 圖**（KB-07 §3 必畫）：runbook 關鍵流程（P0 incident response：detect→killswitch→稽核→通報→RCA）畫 mermaid flowchart

**Review personas**:
- `pm`: 是否符合 release plan 的 rollout
- `qa`: defect 已清或被接受
- `arch`: 重大架構風險已標 known + mitigation

---

## Review Intensity Dial

| 等級 | 行為 | Token 規模 | 適用 |
|:-----|:-----|:-----------|:-----|
| `light` | 1 persona self-critique | 低 | 低風險 gate、迭代版本 |
| `standard` | 2 personas 並行 + orchestrator 合併 | 中 | 預設 |
| `strict` | 3 personas 並行 + orchestrator + 衝突點顯化 | 高 | PRD/NFR/API/Schema/Release |
| `dry-run` | 列 critique 框架不真實 dispatch | 極低 | 業主預覽用 |

業主可在 state.json 改 `review_intensity_default`，或對個別 gate 用 `/devteam-freeze <gate> --intensity=<level>`。

---

## ADR Supersede Chain 判定規則

> Source: Roundtable A (2026-05-27) D2 + 業主 Q4=C。
> 此段補 Gate 4 (NFR + ADR Baseline) freeze 前的 supersede 判定 SOP；boundary criteria 在 [`13_doc_migration_playbook §8`](13_doc_migration_playbook.md) 有完整 case study。

### 判定三類

| 類別 | Status 標記 | 判定門檻 | 處置流程 |
|:-----|:------------|:---------|:---------|
| **已覆寫** | `Status: Superseded by <ADR-or-clause>` | 同時滿足 C1+C2+C3（[ref: KB-13 §8.1]） | Architect 直 merge（Q4=C），不走 Lane A |
| **仍 valid** | `Status: Reviewed, Still Valid Under M-NN` | 任一滿足 V1/V2/V3（[ref: KB-13 §8.2]） | 走 Lane A critique（arch+sa+pm 三方），業主裁決 |
| **部分覆寫** | `Status: Partially Superseded` | 能拆 sub-decision，部分衝突部分仍 valid（[ref: KB-13 §8.3]） | 拆寫補充 ADR；強制 Lane A critique |

### 「已覆寫」criteria（必三條全 yes）

被歸為 Superseded 必須符合：

- **C1: 直接衝突** — 新規格 P0 規則 / BR clause 與舊 ADR Decision 段落核心結論不可共存
- **C2: 同一 scope** — 新規格覆寫範圍與舊 ADR scope 完全或近完全重疊
- **C3: 無共存路徑** — 不存在同時 honor 舊 ADR + 新規格的實作方案

若三條只滿足 1-2 條 → 走「部分覆寫」或「仍 valid」判定。

### 「仍 valid」criteria（任一即可）

- **V1: 架構/技術選型基底未變** — ADR 講技術基底（DB / framework / cache），新規格只動 business rule
- **V2: 新規格未蓋過 ADR scope** — module 拆分沒涵蓋 ADR 的 cross-cutting 主題
- **V3: ADR Context 段部分過時但 Decision 仍適用** — Decision 段描述的決策原則對新模組仍適用，只是 Context 提到的舊模組名稱已過時

### Boundary case（部分覆寫）

當 ADR 含 N 個 sub-decision 但新規格只覆寫其中 M 個（M < N）：

```
是否能拆 sub-decision？
├─ 是 → 標 status: partially_superseded
│       frontmatter:
│         superseded_clauses:
│           - "Decision §2.1 by <new-ADR>"
│         still_valid_clauses:
│           - "Decision §2.2, §4"
│       Lane A critique 必走（不可 Architect 單獨 merge）
│
└─ 否（單一 Decision 段、模糊不一致）→ 強制 Lane A critique
   critique 結論：
     ├─ 多數實質衝突 → 升 Superseded
     └─ 多數可詮釋仍 valid → Reviewed_Still_Valid + 加 "Interpretation Note"
```

### Lane 路由規則

| Status | Review Lane | Reviewer | 業主介入點 |
|:-------|:-------------|:---------|:-----------|
| Superseded（C1+C2+C3） | — (直 merge) | Architect | ADR-100 簽核 |
| Partially Superseded | Lane A strict | arch + sa + pm | critique report 簽核 |
| Reviewed Still Valid | Lane A standard | arch + sa | critique report 簽核 |
| 模糊不可判 | 升 Lane B Forum-Lite | proposer + critics | facilitator 三訊號 AND 後升業主 |

### Gate 4 ADR Baseline evidence 強制項

當 cascade 大量 ADR 時（如本次 73 個 ADR），Gate 4 evidence 額外加：

- [ ] ADR-100 supersede index 已建（列所有 ADR + status + reviewer）
- [ ] 所有 `superseded` 標記的 ADR 已 frontmatter 更新 `superseded_by` + `superseded_on` + `superseded_reason`
- [ ] 所有 `partially_superseded` ADR 已新增補充 ADR 或在 ADR-100 內註明拆分
- [ ] CI 跑 traceability matrix tool，§6 Health Issues `broken_supersede` count = 0

[ref: KB-13 §2 ADR Supersede 判定樹]、[ref: KB-13 §8 邊界 criteria]

---

## Evidence 儲存

每個 gate 的 evidence 寫入 `.claude/context/devteam/evidence/<gate>-<feature>-<date>.md`，至少含：

```markdown
# Evidence: <gate> — <feature>

> **日期**: <ISO>
> **Owner driver**: <driver>
> **Intensity**: <level>

## Checklist 滿足項
- [x] ...
- [x] ...

## Review report
連到 .claude/context/devteam/reviews/<gate>-<feature>-<date>.md

## 業主裁決
- 接受項: ...
- 拒絕項 + 理由: ...
- 後續 follow-up: ...
```
