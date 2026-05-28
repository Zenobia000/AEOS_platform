---
name: engineering-charter
description: AEOS 工程團隊文化憲章 — 一頁式的工程信仰、決策原則、品質紅線
status: active
type: principles
created: 2026-05-14
owner: CTO
tier: 0
---

# AEOS Engineering Charter

> One-page contract. Every engineer reads this on day 1 and quotes it in design discussions.

## 1. Mission

我們不在做 Agent Framework。我們在做 **AI 員工的人資 / 治理系統**。

每一行 code 都要回答：「這對客戶在 7 天上線一位可審計、可回滾、可治理的 AI 員工有幫助嗎？」沒幫助 → 不做。

## 2. Five Engineering Principles

| # | 原則 | 具體含義 |
|---|---|---|
| 1 | **Governance-first** | 任何 AI 對外行為**必先過 audit log + policy check**。沒這兩條的 path 一律不上線。 |
| 2 | **Frozen Runtime** | 生產環境的 AI 員工是**不可變的**。學習、改進、調 prompt 一律在 Training Room；上線版本 = 凍結版本 + 版本號。 |
| 3 | **Skill as Asset** | Skill 是 git 化、版本化、測試化、可回滾的資產。**沒過 Quality Gate 不上線**，沒辦法 rollback 的 Skill 不存在。 |
| 4 | **Simplicity over Sophistication** | 3 層縮排上限。10 行 if/else 改寫成 4 行無條件分支才算「好品味」。Linus 規則。 |
| 5 | **Pragmatism over Theory** | 為**真實的、生產環境會出現**的問題寫 code。「未來可能需要」= 不做。 |

## 3. How We Decide

| 決策性質 | 機制 |
|---|---|
| 改動觸碰 flow / contract / data / architecture | 跑 `sunnydata-change-impact-analysis` skill 產 CIA（硬 gate） |
| 跨模組、無法 revert 的技術選型 | 寫 ADR ≤ 1 頁，PR 審 |
| 單檔內、可 revert 的實作選擇 | Code review 直接決，不寫 ADR |
| 「我覺得這樣比較好」 | 不是決策，是意見。寫 ADR 或閉嘴。 |

## 4. Code Quality Bar

- 函式 < 50 行；檔案 < 800 行；縮排 ≤ 3 層
- 命名動詞-名詞（`fetchKnowledgeCard`），禁止 `data`、`info`、`stuff`
- 不可變優先（spread / immutable methods），不修既有物件
- 錯誤在邊界處驗證、處理；**禁止靜默吞錯**
- 不可寫死秘密、API key（commit-time hook 會擋）
- 測試覆蓋 ≥ 80%（unit + integration）；新功能必含測試

詳細風格規則見 `.claude/rules/coding-style.md`、`.claude/rules/testing.md`、`.claude/rules/security.md`。

## 5. Hard No

| 禁止 | 違反例 |
|---|---|
| 在 main / master 上直接 commit | 一律 PR |
| `git stash` 當工作流 | 開分支 |
| 在 prod runtime 中讓模型自我修改 | 違反 Frozen Runtime |
| 跳過 audit log / policy check 的捷徑 path | 違反 Governance-first |
| 把 spec 矛盾「自己合理化」 | 停下來回報，引用 ID |
| `--no-verify` 跳過 hook | 修問題本身 |
| 沒過 Skill Quality Gate 就上 production | 違反 Skill as Asset |

## 6. Decision Authority

| 角色 | 權限 |
|---|---|
| CTO | 架構、技術選型、ADR 終審、Quality Gate 通過權 |
| Tech Lead | Module 內實作決策、code review approval |
| Engineer | PR 提出、ADR 草擬、改進建議 |
| 任何人 | 對任一條決策提出「為什麼」並要求書面回答 |

## 7. Working Style

- **Async-first**：書面為主；會議是最後手段
- **每週一次 90 分鐘 architecture sync**（CTO + 工程全員）；無 daily standup
- **PR < 400 行**；超過先拆
- **Code review SLA：24 小時內回覆**；不阻塞 > 1 工作日

## 8. Linked Rules

- 編碼風格：`.claude/rules/coding-style.md`
- Git 流程：`.claude/rules/git-workflow.md`
- 變更治理：`.claude/rules/change-governance.md`
- 文件穩定性層級：`.claude/rules/context-stability.md`
- 安全規範：`.claude/rules/security.md`
- 測試規範：`.claude/rules/testing.md`

---

**版本**：v0.1 · 2026-05-14 · 由 CTO 簽署
**修訂**：要改這份憲章，須寫 ADR 並過 1 週 RFC 期。
