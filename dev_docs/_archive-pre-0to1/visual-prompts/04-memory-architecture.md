# Slide 4 — AEOS 記憶架構圖 (AI Employee Memory Architecture)

> **用途**：給 GPT-4o / DALL-E 3 / Midjourney 等 image generation tool 生成投影片
> **建議工具**：GPT-4o image generation (英文 prompt 準確度最高)
> **對應決策文件**：ADR-0010-memory-architecture.md、domain-model.md §3.5

---

## 設計目標

一頁投影片同時傳達四件事：
1. **五層記憶模型**：L1 → L2 → L2.5 → L3 → L4 的完整層級與 Phase 1 覆蓋範圍
2. **Frozen Runtime 的精確定義**：凍結「行為」不凍結「記憶」— 三類風險分層
3. **記憶治理哲學**：記憶是治理問題，不是儲存問題；不需要 Vector DB 做對話記憶
4. **L2.5 Session Summary**：Phase 1 的關鍵差異化 — AI 員工具備跨 session 事實記憶

核心訊息：**「Frozen Runtime freezes behavior, not memory. An AI that can't change its strategy is safe. An AI that can't remember anything is useless.」**

---

## 視覺結構

```
方向：兩欄式佈局 (左 55% / 右 45%)
左欄：五層記憶堆疊圖（主視覺，由下而上）
右欄上：三類風險分層矩陣（事實/推論/行為）
右欄下：L2.5 Session Summary 流程圖
底部：一句話 tagline（全寬）
比例：16:9
```

### 色彩語意

| 顏色 | 語意 | Hex |
| :--- | :--- | :--- |
| 綠色 | Phase 1 已建 / 允許 | #10B981 |
| 藍色 | Phase 1 新增 (L2.5) | #3B82F6 |
| 灰色 | Phase 2 延後 | #9CA3AF |
| 橘色 | 警告 / 中風險 | #F59E0B |
| 紅色 | 禁止 / 高風險 | #EF4444 |
| 深灰 | 基礎設施層 | #374151 |
| 淺灰 | 背景 / 分隔線 | #F3F4F6 |

---

## 元素清單

### 左欄 — 五層記憶堆疊（佔 55%）

```
標題：「Five-Layer Memory Model」
副標題：「From hot context to cold patterns — Phase 1 covers L1–L3」

由下而上的 5 個水平色帶，每層含簡要說明：

┌─────────────────────────────────────────────────────────┐
│ L4 — Operational Memory（灰色，虛線邊框）               │
│ 跨對話累積模式：失敗分類、客戶偏好                       │
│ Phase 2 — Compiler 3 + Training Room                    │
│ 標籤：「PHASE 2」灰色 badge                              │
├─────────────────────────────────────────────────────────┤
│ L3 — Tenant Knowledge（綠色）                           │
│ KnowledgeCard (pgvector) + Skill (Git/YAML)             │
│ 人類管理：draft → approve → production                   │
│ 三分類 icon：Static | Policy | Dynamic                   │
│ 標籤：「PHASE 1 ✅」綠色 badge                           │
├─────────────────────────────────────────────────────────┤
│ L2.5 — Session Summary（藍色，加粗邊框，最醒目）         │
│ 對話結束 → AI 自動摘要 → PII 遮罩 → ≤ 200 token        │
│ 下次同一客戶來電 → 注入 context                          │
│ 標籤：「PHASE 1 NEW ✅」藍色 badge + 星號 icon           │
├─────────────────────────────────────────────────────────┤
│ L2 — Session Memory（綠色）                             │
│ Redis (hot) + PostgreSQL Message (persistent)            │
│ 生命週期：對話開始 → 結束 + 5min grace                   │
│ 標籤：「PHASE 1 ✅」綠色 badge                           │
├─────────────────────────────────────────────────────────┤
│ L1 — Working Memory（綠色）                             │
│ LLM context window — 8K token limit                     │
│ 保留最近 5 輪原文 + RAG top-5 chunks                     │
│ 標籤：「PHASE 1 ✅」綠色 badge                           │
└─────────────────────────────────────────────────────────┘

層與層之間用箭頭連接，標示資料流方向：
  L1 ↔ L2（雙向：context window 管理）
  L2 → L2.5（單向：對話結束時摘要）
  L2.5 → L1（單向：下次對話注入）
  L3 → L1（單向：RAG retrieval 注入）
  L4 ⇢ L3（虛線：Phase 2 回饋更新 KB/Skill）

左下角基礎設施圖示（深灰小方塊）：
  PostgreSQL 15 + pgvector | Redis 7 | PII Gateway (ADR-0005)
```

### 右欄上 — 三類風險分層矩陣（佔右欄 50%）

```
標題：「What Frozen Runtime Actually Freezes」
副標題：「Freeze behavior, not memory」

三行表格式方塊，每行一類：

┌─ 事實觀察 ─────────────────────── 風險：低 (綠) ──┐
│ 「客戶問了退貨流程」                                │
│ Phase 1：允許 ✅ — L2.5 自動寫入                    │
│ 治理：PII 遮罩 + ≤ 200 token + audit               │
└────────────────────────────────────────────────────┘

┌─ 模式推論 ─────────────────────── 風險：中 (橘) ──┐
│ 「這客戶偏好簡短回答」                              │
│ Phase 2：需標記信心度 + 失效條件                    │
│ 治理：Expert Review + Evaluation Service            │
└────────────────────────────────────────────────────┘

┌─ 行為改變 ─────────────────────── 風險：高 (紅) ──┐
│ 「我應該改用更正式的語氣」                          │
│ 永遠禁止 ✗ — Frozen Runtime 核心保護               │
│ 治理：不可自我修改 Skill / prompt / persona         │
└────────────────────────────────────────────────────┘

右側加一個鎖/解鎖的視覺隱喻：
  🔓 記憶開放（事實觀察 — 低風險）
  🔒 行為凍結（自我改進 — 高風險）
```

### 右欄下 — L2.5 Session Summary 流程圖（佔右欄 50%）

```
標題：「L2.5 in Action — Cross-Session Fact Memory」

水平流程，兩個場景並排：

場景 A（第一通電話）：
  [Customer icon] → [Chat bubble: "訂單 #1234 到哪了？"]
  → [AI Employee] → [Response: "預計明天送達"]
  → [對話結束] → [Summary box (藍): "客戶詢問訂單 #1234 配送進度，已告知預計明天送達。outcome: resolved"]

場景 B（第二通電話，隔天）：
  [同一 Customer icon] → [Chat bubble: "我昨天問過的訂單..."]
  → [AI Employee + 注入 icon ⬅ Summary from A]
  → [Response: "您昨天詢問的訂單 #1234，已於今早送達，需要確認嗎？"]

場景 A 和 B 之間用虛線弧形箭頭連接，標示：
  「summary 存入 DB → 下次自動注入 context」

底部小字數據：
  寫入：≤ 200 token | 讀取：最近 3 筆 | 預算：≤ 600 token
  保留：90 天（跟隨 data_retention_days）
```

### 底部 — Tagline（全寬）

```
大字引言（粗體，置中）：

  "Memory is a governance problem, not a storage problem."
  「記憶是治理問題，不是儲存問題 — 凍結行為、開放事實、延後推論」

右下角補充：
  "No vector DB for conversations. pgvector for KB only."
  AEOS — ADR-0010 Memory Architecture — 2026
```

---

## GPT-4o Image Generation Prompt (English)

```
Create a professional one-page presentation slide titled
"AEOS Memory Architecture — Five Layers, Three Risk Classes".

Layout: Two-column layout on white background. Left column 55% width,
right column 45%. Full-width tagline bar at bottom.
16:9 aspect ratio.

Visual style: Clean, modern presentation slide. Rounded rectangles,
subtle shadows, professional enterprise look. Similar to a Stripe or
Linear product architecture diagram — information-dense but readable.

=== LEFT COLUMN (55%) — "Five-Layer Memory Model" ===

Five horizontal bands stacked vertically (bottom to top), each representing
a memory layer. Use thin connecting arrows between layers.

Layer 1 (bottom, Green #10B981): "L1 — Working Memory"
  - "LLM context window — 8K token limit"
  - "Keep last 5 turns + RAG top-5 chunks"
  - Green badge: "PHASE 1 ✅"

Layer 2 (Green #10B981): "L2 — Session Memory"
  - "Redis (hot) + PostgreSQL Message (persistent)"
  - "Lifecycle: conversation start → end + 5min"
  - Green badge: "PHASE 1 ✅"

Layer 2.5 (BLUE #3B82F6, thicker border, most prominent):
  "L2.5 — Session Summary"
  - "Conversation end → AI auto-summary → PII masked → ≤ 200 tokens"
  - "Next visit by same customer → inject into context"
  - Blue badge with star: "PHASE 1 NEW ✅"

Layer 3 (Green #10B981): "L3 — Tenant Knowledge"
  - "KnowledgeCard (pgvector) + Skill (Git/YAML)"
  - "Human managed: draft → approve → production"
  - Three small icons: "Static | Policy | Dynamic"
  - Green badge: "PHASE 1 ✅"

Layer 4 (top, Gray #9CA3AF, dashed border): "L4 — Operational Memory"
  - "Cross-conversation patterns: failure taxonomy, customer preferences"
  - "Phase 2 — Compiler 3 + Training Room"
  - Gray badge: "PHASE 2"

Arrows between layers:
  - L1 ↔ L2 (bidirectional, solid): "context window mgmt"
  - L2 → L2.5 (solid): "end-of-conversation summary"
  - L2.5 → L1 (solid, blue highlight): "inject on next visit"
  - L3 → L1 (solid): "RAG retrieval"
  - L4 ⇢ L3 (dashed gray): "Phase 2: feedback updates KB/Skill"

Bottom of left column: small dark gray bar showing infrastructure:
  "PostgreSQL 15 + pgvector | Redis 7 | PII Gateway (ADR-0005)"

=== RIGHT COLUMN TOP (45% width, ~50% height) ===
Title: "What Frozen Runtime Actually Freezes"
Subtitle: "Freeze behavior, not memory"

Three stacked boxes representing risk classes:

Box 1 (Green #10B981 left border):
  Header: "Fact Observation — LOW RISK"
  Example: '"Customer asked about return policy"'
  Status: "Phase 1: ALLOWED ✅ — L2.5 auto-write"
  Governance: "PII mask + ≤ 200 tokens + audit trail"

Box 2 (Orange #F59E0B left border):
  Header: "Pattern Inference — MEDIUM RISK"
  Example: '"This customer prefers short answers"'
  Status: "Phase 2: Requires confidence score + expiry condition"
  Governance: "Expert Review + Evaluation Service"

Box 3 (Red #EF4444 left border):
  Header: "Behavior Change — HIGH RISK"
  Example: '"I should use a more formal tone"'
  Status: "NEVER ALLOWED ✗ — Frozen Runtime core"
  Governance: "Cannot self-modify Skill / prompt / persona"

Right side visual metaphor:
  Unlocked padlock icon next to Box 1: "Memory: OPEN"
  Locked padlock icon next to Box 3: "Behavior: FROZEN"

=== RIGHT COLUMN BOTTOM (~50% height) ===
Title: "L2.5 in Action — Cross-Session Fact Memory"

Two scenarios side by side (or stacked), connected by a curved dashed arrow:

Scenario A "First Call":
  Customer speech bubble: "Where is order #1234?"
  AI response: "Expected delivery tomorrow."
  → End of conversation
  → Blue summary card: "Customer asked about order #1234 delivery.
     Informed: arriving tomorrow. Outcome: resolved."

Scenario B "Next Day Call":
  Same customer speech bubble: "About my order from yesterday..."
  [Injection icon ← Summary from A]
  AI response: "Your order #1234 was delivered this morning.
     Want me to confirm?"

Curved arrow from Scenario A summary to Scenario B injection point,
labeled: "summary stored → auto-injected on next visit"

Small data stats below:
  "Write: ≤ 200 tokens | Read: last 3 summaries | Budget: ≤ 600 tokens
   Retention: 90 days (follows data_retention_days)"

=== BOTTOM BAR (full width) ===

Centered quote in large bold text:
  "Memory is a governance problem, not a storage problem."

Below in smaller text:
  "凍結行為、開放事實、延後推論"

Bottom-right: "No vector DB for conversations. pgvector for KB only."
Bottom-far-right: "AEOS — ADR-0010 Memory Architecture — 2026"

=== ADDITIONAL NOTES ===
- L2.5 should be the most visually prominent element (blue, thicker border)
- L4 should look clearly deferred (gray, dashed)
- The three risk boxes should have clear color-coded left borders (green/orange/red)
- All text must be clearly readable at presentation scale
- No decorative illustrations — every element carries meaning
- Professional, muted color palette — not neon
```

---

## GPT-4o 中文備援 Prompt

```
建立一張專業投影片，標題為「AEOS 記憶架構 — 五層模型 × 三類風險」。

排版：兩欄佈局，白底。左欄 55%、右欄 45%。底部全寬標語列。
16:9 比例。

視覺風格：簡潔現代的簡報投影片，圓角矩形、輕微陰影、專業企業風格。
類似 Stripe 或 Linear 的產品架構圖 — 資訊密度高但可讀。

=== 左欄 (55%) —「五層記憶模型」===

5 個水平色帶由下而上堆疊，每層代表一個記憶層級，層間用箭頭連接。

Layer 1（底層，綠色 #10B981）：「L1 — Working Memory 工作記憶」
  - LLM context window — 8K token 上限
  - 保留最近 5 輪原文 + RAG top-5 chunks
  - 綠色標籤：PHASE 1 ✅

Layer 2（綠色）：「L2 — Session Memory 會話記憶」
  - Redis（熱）+ PostgreSQL Message（持久）
  - 生命週期：對話開始 → 結束 + 5min
  - 綠色標籤：PHASE 1 ✅

Layer 2.5（藍色 #3B82F6，加粗邊框，最醒目）：
  「L2.5 — Session Summary 對話摘要記憶」
  - 對話結束 → AI 自動摘要 → PII 遮罩 → ≤ 200 token
  - 下次同一客戶來電 → 注入 context
  - 藍色星號標籤：PHASE 1 NEW ✅

Layer 3（綠色）：「L3 — Tenant Knowledge 租戶知識」
  - KnowledgeCard (pgvector) + Skill (Git/YAML)
  - 人類管理：draft → approve → production
  - 三個小 icon：Static | Policy | Dynamic
  - 綠色標籤：PHASE 1 ✅

Layer 4（頂層，灰色 #9CA3AF，虛線邊框）：「L4 — Operational Memory 營運記憶」
  - 跨對話累積模式：失敗分類、客戶偏好
  - Phase 2 — Compiler 3 + Training Room
  - 灰色標籤：PHASE 2

層間箭頭：
  - L1 ↔ L2（雙向實線）：context window 管理
  - L2 → L2.5（實線）：對話結束摘要
  - L2.5 → L1（實線，藍色高亮）：下次對話注入
  - L3 → L1（實線）：RAG 檢索
  - L4 ⇢ L3（灰虛線）：Phase 2 回饋更新 KB/Skill

左欄底部深灰基礎設施條：
  PostgreSQL 15 + pgvector | Redis 7 | PII Gateway (ADR-0005)

=== 右欄上半 (45%，~50% 高度) ===
標題：「Frozen Runtime 到底凍結什麼」
副標題：「凍結行為，不凍結記憶」

三個堆疊方框，各有色彩左邊框：

方框 1（綠色左邊框 #10B981）：
  標題：「事實觀察 — 低風險」
  範例：「客戶問了退貨流程」
  狀態：Phase 1 允許 ✅ — L2.5 自動寫入
  治理：PII 遮罩 + ≤ 200 token + audit

方框 2（橘色左邊框 #F59E0B）：
  標題：「模式推論 — 中風險」
  範例：「這客戶偏好簡短回答」
  狀態：Phase 2 需信心度 + 失效條件
  治理：Expert Review + Evaluation Service

方框 3（紅色左邊框 #EF4444）：
  標題：「行為改變 — 高風險」
  範例：「我應該改用更正式的語氣」
  狀態：永遠禁止 ✗ — Frozen Runtime 核心
  治理：不可自我修改 Skill / prompt / persona

右側鎖頭圖示：
  🔓 記憶開放（事實觀察）
  🔒 行為凍結（自我改進）

=== 右欄下半 (~50% 高度) ===
標題：「L2.5 實戰 — 跨 Session 事實記憶」

兩個場景上下排列，用弧形虛線箭頭連接：

場景 A「第一通電話」：
  客戶對話泡泡：「訂單 #1234 到哪了？」
  AI 回覆：「預計明天送達。」
  → 對話結束
  → 藍色摘要卡：「客戶詢問訂單 #1234 配送進度，已告知預計明天送達。outcome: resolved」

場景 B「隔天來電」：
  同一客戶對話泡泡：「我昨天問過的訂單...」
  [注入 icon ⬅ 場景 A 的摘要]
  AI 回覆：「您昨天詢問的訂單 #1234 已於今早送達，需要確認嗎？」

弧形箭頭標示：「摘要存 DB → 下次自動注入 context」

底部數據小字：
  寫入：≤ 200 token | 讀取：最近 3 筆 | 預算：≤ 600 token
  保留：90 天（跟隨 data_retention_days）

=== 底部（全寬）===

置中大字粗體引言：
  "Memory is a governance problem, not a storage problem."

下方小字：
  「凍結行為、開放事實、延後推論」

右下角：
  "No vector DB for conversations. pgvector for KB only."
  AEOS — ADR-0010 Memory Architecture — 2026
```

---

## 各工具使用建議

| 工具 | 建議用法 |
| :--- | :--- |
| **GPT-4o image generation** | 直接貼英文 prompt，輸出品質最高 |
| **DALL-E 3** | 英文 prompt + `--style presentation slide` |
| **Midjourney v6** | 英文 prompt 末加 `--ar 16:9 --style enterprise slide --v 6` |
| **Excalidraw / draw.io** | 用「元素清單」段落作為手繪 checklist |
| **Canva / Keynote / PowerPoint** | 手動排版兩欄式，用色彩語意表對照 |

---

## 預期輸出檢核

生成圖片後檢核下列要點：

```
□ 兩欄佈局清晰，比例約 55/45
□ 左欄五層由下而上順序正確（L1 最底，L4 最頂）
□ L2.5 為最醒目的藍色色帶（加粗邊框 + 星號標籤）
□ L4 為灰色虛線邊框，明確標示 Phase 2
□ 層間箭頭方向正確（特別是 L2.5 → L1 的「注入」箭頭）
□ 右欄上半三個風險方框有綠/橘/紅色彩左邊框
□ 事實觀察 = 允許、模式推論 = Phase 2、行為改變 = 禁止
□ 右欄下半兩個場景清晰呈現「第一通 → 摘要 → 第二通注入」的流程
□ 鎖頭圖示（開鎖 = 記憶開放，上鎖 = 行為凍結）清晰可辨
□ 底部引言和數據小字清晰可讀
□ 16:9 比例
□ 整體風格專業、資訊密度高、無多餘裝飾
```
