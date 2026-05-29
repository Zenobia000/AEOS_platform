# ADR-0004: 知識攝取與治理管線（core 骨架 + vertical pack 插點）

> **檔名:** `ADR-0004-knowledge-ingestion-governance-pipeline.md`
> **狀態:** 提議中 | **日期:** 2026-05-28 | **決策者:** devteam-arch
> **負責人:** TL | **審核:** ARCH | **追蹤:** B1 原料端需求（上游觸發者）
> **取代:** — | **被取代:** —
> **來源:** `docs/architecture/adr/ADR-0004-knowledge-ingestion-governance-pipeline.md` + `docs/architecture/knowledge-pipeline.md`

---

## 1. 背景與問題

- **上下文**: B1（混亂知識→可用草稿）的原料來源多且異質（客服對話、公司文件、處理報告、產品資料、規章），且每產業治理/精煉方式不同，但需要一個通用骨架。
- **問題**: 既有 §6.3 知識三分類、PII 脫敏、ADR-0003 結構化 contact、SkillOps、training room 都已是組件，缺一條把它們串起來的攝取管線。全塞 RAG 是幻覺/外洩根源。
- **驅動因素/約束**:
  - core / vertical 邊界清晰（換產業不動骨架）— high（ADR-0002）
  - 治理內建（分類/脫敏/源綁定/覆核）= 防 AI slop — high
  - 複用性（一條管線服多垂直）— high
  - 可漸進（最小 B1 路徑 → 長成全管線）— high

## 2. 考量的選項

### 選項一: 8 階段治理精煉管線（core 骨架 + pack config）

- **描述**: `ingest → de-identify → classify(三分類) → extract → govern(源綁定/衝突/合規/版控) → review(人類) → publish(版本化) → eval(採用率飛輪)`；階段通用、各階段 config 換產業。
- **優點**: 跨垂直複用；治理內建防幻覺/slop；最小 B1 路徑可只走 3 格（ingest→classify 全 Static→draft→eval），漸進長大。
- **缺點**: 管線複雜度；介面契約設計成本。
- **成本/複雜度**: 中（骨架+契約）

### 選項二: 全部丟進 RAG（無分類/治理）

- **優點**: 最快、最直覺。
- **缺點**: Dynamic 丟 RAG → 過期幻覺；規章丟 RAG → LLM 模糊解釋踩線；無源綁定 → 幻覺根源；無脫敏 → 個資外洩。
- **成本/複雜度**: 低（但任何上線場景皆不可行）

### 選項三: 每垂直各刻一套攝取

- **優點**: 單垂直最直覺。
- **缺點**: N 垂直 = N 套分岔；違反平台命題；治理品質不一。
- **成本/複雜度**: 中（短期）/ 高（長期）

## 3. 決策

**選擇**: 選項一 — 通用 8 階段治理精煉管線，core 骨架不變、vertical pack 注入各階段 config。

**理由**: 「分類在前、脫敏、源綁定、人類覆核、版控」是任何垂直把 AI 放進真實業務的剛需（Care Copilot feasibility 已證客戶獨立收斂到這些）；全塞 RAG（選項二）違反 §6.3 且是幻覺/外洩根源；每垂直 fork（選項三）崩於第二個垂直。接受的 trade-off = 管線複雜度，以「最小 B1 路徑只走 3 格、其餘階段被真實需求觸發才建」緩解。

**每階段 pack 插點**：source adapters / 敏感欄位 / 分類標準 / 萃取 prompt / **合規紅線詞庫** / 覆核標準 / knowledge schema / B1 rubric。

- **✅ 適用範圍**: 所有「生料 → 受治理知識」的攝取；core 8 階段 + 各階段 pack config 槽。
- **❌ 不適用**: Dynamic 即時資料（走 Tool/API live-query，不進管線存）；pack 不得繞過 core 治理。

## 4. 後果

- **正面**: 一條管線服多垂直；治理內建防幻覺/slop/外洩、源綁定可稽核；與既有組件對齊，非另起爐灶。
- **負面**: 8 階段全建很重 → **不可在 B1 前建完**，最小 B1 路徑只走 3 格（mitigation：spec 標註最小路徑）；介面契約高槓桿（mitigation：先用 Care Copilot 一個 pack 驗證契約再定型）；pack 可能變後門（mitigation：pack = config 資料，所有執行仍過 core govern，同 ADR-0002 約束）。
- **影響範圍**: `05 架構與設計` §4（knowledge_unit / contact 結構對齊管線）、`07 模組規格`（knowledge/ingest 模組）。
- **可逆性 / 重新評估觸發**: 半可逆（raw_item / knowledge_unit / pack-config 介面契約定型後改動成本大）；開始吃客服對話原始 log（噪音+PII+量）時觸發啟用 [2]De-id + [4]Extract。

## 5. 執行計畫

1. pipeline spec（各階段 I/O schema + 最小路徑）— P2/P3（`knowledge-pipeline.md`）
2. raw_item / knowledge_unit / pack-config schema 定型 — P3
3. 以 Care Copilot 為第一個 pack 驗證契約 — P3（feasibility §8）

### 最小 B1 路徑（W1 只走 3 格）

```text
[1] 貼上 markdown → [3] 全當 Static → draft → [8] eval 採用率   (= aeos-mvg W1)
```

---

| 日期 | 審核人 | 備註 |
| :--- | :--- | :--- |
| 2026-05-28 | ARCH | 初版 Proposed；對齊 knowledge-pipeline.md §1 介面契約 |
