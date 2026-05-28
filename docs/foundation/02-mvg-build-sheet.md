---
id: FND-02-MVG-BUILD-SHEET
title: MVG Build Sheet — 最薄可建構垂直切片
status: canonical
type: build-spec
handoff_ready: true
---

# MVG Build Sheet — 最薄可建構垂直切片

> 這份是 **coding agent 的 handoff**，讀完能直接開工。對映賭注 [`00-the-bet.md`](./00-the-bet.md) 的 B1。

---

## 1. 最薄切片 = 一條鏈路

最致命的是 B1：一坨真實混亂知識，能在數天內變成可用回覆。證明它只需這條鏈路跑通一次：

```
真實客戶訊息 (LINE)
   → 檢索該客戶的知識 (RAG)
   → Claude 產生草稿回覆
   → 人類 approve / edit / reject (Draft Mode)
   → 全程進 audit log
   → 量一個數字：草稿採用率
```

**這一條 = 整個 MVG。** 採用率同時證偽 B1（知識可不可用）與 B2（治理介入划不划算）。其他全部晚點加。

## 2. 一支單體 service（不是微服務）

```
aeos-mvg/  (單一 Python 服務，FastAPI)
├── webhook.py     # LINE webhook 入口（HMAC 驗簽 → 入 queue）
├── ingest.py      # 貼上 markdown → chunk → embed → 存 pgvector
├── draft.py       # 檢索 + Claude 產草稿 + 存 draft + 通知 expert
├── review.py      # expert approve/edit/reject 介面（最簡 web 或 LINE）
├── audit.py       # 每一步寫 audit log
├── killswitch.py  # 一鍵全停（讀一個 flag，30 秒內生效）
└── eval.py        # 吃 testset.csv，跑全 50 題，印 pass rate
```

> 未來的 11 個 bounded context（audit/training-room/evaluation/tenant/skill/tool/admin/rag/runtime/conversation/channel）在切片裡就是上面 7 個檔案。**等真的需要拆，再拆。不要先拆。**

## 3. 最小資料模型（4 張表）

```sql
tenant         (id, name)                                  -- 1 筆：pilot 客戶
knowledge_chunk(id, tenant_id, text, embedding, source)    -- RAG 來源
conversation   (id, tenant_id, line_user_id, created_at)
message        (id, conversation_id, role, text,           -- role: user/draft/sent
                draft_text, decision, decided_by,          -- decision: approve/edit/reject
                used_chunks jsonb, model, created_at)      -- audit 全在這欄
```

`message` 同時是對話紀錄 + audit log + 訓練素材（approve/edit/reject 就是離線學習回流）。**一張表幹三件事，消滅資料複製。**

## 4. 外部依賴

| 元件 | 自製/外包 | 切片選擇 |
|---|---|---|
| LLM | 外包但抽象 | Claude API（`claude-haiku-4-5` 檢索分流 + `claude-opus-4-7` 產草稿）；包一層 `llm.py`，換模型不改業務碼 |
| 向量檢索 | 外包 | Postgres + pgvector（別上 Pinecone，過早） |
| Channel | 外包 | LINE Messaging API |
| 基礎設施 | 外包 | 單台 VM（~$50/月）。**別上 K8s** |
| 記憶/治理/草稿閘門 | **自製** | 上面的 service，這是護城河 |

## 5. 開工順序（按「最快看到一則真實草稿」排，不按架構分層）

```
W1  ① ingest.py：貼 1 個真客戶 markdown → 存 pgvector，手動驗檢索對不對
    ② draft.py（離線版）：給問題字串 → 檢索 → Claude 產草稿 → print
       ← 這步就能跑 eval.py 對 50 題測試集打 B1，不用等 LINE
W2  ③ webhook.py：LINE 收訊（HMAC 驗簽）→ 存 message(role=user)
    ④ 串 ②③：收到 LINE 訊息自動產草稿存 DB + 通知 expert
    ⑤ review.py：expert approve/edit/reject；approve→LINE 回發；全進 audit
    ⑥ killswitch.py：一個 flag 全停
W3  ⑦ 接真實 pilot 客戶的真知識 + 真 LINE，跑 Draft Mode，開始量採用率
```

**W1 結束就能用 `eval.py` 打 B1**——最致命賭注最早驗，LINE 串接甚至可晚於「知道知識到底可不可用」。

## 6. 不可違反的鐵律（成本極低但出事致命，五步法刪的是冗餘不是安全網）

```
1. 學習/生產分離：上線配置(prompt+KB快照)凍結；approve/edit/reject 存起來供「離線」改版，不准線上即時學習改行為
2. 草稿模式強制：切片階段 AI 永不自動發訊，人類審每一則
3. Kill switch：30 秒內全停，第一週就要有
4. Audit 全覆蓋：每則記 用了哪些 chunk + 哪個 model + 人類決定
5. PII 紅線：HMAC 驗簽 / secrets 不進 git / DB 連線 TLS / tenant_id 強制 scope（單租戶也要寫對）；簽 pilot 前先簽 DPA
```

## 7. 明確不做（做了就是違反這份 build sheet）

```
× 微服務拆分          × Skill registry / 多 skill / 版本化 UI
× Canary 流量分配     × 信心閾值自動發
× Web chat / 多 channel  × 多語言
× Email digest / Dashboard  × 訂單寫入（只查不寫）
× 多租戶 / 跨租戶     × K8s / 完整 observability stack
× agent framework     × OpenAPI / 完整 ERD / domain-model 全集
× 主動推送            × 自動 KB 爬取 / PDF-DOCX 解析
```

## 8. 交付定義（這份 build sheet 算完成，當）

```
□ eval.py 對真客戶 50 題測試集印出 pass rate
□ 一則真實 LINE 訊息 → 草稿 → expert approve → LINE 回發，全鏈路跑通一次
□ message 表能完整還原任一則對話的：知識來源 + model + 人類決定
□ kill switch 實測 30 秒內全停
□ 跑 ≥ 1 個真實 pilot 客戶，連續量 ≥ 2 週採用率
```

採用率交給 [`03-validation-and-kill.md`](./03-validation-and-kill.md) 判生死。
