# Strategy — docs/ 完整性與盲點審計（5-persona 團隊討論）

> **📋 Status**: reviewed（5 persona 並行掃描 + facilitator 互相討論收斂）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: facilitator（arch · ba · dba · qa · pm 交叉）
> **🔖 Version**: v1
> **🔗 Related**: `reviews/multi-role-care-copilot-2026-05-28.md`（前一輪 per-doc blocker）· `governance/stakeholders.md`

---

## 📋 Executive Summary

> [!IMPORTANT]
> **TL;DR (30s)**: 團隊獨立掃描後**收斂到同一個根因** —— **盲點不是隨機的,精準落在「沒人被指派」的角色之間**。stakeholder map 只有 4 角色,缺 **安全 / 法務 / GTM / AI-Architect / SRE-ops** owner,而五大盲點(威脅模型 / 合規法務 / 測試真值集 / GTM 執行 / DR-secret)正好對應這些缺席角色。**盲點 = 缺席團隊角色的影子。** 修文件之前,先補人(或明確指派代理人)。

| 維度 | 摘要 |
|:---|:---|
| **🎯 結論** | 盲點 = 缺席角色的影子;補 owner 比補文件更根本 |
| **📊 規模** | 5 個跨界盲點（無人 own）· 6 類缺檔 · 5 份不完整 · 2 個一致性裂縫 |
| **🚀 狀態** | ⚠️ 2 個盲點(威脅模型 / migration 實檔)被多 persona 判**上線前致命** |
| **🎯 下一步** | 指派 5 個缺席 owner（可一人兼）→ 補致命缺口 → 收斂命名 |

---

## 🎯 根因：盲點 ↔ 缺席角色（互相討論的收斂）

| 盲點（無人 own） | 落在哪些角色之間 | 缺席的 owner |
|:--|:--|:--|
| 威脅模型 / prompt injection / 攻擊面 | arch × dba × (security) | **安全 owner** |
| 同意書 / DPA / FTC 詞庫法源 / 隱私政策 | ba × (legal) | **法務 owner** |
| 測試真值集（50 題 / 200 標註 / 50 詞庫） | qa × ba × (AI-Architect) | **AI-Architect / 資料 owner** |
| GTM 病毒 / Top Leader 抽成 / 招募 SOP | pm × po × (GTM Lead) | **GTM owner** |
| DR / RPO / backup / secret 輪替 | arch × dba × (sre) | **SRE-ops owner** |

> [!NOTE]
> stakeholder map 現只列 4 角色（CEO / 直銷商 / 終端客戶 / coding agent），上述 5 個 owner **全缺**。pilot_run §9 也自承「AI Architect 缺位、法務顧問缺位」。文件盲點是組織盲點的鏡像。

---

## ❌ 五大盲點（跨 persona 收斂，無人 own）

| # | 盲點 | 致命性 | 多 persona 證據 | 修法 |
|:--|:--|:--:|:--|:--|
| **G1** | `docs/security/` 全空 — 威脅模型無人 own | 🔴 上線前致命 | arch B-1 + dba B-2 | 新增 `security/threat-model.md`（STRIDE / prompt injection 防禦設計 / 多租戶攻擊面 / pack 投毒 / secret 輪替）;鐵律「跨tenant=0」要有對抗路徑驗證 |
| **G2** | migration 只有 ERD 口頭註記,無實際 `.sql` | 🔴 上線前致命 | dba B-1 | 產 `data/migrations/*.sql`（up/down + RLS policy 原文 + HNSW + composite index）= handoff 的 schema source of truth |
| **G3** | 合規法務無 owner（同意書/DPA/詞庫法源/隱私政策） | 🟠 碰真資料前必補 | ba B-1/B-2/B-3 | `governance/consent-and-dpa.md` + `governance/compliance-lexicon-authority.md`;stakeholder map 補法務+data subject |
| **G4** | 測試真值集無 owner（pass rate 算不出來） | 🟠 阻 B1 驗收 | qa B-1 + pm B-3 | `qa/test-data-strategy.md`（誰標/版本/分母）;指派 AI-Architect |
| **G5** | GTM 執行無 owner（CAC/churn 生死數字沒人管） | 🟠 商業收斂後沒人執行 | pm B-2 | `strategy/gtm-execution.md`（Top Leader 抽成設計 / 招募 SOP / 病毒係數量測）;指派 GTM owner |

---

## ⚠️ 不完整的文件（有但缺關鍵）

| 文件 | 缺什麼 | persona |
|:--|:--|:--|
| ADR-0001~0004 | 全 `proposed` 未 frozen,但 C4/NFR/ERD 已以其為前提 | arch B-3 |
| nfr / runbook / release-readiness | RPO/backup/還原演練/secret 輪替 只有散落 1-line 待辦,無 DR 文件 | arch B-2 + dba S-1/S-2 |
| test-plan | acceptance↔FR 追溯斷鏈;CI gate / perf baseline / 回歸基準無歸屬 | qa B-2/S-1/S-2 |
| system-spec | 缺 BR-7 同意/資料請求、BR-8 合規 authority+法源 | ba S-1 |
| openapi | Error/idempotency/response schema 仍是「待落地」註記 | (前輪 B-5) |

## ❌ 缺檔（標準佈局該有、完全沒有）

| 路徑 | 用途 | 缺席 owner |
|:--|:--|:--|
| `docs/security/threat-model.md` | 威脅模型（G1） | 安全 |
| `docs/data/migrations/*.sql` | 實際 schema（G2） | dba |
| `docs/governance/consent-and-dpa.md` | 同意/DPA（G3） | 法務 |
| `docs/qa/test-data-strategy.md` | 真值集（G4） | AI-Architect |
| `docs/strategy/gtm-execution.md` | GTM 執行（G5） | GTM |
| `docs/ops/dr-backup.md` | DR/RPO/secret | SRE |
| `docs/ux/onboarding-7day.md` | 早期 churn 防線（pm S-2） | ux+pm |
| `architecture/dr/` | 變更決策記錄 | arch（暫無變更,OK 延後） |

## 🔧 一致性裂縫（必修,slop 來源）

| # | 裂縫 | 修法 |
|:--|:--|:--|
| N1 | **命名分裂** ai-cs-mvg ↔ care-copilot;PRD 引用 `user-flow-ai-cs-mvg.md`(死連結) | 統一對外名 **care-copilot**,ai-cs-mvg 降為 PRD 內「B1 技術切片」代號,修死連結 |
| N2 | **兩份 PRD 並存** ai-cs-mvg(eval-only/北極星=approve率) vs pilot_run(11工具/北極星=Care Action) | 明定 source of truth：哪份是 freeze 賭注、哪份是垂直商品全集 |

---

## 🎯 優先序（先補人,再補致命缺口）

| 序 | 行動 | 為什麼先 |
|:--|:--|:--|
| 1 | **指派 5 個缺席 owner**（可一人兼代） | 盲點根因;沒 owner 文件補了也腐爛 |
| 2 | **G1 威脅模型 + G2 migration .sql** | 兩個「上線前致命」,且 handoff 需要 |
| 3 | **N1 命名收斂 + 修死連結** | slop 來源,cascade 範圍小先清 |
| 4 | G3 合規法務 + G4 測試真值集 | 碰真資料 / 打 B1 前必補 |
| 5 | G5 GTM + onboarding + DR | pilot 招募與留存執行 |

---

## 🔍 Drill-down：5-persona 原始 critique

<details>
<summary>展開 arch / ba / dba / qa / pm 完整輸出</summary>

**arch**:G1 security 空=威脅模型無人 own(STRIDE/injection/跨tenant提權/pack投毒);G2 dr 空+recovery 散落 1-line;ADR 全 proposed 但下游已依賴;C4 缺 L3(anti-bypass 驗不了);容量無飽和觸發閾值。

**ba**:同意書/隱私政策無規格無 own(終端客戶=data subject 卻標 low);FTC/FDA 詞庫無法源無 authority(誰簽核/誤判申訴);DPA/法務 review 無 owner 無里程碑;語音 TTS 隱私卡同缺位。補 BR-7/BR-8 + stakeholder 補法務/data subject/品牌方。

**dba**:migration 零實檔(RLS/HNSW/index 只口頭=未保護,致命);security 空(injection 只 1 條測試無防禦設計,致命);backup/PITR/RPO 散落待補(PII 刪除緩衝需 PITR≥7天否則合規漏洞);secret 只「不進 git」無輪替。audit_event 拆表是最扎實一塊。

**qa**:test data strategy 全空(50題/200標註/50詞庫 無人產無版控=pass rate 算不出);acceptance↔FR 追溯斷鏈(FR-003/005/006 無 neg case);CI gate/perf baseline/回歸基準無 owner;pilot KILL 數值誰量測無 instrument。

**pm**:命名分裂(care-copilot 統一);GTM 病毒+Top Leader 抽成無 owner 無規格(生死數字沒人執行);KPI baseline 缺(50% 可能是退步);兩份 PRD 北極星/scope 對不齊;onboarding 7日無規格;垂直#2 ≥70%複用無量測定義。

</details>

---

## 🔗 Cross References
- 前輪 per-doc blocker：[`reviews/multi-role-care-copilot-2026-05-28.md`](../../.claude/context/devteam/reviews/multi-role-care-copilot-2026-05-28.md)
- 商業模式收斂：[`strategy/business-model-convergence.md`](./business-model-convergence.md)
- stakeholder（待補 5 角色）：[`governance/stakeholders.md`](../governance/stakeholders.md)
