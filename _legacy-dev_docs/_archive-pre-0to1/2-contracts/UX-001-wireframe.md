---
id: UX-001
title: Wireframe & Screen Flow — Phase 1 Admin / Expert Web SPA
status: active
type: ux-wireframe
created: 2026-05-14
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 2
related: [UF-001, UF-002, UF-003, UF-005, API-001]
---

# UX-001 — Phase 1 Web SPA Wireframe

> 線稿級 ASCII wireframe，**不用 Figma**（節省工具稅）。
> Phase 1 共 7 個主畫面 + 1 個全域元件。Expert 與 CTO 共用一套後台，靠 scope 控制可見性。

## 0. Information Architecture

```
/login                                 [全民]
/                ─ Dashboard           [Expert, CTO]
/knowledge       ─ KC 列表/編輯/上傳    [Expert]
/test-sets       ─ Test Set 編輯/Run    [Expert]
/draft-inbox     ─ Draft Mode 審核     [Expert]
/conversations   ─ 對話查詢/審計        [Expert, CTO]
/admin           ─ Employee / Skill / Kill switch [CTO]
/audit           ─ Audit log 查詢       [CTO]
```

## 1. 全域 Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [AEOS]  Dashboard  Knowledge  TestSets  DraftInbox          │
│         Conversations  Admin*  Audit*       [{user}] [⚙]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│             ── Page content here ──                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Tenant: 「小貓咖啡」  Env: Production  AI: ● Live   v1.0.3  │
└─────────────────────────────────────────────────────────────┘
```

*Admin / Audit 標籤僅 CTO scope 可見

底部 status bar：tenant 名 + 當前 Employee 狀態（Live / Paused / Draft）+ 版本

## 2. /knowledge — Knowledge Card 列表 + 上傳

```
┌─ Knowledge ──────────────────────────────────────────────┐
│ [+ Upload]  [Status: All ▼]  [Tags: ▼]  Search: [______] │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ☐ 營業時間            tags: 基本資訊   approved  ⋮  │ │
│ │ ☐ 退貨流程            tags: 售後       draft     ⋮  │ │
│ │ ☐ 商品 A 規格         tags: 商品/A     approved  ⋮  │ │
│ │ ☐ 訂單查詢方式        tags: 訂單       draft     ⋮  │ │
│ │ ...                                                  │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Total 47 cards | 31 approved | 16 draft | 0 archived    │
└──────────────────────────────────────────────────────────┘
```

點 row → 進編輯頁。Upload modal：

```
┌─ Upload Knowledge Source ─────────────────────────┐
│  ○ File (PDF/DOCX/MD)   ○ URL                     │
│                                                   │
│  [ Drop file here or click to browse ]            │
│                                                   │
│           [Cancel]      [Start Ingest]            │
└───────────────────────────────────────────────────┘
```

## 3. /knowledge/{id} — KC 編輯

```
┌─ Edit Knowledge Card ────────────────────────────────────┐
│ Title: [ 退貨流程                                       ]│
│ Tags:  [ 售後 ] [ 退貨 ] [+]                            │
│                                                          │
│ ┌─ Markdown body ───┐  ┌─ Source preview ─────────┐    │
│ │ # 退貨流程         │  │ 從 returns.pdf p.3 切出  │    │
│ │                   │  │ ...                       │    │
│ │ 客戶可在 7 天內   │  │ 「凡於本店購買之商品，   │    │
│ │ 申請退貨...       │  │ 顧客於收貨後七日內...」 │    │
│ │                   │  │                           │    │
│ └───────────────────┘  └───────────────────────────┘    │
│                                                          │
│ Valid: [from 2026-05-01] [until ____________]           │
│ Status: draft                                            │
│                                                          │
│ [Save Draft]  [Archive]  [⚡ Approve]  [Split] [Merge]  │
└──────────────────────────────────────────────────────────┘
```

## 4. /test-sets/{id} — Test Set 編輯 + Run

```
┌─ Test Set: v1 baseline (47/50 filled) ─────────────────────────┐
│ [+ Add row]  [Run Test ▶]                                      │
│                                                                │
│ #  Question                  Expected   Keywords    Last Run   │
│ ───────────────────────────────────────────────────────────── │
│ 1  你們營業時間？             accept    09,21       ✓ pass    │
│ 2  禮拜天有開嗎？             accept    日,休       ✗ fail    │
│ 3  退貨幾天內？               accept    7,七        ✓ pass    │
│ 4  我要客訴                   handoff   --          ✓ pass    │
│ 5  ... (47 more rows)                                          │
│                                                                │
│ Pass rate: 38 / 47 = 80.8%  (last run 2026-05-08 14:23)        │
└────────────────────────────────────────────────────────────────┘
```

點 row 展開：

```
┌─ Row #2 detail ─────────────────────────────────────────┐
│ Question: 禮拜天有開嗎？                                │
│ Expected: accept   Keywords: 日,休                      │
│                                                         │
│ AI response (run 2026-05-08):                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │「我不確定週日營業時間，請稍候，我為您轉接客服。」  ││
│ └─────────────────────────────────────────────────────┘│
│ Retrieved KCs: [營業時間 (similarity 0.62)]            │
│ Judgment: FAIL (handoff but expected accept)           │
│                                                         │
│ [Add KC to fix this]  [Mark actually correct]          │
└─────────────────────────────────────────────────────────┘
```

## 5. /draft-inbox — Draft Mode 審核（UF-003）

```
┌─ Draft Inbox  (3 pending) ─────────────────────────────────────┐
│  [Pending ▼]  Sort: oldest first ▼                             │
│                                                                │
│ ┌─ 14:32  user pseudo:Uabc12...  · 2 min ago ────────────────┐ │
│ │ User: 你們週日有開嗎？                                     │ │
│ │ ───                                                        │ │
│ │ Draft (Skill v1.0.3, conf 0.62):                          │ │
│ │ 我們週一到週六 09:00-21:00 營業；週日固定公休。           │ │
│ │ 如需週日聯繫，可透過 [客服信箱] 留言。                   │ │
│ │ ───                                                        │ │
│ │ Used KC: 營業時間, 客服聯繫                                │ │
│ │                                                            │ │
│ │ [✓ Approve & Send]  [✏ Edit]  [✗ Reject (人工接手)]      │ │
│ └────────────────────────────────────────────────────────────┘ │
│ ┌─ 14:28  user pseudo:Udef34...  · 6 min ago ────────────────┐ │
│ │ User: 我要退貨                                             │ │
│ │ Draft (Skill v1.0.3, conf 0.81):                          │ │
│ │ ...                                                        │ │
│ └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

Edit mode → textarea inline + Send / Cancel。Reject → modal 問原因。

## 6. /conversations — 對話查詢與審計

```
┌─ Conversations  Filter: [date] [channel] [outcome] [auto/draft] ┐
│                                                                  │
│ Time         User       Channel  Outcome    Auto?  Msgs  Action │
│ 14:32 today  Uabc...    line     resolved   draft   4    [View] │
│ 14:11 today  Udef...    line     handoff    auto    7    [View] │
│ 13:50 today  Uxyz...    line     resolved   auto    3    [View] │
│ ...                                                              │
│                                                                  │
│ Today: 42 conversations | 78% resolved | 12% handoff | 10% auto │
└──────────────────────────────────────────────────────────────────┘
```

點 View → 線性對話 view（user 左、AI 右），每則旁邊註明：Skill version、引用 KC、tool calls、cost。

## 7. /admin — CTO 限定

```
┌─ Admin ─────────────────────────────────────────────────────────┐
│                                                                 │
│ ┌─ Employee: 小美客服 v1.0 ──────────────────────────────────┐ │
│ │ Status: ● Live   Auto reply: [10% ▼]                       │ │
│ │ Skills bound: customer-service/faq-respond@1.0.3 (prod)    │ │
│ │ Channels: LINE (channel_id: 1234567)                       │ │
│ │                                                            │ │
│ │ [Change persona]  [Bind skill]  [Re-test]                 │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ ⚠ Emergency Controls ────────────────────────────────────┐ │
│ │                                                            │ │
│ │       [  ⛔  DISABLE AI  ]                                │ │
│ │                                                            │ │
│ │  Last incident: none in past 30 days                      │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ Daily Stats (yesterday) ─────────────────────────────────┐ │
│ │ Conversations: 47  Auto: 5  Draft approved: 38  Override: 4│ │
│ │ Cost (LLM tokens): NT$ 87                                 │ │
│ └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

Click DISABLE AI → 二次確認 modal（紅底）：

```
┌─ Confirm: Disable AI ───────────────────────────────┐
│ This will immediately stop AI replies for "小美客服"│
│ All new messages will go to Expert handover.         │
│                                                      │
│ Reason (required): [_________________________]      │
│                                                      │
│        [Cancel]      [⛔ Yes, Disable AI]            │
└──────────────────────────────────────────────────────┘
```

## 8. / — Dashboard（首頁）

```
┌─ Today ────────────────────────────────────────────────────────┐
│  Conversations 47    Auto-reply 12%    Handoff 8%             │
│  Pending drafts 3    Pass rate trend (last 7d): ↗ 78% → 84%   │
│                                                                │
│  ⚠ 2 Alerts (last 24h)                                        │
│   · KC「退貨流程」上次測試 fail（pass rate 60%）              │
│   · 1 conversation marked 'error' (詳情 →)                    │
└────────────────────────────────────────────────────────────────┘
```

## 9. /login

```
┌─ AEOS ──────────────────────────────────┐
│         小貓咖啡 - 員工後台             │
│                                         │
│  Email:    [_____________________]      │
│  Password: [_____________________]      │
│                                         │
│  [ Sign in ]                            │
│                                         │
│  忘記密碼？ 聯絡 onboarding@aeos.app    │
└─────────────────────────────────────────┘
```

## 10. Design tokens（Phase 1 直接套 Tailwind / shadcn 預設）

- 色：primary = Tailwind blue-600；danger = red-600；success = green-600
- 字：system sans-serif；中文 Noto Sans TC
- 間距：4 / 8 / 16 / 24 / 32
- 圓角：sm (4px) 為主；button md (6px)；card lg (8px)
- 元件庫：shadcn/ui（Button / Card / Dialog / Input / Select / Tabs / Toast）
- Icon：lucide-react

**禁止**：自寫元件、Animation Framework（Phase 1 不做動畫）、carousel、infinite scroll

## 11. Responsive

- 後台 desktop-first，最小寬度 1280px
- Tablet（768–1280）：side nav 收摺成 hamburger
- Mobile：Phase 1 **不支援**（Expert 用桌機）；只有 Draft Inbox 有 mobile-friendly view（讓 Expert 可在外面也能 approve）

## 12. Accessibility（最低標）

- 所有 button 有 aria-label
- 表單欄位 label 對應 input
- 顏色對比 ≥ WCAG AA
- Keyboard navigable（Tab 順序合理）
- 暫不做 screen reader 細部優化（Phase 2）

## 13. 不做的事

- Dark mode（Phase 2）
- 自訂主題色（鎖預設）
- 即時 collaborative editing（Phase 3）
- Real-time push 給 Web（用 polling 5s；Phase 2 加 SSE / WebSocket）

## 14. 連結
- 對應流程：`UF-001` ~ `UF-005`
- 後端 API：`API-001-internal.md`
- 設計決策：（待 ADR-0008 frontend stack）
