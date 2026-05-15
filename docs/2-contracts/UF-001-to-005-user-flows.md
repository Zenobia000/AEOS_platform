---
id: UF-001..UF-005
title: User Flows — 5 個關鍵使用流程
status: active
type: user-flow
created: 2026-05-14
last-synced-with: efb63b3efff9a280e178f46124f39db8d0141b54
owner: CTO
tier: 2
related: [BF-001, PRD-001]
---

# User Flows v0 — UF-001 到 UF-005

> 從 PRD-001 §4 抽出的 5 個關鍵互動流程。每個 UF 對應 1 個 SF（系統時序）、1 個 AC（驗收）、可能跨多個 API。

## UF-001 — Expert 上傳 KB → KC draft → review → approve

**Actor**：Expert（客戶端領域專家）
**Goal**：把客戶現有的 FAQ / SOP 轉成 AI 可用的 Knowledge Cards
**Pre-condition**：Tenant 已建、Expert 有 login

| # | 動作 | 系統反應 |
|---|---|---|
| 1 | 在「KB 管理」頁按「+ 上傳」 | 顯示上傳區（PDF/DOCX/MD/URL） |
| 2 | 上傳檔案或貼 URL | 顯示 "Ingest 中..." progress |
| 3 | 等待（< 5 分鐘） | 完成後 redirect 到 "KC Draft List"，列出本次產的 KC |
| 4 | 逐張 review KC：標題、內容、tags | 編輯框可修改；右側顯示原文 source 段落 |
| 5 | 按 "Approve" | KC status: draft → approved；列表標記綠勾 |
| 6 | 按 "Archive"（如為錯誤產出） | KC status: draft → archived；不會被檢索 |

**Post-condition**：至少 5 張 KC `status=approved`；準備進 UF-002

**Alt flows**：
- **A1 切片過細**：點 "merge with next" → 把連續 N 張 KC 合併
- **A2 切片過粗**：點 "split here" → 在 cursor 位置切兩張
- **A3 原文錯誤**：點 "edit raw source" → 修改 markdown → 重切

**Non-functional**：
- 單檔上傳 ≤ 20 MB
- Ingest p95 < 3 分鐘 / 100 頁 PDF
- 跨檔案不可衝撞（並發 ingest 不會壞 KC 順序）

**Links**：`SF-001`, `API-001 §KB`, `AC-001`

---

## UF-002 — Expert 共寫 50 題 test set + 跑測試

**Actor**：Expert
**Goal**：建立可重跑的 test set 作為 AI 品質 gate
**Pre-condition**：UF-001 完成（已有 ≥ 5 張 approved KC）+ Employee draft 已建

| # | 動作 | 系統反應 |
|---|---|---|
| 1 | 進入「Test Set 編輯器」 | 空白表格 50 行（question, expected_outcome, expected_keywords） |
| 2 | 逐題填寫題目 | 自動 save draft（每 5 秒） |
| 3 | 對每題選 `accept` / `decline` / `handoff` | 不選 → 預設 `accept` |
| 4 | 可選：填 expected_keywords（含哪些字串視為通過） | 留空 → 用 LLM judge |
| 5 | 完成後按 "Run Test" | 進度條：對 Employee 當前配置跑 50 題 |
| 6 | 看結果頁：pass rate + 逐題 detail | 每題：AI 回答 vs expected outcome；失敗題紅標 |
| 7 | 失敗題：點 "Add KC to fix this" | 跳到 UF-001 KC 編輯，回填上下文 |

**Post-condition**：Test pass rate ≥ 70%（Day 5 gate）

**Alt flows**：
- **A1 LLM judge 不準**：手動 mark "actually correct"，下次 re-run 忽略此題的自動判定
- **A2 想跑單題**：每題行末有 "Re-run this" 按鈕

**Non-functional**：
- Run 50 題總時間 ≤ 5 分鐘
- 每題結果可逐筆 view（含 LLM raw response + retrieved KCs）

**Links**：`SF-002`, `API-001 §TestSet`, `AC-002`

---

## UF-003 — Draft Mode：LINE 收訊 → Expert approve → 送出

**Actor**：終端使用者（end user）+ Expert（審核）
**Goal**：上線前讓 Expert 審核每一則 AI 草稿，確認品質才放行
**Pre-condition**：Test pass rate ≥ 70%、LINE webhook 已 setup

| # | Actor | 動作 | 系統反應 |
|---|---|---|---|
| 1 | End User | 在 LINE 傳訊息給 OA | LINE webhook 進 AEOS |
| 2 | AEOS | 收訊息 → 跑 RAG + LLM → 產 draft | message status: `draft_pending` |
| 3 | AEOS | 推送通知給 Expert | LINE Notify / web push |
| 4 | Expert | 開「Draft Inbox」頁 | 顯示 pending list（最舊在上） |
| 5 | Expert | Click 一則 → 看 user message + AI draft + 引用的 KC | 三欄式：user msg / draft / KC sources |
| 6 | Expert | 選一：(a) Approve & Send / (b) Edit & Send / (c) Reject & Take Over | 對應動作下 §6.a/b/c |
| 6a | AEOS | Approve：直接送 LINE Push 給 end user | message status: `sent`；audit `expert_approved` |
| 6b | AEOS | Edit：Expert 在 textarea 改寫 → 送出 | message status: `sent_edited`；audit `expert_edited` 含 diff |
| 6c | AEOS | Reject：標記人工接手 | message status: `expert_takeover`；Expert 自行在 LINE 回（透過 AEOS 介面） |

**Post-condition**：End user 在 ≤ 60 秒內收到回覆

**Alt flows**：
- **A1 過載**：Pending > 20 → 警示 Expert；超時 5 分鐘自動推 fallback 訊息「客服稍後回覆」
- **A2 Expert 離線**：超時 10 分鐘 → fallback「客服稍後回覆」+ 標 `escalation_needed`

**Non-functional**：
- Webhook ACK ≤ 1 秒（背景 enqueue 處理）
- Draft 生成 p95 ≤ 5 秒
- Expert 通知 latency ≤ 2 秒
- 每則 approve/edit/reject 進 audit log

**Links**：`SF-003`, `API-002 LINE`, `AC-003`

---

## UF-004 — Canary Live：信心閾值自動 fallback

**Actor**：End user + AEOS System +（背景）Expert
**Goal**：逐步開放自動回覆，低信心題仍走人工
**Pre-condition**：UF-003 Draft Mode 過關（override < 50%）

| # | 動作 | 系統反應 |
|---|---|---|
| 1 | CTO 在 Admin 將 `auto_reply_pct` 設 10% | 系統 hash(conversation_id) % 100 < 10 走自動 |
| 2 | End User 傳訊息 | AEOS 跑 RAG + LLM → 產 reply + confidence score |
| 3a | 若 confidence ≥ 0.75 **且**在 auto 流量內 | 直接 LINE Push 送出；audit `auto_sent` |
| 3b | 若 confidence < 0.75 **或**不在 auto 流量內 | 進 Draft Mode（同 UF-003） |
| 4 | CTO 每日 monitor dashboard | 自動 vs Draft 分布、override 率、incident |
| 5 | 滿足條件（24h 無 P0）→ 將 `auto_reply_pct` 提升到 50% → 100% | 同上機制，閾值不變 |

**Post-condition**：100% Live、後續仍依 confidence 動態 fallback

**Alt flows**：
- **A1 偵測 anomaly**：1 小時內 P0 ≥ 1 / 客戶投訴 → 自動降回 Draft Mode（不需人工）
- **A2 客戶要求暫停**：見 UF-005

**Non-functional**：
- Auto reply p95 latency ≤ 3 秒（含 LLM）
- Confidence score 校正：每 24h 用實際 expert override 更新閾值（Phase 2 自動化；Phase 1 手動 review）

**Links**：`SF-004`, `API-001 §Conversation`, `AC-004`, `NFR-001`

---

## UF-005 — 緊急 Kill Switch

**Actor**：CTO / Onboarding Eng / 客戶 Admin
**Goal**：≤ 30 秒內把 AI 完全停下、所有訊息走人工
**Pre-condition**：Employee 已 Live；CTO/客戶 Admin 有權限

| # | 動作 | 系統反應 |
|---|---|---|
| 1 | 進 Admin → "Emergency Controls" | 顯示紅色大按鈕「DISABLE AI」+ 二次確認 |
| 2 | Click → 輸入原因（free text） | 確認 modal：「將停止 AI 自動回覆，並切到人工。確定？」 |
| 3 | Confirm | 系統設 Employee.status = `paused`；audit `emergency_disable` 含原因、actor、時間 |
| 4 | 即時生效 | 新進訊息全部標 `expert_takeover`；不跑 LLM；前端推給 Expert |
| 5 | 系統推 Slack/Email/SMS 給 CEO + CTO | 通知內容含 actor、原因、時間 |
| 6 | 處理後，CTO 進 Admin → "Re-enable AI" | 二次確認 → status: paused → live |

**Post-condition**：AI 停或恢復，全程審計可追

**Alt flows**：
- **A1 系統自動觸發**：UF-004 §A1 anomaly 偵測 → 自動降回 Draft Mode（**非**完全停，仍可走 Expert review）
- **A2 全 tenant 緊急**：AEOS 內部 super-admin 可一鍵停一個 tenant（合約糾紛、嚴重 incident）

**Non-functional**：
- 從點擊到生效 ≤ 30 秒（含 webhook 立即攔截）
- 期間進來的訊息**絕不丟失**（仍進 conversation 表，僅不自動回）
- Audit log 必含原因、actor、時間戳

**Links**：`SF-005`, `API-001 §Admin`, `AC-005`

---

## 共通約束

- 所有 UF 上的每個動作 → 必發 `AuditEvent`（見 `domain-model.md` §2.8）
- 所有狀態變更 → 對應 `Domain Event`（見 `domain-model.md` §3）
- UF 不變期間：本 Phase 1 凍結；要改寫 CIA（見 `.claude/rules/change-governance.md`）
