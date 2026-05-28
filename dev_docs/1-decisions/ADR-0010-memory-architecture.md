---
id: ADR-0010
title: AI Employee Memory Architecture
status: accepted
date: 2026-05-15
deciders: CTO
tier: 1
---

# ADR-0010 — AI 員工記憶架構

## Context

AEOS 的記憶相關決策散布在多份文件中：

| 面向 | 現有文件 | 已決策 |
|---|---|---|
| 對話儲存 | domain-model §2.3–2.4 | append-only Message + PII masking |
| Session 狀態 | SAD-v0.1, ADR-0002 | Redis 熱快取 |
| 知識庫 RAG | domain-model §2.6, db-schema | KnowledgeCard + pgvector |
| PII 治理 | ADR-0005 | 遮罩後才寫入，原文加密分離 |
| Tenant 隔離 | ADR-0007 | RLS + 應用層雙重防護 |
| Context window | QUOTA-001 §4.2 | 8K token 上限 + 自動摘要 |
| 生產凍結 | ADR-0002 | Frozen Runtime，不可自我學習 |

**缺少的是一份統一文件**，定義：
1. 記憶的分層模型（哪些層已建、哪些 Phase 2）
2. 寫入紀律（什麼值得記、什麼不記）
3. 記憶整理策略（合併、去重、衝突調解）
4. 記憶存取方式（Tool vs Infrastructure）
5. 向量檢索的使用邊界

### 外部研究參考

兩篇關鍵文章影響本 ADR 的設計方向：

**「Post-MCP 時代：Skills vs MCP」**（2026-03）：
- 中間結果存檔案、不佔 context window — 對應 AEOS Worker 非同步處理模式
- Skills 是純 Markdown，零維護 — 對應 AEOS Skill Registry 的 YAML/Git 設計

**「Agent Memory 不需要 Vector DB」**（2026-04）：
- 記憶是**治理問題**，不是儲存問題
- ChatGPT 只記 33 條事實；Claude Code 用檔案索引不用 vector
- Mastra 達 LongMemEval 94.87% 最高分 — 無向量檢索
- 記憶操作 = ADD / UPDATE / DELETE / NOOP，不只是保存
- 可推導內容不存；只記「未來三個月以上仍影響回答」的資訊
- 大多數專用 agent 的記憶量永遠不會達到需要向量檢索的規模

---

## Decision

### 1. 記憶四層模型

AEOS AI 員工的記憶分為五層，由短到長、由熱到冷：

```
┌────────────────────────────────────────────────────────┐
│ L1 — Working Memory（工作記憶）                         │
│ 當前對話的 context window                               │
│ 生命週期：單次 LLM 呼叫                                 │
│ 儲存：LLM prompt（in-memory）                           │
│ 狀態：已建 ✅（QUOTA-001 §4）                           │
├────────────────────────────────────────────────────────┤
│ L2 — Session Memory（會話記憶）                         │
│ 單次對話的完整歷程 + 暫存狀態                            │
│ 生命週期：Conversation 開始 → 結束 + 5min grace         │
│ 儲存：Redis（熱）+ PostgreSQL Message 表（持久）         │
│ 狀態：已建 ✅（SAD-v0.1, domain-model §2.3–2.4）       │
├────────────────────────────────────────────────────────┤
│ L2.5 — Session Summary（對話摘要記憶）⬅ Phase 1 新增    │
│ 對話結束時 AI 自動產生的結構化摘要                        │
│ 下次同一 end_user 來電時注入 L1 context                  │
│ 生命週期：跟隨 data_retention_days（預設 90 天）         │
│ 儲存：PostgreSQL Conversation.summary 欄位              │
│ 狀態：Phase 1 建置 ✅                                   │
├────────────────────────────────────────────────────────┤
│ L3 — Tenant Knowledge（租戶知識）                       │
│ 客戶的靜態知識 + 技能 + 政策                             │
│ 生命週期：手動管理（create / approve / archive）         │
│ 儲存：KnowledgeCard（pgvector）+ Skill（Git/YAML）      │
│ 狀態：已建 ✅（domain-model §2.5–2.6, ADR-0003）       │
├────────────────────────────────────────────────────────┤
│ L4 — Operational Memory（營運記憶）                     │
│ 跨對話累積的模式：常見問題分類、失敗模式、客戶偏好        │
│ 生命週期：自動累積 + 定期整理                            │
│ 儲存：待定（Phase 2）                                   │
│ 狀態：Phase 2 由 Compiler 3 負責 ❌                     │
└────────────────────────────────────────────────────────┘
```

#### L2.5 — Session Summary（Phase 1 新增）

**設計原則**：Frozen Runtime 凍結的是「AI 的行為（Skill / prompt）」，不是「AI 的記憶」。記下「發生了什麼事」與 append-only Message 本質相同，不屬於自我改進。

**為什麼需要**：
- 人類客服上班第一天就會在 CRM 記下客戶備註；AI 員工不該連這個能力都沒有
- 「這位客人上次問了退貨」不是推論，是事實 — 風險等級低
- 餐飲場景（過敏資訊）、長照場景（用藥紀錄）中，跨 session 記憶是**安全需求**
- 沒有 L2.5 的 AI 員工每次對話都從零開始，客戶體驗劣於人類新手

**記憶寫入的三類風險區分**：

| 類型 | 範例 | 風險 | Phase 1 |
|---|---|---|---|
| **事實觀察** | 「客戶問了退貨流程」 | 低 | **允許** — L2.5 自動寫入 |
| **模式推論** | 「這客戶偏好簡短回答」 | 中 | Phase 2（需標記信心度 + 失效條件） |
| **行為改變** | 「我應該改用更正式的語氣」 | 高 | **禁止** — Frozen Runtime 核心保護 |

**實作規格**：

```sql
-- Schema 變更
ALTER TABLE conversation ADD COLUMN summary TEXT;
-- summary 由 AI 於對話結束時產生
-- 已過 PII 遮罩（複用 ADR-0005 pipeline）
-- 不含原始對話內容，僅結構化摘要
```

**寫入規則**：
- 觸發時機：對話結束時（`ended_at` 被設定時），系統自動觸發
- 摘要格式：結構化純文字，≤ 200 token
- 只記事實觀察（「客戶問了什麼、結果如何」），不記推論（「客戶的情緒」）
- 過 PII 遮罩後才寫入（複用 ADR-0005 機制）
- Audit event：`summary.generated`，記錄觸發的 conversation_id

**讀取規則**：
- 下次同一 `end_user_pseudo_id` + 同一 `tenant_id` 開啟新對話時
- 系統自動撈取最近 N 筆 conversation summary（N = 3，可配置）
- 注入 L1 Working Memory 的 system prompt 區段
- Token 預算：≤ 600 token（3 筆 × 200 token）
- 從 QUOTA-001 §4.1 的 system prompt 1,000 token 配額中扣除

**不做的事**：
- 不做跨 tenant 的 summary 共享
- 不做 summary 的向量化或語意搜尋
- 不讓 AI 員工主動修改或刪除 summary（append-only 精神）
- 不記推論或情緒判斷

**保留期限**：跟隨 `Tenant.data_retention_days`（預設 90 天），summary 隨 conversation 一起過期清除

#### L1 → L2 的銜接（Context Window 管理）

當 L1 空間不足（對話歷史超過 8K token）：
- 自動摘要前 N 輪，保留最近 5 輪原文（QUOTA-001 §4.2）
- 摘要結果存回 L2（Redis session + Message 表標記 `_summarized`）
- RAG retrieval 從 L3 注入 top-5 chunks，每 chunk ≤ 500 token

#### L3 的三分類（既有，不改）

| 類型 | 範例 | 記憶歸屬 | 存取方式 |
|---|---|---|---|
| Static Knowledge | FAQ、產品規格、SOP | KnowledgeCard + RAG | 被動：RAG pipeline 自動注入 |
| Policy Knowledge | 退貨規則、合規限制 | Skill YAML + Rule Engine | 被動：Skill 內建 |
| Dynamic Knowledge | 訂單狀態、庫存 | Tool（API Adapter） | 主動：Tool call at runtime |

**記憶（L4）不屬於以上三類** — 它是「從對話中習得的模式」，與「預先建立的知識」本質不同。Phase 2 再定義其 aggregate 與存取機制。

**L2.5 Session Summary 屬於 Static Knowledge 的變體** — 它是結構化事實，不是習得模式。差異在於：L3 由人類手動建立，L2.5 由系統在對話結束時自動產生。

#### L4 不做的理由（Phase 1）

- 單一 tenant 的 Pilot 期對話量不足以累積有意義的模式
- L4 涉及「模式推論」（風險中），需要信心度標記和失效條件 — Phase 1 缺少這些機制
- 缺少 Evaluation Service 來驗證記憶品質（Phase 2 才建）
- 外部研究佐證：大多數專用 agent 永遠不會達到需要跨對話記憶的規模
- **注意**：L2.5（事實觀察）不受此限制 — 它已在 Phase 1 啟用

#### L4 的 Phase 2 啟動條件

同時滿足以下**全部**條件時，啟動 L4 設計：
1. 單一 tenant 累積 > 10,000 對話
2. Training Room 已上線（Compiler 3 可用）
3. Evaluation Service 可量化記憶品質（FCR 提升、hallucination 不惡化）
4. Policy Engine 可控制記憶的讀寫權限

---

### 2. 向量檢索策略

| 對象 | 是否向量化 | 理由 |
|---|---|---|
| KnowledgeCard（L3） | **是** — pgvector + OpenAI embedding | 知識量可達數百張卡片，語意搜尋有價值 |
| 對話歷史（L2） | **否** | Phase 1 對話量不到需要相似度檢索的規模 |
| 營運記憶（L4） | **Phase 2 評估** | 依累積量決定：結構化查詢優先，向量化作為 fallback |
| Audit Event | **否** | 結構化查詢（tenant_id + event_type + 時間範圍）足夠 |

**原則**：向量檢索是「記憶量超過結構化查詢能力時」的升級手段，不是預設選擇。

---

### 3. 寫入紀律

記憶寫入依風險等級分層治理。Frozen Runtime 保護的是「行為改變」，不是「事實記錄」。

| 寫入路徑 | 觸發者 | 寫入層 | 治理 | Phase 1 |
|---|---|---|---|---|
| 對話 Message 追加 | 系統自動 | L2 | PII 遮罩（ADR-0005）→ append-only | ✅ |
| **對話結束摘要** | **系統自動（AI 產生）** | **L2.5** | **PII 遮罩 → ≤ 200 token → 只記事實 → audit** | **✅** |
| KnowledgeCard 建立/更新 | 人類管理員 | L3 | draft → approve 流程 | ✅ |
| Skill 版本發布 | 人類管理員 | L3 | Quality Gate（test_pass_rate ≥ 0.80） | ✅ |
| Audit Event | 系統自動 | 橫跨 | append-only，永不刪改 | ✅ |

**Phase 1 禁止的寫入**：
- AI 員工修改自己的 Skill prompt 或 persona_config（行為改變 — Frozen Runtime 核心）
- AI 員工自行安裝新 Skill 或 Tool（權限擴張）
- AI 員工寫入推論或情緒判斷到 L2.5（只允許事實觀察）

**Phase 2 新增路徑**（L4）：
- Compiler 3 從對話 log 抽取模式 → 人類 Review → 寫入 L4
- 寫入紀律（來自外部研究）：
  - 只記「未來三個月以上仍影響回答」的資訊
  - 可推導內容不存（程式碼結構、log、可重新計算的統計）
  - 區分：**明確事實** vs **推論觀察** vs **待驗證假設**
  - 推論需附：證據來源、信心度、失效條件

---

### 4. 記憶整理策略

#### Phase 1：人工整理

| 整理動作 | 觸發者 | 頻率 |
|---|---|---|
| KnowledgeCard 過期（valid_until） | 系統提醒 + 人類審核 | 持續 |
| KnowledgeCard 內容更新 | 人類管理員 | 按需 |
| 對話歷史清除（超過 data_retention_days） | 系統自動 | 每日 |
| Audit Event | 永不整理 | — |

#### Phase 2：Compiler 3 自動整理

背景處理流程（Hot path vs Background 的選擇 = **Background**）：

```
Production 對話 log
  ↓ (deidentified, batched)
Compiler 3 (background worker)
  ├── 抽取：常見問題模式、失敗分類
  ├── 合併：去重、衝突調解
  ├── 修剪：降權過時模式、刪除無效推論
  └── 產出：L4 記憶候選
  ↓
人類 Expert Review
  ↓
寫入 L4 / 更新 L3 KnowledgeCard / 更新 Skill
```

**衝突調解規則**（不直接覆蓋，條件化更新）：
- 舊記憶：「客戶通常問營業時間」
- 新觀察：「最近兩週客戶主要問退貨流程」
- 更新為：「客戶常問營業時間；近期退貨流程詢問量上升（2026-05 觀察）」
- 標記失效條件：若退貨詢問佔比回降至 < 10%，恢復舊權重

---

### 5. 記憶存取方式：Infrastructure，非 Tool

Phase 1 決策：**記憶存取是 Infrastructure**，不暴露為 Tool。

| 方式 | 優點 | 缺點 | Phase 1 選擇 |
|---|---|---|---|
| **Infrastructure**（內建於 RAG pipeline） | 治理簡單、無額外 policy 需求、audit 自動覆蓋 | 彈性低 | **選此** |
| **Tool**（AI 員工主動呼叫 `retrieve_memory`） | 彈性高、可按需查詢 | 需 Tool Gateway policy、需防止記憶污染 | Phase 2 評估 |

**Phase 2 暴露為 Tool 的前提條件**：
1. Tool Gateway + Policy Engine 已上線
2. 有 `memory.read` / `memory.write` 的 RBAC 權限控制
3. 所有記憶 Tool 呼叫過 Audit（ToolInvocation 記錄）
4. 記憶寫入需 human-in-the-loop approval（防止 Knowledge Pollution）

---

### 6. Knowledge Pollution 防護

風險：AI 員工將 Customer A 的對話模式自動寫入共享記憶，汙染 Customer B 的回答。

| 層級 | 防護措施 | Phase |
|---|---|---|
| Tenant 隔離 | RLS + tenant_id（ADR-0007） | 1 ✅ |
| Frozen Runtime | 生產 agent 不可寫入 L3/L4，不可改行為 | 1 ✅ |
| L2.5 範圍限制 | 只記事實觀察，不記推論；≤ 200 token；過 PII 遮罩 | 1 ✅ |
| L2.5 讀取隔離 | summary 帶 tenant_id + end_user_pseudo_id，只對同一終端用戶可見 | 1 ✅ |
| 寫入審核 | L3 需人類 approve；L4 需 Expert Review | 1(L3) / 2(L4) |
| 內容隔離 | L4 記憶帶 `tenant_id`，跨 tenant 不可互讀 | 2 |
| 匿名聚合 | 跨 tenant 統計只做匿名化聚合（opt-in） | 3+ |

---

## Consequences

### 正向

- 記憶架構有統一定義，新 engineer 加入時有單一參考點
- L2.5 讓 Phase 1 AI 員工具備跨 session 事實記憶，客戶體驗不劣於人類新手
- Frozen Runtime 定義更精確：凍結「行為」而非「記憶」，避免過度保護
- 向量檢索策略符合外部最佳實踐：不過度使用，不提前引入複雜度
- 三類風險分層（事實/推論/行為）讓未來 L4 的啟用有清晰的升級路徑

### 負向

- L2.5 增加 Phase 1 少量開發工作（schema 變更 + 摘要生成 + 注入邏輯）
- 摘要品質依賴 LLM — 若 LLM 在摘要中產生幻覺，會污染未來對話
- Context window 摘要演算法未在本 ADR 定義（需額外設計文件）
- L4 設計延後可能導致 Phase 2 設計壓力集中

### 風險與緩解

| 風險 | 緩解 |
|---|---|
| L2.5 摘要產生幻覺 | 限制只記事實（「客戶問了 X」）；≤ 200 token 限制幻覺空間；audit 可追溯 |
| L2.5 摘要洩漏 PII | 複用 ADR-0005 PII 遮罩 pipeline；summary 不含原始對話 |
| L2.5 摘要消耗 LLM token 預算 | 摘要產生用 T1 模型（gpt-4o-mini）；≤ 200 token output；成本可忽略 |
| L2.5 注入佔用 context window | 最多 3 筆 × 200 token = 600 token；從 system prompt 1,000 配額扣除 |
| Context 摘要品質影響 FCR | QUOTA-001 的保留最近 5 輪策略 + Phase 2 摘要演算法優化 |
| Phase 2 啟動時 L4 設計從零開始 | 本 ADR 已預定方向（Compiler 3 + background + human review） |
| 記憶整理成為運維負擔 | Phase 1 記憶量低（只有 L3 手動管理 + L2.5 自動過期）；Phase 2 自動化 |

---

## Alternatives Considered

| 方案 | 為何不選 |
|---|---|
| 從 Day 1 建 L4 + 向量化對話 | L4 涉及模式推論（風險中），需 Evaluation Service 驗證；Phase 1 對話量不足 |
| Phase 1 完全不做跨 session 記憶 | 客戶體驗劣於人類新手；餐飲/長照場景中跨 session 記憶是安全需求 |
| 用 Vector DB（Qdrant/Weaviate）取代 pgvector | 增加基礎設施複雜度；pgvector 對 Phase 1 規模綽綽有餘 |
| 暴露 Memory as Tool（Phase 1） | 缺少 Policy Engine 防護；Knowledge Pollution 風險高 |
| 用 MCP Server 做記憶存取 | AEOS 用 Tool Gateway，不走 MCP；MCP 的 token 消耗高（外部研究佐證） |
| 完全不做 L4（永遠人工管理） | 限制 Phase 2+ 的產品進化能力；Training Room 需要 L4 支撐 |

---

## Implementation Notes

### Phase 1 變更（L2.5 Session Summary）

1. **DB schema**：`ALTER TABLE conversation ADD COLUMN summary TEXT;`
2. **摘要產生**：對話結束時觸發 Worker job → T1 模型產生摘要 → PII 遮罩 → 寫入 summary 欄位
3. **摘要注入**：新對話開啟時，查詢同一 `end_user_pseudo_id` 最近 3 筆 summary → 注入 system prompt
4. **Audit**：每次 summary 產生記錄 `audit_event(event_type='summary.generated')`
5. **domain-model.md**：已新增 §3.5 Memory Layer Mapping（交叉引用）
6. **QUOTA-001 §4.2**：已加引用本 ADR
7. **db-schema.md**：需新增 `conversation.summary` 欄位定義

### Phase 2 變更

- 啟動 L4 時，需新增 ADR-0010-supplement 或 supersede 本 ADR
- L2.5 可演進為帶「推論」能力（需加信心度 + 失效條件欄位）

---

## Related

- ADR-0002 — Agent Runtime（Frozen Runtime 原則）
- ADR-0005 — Data Retention & PII（記憶安全邊界）
- ADR-0007 — Tenant Isolation（記憶隔離基礎）
- QUOTA-001 §4.2 — Context window 管理
- domain-model.md §2.3–2.6 — Conversation / Message / KnowledgeCard aggregates
- 02-product-architecture.md §9–10 — SkillOps Pipeline + Training Room
- visual-prompts/02-sa-process-flow.md — Compiler 3 在流程中的位置
