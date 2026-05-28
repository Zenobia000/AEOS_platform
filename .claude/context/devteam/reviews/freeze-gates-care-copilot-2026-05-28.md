# Freeze Gates 按部就班補跑 — care-copilot

> **日期**: 2026-05-28
> **觸發**: 業主 /goal「回到衝刺前按部就班跑一遍」— momentum 模式下 8 gate 卡在 ready_to_review，本次補跑 freeze ceremony。
> **方法**: 逐 gate 驗 evidence(對照 KB-04)+ 跑 `scripts/check-doc-consistency.sh`(linter 全綠)+ consolidate 本 session review + Elon-lens 裁決。
> **Intensity**: 依 KB-04（strict for 1/4/5a/5b/7）。

---

## 📋 總結

| Gate | 名稱 | Evidence | Review 來源 | 裁決 |
|:--|:--|:--:|:--|:--:|
| 1 | PRD Freeze | ✅ 6/6 | R2 + 本session 命名/ADR 修 + ba audit | 🟢 **frozen** |
| 2 | UX Flow | ✅ 4/4（R3 補閉環） | ux-persona 本次補審 | 🟢 **frozen** |
| 3 | System Spec | ✅ 5/5 | arch+qa roundtable + ba audit | 🟢 **frozen** |
| 4 | NFR+ADR | ✅ 5/5 | arch+dba roundtable + pm/sre/dba audit | 🟢 **frozen** |
| 5a | API Contract | 🟡 4/5 | sd roundtable | 🟢 **frozen**（W2 條件） |
| 5b | DB Schema | ✅ 5/5 | dba roundtable 逐欄驗 | 🟢 **frozen** |
| 6 | Test Ready | 🟡 3/4 | qa roundtable | 🟢 **frozen**（pre-B1 條件） |
| 7 | Release Ready | ❌ 3/5 | pm/qa/arch | 🔴 **BLOCKED** |

> linter `scripts/check-doc-consistency.sh`：**8/8 通過**（斷連結0/命名分裂0/ID0/TC-SEC一致/meta parity/鐵律覆蓋/orphan FR0/UC計數）。

---

## Gate 1 — PRD Freeze 🟢（ba/sa/ux, strict）
- [x] Problem Statement 三項 · [x] KPI 量化（K1 approve≥50%/總採用≥70%）· [x] persona+scenario · [x] in/out scope · [x] risks · [x] open questions（OQ-002）
- Review：R2 修正 + 本 session N1 命名收斂 + Decision Log ADR-TBD→0001~0004。
- **裁決 frozen**：ai-cs-mvg = AEOS 核心切片 PRD（freeze 賭注）。後續改走 DR。

## Gate 2 — UX Flow 🟢（pm/qa, standard）
- [x] 核心 flow（R3 補 UC-3 edit→重過合規閉環）· [x] error/empty/loading/offline/partial state · [x] a11y（WCAG 2.1 AA）· [x] 高風險互動驗證假設（R3 取代 TBD prototype）
- Review：ux-persona 補審 🟡 → B-1/S-2 已修（R3）。
- **裁決 frozen**。

## Gate 3 — System Spec 🟢（arch/qa, standard）
- [x] UC-1~5（actor/trigger/steps/acceptance，B-1 量化）· [x] BR-1~8（ID+source）· [x] edge cases · [x] 依賴可追溯 · [x] acceptance QA 可用
- **裁決 frozen**。

## Gate 4 — NFR+ADR Baseline 🟢（pm/sre/dba, strict）
- [x] NFR 9 維 baseline · [x] ADR×4 · [x] C4 L1+L2+L3（已修部署拓樸） · [x] failure modes 6 · [x] observability 前置
- ADR supersede：無（全初版，broken_supersede=0）。
- **裁決 frozen**。ADR 維持 Proposed（ADR-0002/0004 刻意延至 B1 後鎖版，arch 判定非 blocker）。

## Gate 5a — API Contract 🟢（pm/qa/sre, strict）— W2 條件
- [x] OpenAPI 完整（endpoint+schema+auth+error $ref 已接）· [x] timeout/失敗策略（failure 表）· [x] mock 可生（3.1）· [x] 平行工作
- [ ] **Idempotency-Key + x-governance breaking-change 政策** → **W2 落地**（W1 eval-only 無 live API，非 W1 blocker）。
- **裁決 frozen as W1 baseline**；W2 follow-up：idempotency / x-governance / IngestResult·EvalResult 綁定。

## Gate 5b — DB Schema 🟢（arch/qa/sre, strict）
- [x] logical+physical（ERD+migration）· [x] up/down script（dba 驗 reverse-order CASCADE）· [x] backfill（結構化 contact 雙寫≥1 release）· [x] index/retention/PII map（含特種個資 health_focus）· [x] 一致性測試假設（TC-SEC-01）
- **裁決 frozen**。embedding `vector(1024)` = ASSUMPTION（W2 對齊 embedding 模型）。

## Gate 6 — Test Ready 🟢（arch/devops, standard）— pre-B1 條件
- [x] test plan（scope/levels/env/cases/automation/exit）· [x] non-functional（perf/security/隔離）· [x] defect triage
- [ ] **test data strategy（50題/200標註/50詞庫真值集）** → **G4 defer，AI-Architect own，B1 run 前必補**（無分母則 pass rate 不可算）。
- **裁決 frozen as 計畫就緒**；pre-B1 硬條件：`qa/test-data-strategy.md` 須先存在。

## Gate 7 — Release Ready 🔴 BLOCKED（pm/qa/arch, strict）
- [x] runbook+alerts（含注入告警）· [x] rollback 可執行（killswitch 30s+心跳驗證）· [x] Go/No-Go 標準明文 · [x] 單 pilot draft-mode（無需 canary）
- [ ] **security Go/No-Go 未滿足**：threat-model §6 清單需**一次外部法務/安全 sign-off**（pilot 碰真 PII 入場券）— 未做。
- [ ] **真 pilot 資料未到（OQ-002）**：B1 採用率需真 Synergy 教練資料才算數;範例資料只證產線會轉。
- **裁決 BLOCKED**：不蓋橡皮章。release 解鎖前置 = ① 法務 sign-off（consent-and-dpa + lexicon-authority）② 簽下 Synergy pilot 取真資料。兩者皆外部依賴，非文件可解。

---

## Elon-lens 裁決摘要
- **frozen 1-6**：內部一致性收斂（linter 全綠 + traceability matrix 對齊），可作 handoff baseline；變更走 DR/cascade。
- **5a/6 附條件而非假 frozen**：W2(API idempotency)、pre-B1(test 真值集)是真依賴，明文標 follow-up 不藏。
- **Gate 7 誠實 blocked**：legal sign-off + 真 pilot 資料是「驗證正確」的入場券，文件層到頂也跨不過——這是賭注的真天花板（OQ-002），不是文件缺漏。

## 後續（業主動作）
1. 簽 Synergy pilot（OQ-002）→ 解 Gate 7 資料前置 + 啟動 B1。
2. 一次外部法務 review（consent-and-dpa + lexicon-authority sign-off）→ 解 Gate 7 security 前置。
3. AI-Architect 補 `qa/test-data-strategy.md`（G4）→ 解 Gate 6 pre-B1 條件。
