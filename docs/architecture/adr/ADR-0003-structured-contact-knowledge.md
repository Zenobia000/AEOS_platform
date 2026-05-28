# ADR-0003 — 結構化 contact（活檔案）納入 knowledge 模型

> **📋 Status**: Proposed
> **🗓 Date**: 2026-05-28
> **👤 Owner**: `devteam-arch`
> **🔖 Version**: v1
> **🎯 Scope**: feature（knowledge 模型擴充，跨垂直可複用）
> **🏷 Tags**: knowledge-model, structured-data, privacy, tenant-isolation, memory
> **🔗 Feature**: care-copilot
> **🔗 Related KB**: KB-11 §1-§3（資料分級/PII/合規邊界）

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: 「活檔案」（每客戶 7 欄位 + 互動時間軸）是**結構化 contact 記錄**，不是文件 RAG。把它列為 knowledge 模型的**第一類實體（Dynamic Knowledge 變體，per-tenant + RLS + append-only 時間軸）**，與 doc-RAG 區隔。

| 維度 | 摘要 |
|:---|:---|
| **🎯 Decision** | Option A：結構化 contact 為一級 knowledge 實體，與 doc-RAG 區隔 |
| **🤔 Why** | 活檔案是結構化查詢對象非語意檢索；硬塞 RAG 會幻覺、失精度 |
| **🚀 Status** | ⏳ Proposed |
| **📊 Reversibility** | 半可逆（資料模型，遷移有成本） |
| **🎯 下一步** | design driver 出 ERD（contact entity + timeline） |

---

## 🎯 Context

- **觸發**：feasibility §3 標活檔案為 🟡 — AEOS 既有知識偏「文件/RAG」（`02 §6.3` 三分類 Static/Policy/Dynamic），活檔案是**結構化 CRM 記錄**（基本資料、健康關注、家庭、互動史、標籤）。
- **技術限制**：legacy ADR-0010 記憶五層；legacy ADR-0007 多租戶隔離；隱私底線 = 不爬 LINE 對話歷史，全由直銷商主動補。
- **相關 NFR**：Privacy（PII 分級、保留期、可刪除）；多租戶 contact 0 串（feasibility 情境 14 紅隊必過）。

---

## 📐 Decision Drivers

| Priority | Driver | Weight | Reference |
|:---:|:---|:---|:---|
| 1 | 精度（結構化查詢 vs 語意檢索幻覺） | high | `02 §6.3` |
| 2 | 多租戶 contact 隔離（blast radius） | high | legacy ADR-0007 |
| 3 | Privacy（PII 分級 / 保留 / 刪除） | high | KB-11 §1-§3 |
| 4 | 與既有知識三分類的 boundary 一致 | medium | `02 §6.3` |

---

## 🔍 Options Considered

### Option A — 結構化 contact 為一級 knowledge 實體

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 結構化查詢精準（年資/標籤/互動史 直接 query，不幻覺）<br>• per-tenant + RLS 天然隔離<br>• append-only 互動時間軸 = audit 友善<br>• 對映知識三分類的 Dynamic（即時/單筆查詢） |
| **Cons** | • knowledge 模型複雜度上升；需與 RAG / Policy 路由清楚 |
| **Fit** | CRM 式結構化關係資料 |
| **Anti-fit** | 自由文本知識（那走 RAG） |
| **Cost / Effort** | M |

### Option B — 把 contact 當文件塞進 pgvector RAG

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 複用既有 RAG 管線 |
| **Cons** | • 結構化欄位語意檢索化 → 過期/幻覺、無法精準 query 年資/標籤<br>• 違反 `02 §6.3`「Dynamic 不可放 RAG」鐵律 |
| **Anti-fit** | 結構化記錄 |

### Option C — 獨立 CRM 微服務

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 邊界乾淨 |
| **Cons** | • pilot 階段過早拆服務（違反最薄切片）；與 knowledge 治理/Audit 雙寫 |
| **Anti-fit** | pilot 規模 |

---

## ✅ Decision

> [!IMPORTANT]
> **選擇**：Option A — 結構化 contact 為 knowledge 模型的一級實體（Dynamic Knowledge 變體）。
>
> **理由**：活檔案的查詢本質是結構化（依標籤/年資/互動史精準取），語意檢索（Option B）會犧牲精度且違反 §6.3 鐵律；獨立微服務（Option C）對 pilot 過早。接受的 trade-off = knowledge 模型複雜度上升，須明確路由「結構化 contact 走 query / 自由文本走 RAG / 規章走 Policy」。

| 範疇 | 說明 |
|:---|:---|
| **✅ 適用範圍** | 每客戶結構化記錄 + append-only 互動時間軸；per-tenant + RLS |
| **❌ 不適用** | 自由文本知識（走 RAG）；不爬 LINE 歷史（直銷商主動補） |
| **🔓 可逆性** | 半可逆 — 資料模型遷移有成本 |

---

## 📊 Consequences

### ✅ Positive
- 結構化查詢精準、不幻覺；隔離與 audit 天然
- 此抽象垂直無關（任何垂直的「客戶/聯絡人」皆適用）→ 可放進 core 或共用層，非 Care Copilot 專屬

### ⚠️ Negative
> [!WARNING]
- knowledge 模型新增實體 + 路由分支（structured-contact / doc-RAG / policy）複雜度上升（mitigation：KnowledgeRouter 明確三路，沿用 §6.3）
- 與 legacy ADR-0010 記憶層關係須釐清（活檔案屬 L3 租戶知識的結構化變體，非 L4 推論記憶）

### 🎯 Follow-up Work
| Action | Owner | Due | Reference |
|:---|:---|:---|:---|
| ERD：contact entity（7 欄位）+ interaction timeline | devteam-design | P3 | — |
| KnowledgeRouter 三路路由（contact/RAG/policy） | devteam-design | P3 | `02 §6.3` |
| PII 分級 + 保留/刪除（30 天匯出 / 7 天刪除） | devteam-design | P3 | KB-11 §2 |

### 📉 影響的下游文件
| Doc | Impact |
|:---|:---|
| `docs/data/erd-care-copilot.md` | 新增 contact + timeline 結構 |
| `docs/architecture/c4-l2-care-copilot.md` | knowledge container 含結構化 contact store |

---

## 🔗 Links
| Asset | Path |
|:---|:---|
| **Feasibility** | [`docs/architecture/feasibility-AEOS-x-care-copilot.md`](../feasibility-AEOS-x-care-copilot.md) §3 #1 |
| **延續 ADR** | legacy ADR-0010（記憶五層 L3）·`_legacy-dev_docs/02-product-architecture.md` §6.3 知識三分類 |
| **KB references** | [[11_data_and_stack_catalog]] |

---

## ✍️ Sign-off
- [ ] **Architect** (owner): ____________ / Date: ____________
- [ ] **Tech Lead**: ____________ / Date: ____________

---

**End of ADR**
