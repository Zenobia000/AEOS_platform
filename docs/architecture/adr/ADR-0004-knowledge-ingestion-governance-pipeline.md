# ADR-0004 — 知識攝取與治理管線（core 骨架 + vertical pack 插點）

> **📋 Status**: Proposed
> **🗓 Date**: 2026-05-28
> **👤 Owner**: `devteam-arch`
> **🔖 Version**: v1
> **🎯 Scope**: cross-team（AEOS 平台核心 — B1 的原料端）
> **🏷 Tags**: knowledge-pipeline, ingestion, governance, vertical-pack, knowledge-classification
> **🔗 Feature**: care-copilot
> **🔗 Related KB**: KB-11 §1-§3（資料分級/PII/合規）

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: 把「異質生料 → 受治理知識」設計成一條**通用 8 階段精煉管線**（ingest→de-id→classify→extract→govern→review→publish→eval）。**階段(機制)是 core 通用、不變**；**每產業差異是插進各階段的 config(vertical pack)**。換產業只換 config，不動骨架。這是 B1 的原料端,也是「AEOS 跨垂直」在知識層的落地。

| 維度 | 摘要 |
|:---|:---|
| **🎯 Decision** | Option A：8 階段治理精煉管線，core 骨架 + pack config |
| **🤔 Why** | 分類在前/源綁定/人類覆核 是垂直無關剛需；config 才是產業差異 |
| **🚀 Status** | ⏳ Proposed |
| **📊 Reversibility** | 半可逆（介面契約定型後改動 blast radius 大） |
| **🎯 下一步** | spec：`docs/architecture/knowledge-pipeline.md`（各階段 I/O + 最小 B1 路徑） |

---

## 🎯 Context

- **觸發**：B1（混亂知識→可用草稿）的**原料來源多且異質**——客服對話、公司文件、處理報告、產品資料、規章——且**每產業治理/精煉方式不同**，但需要一個**通用骨架**。
- **技術限制**：既有 §6.3 知識三分類、legacy ADR-0005 PII 脫敏、ADR-0003 結構化 contact、§9 SkillOps、§10 training room 都已是組件，缺一條把它們串起來的攝取管線。
- **相關 NFR**：Privacy（PII 先脫敏）、Auditability（源綁定）、跨租戶隔離。

---

## 📐 Decision Drivers

| Priority | Driver | Weight | Reference |
|:---:|:---|:---|:---|
| 1 | core / vertical 邊界清晰（換產業不動骨架） | high | ADR-0002 |
| 2 | 治理內建（分類/脫敏/源綁定/覆核）= 防 AI slop | high | KB-11, §6.3 |
| 3 | 複用性（一條管線服多垂直） | high | foundation/01 |
| 4 | 可漸進（最小 B1 路徑 → 長成全管線） | high | foundation/00 |

---

## 🔍 Options Considered

### Option A — 8 階段治理精煉管線（core 骨架 + pack config）

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 階段通用、config 換產業 → 跨垂直複用<br>• 治理(三分類/脫敏/源綁定/覆核/版控)內建,防幻覺與 slop<br>• 最小 B1 路徑可只走 3 格,漸進長大 |
| **Cons** | • 管線複雜度;介面契約設計成本 |
| **Fit** | 多來源、多垂直、需治理的知識攝取 |
| **Anti-fit** | 單檔貼上的玩具場景（但那只是走最小路徑） |
| **Cost / Effort** | M（骨架+契約） |

### Option B — 全部丟進 RAG（無分類/治理）

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 最快、最直覺 |
| **Cons** | • §6.3 點名反模式:訂單等 Dynamic 丟 RAG → 過期幻覺;規章丟 RAG → LLM 模糊解釋踩線;無源綁定 → 幻覺根源;無脫敏 → 個資外洩 |
| **Anti-fit** | 任何要上線的企業場景 |

### Option C — 每垂直各刻一套攝取

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 單垂直最直覺 |
| **Cons** | • N 垂直 = N 套分岔;違反平台命題;治理品質不一 |
| **Anti-fit** | 橫向平台 |

---

## ✅ Decision

> [!IMPORTANT]
> **選擇**：Option A — 通用 8 階段治理精煉管線，core 骨架不變、vertical pack 注入各階段 config。
>
> **理由**：「分類在前、脫敏、源綁定、人類覆核、版控」是任何垂直把 AI 放進真實業務的剛需（Care Copilot feasibility 已證客戶獨立收斂到這些）；全塞 RAG（B）違反 §6.3 且是幻覺/外洩根源；每垂直 fork（C）崩於第二個垂直。接受的 trade-off = 管線複雜度,以「最小 B1 路徑只走 3 格、其餘階段被真實需求觸發才建」緩解。

| 範疇 | 說明 |
|:---|:---|
| **✅ 適用範圍** | 所有「生料 → 受治理知識」的攝取;core 8 階段 + 各階段 pack config 槽 |
| **❌ 不適用** | Dynamic 即時資料(走 Tool/API live-query,不進管線存);pack 不得繞過 core 治理 |
| **🔓 可逆性** | 半可逆 — raw_item / knowledge_unit / pack-config 介面契約定型後改動成本大 |

### 8 階段（core 機制）
`ingest → de-identify → classify(三分類) → extract → govern(源綁定/衝突/合規/版控) → review(人類) → publish(版本化) → eval(採用率飛輪)`
詳見 `docs/architecture/knowledge-pipeline.md`。

### 每階段的 pack 插點（vertical 差異）
source adapters / 敏感欄位 / 分類標準 / 萃取 prompt / **合規紅線詞庫** / 覆核標準 / knowledge schema / B1 rubric。

---

## 📊 Consequences

### ✅ Positive
- 一條管線服多垂直;換產業換 config 即可
- 治理內建 → 防幻覺/slop/外洩,源綁定可稽核
- 與既有組件(§6.3 / legacy ADR-0005 / 0003 / §9 / §10 / §12)對齊,非另起爐灶

### ⚠️ Negative
> [!WARNING]
- 8 階段全建很重 → **不可在 B1 前建完**;最小 B1 路徑只走 ingest→classify(全 Static)→draft→eval(= `aeos-mvg` W1)。每階段被真實需求觸發才加（mitigation：spec 標註最小路徑）
- 介面契約是高槓桿,錯了改動大（mitigation：先用 Care Copilot 一個 pack 驗證契約再定型）
- pack 可能變繞過治理的後門（mitigation：pack = config 資料,所有執行仍過 core govern；ADR-0002 同款約束）

### 🎯 Follow-up Work
| Action | Owner | Due | Reference |
|:---|:---|:---|:---|
| pipeline spec（各階段 I/O schema + 最小路徑） | devteam-arch/design | P2/P3 | `knowledge-pipeline.md` |
| raw_item / knowledge_unit / pack-config schema 定型 | devteam-design | P3 | — |
| 以 Care Copilot 為第一個 pack 驗證契約 | devteam-design | P3 | feasibility §8 |

### 📉 影響的下游文件
| Doc | Impact |
|:---|:---|
| `docs/data/erd-care-copilot.md` | knowledge_unit / contact 結構對齊管線 |
| `docs/architecture/c4-care-copilot.md` | Knowledge container 內含管線階段 |

---

## 🔗 Links
| Asset | Path |
|:---|:---|
| **Pipeline spec** | [`docs/architecture/knowledge-pipeline.md`](../knowledge-pipeline.md) |
| **延續 ADR** | ADR-0002(vertical pack)·ADR-0003(結構化 contact)·legacy ADR-0005(PII)·`02 §6.3`(三分類)·§9 SkillOps·§10 training room |
| **KB references** | [[11_data_and_stack_catalog]] |

---

## ✍️ Sign-off
- [ ] **Architect** (owner): ____________ / Date: ____________
- [ ] **Tech Lead**: ____________ / Date: ____________

---

**End of ADR**
