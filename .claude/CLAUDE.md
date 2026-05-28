# DevTeam Harness — Project Instructions

## 概述

業主提出痛點後，AI agent harness 扮演整個軟體開發團隊，依真實流程（6 phases P0–P5 + handoff × 7 freeze gates × 12 critique persona × 並行主線）產出**所有規範文件**（PRD、User Flow、System Spec、ADR、C4、OpenAPI、ERD、Test Plan、Runbook、Release Readiness），最後把規範包交給外部 coding agent 實作。所有 devteam 相關 skill/command 前綴為 `devteam-`。

> 角色三套枚舉（產品 10 角色 / 12 persona / 7 driver）的單一對照表見 `devteam_knowledge_base/01_role_responsibilities.md` §產品角色 ↔ Persona ↔ Driver Crosswalk。

## 指令一覽

| 指令 | 用途 | 對應 Skill |
| :--- | :--- | :--------- |
| `/devteam` | 主入口，依 Phase DAG 路由到下一個 driver | devteam-router |
| `/devteam-pm` | P0 Discovery / PRD 產出 | devteam-pm |
| `/devteam-analyst` | P1 Analysis / System Spec + Rules | devteam-analyst |
| `/devteam-ux` | P1 Analysis / User Flow + State Coverage | devteam-ux |
| `/devteam-arch` | P2 Architecture / ADR + C4 + NFR | devteam-arch |
| `/devteam-design` | P3 Design / OpenAPI + ERD + Migration | devteam-design |
| `/devteam-qa` | P4 Delivery / Test Plan + Exit Criteria | devteam-qa |
| `/devteam-ops` | P5 Release / Runbook + SLO + Readiness | devteam-ops |
| `/devteam-status` | 查看當前 session 狀態（phase / gate / 文件成熟度） | devteam-status |
| `/devteam-freeze <Gate>` | 手動觸發 freeze gate multi-role review（Lane A） | (router 內建) |
| `/devteam-review <doc>` | 手動觸發任意文件的 critique（Lane A，不需 gate ready） | (router + agents) |
| `/devteam-forum <doc>` | **Lane B 多輪辯論**（proposer ↔ critics ↔ facilitator） | (router + agents) |
| `/devteam-roundtable <topic>` | **Lane C 圓桌探索性對話**（MoM-first：業主只看 MoM 不看 transcript、background mode、drill-down 可叫） | devteam-roundtable |
| `/devteam-handoff <feature>` | 產 specs/handoff.md 給 coding agent | (router 內建) |

## Phase DAG

```
P0_DISCOVERY ──▶ Gate1_PRD ──▶ P1_ANALYSIS (analyst + ux 並行)
              ──▶ Gate2_UXFlow + Gate3_SystemSpec ──▶ P2_ARCHITECTURE
              ──▶ Gate4_NFR_ADR ──▶ P3_DESIGN ──▶ Gate5a_API + Gate5b_DBSchema
              ──▶ P4_DELIVERY ──▶ Gate6_TestReady
              ──▶ P5_RELEASE ──▶ Gate7_Release ──▶ Handoff
```

每個 freeze gate 前自動 dispatch multi-role critique（intensity dial：light / standard / strict / dry-run）。完整規則見 `devteam_knowledge_base/02_lifecycle_phases.md` 與 `04_freeze_gates.md`。

## Lane A vs Lane B vs Lane C Review 機制

| Lane | 觸發 | 用途 |
|:-----|:-----|:-----|
| **A — Critique Pipeline** | Freeze gate ready / `/devteam-review` | 單向 critique → orchestrator merge → 業主裁決。90% review 走這條 |
| **B — Forum-Lite** | Lane A 出現 `conflicts_count ≥ 2` 自動提示業主 / `/devteam-forum` | 跨領域 trade-off 與衝突收斂。proposer ↔ critics 多輪辯論，facilitator 三訊號 AND 判定收斂或強制升級。max 3 rounds，~45k token |
| **C — Roundtable**（MoM-first PoC） | 業主自然語言「對 X 開會」「找 Y 跟 Z 討論」/ `/devteam-roundtable` | 探索性對話。**預設 background mode** — 龍蝦自己跑完整場會議，業主**預設不看 transcript**，只讀大廠 PM 風格 MoM（Executive Summary + Decisions + Action Items + Open Questions）。業主只在 Open Questions 動，投入時間 < 1 分鐘 / 場。Drill-down 隨叫隨到。Foreground mode 為 opt-in 給好奇 / 學習場景 |

Lane B 不取代 Lane A，Lane C 不取代 A/B。Lane C 結束後業主回 Open Questions，主 Claude 走對應 driver skill 寫 ADR/DR + 更新 PRD/spec。詳見：
- Lane A/B：`devteam_knowledge_base/05_meeting_protocols.md` Forum-Lite 段落
- Lane C：`.claude/skills/devteam-roundtable/SKILL.md`、`example-transcript.md`
- MoM 模板：`devteam_knowledge_base/templates/mom.md`

## 知識庫與範本

- `devteam_knowledge_base/01_role_responsibilities.md` — 12 persona cheat sheet + RACI
- `devteam_knowledge_base/02_lifecycle_phases.md` — Phase DAG、re-entry、cascade policy
- `devteam_knowledge_base/03_document_templates.md` — 範本索引與使用規則
- `devteam_knowledge_base/04_freeze_gates.md` — 7 個 gate 的 owner / evidence / personas
- `devteam_knowledge_base/05_meeting_protocols.md` — Multi-role review prompt + orchestrator 合併
- `devteam_knowledge_base/06_quality_attributes_catalog.md` — NFR / SLO / DORA / ISO 29148 / NIST SSDF
- `devteam_knowledge_base/07_diagram_picker.md` — UML/C4/ERD/wireframe 選圖樹 + state coverage checklist
- `devteam_knowledge_base/08_api_design_catalog.md` — REST/GraphQL/gRPC/event 選型 + error code + idempotency + versioning
- `devteam_knowledge_base/09_observability_catalog.md` — log/metric/trace 三柱 + SLI 命名 + alert routing + burn rate
- `devteam_knowledge_base/10_resilience_patterns.md` — retry/CB/bulkhead/timeout + 藍綠/canary + expand-contract + RTO/RPO
- `devteam_knowledge_base/11_data_and_stack_catalog.md` — 資料分級 / PII / GDPR + DB/messaging/auth/cache 選型
- `devteam_knowledge_base/12_document_format_standard.md` — 文件格式標準（Universal Header / mermaid / 一致性尺）
- `devteam_knowledge_base/13_doc_migration_playbook.md` — ADR supersede 判定樹 + doc 遷移 boundary case study
- `devteam_knowledge_base/voice-profiles.md` — 12 角色語言指紋（vocab / tone / taboo / frame / example）。persona agent 與 driver skill 開場必讀對應段
- `devteam_knowledge_base/templates/` — PRD / User Flow / System Spec / C4 / ADR / DR / OpenAPI / ERD / Test Plan / Runbook / Release Readiness / Handoff

## Session 狀態

DevTeam state 三層持久化於 `.claude/context/devteam/`：
- `state.json` — session metadata + phase + freeze gates + pending decisions + cascade policy
- `documents/index.json` + `<doc>.meta.json` — 文件成熟度與依賴
- `adr-ledger.json` — 跨 feature 的 ADR / DR 決策鏈
- `session-<id>.md` — 互動 narrative
- `reviews/`、`evidence/` — review 報告與 freeze 證據

## 規範產出位置

所有規範文件落在 `docs/`（PRD / UX / Analysis / Architecture / API / Data / QA / Ops / Release），coding agent 透過 `specs/<feature>/handoff.md` 接手。

---

## Scope 邊界（harness 不做什麼）

harness 是 **spec 產生器**，不是 build/run 引擎。以下刻意不在產出範圍內，由下游承接：

| 邊界 | 誰承接 | harness 觸點 |
| :--- | :--- | :--- |
| **Dev / Build code**（實作、unit test、coding standard、PR template） | 外部 coding agent | `specs/<feature>/handoff.md` 為交接契約；harness 無 dev persona/driver |
| **Operate runtime loop**（填寫 postmortem 實例、capacity、on-call、cost monitor） | 運維團隊 / SRE on-call | harness 只產 runbook / SLO / postmortem **範本** 與 release readiness 證據 |
| **Sprint backlog 執行**（ordered backlog、sprint planning） | PO / Scrum 流程 | harness 為 feature-spec 導向；PO persona 只在 gate critique 優先序，不 author backlog |

`product_to_launch`（Launch Atlas 圖鑑）列的 54 交付物是**教育型 catalog**（教你每個交付物 + 附可貼用 prompt），不是 harness 自動產出清單；兩者範疇不同，勿視為缺失。

---

## Skill 使用規則

遇到軟體規範產出 / 業主痛點分析，**先透過 Skill tool 載入對應 devteam-* skill 再行動**。

優先序：
1. **使用者明確指示** — 最高
2. **Skills** — 覆蓋預設系統行為
3. **預設系統提示** — 最低

## Agents

| Agent | 用途 |
| :--- | :--- |
| `devteam-orchestrator` | Multi-role critique 合併、衝突點顯化、失敗降級（output `conflicts_count` 給 router 判 Lane B 升級） |
| `devteam-proposer` | **Lane B Forum-Lite**：R1 提案（議題 + dimensions + trade-off）/ R3 回應 critique |
| `devteam-facilitator` | **Lane B Forum-Lite**：三訊號 AND 收斂判定 + 升級裁決，不 merge 不 critique |
| `devteam-pm-persona` | PM critique 視角（問題 / KPI / scope） |
| `devteam-po-persona` | PO critique 視角（backlog priority / ownership） |
| `devteam-ba-persona` | BA critique 視角（stakeholder / rules / 合規） |
| `devteam-sa-persona` | SA critique 視角（use case / acceptance / edge case） |
| `devteam-ux-persona` | UX critique 視角（task success / state / a11y） |
| `devteam-ui-persona` | UI critique 視角（component state / token / responsive） |
| `devteam-arch-persona` | Architect critique 視角（NFR / boundary / failure modes） |
| `devteam-sd-persona` | SD critique 視角（API 平行實作 / error model） |
| `devteam-dba-persona` | DBA critique 視角（migration / PII / index） |
| `devteam-qa-persona` | QA critique 視角（可測性 / exit criteria） |
| `devteam-devops-persona` | DevOps critique 視角（pipeline / rollback） |
| `devteam-sre-persona` | SRE critique 視角（SLO / alert / incident） |
