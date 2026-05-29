# ADR-0003: 結構化 contact（活檔案）納入 knowledge 模型

> **檔名:** `ADR-0003-structured-contact-as-knowledge-entity.md`
> **狀態:** 提議中 | **日期:** 2026-05-28 | **決策者:** devteam-arch
> **負責人:** TL | **審核:** ARCH | **追蹤:** feasibility §3 #1（上游觸發者）
> **取代:** — | **被取代:** —
> **來源:** `docs/architecture/adr/ADR-0003-structured-contact-knowledge.md`

---

## 1. 背景與問題

- **上下文**: feasibility §3 標活檔案為 🟡 — AEOS 既有知識偏「文件/RAG」（三分類 Static/Policy/Dynamic），但「活檔案」是**結構化 CRM 記錄**（每客戶 7 欄位 + 互動時間軸：基本資料、健康關注、家庭、互動史、標籤）。
- **問題**: 結構化關係資料若硬塞 doc-RAG，語意檢索會過期/幻覺、無法精準 query 年資/標籤，且違反「Dynamic 不可放 RAG」鐵律。
- **驅動因素/約束**:
  - 精度（結構化查詢 vs 語意檢索幻覺）— high
  - 多租戶 contact 隔離（blast radius）— high
  - Privacy（PII 分級 / 保留 / 刪除）— high
  - 與既有知識三分類 boundary 一致 — medium
  - 約束：不爬 LINE 對話歷史，全由直銷商主動補。

## 2. 考量的選項

### 選項一: 結構化 contact 為一級 knowledge 實體（Dynamic Knowledge 變體）

- **優點**: 結構化查詢精準（年資/標籤/互動史 直接 query，不幻覺）；per-tenant + RLS 天然隔離；append-only 互動時間軸 = audit 友善；對映知識三分類的 Dynamic。
- **缺點**: knowledge 模型複雜度上升，需與 RAG / Policy 路由清楚。
- **成本/複雜度**: 中

### 選項二: 把 contact 當文件塞進 pgvector RAG

- **優點**: 複用既有 RAG 管線。
- **缺點**: 結構化欄位語意檢索化 → 過期/幻覺、無法精準 query；違反 `02 §6.3`「Dynamic 不可放 RAG」鐵律。
- **成本/複雜度**: 低（但錯）

### 選項三: 獨立 CRM 微服務

- **優點**: 邊界乾淨。
- **缺點**: pilot 階段過早拆服務（違反最薄切片）；與 knowledge 治理/Audit 雙寫。
- **成本/複雜度**: 高

## 3. 決策

**選擇**: 選項一 — 結構化 contact 為 knowledge 模型一級實體（Dynamic Knowledge 變體）。

**理由**: 活檔案查詢本質是結構化（依標籤/年資/互動史精準取），語意檢索（選項二）犧牲精度且違反 §6.3 鐵律；獨立微服務（選項三）對 pilot 過早。接受的 trade-off = knowledge 模型複雜度上升，須明確路由「結構化 contact 走 query / 自由文本走 RAG / 規章走 Policy」（KnowledgeRouter 三路）。

- **✅ 適用範圍**: 每客戶結構化記錄 + append-only 互動時間軸；per-tenant + RLS。
- **❌ 不適用**: 自由文本知識（走 RAG）；不爬 LINE 歷史（直銷商主動補）。

## 4. 後果

- **正面**: 結構化查詢精準、不幻覺；隔離與 audit 天然；此抽象垂直無關（任何垂直的「客戶/聯絡人」皆適用）→ 可放進 core 或共用層。
- **負面**: knowledge 模型新增實體 + 路由分支（structured-contact / doc-RAG / policy）複雜度上升（mitigation：KnowledgeRouter 明確三路）；與 legacy 記憶層關係須釐清（活檔案屬租戶知識的結構化變體，非推論記憶）。
- **影響範圍**: `05 架構與設計` §4.1 ERD（新增 contact + interaction timeline）、`07 模組規格`（knowledge 模組）。
- **可逆性 / 重新評估觸發**: 半可逆（資料模型遷移有成本）；結構化 contact 雙寫 ≥ 1 release 再切讀（migration README）。

## 5. 執行計畫

1. ERD：contact entity（7 欄位）+ interaction timeline — P3（見 `05` §4.1 / `07`）
2. KnowledgeRouter 三路路由（contact / RAG / policy）— P3
3. PII 分級 + 保留/刪除（30 天匯出 / 7 天刪除）— P3（見 `13` §B）

---

| 日期 | 審核人 | 備註 |
| :--- | :--- | :--- |
| 2026-05-28 | ARCH | 初版 Proposed |
