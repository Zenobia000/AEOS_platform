# VibeCoding 工作流程模板索引

> **版本:** v3.2 | **更新:** 2026-05-26
> **負責人:** PM + TL | **適用範圍:** 全域（總覽 / 索引）

---

## 模板清單

### 階段 0: 總覽與工作流

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 01 | [workflow_manual.md](./01_workflow_manual.md) | 開發流程使用說明書，完整流程與 MVP 模式選擇 |

### 階段 1: 規劃 (02-03)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 02 | [project_brief_and_prd.md](./02_project_brief_and_prd.md) | 專案簡報與 PRD |
| 03 | [behavior_driven_development_guide.md](./03_behavior_driven_development_guide.md) | BDD 指南與 Gherkin 範本 |

### 階段 2: 架構與設計 (04-06)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 04 | [architecture_decision_record_template.md](./04_architecture_decision_record_template.md) | ADR 模板 |
| 05 | [architecture_and_design_document.md](./05_architecture_and_design_document.md) | 架構與設計文檔 (C4/DDD) |
| 06 | [api_design_specification.md](./06_api_design_specification.md) | API 設計規範 |

### 階段 3: 詳細設計 (07-10)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 07 | [module_specification_and_tests.md](./07_module_specification_and_tests.md) | 模組規格與測試案例 (DbC) |
| 08 | [project_structure_guide.md](./08_project_structure_guide.md) | 專案結構指南 |
| 09 | [file_dependencies_template.md](./09_file_dependencies_template.md) | 模組依賴關係分析 |
| 10 | [class_relationships_template.md](./10_class_relationships_template.md) | 類別關係文檔 (UML) |

### 階段 4: 開發與品質 (11-12, 17)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 11 | [code_review_and_refactoring_guide.md](./11_code_review_and_refactoring_guide.md) | 程式碼審查與重構指南 |
| 12 | [frontend_architecture_specification.md](./12_frontend_architecture_specification.md) | 前端架構規範 |
| 17 | [frontend_information_architecture_template.md](./17_frontend_information_architecture_template.md) | 前端資訊架構規範 |

### 階段 5: 安全與部署 (13-14)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 13 | [security_and_readiness_checklists.md](./13_security_and_readiness_checklists.md) | 安全與生產準備檢查清單 |
| 14 | [deployment_and_operations_guide.md](./14_deployment_and_operations_guide.md) | 部署與運維指南 |

### 階段 6: 維護與管理 (15-16)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 15 | [documentation_and_maintenance_guide.md](./15_documentation_and_maintenance_guide.md) | 文檔與維護指南 |
| 16 | [wbs_development_plan_template.md](./16_wbs_development_plan_template.md) | WBS 開發計劃模板 |

### 階段 7: 變更治理 (19-20)

| # | 檔名 | 用途 |
| :---: | :--- | :--- |
| 19 | [change_request_template.md](./19_change_request_template.md) | 變更請求 CR-NNNN（上線後變更的單據與裁決紀錄） |
| 20 | [change_impact_analysis.md](./20_change_impact_analysis.md) | 變更影響分析 CIA-NNNN（觸碰 flow/contract/data/architecture 的硬 gate） |

---

## 使用流程

```mermaid
graph LR
  A[01 選擇模式] --> B[02 PRD] --> C[03 BDD]
  C --> D[04 ADR + 05 架構]
  D --> E[06 API + 07 模組]
  E --> F[08 結構 + 09 依賴 + 10 類別]
  F --> G[11 審查 + 12/17 前端]
  G --> H[13 安全]
  H --> I[14 部署]
  I --> J[15 文檔 + 16 WBS]
```

> **變更治理**：上線後任何 spec 變更 → `19 CR`；觸碰 flow / contract / data / architecture → `20 CIA` 硬 gate（§8 Human Decisions 未填不可動 code）。

---

## ID 命名規範

所有跨檔追蹤都使用統一 ID prefix。格式 `<PREFIX>-<NNNN>`，NNNN 為 4 位流水號（從 0001 起編），同一 prefix 在專案內唯一。

### Prefix 一覽

**閱讀此表前先理解兩種 ID 的差別**：

| 類型 | 說明 | 範例 prefix |
| :--- | :--- | :--- |
| **Inline ID**（body 內） | 多個 ID 共存於同一份檔案的內容中，**不獨立成檔** | `E-`、`US-`、`SC-`、`Q-`、`D-`、`API-`、`MOD-`、`TC-`、`RISK-`、`WBS-`、`QG-` |
| **File ID**（獨立成檔） | 每個 ID 對應一個 `.md` 檔，檔名 `<PREFIX>-NNNN-<slug>.md` | `ADR-`、`CR-`、`CIA-` |

例：02 PRD 是**一份檔案**，body 內可同時出現 `E-0001`、`US-0001`、`US-0002`、`Q-0001`、`D-0001`，沒有 `E-0001.md` 這種獨立檔。

| Prefix | 類型 | 名稱 | 出現於 | 生命週期 | 上游 | 下游 |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `E-` | Inline | Epic | 02 PRD body | 永久 | — | `US-` |
| `US-` | Inline | User Story | 02 PRD body | 永久 | `E-` | `SC-`, `MOD-`, `TC-`, `WBS-` |
| `SC-` | Inline | BDD Scenario | 03 BDD `.feature` body | 永久 | `US-` | `TC-` |
| `Q-` | Inline | Open Question | 02 PRD body | 暫時（裁決後關閉） | `US-` | `D-` 或 `ADR-` |
| `D-` | Inline | In-line Decision | 02 PRD body | 暫時（升級或定案） | `Q-` | `ADR-`（若升級） |
| `ADR-` | **File** | Architecture Decision Record | `docs/adr/ADR-NNNN-<slug>.md` | 永久（可 superseded） | `D-` 或 `CR-` | `ARCH-`、影響的 `MOD-`/`API-` |
| `API-` | Inline | API Endpoint | 06 API spec body | 永久 | `US-` | `TC-`、`MOD-` |
| `MOD-` | Inline | Module Spec | 07 Module spec body | 永久 | `US-` | `TC-` |
| `TC-` | Inline | Test Case | 07 Module / 03 BDD body | 永久 | `SC-` 或 `MOD-` | — |
| `CR-` | **File** | Change Request | `docs/cr/CR-NNNN-<slug>.md` | 暫時（裁決後關閉） | 任何上線後變更請求 | `CIA-`、新 `ADR-` |
| `CIA-` | **File** | Change Impact Analysis | `docs/cia/CIA-NNNN-<slug>.md` | 暫時（決策後歸檔） | `CR-` | 新 `ADR-`、修改的 `MOD-`/`API-` |
| `QG-` | Inline | Quality Gate 階段 | 01 §6 固定枚舉（G0~G4） | 固定枚舉 | — | — |
| `RISK-` | Inline | Risk Item | 16 WBS §5 body | 暫時（緩解後關閉） | — | 可能升級為 `CR-` |
| `WBS-` | Inline | WBS Task | 16 WBS §3 body | 暫時（完成後封存） | `US-` | — |

### 升級路徑

```text
Q-001 ──── 開發中暫存問題
  ↓ 裁決
D-001 ──── 簡單可在 PRD 內定案
  ↓ 影響架構/契約
ADR-0001 ── 升級為架構決策
  ↓ 上線後變更
CR-0001 ── 變更請求單據
  ↓ 觸碰 flow/contract/data/arch
CIA-0001 ── 影響分析硬 gate
  ↓
新 ADR / 修改 MOD/API
```

### 檔名規範（落成獨立檔案的 ID）

`ADR-`、`CR-`、`CIA-` 三種 prefix 會落成獨立 `.md` 檔案；其餘 prefix（`E-/US-/SC-/Q-/D-/API-/MOD-/TC-/RISK-/WBS-/QG-`）只出現在其他檔的 body 或 frontmatter，不獨立成檔。

**檔名格式**：`<PREFIX>-<NNNN>-<short-kebab-slug>.md`

| 規則 | 說明 |
| :--- | :--- |
| Slug 長度 | ≤ 50 字元（含 prefix 與流水號） |
| Slug 字元 | 小寫 ASCII + 連字符；**禁用**中文、空格、底線、駝峰 |
| Slug 內容 | 描述「**做什麼**」而非「為什麼」；動詞 + 名詞 |
| 內部引用 | 仍寫 bare ID（`ADR-0007`），**不寫**全檔名；改檔名不影響引用 |

**範例**：

| 場景 | 檔名 | body / `traces:` 中寫 |
| :--- | :--- | :--- |
| 選 PostgreSQL 為訂單庫 | `ADR-0007-use-postgres-for-orders.md` | `ADR-0007` |
| 拆分 monolith | `ADR-0012-split-monolith-into-services.md` | `ADR-0012` |
| 棄用 v1 API | `CR-0023-deprecate-v1-api.md` | `CR-0023` |
| Stripe 升級 v2 → v3 | `CIA-0005-upgrade-stripe-v2-to-v3.md` | `CIA-0005` |
| 訂單 schema 加 status 欄 | `CIA-0009-add-status-column-to-orders.md` | `CIA-0009` |

**反例**：

```text
❌ ADR-0007.md                                    無 slug，看不出內容
❌ ADR-0007-Use_Postgres_For_Orders.md            底線 + 大寫
❌ ADR-0007-使用-postgres-當訂單資料庫.md         中文，跨平台不安全
❌ ADR-0007-postgres-because-it-is-mature.md      slug 描述「為什麼」（屬 body）
❌ ADR-0007-use-postgresql-as-the-primary-rdbms-for-the-order-management-service.md  過長
```

**檔案搬遷 / 重命名**：

- 改 slug 時 **保留 ID**（`ADR-0007` 不變），只動 slug
- 用 `git mv` 保留歷史
- 若 ID 本身需作廢 → 新建一個 `superseded by` 指向新 ADR，舊檔狀態改 `superseded`
- 內部引用全用 bare ID 的好處：改檔名零連動風險

### Frontmatter 中的 `traces:` 欄位

每個有 ID 的檔案在 frontmatter 宣告上游引用：

```yaml
---
id: TC-0023
traces:
  user_story: US-0007
  scenario: SC-0012
  module: MOD-0004
  adr: [ADR-0002, ADR-0005]
---
```

### Traceability Matrix

跨檔 ID 追蹤總表預設**不獨立成檔**，由各檔的 `traces:` 欄位 + 工具自動匯總產生。若需手動視圖，可在 16 WBS 內附「ID 追蹤」段落。

---

## 依角色查找

| 角色 | 常用模板 |
| :--- | :--- |
| PM | 01, 02, 16, 19 |
| PO | 02, 03, 17 |
| TL | 01, 04, 05, 11, 19, 20 |
| ARCH | 05, 09, 10, 20 |
| 後端 DEV | 07, 08, 11 |
| 前端 DEV | 12, 17 |
| QA | 03, 07, 11 |
| SEC | 06, 13 |
| SRE/OPS | 13, 14 |

---

## 版本記錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v3.2 | 2026-05-26 | P0+P1 補強：(1) 統一 ID 命名規範 14 種 prefix + 升級路徑 (2) Quality Gate 量化為 QG-G0~G4 + 13 §F 量化判準 (3) 17 檔 frontmatter schema 統一（負責人/審核/追蹤） (4) 新增 19 CR + 20 CIA 變更治理模板 (5) 補檔案邊界互引（06↔13、11↔14、13↔14、02↔16） (6) 14 §6 Rollback Plan 從 4 行擴寫為 8 子段（含反向 migration、不可逆變更處置、對外通訊） |
| v3.1 | 2026-05-26 | 模板 05 升 v2.0：依實戰回灌補齊 C4 嚴格規則、命名防呆、Sequence/Deployment 必填、DDD 戰略+戰術雙層、跨文件一致性 checklist |
| v3.0 | 2026-03-16 | 全面精簡優化，移除冗餘的 01_cookbook，統一繁中 |
| v2.1 | 2025-10-03 | 新增 17_frontend_information_architecture |
| v2.0 | 2025-10-03 | 重新組織序號，新增 INDEX |
| v1.0 | 2025-10-01 | 初始版本 |
