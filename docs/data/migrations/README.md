# Migrations — care-copilot schema

> **📋 Status**: frozen（Gate 5b DB Schema，2026-05-28；變更走 DR）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: `devteam-design`（dba）
> **🔖 Version**: v1
> **🎯 Scope**: care-copilot schema migration（handoff 的 schema source of truth）
> **🔗 Related**: `docs/data/erd-care-copilot.md` · `security/threat-model.md`（RLS/append-only）

## 慣例

- 檔名:`<NNNN>_<name>.up.sql` / `.down.sql`（golang-migrate 風格,任何 runner 皆可套）。
- 一個 migration = 一個邏輯變更,可前進可回滾(down 已驗 reverse-order drop)。
- RLS policy **原文納 migration**（不靠口頭),跨租戶隔離隨 schema 走。

## 關鍵設計

| 項目 | 決策 | 理由 |
|:---|:---|:---|
| **RLS** | 每業務表 `ENABLE + FORCE` + `tenant_isolation` policy（`USING` + `WITH CHECK`） | 鐵律「跨 tenant=0」;FORCE 防 app 以 table owner 連線繞過 |
| **租戶解析** | `current_tenant()` 讀 `app.current_tenant` GUC;缺值回 NULL → deny | app 每 request `SET app.current_tenant`;忘設 = 查無資料(安全預設) |
| **audit append-only** | schema 層 `audit_no_update`/`audit_no_delete` policy `USING(false)` **直接 deny**（主防線,不依賴部署） | 不外包給角色 migration;即使 role 被誤授權也擋（threat-model T-T-02） |
| **app DB role** | 須為 **RLS-enforced、非 superuser、無 BYPASSRLS、無 CREATE/DROP**（縱深防禦,非 append-only 唯一保證） | threat-model T-E-01;角色 migration 依部署環境另立 |
| **embedding 維度** | `vector(1024)` = **ASSUMPTION**（Voyage voyage-3） | W1 不接 DB;W2 選定 embedding 模型後,維度須與其一致,否則改本 migration |
| **HNSW** | `knowledge_chunk.embedding` 用 hnsw + cosine | doc-RAG（W2） |
| **composite index** | interaction / message 用 `(tenant_id, contact_id)` | 最常見查詢路徑（某客戶時間軸 / 對話） |

## 上線注意（接 ERD R2 B-4）

- **結構化 contact 雙寫**:若從既有非結構化來源遷入,上線走雙寫 ≥ 1 release 再切讀。
- **PITR**:備份視窗須涵蓋 ≥ 7 天刪除緩衝（PII 刪除後備份殘留 ≤7 天,接 `consent-and-dpa.md` 權利執行）。
- **跨租戶測試**:migration 後自動跑 TC-SEC-01（以 tenant A 查 tenant B → 全空/403),見 `security/threat-model.md`。
