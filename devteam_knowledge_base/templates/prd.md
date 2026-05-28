# PRD — {Feature Name}

> **📋 Status**: draft | reviewed | frozen | superseded
> **🗓 Last updated**: YYYY-MM-DD
> **👤 Owner**: {PM name}
> **🔖 Version**: v{n}
> **🔗 Related**: ADR-NNN · DR-NNN · KB-N §X

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: {一句話講完此 feature 解什麼問題、給誰用、最大爭議是什麼。30 秒讓任何讀者抓到「為什麼這個 feature 值得 build」。}

| 維度 | 摘要 |
|:---|:---|
| **🎯 目標** | {一句話商業目標} |
| **👥 主要 persona** | {role + scale} |
| **📊 主要 KPI** | {K1 名稱 + 目標值} |
| **🚀 狀態** | {emoji} {status — e.g. ⚠️ ready_to_review, 🔒 frozen} |
| **🎯 下一步** | {next concrete action} |

---

## 🎯 Problem Statement

- **現況**: {現在發生什麼事；who suffers from what}
- **為什麼值得解**: {商業 / 用戶價值，最好量化}
- **不解的成本**: {量化或可推論的影響 — churn / cost / risk}

> [!NOTE]
> 三項都不可空。若無資訊用 `<TBD by stakeholder>` 佔位，列入下方 Open Questions。

---

## 🧩 Jobs To Be Done (JTBD)

> [!NOTE]
> JTBD = 使用者想完成的任務（非功能清單）。**UX driver 主筆內容、PM driver = PRD doc owner**（見 [[01_role_responsibilities]] §Crosswalk）。每個 job 必須有 ≥ 1 條 success criterion；`user-flow.md` 以 anchor 下游引用（`#jtbd-J1`）作為 task success 判準，不可只寫敘事散文。必填段。

| ID | When（情境） | I want to（任務） | So I can（動機 / 結果） | Success criterion（完成什麼算成功，可被 user-flow 引用） |
|:---|:---|:---|:---|:---|
| <a id="jtbd-J1"></a>J1 | {觸發情境} | {想完成的任務} | {underlying 動機} | {可觀測的完成判準} |
| <a id="jtbd-J2"></a>J2 | ... | ... | ... | ... |

---

## 📊 Goals & Success Metrics

| 類別 | 目標 | 量化指標 | 觀測週期 |
|:---|:---|:---|:---|
| **Business Goal** | {定性目標} | — | — |
| **User Goal** | {定性目標} | — | — |
| **KPI K1** | {what} | {target value} | {weekly / monthly / quarterly} |
| **KPI K2** | {what} | {target value} | {period} |
| **Counter-metric C1** | 避免 over-optimization | {副指標 + 上限} | — |

> [!IMPORTANT]
> KPI 必填且可量化。不可寫「使用度高」這類無法測量的描述。

---

## 🔬 Value Hypothesis

> [!IMPORTANT]
> 防「假成功當真成功」。每條假設必含 **counter-metric + 成功閾值**（P0 必填）；樣本 N / 觀測窗在 0-1 模糊期可標 `<TBD, gate 前補>`，不擋 PRD freeze。QA 以此導出可測 exit criteria — 寫不出成功閾值的假設等於沒假設。必填段。

| ID | 假設（We believe…） | 成功定義（… will result in，含閾值） | Counter-metric（避免副作用） | 樣本 / 觀測窗 | 對應 JTBD / KPI |
|:---|:---|:---|:---|:---|:---|
| VH-1 | {若做 X} | {指標 ≥ 閾值} | {副指標 + 上限} | {N / 期間 或 `<TBD>`} | J1 / K1 |
| VH-2 | ... | ... | ... | ... | ... |

---

## 👥 Users & Scenarios

- **Primary Persona**: {角色 + 關鍵脈絡 + 規模 (e.g. < 100 / 100-10k / > 1M)}
- **Secondary Persona**: {若有}
- **Key Scenario**（主任務流）:
  1. {step 1}
  2. {step 2}
  3. {step 3}
- **Edge Cases**:
  - {edge 1}
  - {edge 2}

---

## 🎯 Scope

### ✅ In Scope
- {item 1}
- {item 2}

### ❌ Out of Scope

> [!WARNING]
> Out of Scope **不可空** — 明確界定不做什麼，避免日後 scope creep。

- {explicitly excluded item 1}
- {explicitly excluded item 2}

### 🎚 Prioritized Scope Slice

> [!NOTE]
> harness 為 feature-spec 導向、**不產 sprint backlog**（取代產品的 Ordered Backlog；見 [[01_role_responsibilities]] §Crosswalk）。排序在此用 MoSCoW + P0/P1/P2 收口，**PM driver single owner**。此處只排序、連回 Value Hypothesis；item 的 acceptance criteria **單一真相源在 system-spec**（use case priority 欄），不在此重寫。

| Slice | MoSCoW | 對應 FR / Use Case | 排序理由（連 Value Hypothesis） |
|:---|:---|:---|:---|
| P0 | Must | FR-001 | VH-1 核心驗證 |
| P1 | Should | FR-002 | — |
| P2 | Could | — | — |
| — | Won't（this release） | {見 Out of Scope} | — |

---

## 🔗 User Flow Links

| Asset | Location |
|:---|:---|
| Journey | [`docs/ux/user-flow-{feature}.md`](../ux/user-flow-{feature}.md) |
| Wireframe | {link / TBD} |
| Prototype | {link / TBD} |

---

## 📋 Functional Requirements

| ID | Description | Acceptance Criteria | Priority |
|:---|:---|:---|:---:|
| FR-001 | {what user / system does} | {testable criterion} | P0 |
| FR-002 | ... | ... | P1 |

---

## 🛡 Non-Functional Requirements

| Dimension | Requirement | Target | Reference |
|:---|:---|:---|:---|
| **⚡ Performance** | {latency / throughput} | p95 < {ms} | [[06_quality_attributes_catalog]] §1 |
| **🔁 Reliability** | {availability target / SLO} | {99.9% / best-effort} | [[06_quality_attributes_catalog]] §2 |
| **🔒 Security** | {auth / data classification} | {PII / SOC2 / N/A} | [[11_data_and_stack_catalog]] §1 |
| **♿ Accessibility** | WCAG level | {AA / N/A} | — |
| **📜 Auditability** | {log retention / read access} | {30d / 90d / N/A} | — |
| **📈 Scalability** | {concurrent users / data volume} | {N users / N GB} | — |

---

## 🔌 Dependencies

| Type | Detail |
|:---|:---|
| **Upstream** | {上游系統 / 團隊} |
| **Downstream** | {下游消費者} |
| **External systems** | {3rd-party APIs / vendors} |
| **Data / API** | {input / output sources} |
| **Stack constraint** | {language / framework / cloud — from bootstrap} |

---

## ⚠️ Risks & Open Questions

> [!IMPORTANT]
> Risks 與 OQ 是業主主要決策區。每條都需 owner + by-when。

### Risks

| ID | Risk | Severity | Mitigation |
|:---|:---|:---:|:---|
| R-001 | {what could go wrong} | 🔴 high | {how to mitigate} |
| R-002 | ... | 🟡 medium | ... |

### Open Questions

| ID | Question | Why ask | Options | Recommendation | Owner | Due |
|:---|:---|:---|:---|:---|:---|:---|
| OQ-001 | {question} | {value judgment / scope / risk} | A: {opt} · B: {opt} | {推薦 + 理由} | 業主 | {date} |
| OQ-002 | ... | ... | ... | ... | ... | ... |

---

## 🚀 Release Plan

| 項目 | 說明 |
|:---|:---|
| **Rollout strategy** | canary · staged · big-bang ({依規模選 — 見 [[10_resilience_patterns]] §3.1}) |
| **Timeline** | {first release deadline} |
| **Observability** | {key metrics / dashboard link} |
| **Rollback trigger** | {what condition triggers rollback} |
| **Rollback owner** | {role / on-call} |

---

## 📝 Decision Log

> 此處 list ADR / DR 而非詳述。完整內容在 `docs/architecture/adr/` 與 `docs/architecture/dr/`。

| ID | Type | Topic | Status |
|:---|:---|:---|:---:|
| ADR-NNN | ADR | {one-line topic} | ✅ accepted |
| DR-NNN | DR | {one-line topic} | ✅ accepted |

---

## 🔗 Cross References

- **Stakeholder map**: [`docs/governance/stakeholders.md`](../../docs/governance/stakeholders.md)
- **User flow**: [`docs/ux/user-flow-{feature}.md`](../../docs/ux/user-flow-{feature}.md)
- **System spec** (downstream): [`docs/analysis/system-spec-{feature}.md`](../../docs/analysis/system-spec-{feature}.md)
- **C4 diagram** (downstream): [`docs/architecture/c4-{feature}.md`](../../docs/architecture/c4-{feature}.md)
- **KB catalog refs**: [[06_quality_attributes_catalog]] · [[10_resilience_patterns]] · [[11_data_and_stack_catalog]]

---

## ✍️ Sign-off

> [!IMPORTANT]
> Gate 1 PRD Freeze 需要業主明確簽核。Reviewer 在 multi-role critique 後才簽。

- [ ] **PM** (owner): ____________ / Date: ____________
- [ ] **Stakeholder**: ____________ / Date: ____________
- [ ] **Review verdict**（from `reviews/Gate1_PRD-{feature}-{date}.md`）: ✅ ready / ⚠️ revise / ❌ blocked

---

**End of PRD**

> 給業主：你主要要看的是 **📋 Executive Summary** + **🎯 Goals & KPI** + **⚠️ Risks & Open Questions** + **✍️ Sign-off** 四段。
> 其他段落是給下游 phase（analyst / ux / arch）作為輸入。
