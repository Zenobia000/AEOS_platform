# dev_docs — care-copilot（依 VibeCoding 模板實例化）

> **來源**：本目錄是把 `docs/`（AEOS care-copilot 最薄切片乾淨關鍵路徑）依 `VibeCoding_Workflow_Templates/` 的模板格式**個別產出**的成果。
> **產出原則**：只實例化「`docs/` 已有真實源內容」的 9 個模板；code-level（08–12/17）與變更治理（19–20）因尚無 code / 尚無上線後變更，刻意不產（避免空殼文件，違反 foundation/01「驗證前不文件化想像」）。
> **單一事實來源仍是 `docs/`**：本目錄是 VibeCoding 格式的鏡像視圖，若與 `docs/` 衝突，以 `docs/` frozen 文件為準。

---

## 已產出對照表

| VibeCoding 模板 | dev_docs 產出 | 主要來源（docs/） |
| :--- | :--- | :--- |
| 02 PRD | [`02_project_brief_and_prd.md`](./02_project_brief_and_prd.md) | `prd/ai-cs-mvg.md` + `foundation/00~03` + `governance/stakeholders.md` |
| 03 BDD | [`03_behavior_driven_development_guide.md`](./03_behavior_driven_development_guide.md) | `qa/test-plan-care-copilot.md` + `analysis/system-spec-care-copilot.md` + `ux/user-flow-care-copilot.md` |
| 04 ADR | [`adr/ADR-0001`](./adr/ADR-0001-adopt-nanobot-frozen-runtime.md) … `ADR-0004` | `architecture/adr/*` + `feasibility-AEOS-x-care-copilot.md` |
| 05 架構與設計 | [`05_architecture_and_design_document.md`](./05_architecture_and_design_document.md) | `architecture/c4` + `nfr` + `knowledge-pipeline` + `data/erd` |
| 06 API 設計 | [`06_api_design_specification.md`](./06_api_design_specification.md) | `api/openapi-care-copilot.yaml` |
| 07 模組規格與測試 | [`07_module_specification_and_tests.md`](./07_module_specification_and_tests.md) | `analysis/system-spec` + `data/erd` + `data/migrations/` |
| 13 安全與準備 | [`13_security_and_readiness_checklists.md`](./13_security_and_readiness_checklists.md) | `security/threat-model.md` + `ops/release-readiness` + `governance/*` |
| 14 部署與運維 | [`14_deployment_and_operations_guide.md`](./14_deployment_and_operations_guide.md) | `ops/runbook-care-copilot.md` + `ops/release-readiness` |
| 16 WBS | [`16_wbs_development_plan.md`](./16_wbs_development_plan.md) | `foundation/02-mvg-build-sheet.md` + `foundation/03-validation-and-kill.md` |

## 未產出（刻意）

| 模板 | 不產原因 |
| :--- | :--- |
| 08 結構 / 09 依賴 / 10 類別 | 切片 = 單體 7 檔（`webhook/ingest/draft/review/audit/killswitch/eval`），尚未開工；待 coding agent 落地後再生 |
| 11 Code Review / 12 前端架構 / 17 前端 IA | 無 code、無前端（W2 才有「最笨一張 web 列表頁」），無源可鏡像 |
| 15 文檔維護 / 19 CR / 20 CIA | pilot 未上線、無上線後變更；目前變更走 DR（見各 frozen 文件 header） |

## ID 命名（沿用 VibeCoding INDEX §ID 命名規範）

- **File ID**（獨立成檔）：`ADR-NNNN-<slug>.md`（本目錄 `adr/`）。
- **Inline ID**（body 內）：`E-`（Epic）/ `US-`（User Story）/ `SC-`（BDD Scenario）/ `API-` / `MOD-` / `TC-` / `WBS-` / `RISK-` / `Q-` / `D-`。
- care-copilot 既有的 `FR-` / `UC-` / `BR-` / `T-*` / `TC-SEC-*` 為 `docs/` 原生 ID，本目錄保留並交叉引用，不重新編號。
