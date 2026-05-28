---
id: 0TO1-02-MVG-BUILD-SHEET
title: MVG Build Sheet — 最薄可建構垂直切片
status: canonical
type: build-spec
created: 2026-05-28
supersedes_for_build: [PRD-001, SAD-v0.1, API-001, db-schema, MC-001~011, PROJ-001]
handoff_ready: true
---

# MVG Build Sheet — 最薄可建構垂直切片

> 這份是 **coding agent 的 handoff**。讀完能直接開工。
> 它把 PRD-001（已經不錯）再套一次 Elon 五步法——**連 PRD-001 都還太厚**。

---

## 1. 第一性原理：什麼是「最薄切片」

PRD-001 描述了 7 天流程的 6 大功能（KB ingest / config / test set UI / draft mode / canary / audit）。問每一個：**這是證明核心賭注 B1 必需的，還是只是『完整的客服產品該有的』？**

最致命的賭注是 **B1：一坨真實混亂知識，能在數天內變成可用回覆。** 證明它，只需要這條鏈路跑通一次：

```
真實客戶訊息 (LINE)
   → 檢索該客戶的知識 (RAG)
   → Claude 產生草稿回覆
   → 人類 approve / edit / reject (Draft Mode)
   → 全程進 audit log
   → 量一個數字：草稿採用率
```

**這一條鏈路 = 整個 MVG。** 採用率這個數字同時證偽 B1（知識可不可用）和 B2（治理介入成本划不划算）。其他全部可以晚點加。

---

## 2. 從 PRD-001 刪掉什麼（第 2 步：刪除）

| PRD-001 功能 | 切片決定 | 理由 |
|---|---|---|
| Canary 10/50/100% 三檔 toggle | **刪** | 切片永遠停在 Draft Mode（人類審每一則）。先證明草稿好用，再談自動發 |
| Confidence threshold 自動 fallback | **刪** | Draft Mode 下人類審全部，沒有「自動發」就不需要信心閾值 |
| Web chat channel 選項 | **刪** | 只做 LINE。「LINE 或 Web 二選一」→ 直接選 LINE，刪掉抽象 |
| Test set 共寫 **UI**（F-TST-01~04） | **簡化** | 測試集留著（是 §3 validation 的量尺），但用 **CSV + 一支 script** 跑，不做 UI |
| KB ingest 的 PDF/DOCX/URL 全格式 | **簡化** | 切片只收 **Markdown / plain text 貼上**。PDF/DOCX 解析晚點加 |
| 自動切 title+summary、KC draft 審核 UI | **簡化** | 固定 chunk + overlap，存進去就好。KC 審核 UI 晚點加 |
| Email daily digest（F-AUD-03） | **刪** | 切片看 DB / 一個簡單列表頁 |
| nanobot / agent runtime 框架（ADR-0002 的實作） | **延後** | 回答一則訊息不需要 agent framework。切片用**一支直線 Python service**。Frozen Runtime 的**原則**保留（見 §5），框架實作 Phase 2 |
| 多 Skill / Skill registry / Skill 版本化 UI | **延後** | 切片只有 1 個寫死的 prompt（= 1 個 skill v1）。registry 晚點加 |

> **Linus 式裁決**：上面每一個「刪 / 延後」都消滅了一個還不存在的特殊情況。切片沒有「canary 階段 vs draft 階段」的 if 分支——**永遠 draft**。沒有「LINE vs web」的 if 分支——**永遠 LINE**。好品味。

---

## 3. 切片要建什麼（第 3 步：簡化後的最小集）

### 3.1 一支單體 service（不是微服務）

```
aeos-mvg/  (單一 Python 服務，FastAPI)
├── webhook.py     # LINE webhook 入口（HMAC 驗簽 → 入 queue）
├── ingest.py      # 貼上 markdown → chunk → embed → 存 pgvector
├── draft.py       # 檢索 + Claude 產草稿 + 存 draft + 通知 expert
├── review.py      # expert approve/edit/reject 介面（最簡 web 頁 or LINE）
├── audit.py       # 每一步寫 audit log
├── killswitch.py  # 一鍵全停（讀一個 flag，30 秒內生效）
└── eval.py        # 吃 testset.csv，跑全 50 題，印 pass rate
```

> 11 份 MC 契約描述的 11 個 bounded context（audit / training-room / evaluation / tenant / skill / tool / admin / rag / runtime / conversation / channel），在切片裡就是**上面 7 個檔案**。等真的需要拆，再拆。**不要先拆。**

### 3.2 最小資料模型（4 張表，不是 db-schema.md 的全集）

```sql
-- 切片只需要這 4 張。其餘 db-schema.md 的表全部延後。
tenant         (id, name)                              -- 1 筆：pilot 客戶
knowledge_chunk(id, tenant_id, text, embedding, source) -- RAG 來源
conversation   (id, tenant_id, line_user_id, created_at)
message        (id, conversation_id, role, text,        -- role: user/draft/sent
                draft_text, decision, decided_by,        -- decision: approve/edit/reject
                used_chunks jsonb, model, created_at)    -- audit 全在這欄
```

`message` 這張表同時是對話紀錄 + audit log + 訓練素材（approve/edit/reject 就是 §5 的離線學習回流）。**一張表幹三件事，消滅資料複製。**

### 3.3 外部依賴（垂直整合邊界，對映北極星 Part 4）

| 元件 | 自製/外包 | 切片選擇 |
|---|---|---|
| LLM | **外包但抽象** | Claude API（`claude-haiku-4-5` 跑檢索分流 + `claude-opus-4-7` 產草稿）。包一層 `llm.py` 介面，換模型不改業務碼 |
| 向量檢索 | 外包 | Postgres + pgvector（別上 Pinecone，過早） |
| Channel | 外包 | LINE Messaging API |
| 基礎設施 | 外包 | 單台 VM（Hetzner，COST-MODEL 已估 ~$50/月）。**別上 K8s** |
| 記憶/治理/草稿閘門 | **自製** | 就是上面的 service，這是護城河 |

---

## 4. 開工順序（第 4 步：加速 = 最短跑通路徑）

按「最快看到一則真實草稿」排序，不按「架構分層」排序：

```
W1  ① ingest.py：貼上 1 個真客戶的 markdown → 存 pgvector。手動驗檢索回來對不對。
    ② draft.py（離線版）：給一個問題字串 → 檢索 → Claude 產草稿 → print。
       ← 這一步就能跑 eval.py 對 50 題測試集，先打 B1。不用等 LINE。
W2  ③ webhook.py：LINE 收訊（HMAC 驗簽）→ 存 message(role=user)。
    ④ 串 ②③：收到 LINE 訊息自動產草稿存 DB + 通知 expert。
    ⑤ review.py：expert approve/edit/reject；approve→LINE 回發；全進 audit。
    ⑥ killswitch.py：一個 flag 全停。
W3  ⑦ 接真實 pilot 客戶的真知識 + 真 LINE，跑 Draft Mode。開始量採用率。
```

**第 1 週結束就能用 `eval.py` 對測試集打 B1**——這是最致命賭注，最早驗證。LINE 串接（W2）甚至可以晚於知道「知識到底可不可用」。

---

## 5. 不可違反的鐵律（從既有體系 KEEP 的護欄）

切片再薄，這幾條不准省（對映 ledger 的 KEEP 項）：

```
1. 學習/生產分離 (ADR-0002 Frozen Runtime 原則)
   → 上線那份配置(prompt+KB快照)是凍結的。approve/edit/reject 資料存起來，
     供「離線」改版用，不准「線上即時學習」改變員工行為。

2. 草稿模式強制 (PRD F-DFT)
   → 切片階段 AI 永不自動發訊。人類審每一則。這是 B2 的安全網。

3. Kill switch 必存在 (PRD F-CAN-03)
   → 30 秒內全停。寫程式第一週就要有，不是上線前才補。

4. Audit 全覆蓋 (PRD F-AUD)
   → 每則 message 記：用了哪些 chunk、哪個 model、人類決定。存在 message 表。

5. PII 與真實資料紅線 (ADR-0005 + SEC-001 §6.1 抽項)
   → 碰真客戶資料前：LINE webhook HMAC 驗簽、secrets 不進 git、
     DB 連線 TLS、tenant_id 強制 scope（單租戶也要寫對，未來才不用重構）。
   → 簽 pilot 前先簽 DPA (LEGAL-001)。
```

> 注意這 5 條的成本都極低，但都是「出事就致命」的。Elon 五步法第 2 步刪的是**冗餘**，不是**安全網**。分清楚這兩者是好品味的核心。

---

## 6. 明確不做（第 1 步：質疑掉的需求）

切片**明文不做**，做了就是違反這份 build sheet：

```
× 微服務拆分（11 MC 契約）        × Skill registry / 多 skill / 版本化 UI
× Canary 流量分配                 × 信心閾值自動發
× Web chat / 多 channel           × 多語言
× Email digest / Eval Dashboard   × 訂單寫入（只查不寫）
× 多租戶 / 跨租戶                  × K8s / 完整 observability stack
× nanobot / agent framework       × OpenAPI / 完整 ERD / domain-model 全集
× 主動推送                        × 自動 KB 爬取 / PDF-DOCX 解析
```

每一項的「何時加回」見 [`01-delete-ledger.md`](./01-delete-ledger.md) §7。

---

## 7. 交付定義（這份 build sheet 算完成，當）

```
□ eval.py 對真客戶 50 題測試集印出 pass rate
□ 一則真實 LINE 訊息 → 草稿 → expert approve → LINE 回發，全鏈路跑通一次
□ message 表能完整還原任一則對話的：知識來源 + model + 人類決定
□ kill switch 實測 30 秒內全停
□ 跑 ≥ 1 個真實 pilot 客戶，連續量 ≥ 2 週採用率
```

採用率這個數字交給 [`03-validation-and-kill.md`](./03-validation-and-kill.md) 判生死。
