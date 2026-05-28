---
id: 0TO1-README
title: AEOS 0→1 種子文件（Elon 心智模型重置）
status: canonical
type: entry
created: 2026-05-28
supersedes_for_decisions: dev_docs/* (legacy 81-doc corpus)
lens: 第一性原理 / 白癡指數 / 五步工作法 / 垂直整合
---

# AEOS 0→1 — Elon 心智模型重置

> 這 5 份文件是 AEOS **做決策與開工的唯一關鍵路徑**。
> 既有 81 份 `dev_docs` 文件不刪、保留為 reference，但**退出決策關鍵路徑**。
> 為什麼這樣做，見 [`01-delete-ledger.md`](./01-delete-ledger.md)。

---

## 一頁裁決（30 秒讀完）

**事實**：0 行程式碼、0 個 pilot 客戶、$0 營收、81 份企業級規範文件。

**Elon 裁決**：白癡指數爆表的不是產品，是**文件本身**。90% 的文件在解決「想像中的未來企業」的問題，而那些需求是從「真公司都長這樣」**類比**來的，不是從第一性原理推出來的。

**第一性原理重算**：這家公司現在唯一的真需求是——**用最小的東西，證明那個核心賭注是不是真的**。其他全是雜訊。

**核心賭注（要被證偽的那一句）**：

> 一條半自動產線，能把「**一個客服職位 + 一坨真實混亂知識**」，在 **7 天內、人類只簽核一次**，量產出一位能在 LINE 上對真實客戶訊息產生**可被人類採用的草稿回覆**的 AI 員工——而這位員工的記憶可匯出、身體可換通道。

**第一步動作**：不是再寫文件。是**簽一個 pilot 客戶 + 寫第一行程式碼**，去打那條最薄的垂直切片。

---

## 文件地圖（共 5 份，刻意只有 5 份）

| # | 文件 | 一句話 | 取代了誰 |
|---|---|---|---|
| 0 | [`00-the-bet.md`](./00-the-bet.md) | 第一性原理重算 + 兩個白癡指數 + 唯一賭注 + 殺死條件 | 白皮書 00–07/99、投資論述 05、願景 01 |
| 1 | [`01-delete-ledger.md`](./01-delete-ledger.md) | 對 81 份舊文件逐叢集裁決 KEEP/ARCHIVE/KILL + 「加回 10%」清單 | 這份就是「做決策」本身 |
| 2 | [`02-mvg-build-sheet.md`](./02-mvg-build-sheet.md) | 最薄可建構垂直切片 + 開工順序 + coding agent 可接手 | PRD-001、SAD、API-001、db-schema、11 份 MC 契約 |
| 3 | [`03-validation-and-kill.md`](./03-validation-and-kill.md) | 可證偽實驗：什麼數字證明 / 殺死賭注、何時、預先承諾 | PILOT-001、AC-001~005、TEST-001 |

> 沒有第 4 份。如果要加第 6 份文件，先回答 `00-the-bet.md` 的問題：**它降低白癡指數還是只是讓我們覺得安心？**

---

## 與既有 81 份文件的關係

```
dev_docs/
├── _0to1/              ← 你在這裡。決策與開工的唯一關鍵路徑（5 份）
│
├── 00-07, 99           ← 白皮書敘事（KEEP-as-reference，退出關鍵路徑）
├── 1-decisions/        ← 10 份 ADR（部分 KEEP，多數 ARCHIVE，見 ledger）
├── 2-contracts/        ← 19 份契約（多數 ARCHIVE：想像中的未來規範）
├── 3-process/          ← Runbook/Hiring（KILL/ARCHIVE：0 LOC 不需要）
├── 4-exploration/      ← PRD/Cost/ICP（部分 KEEP）
└── ...                 ← 其餘見 ledger
```

逐份裁決見 [`01-delete-ledger.md`](./01-delete-ledger.md)。要不要把 ARCHIVE 類別物理移到 `dev_docs/_archive-pre-0to1/`，等你一句話，我不擅自動你的檔案。

---

## 怎麼用這套

1. **CEO/創辦人**：讀 `00` → `03`。本週只做兩件事：簽 1 個 pilot、把 `00` 的殺死條件變成你對自己的承諾。
2. **要開工的 coding agent**：讀 `02-mvg-build-sheet.md`，那是 handoff。其餘文件按需查 legacy。
3. **想保留某份被判 ARCHIVE 的文件**：去 `01-delete-ledger.md` 看它的判定理由，不同意就推翻——Elon 演算法第 2 步本來就允許「刪錯了再加回來」。

*建立：2026-05-28 — Elon 心智模型 0→1 重置*
