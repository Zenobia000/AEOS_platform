# MoM: DevTeam Harness 缺口補齊規劃（F4 / F5 / F6）

> **📋 Status**: ✅ Converged（含 5 個業主政策題待拍）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: DevTeam Facilitator
> **🔖 Version**: v1
> **🔗 Related**: [`KB 01 role responsibilities`](../../../../devteam_knowledge_base/01_role_responsibilities.md) · [`KB 04 freeze gates`](../../../../devteam_knowledge_base/04_freeze_gates.md) · [`KB 11 data and stack catalog`](../../../../devteam_knowledge_base/11_data_and_stack_catalog.md)

---

**日期**：2026-05-28（2 rounds）
**主持**：DevTeam Facilitator
**與會**：PM、PO、BA、SA、UX、Architect、SD、QA（8 隻龍蝦）
**狀態**：✅ Converged — 三個 open decision 全收斂；5 個 value 政策題留給業主拍

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**：架構審查揪出 3 個 harness 缺口，full team 圓桌兩輪收斂出方案 —— (F4) **不另做 backlog**，改在 PRD 放排序過的 scope slice；(F5) **JTBD + 價值假設** 升為 PRD 必填結構化段；(F6) **新增條件式 STRIDE threat model**，由「資料敏感度」自動觸發掛 Gate 4，不靠人判斷。三案技術上已共識，剩 5 個政策開關需你拍（多半「照建議」即可）。

---

## ✅ Decisions Made

| # | 決議 | Confidence | 可逆性 | 影響範圍 |
|:--|:-----|:-----------|:-------|:---------|
| D1 | **F4 — 不開 `backlog.md`**。PRD 內新增「Prioritized Scope Slice」段（MoSCoW / P0-P1-P2 + 排除項），PM driver single owner。Acceptance criteria 維持單一真相源在 system-spec（use case 加 priority 欄）。產品的「Ordered Backlog」交付物降級改寫為 scope slice。 | 高（八方共識） | 可逆（DR） | `prd.md` / `system-spec.md` / 產品 taxonomy |
| D2 | **F5 — JTBD + Value Hypothesis 升為 `prd.md` 必填段**。JTBD 子段須結構化（每個 job ≥ 1 條「完成什麼算成功」、可被 user-flow anchor 引用），UX driver 主筆內容、PM driver own PRD doc。Value Hypothesis 須含 counter-metric + 成功閾值（P0 必填），樣本 N 可標 TBD 至 gate 前補。 | 高（八方共識） | 可逆（DR） | `prd.md` / `user-flow.md` 下游 |
| D3 | **F6 — 新增 `templates/threat-model.md`（STRIDE）**，與 architect 的 failure-mode 盤點共用骨架（加 threat actor 欄）。Gate 4 **條件式必備**：由資料分級客觀規則自動觸發（見下）。觸發時每條 STRIDE 須回灌：(a) 一個 ADR mitigation decision（可追溯）、(b) API error model + status code + telemetry、(c) 一條 security negative test 寫進 system-spec acceptance。Abuse case 連回 use case alternative flow，雙向編號 `<UC-ID>.alt-N`（SA 維護）。Security 達標常數仍留 NFR matrix（互補非重複）。 | 高（4(A)+4(C) 經 reframe 合體，八方 Accept） | 半可逆（改 Gate 4 + KB） | `templates/threat-model.md`（新）/ `KB 04` Gate 4 / `KB 11 §1` / `system-spec.md` |

**F6 自動觸發規則**（BA 釘死，綁 `KB 11 §1` 既有欄位，可機械判定）：
```
threat_model_required =
    (ERD.pii_type ∈ {identifier, sensitive})
    OR (ERD.classification = restricted)
    OR (surface ∈ {auth, payment})
```
`quasi-identifier` 單獨不觸發（避免 dob 類過度觸發）。Hard rule：無 threat model 且無豁免 DR ⟹ Gate 4 阻擋。合規背書：GDPR Art.32 / Art.35 DPIA、個資法第 27 條 / 特種個資第 6 條。

---

## 🎯 Action Items

| # | Action | Owner | Priority | Status |
|:--|:-------|:------|:---------|:-------|
| A1 | `prd.md` 範本加三段：Prioritized Scope Slice（MoSCoW）、JTBD（結構化 + success criterion）、Value Hypothesis（counter-metric + 閾值，樣本 N 可 TBD） | `devteam-pm` | P0 | ⚪ Open |
| A2 | `system-spec.md` 範本：use case 加 `priority` 欄（吸收排序）；abuse case ↔ UC alternative flow 雙向編號 `<UC-ID>.alt-N`；security negative test 回灌 acceptance | `devteam-analyst` | P1 | ⚪ Open |
| A3 | 新增 `templates/threat-model.md`（STRIDE，共用 failure-mode 骨架 + threat actor 欄 + ADR trace 欄） | `devteam-arch` | P0 | ⚪ Open |
| A4 | `KB 04` Gate 4 evidence 加「條件式 threat model」+ 觸發布林式；`KB 11 §1` 綁觸發規則 + 合規來源 | `devteam-arch` | P0 | ⚪ Open |
| A5 | `KB 03` template index 加 `threat-model.md`；`KB 01` crosswalk + 產品 taxonomy：「Ordered Backlog」→ scope slice、JTBD/value-hypothesis 標 PRD 必填 | `devteam-router` | P1 | ⚪ Open |
| A6 | UX driver SKILL：user-flow 以 anchor 引用 PRD 的 JTBD success criterion（下游連結） | `devteam-ux` | P2 | ⚪ Open |

> Action items 待業主回 Open Questions 後啟動（Q1/Q2 影響 A1/A4/A5 的最終措辭）。

---

## ❓ Open Questions（需要業主回應）

| # | 問題 | 為什麼問業主 | 提案選項 | 建議 |
|:--|:-----|:------------|:---------|:-----|
| Q1 | 是否正式把產品的「Ordered Backlog」交付物**降級改寫**為 PRD 的 Prioritized Scope Slice（會動到 taxonomy + Define stage exit criteria 改「scope 已排序」） | 動到對外交付物清單 = 產品定位 | A: 改寫（harness 明確 feature-spec 導向）<br>B: 保留 backlog 名目但內容用 scope slice | **A** |
| Q2 | threat-model 自動觸發定為 **hard rule**（無豁免 DR 即 Gate 4 阻擋）？ | 合規硬度 = 法務/風險政策 | A: hard rule + DR 豁免<br>B: soft（arch 自由心證，回到原狀） | **A**（GDPR/個資法背書，audit 站得住） |
| Q3 | threat-model 豁免（寫 DR）的 authority 是誰？ | 組織授權政策 | A: arch 可簽 DR、業主 informed<br>B: 只有業主可豁免 | **A** |
| Q4 | `quasi-identifier` 欄位 + `consent_required = explicit` 同表時，是否**升級**觸發 threat model？ | 合規保守度 value 判斷 | A: 升級觸發<br>B: 不觸發（只看 identifier/sensitive） | **A**（保守） |
| Q5 | Value Hypothesis 強制附 **counter-metric** 設為 `prd.md` P0 必填（樣本 N 可 TBD）？ | 防「假成功當真成功」的流程硬度 | A: 強制<br>B: 建議非強制 | **A**（PM 底線） |

> **業主**：每題回 A/B 即可，或「都照建議」一句話帶過。Q1/Q2 是真要拍的（動定位與合規硬度）；Q3/Q4/Q5 偏確認。

---

## ⚠️ Risks Identified

| 風險 | 描述 | 影響 | Mitigation |
|:-----|:-----|:-----|:-----------|
| R1 | threat-model 自動觸發若過寬，每個小 feature 都背 STRIDE | 拖慢上市（C 派原始顧慮） | BA 布林式排除 quasi-identifier 單獨觸發；只 PII/restricted/auth/payment |
| R2 | scope slice 降級後 PM 不嚴格排序 | freeze 時 scope 爭議 | Define exit criteria 改「scope 已排序」+ PM single owner 收口 |
| R3 | JTBD/value-hypothesis 變必填，0-1 模糊期卡 PRD freeze | 流程僵化 | 樣本 N 可 TBD、value-hyp 允許 `<!-- ASSUMPTION -->` 標記不擋 freeze |
| R4 | threat-model.md 與 system-spec abuse case 各寫一份 → 漂走 | dangling、雙真相源 | threat-model.md 僅當 STRIDE 工作底稿；acceptance 單一源在 system-spec；雙向編號 SA 維護 |

---

## 🔗 Cross References

**本次 MoM 引用**：
- 架構審查報告（本 session 對話，未落檔）— 來源 finding F4 / F5 / F6
- 產品 taxonomy: [`product_to_launch/lib/taxonomy.ts`](../../../../product_to_launch/lib/taxonomy.ts)
- 角色 crosswalk: [`KB 01 §產品角色 ↔ Persona ↔ Driver Crosswalk`](../../../../devteam_knowledge_base/01_role_responsibilities.md)

**Catalog references used**（Phase 1.5 注入給龍蝦的決策依據）：
- [[06_quality_attributes_catalog]] §1 9 維度 → 影響 D2（value-hypothesis vs KPI 的錨點關係）
- [[06_quality_attributes_catalog]] §5 NIST SSDF → 影響 D3（安全設計前置）
- [[11_data_and_stack_catalog]] §1-§3 資料分級 / PII / GDPR → 影響 D3 觸發規則與合規背書

**Catalog gaps**：無（龍蝦未標 [CATALOG_GAP]）

**本次 MoM 將被引用**：A1-A6 落地後的 `prd.md` / `system-spec.md` / `threat-model.md` / `KB 04` 修訂

---

## 📌 Next Steps

1. **業主回 Open Questions（Q1-Q5）** → 鎖定 A1/A4/A5 最終措辭
2. **回完即可啟動** A1（prd.md）+ A3（threat-model.md）+ A4（Gate 4）為 P0 一批
3. D3 涉及 Gate 4 結構變更 → A4 完成後建議走一次 `/devteam-review KB04` 確認沒破既有 gate 流程

---

## 🔍 Drill-down（可選閱讀）

- **完整對話 transcript**：[`transcript.md`](./transcript.md)
- **結構化 metadata**：[`notes.yaml`](./notes.yaml)

業主預設不需看上述。想看某隻龍蝦完整論證，一句「給我看 X 的發言」即可。

---

## 📊 Meeting Metadata

```yaml
meeting_id: 2026-05-28-harness-gap-planning
template_version: mom-v1
status: converged
attendees_count: 8
rounds: 2
user_interjections: 0
decisions_count: 3
action_items_count: 6
open_questions_count: 5
risks_count: 4
catalog_refs:
  - kb: 06_quality_attributes_catalog
    section: "§1"
    impact: "D2 value-hypothesis 錨點"
  - kb: 06_quality_attributes_catalog
    section: "§5"
    impact: "D3 安全設計前置"
  - kb: 11_data_and_stack_catalog
    section: "§1-§3"
    impact: "D3 觸發規則 + 合規背書"
catalog_gaps: []
```

---

**End of MoM**

> 給業主：看 §Executive Summary + §Decisions + §Open Questions 三段即可（< 1 分鐘）。回 Q1-Q5 就能啟動落地。
