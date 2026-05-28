# User Flow — care-copilot（最薄切片，expert 視角）

> **Status**: draft · **Owner**: `devteam-ux` · **Date**: 2026-05-28 · **Feature**: care-copilot
> 主 actor：直銷商/expert（Amy）。範圍：草稿 + 合規 + 活檔案。對應 PRD §4 情境 1/3/6/7。

---

## 主流程（happy path）

```
1. 建檔   expert 在客戶詳情頁「貼對話/截圖/手填」→ 活檔案累積（UC-1）
2. 收訊   客戶訊息進來 → 系統檢索活檔案+知識 → 生 3 語氣草稿（UC-2）
3. 把關   草稿過合規低語 → 綠/黃/紅 徽章（UC-4）
4. 審核   expert 看草稿 → approve / edit / reject（UC-3）
5. 送出   approve → 一鍵複製到 LINE（pilot 手動貼）；全程進稽核
```

## 關鍵狀態覆蓋（每步都要有）

| 狀態 | 設計 |
|:---|:---|
| **empty** | 活檔案空 → 引導「貼上對話開始建檔」；無草稿 → 「點生成草稿」 |
| **loading** | 草稿生成中 → skeleton + 進度（p95<5s 內，不空白等待） |
| **error** | LLM 失敗 → 「暫時無法生成，已標需人工，稍後重試」 |
| **success** | 草稿 + 來源引用（citation）+ 合規徽章 |
| **needs_human** | 缺依據 → 明示「知識不足，建議人工回覆」，不給假草稿 |

## 合規 gate 的 UX（紅線是 hard stop）

| 燈 | UX |
|:---|:---|
| 🟢 green | 直接可送 |
| 🟡 yellow | 提醒一行，仍可送 |
| 🔴 red | 跳 modal：標出違規句 + 改寫建議；**送出鈕禁用**，必須採納改寫才解鎖（情境 7/12） |

## a11y / 裝置

- 主裝置 iPhone（PWA）；審核台手機優先、edit textarea 好操作
- 合規徽章不可只靠顏色（色盲）→ 配文字標籤（過/提醒/擋）
- WCAG 等級 pilot `<TBD>`（OQ-NFR-1）

## 兩軌標註

- 🟦 核心流程骨架（建檔→草稿→把關→審核→稽核）垂直無關，可複用
- 🟨 「貼截圖補健康關注」「3 語氣」「FTC 改寫話術」= Care Copilot pack 垂直特定
