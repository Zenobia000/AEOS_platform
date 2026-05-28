# ERD + 模組/Error Model — care-copilot（最薄切片）

> **Status**: draft · **Owner**: `devteam-design` · **Date**: 2026-05-28 · **Feature**: care-copilot
> 對應 ADR-0003（結構化 contact）/ system-spec §3-4 / NFR Privacy。所有表帶 `tenant_id` + RLS。

---

## ERD（切片 6 表）

```
tenant (id, name, data_retention_days, compliance_profile)
   │1
   ├──< contact (id, tenant_id, display_name, health_focus, family, work,
   │             interests, comm_pref, tags jsonb, created_at)        ← 活檔案 7 欄位
   │        │1
   │        └──< interaction (id, contact_id, tenant_id, at, kind, summary)  ← append-only 時間軸
   │
   ├──< knowledge_chunk (id, tenant_id, source, text, embedding vector)  ← doc-RAG(pgvector)
   │
   └──< message (id, tenant_id, contact_id, role, text,
                 draft_text, decision, decided_by, compliance, used_chunks jsonb,
                 model, created_at)        ← 對話+草稿+稽核+訓練素材，一表多用
```

> `message` 一張表幹三件事（對話紀錄 + audit log + 訓練素材），消滅資料複製（foundation/02 §3.2）。
> `contact`(結構化) 與 `knowledge_chunk`(語意檢索) 分開 = ADR-0003 的 KnowledgeRouter 兩路。

## 路由（KnowledgeRouter，§6.3 三分類）

| 查詢 | 路由 | 對象 |
|:---|:---|:---|
| 客戶結構化屬性（年資/標籤/健康關注） | **structured query** | `contact` + `interaction` |
| 產品/FAQ 自由文本 | **RAG** | `knowledge_chunk`(pgvector) |
| 合規規則 | **Policy** | vertical pack 詞庫（非 DB） |

## 模組責任（切片，可平行實作）

| 模組 | 責任 | 軌 |
|:---|:---|:--|
| `runtime`（nanobot 包覆） | agent loop + 編排 | 🟦 core |
| `policy`（合規低語） | regex 詞庫掃描 → green/yellow/red gate | 🟦 core 引擎 + 🟨 pack 詞庫 |
| `knowledge` | KnowledgeRouter（contact/RAG）+ ingest | 🟦 core |
| `draft` | 檢索 + LLM 生成 + needs-human guard | 🟦 core 機制 + 🟨 pack prompt |
| `audit` | append-only 寫入；失敗即回滾 | 🟦 core |
| `eval` | 離線 draft→judge | 🟦 core |

## Error Model

| 類別 | HTTP | 行為 |
|:---|:---|:---|
| 跨租戶存取 | 403 | deny by default；記 audit；紅隊必過 |
| 知識缺依據 | 422 | `needs_human=true`，不回幻覺草稿 |
| 合規紅燈 | 200 + `compliance=red` | 送出鈕禁用，必須改寫（business gate，非 error） |
| LLM 失敗 | 503 / 重試 | fallback_models；仍失敗標 needs_human |
| Audit 寫入失敗 | 500 | 整筆操作回滾（不允許靜默成功） |

## Privacy（NFR 對應）
- `contact`/`interaction` 含 PII；`data_retention_days` 隨 tenant DPA；匯出 30 天 / 刪除 7 天。
- 不爬 LINE 歷史；資料全由直銷商主動補。
