---
name: sunnydata-doc-freshness
description: Use before editing project documents instantiated from VibeCoding templates - files matching ADR-NNNN-*.md / CR-NNNN-*.md / CIA-NNNN-*.md, or any docs/**/*.md with frontmatter id <PREFIX>-NNNN. Checks staleness, traces completeness, bidirectional cross-references between project artifacts. SKIPS edits to VibeCoding_Workflow_Templates/** themselves - those are stable skeletons, not living documents.
---

# Doc Freshness Skill

> **Scope clarification — read this first**
>
> 本 skill 規範的是「**駕駛員從 VibeCoding 模板實例化出來的專案文件**」，
> 例如 `docs/adr/ADR-0007-use-postgres-for-orders.md`、
> `docs/cr/CR-0023-deprecate-v1-api.md`、`docs/prd/PRD-0003-checkout-flow.md`。
>
> **不規範**模板本身（`VibeCoding_Workflow_Templates/*.md`）── 那是穩定骨架，
> 不會頻繁更新；唯有實例化後的文件才會與專案演進一起腐化。

## Purpose

當 AI / 駕駛員對**專案實際產出的文件**做變更時，自動檢查：

1. **Staleness** — `last_updated` 是否需與本次變更同步
2. **Traces** — 宣告的上游 ID 是否仍存在、是否仍 active（非 superseded / archived）
3. **Bidirectional cross-references** — 與其他**專案文件**（非模板）的互引是否雙向完整

## Scope detection

Skill 在以下情境**自動載入**：

| 偵測規則 | 範例 |
| :--- | :--- |
| 檔名匹配 `^(ADR\|CR\|CIA)-\d{4}-.*\.md$` | `docs/adr/ADR-0007-use-postgres-for-orders.md` |
| 檔案 frontmatter 含 `id: <PREFIX>-NNNN` 模式 | `id: PRD-0003`、`id: ARCH-0002` |
| 路徑在 `docs/**/*.md` 且具備兩行 metadata header | 任何專案 doc |

### Skip（**不**載入本 skill）

| 路徑 | 理由 |
| :--- | :--- |
| `VibeCoding_Workflow_Templates/**/*.md` | 模板骨架，靜態不腐化 |
| `.claude/**/*.md` | Harness 規則，由 sunnydata-skill-authoring 管 |
| `node_modules/**`、`.git/**`、`dist/**` | 外部依賴/build artifact |
| 純 README / CHANGELOG | 不在 ID 體系內 |

## Check 1 — Staleness

```text
1. Read 目標檔 frontmatter（前 10 行）
2. 抽取 `last_updated:` 或「**更新:** YYYY-MM-DD」blockquote 變體
3. 如果本次編輯是「實質內容變更」（非 typo、非 frontmatter-only）：
   → 更新 last_updated 為今天 YYYY-MM-DD
4. 若現有 last_updated 已超過 90 天且本次未動：
   → 警告：「此文件 N 天未更新，可能與當前 code 已脫節，建議審視」
5. 若 status: deprecated / superseded / archived：
   → 拒絕編輯，提示「該文件已過期，請改編 superseded_by 指向的新檔」
```

## Check 2 — Traces completeness

每個實例化文件按類型必須宣告對應上游：

| 文件類型 | 必備 frontmatter / header 引用 |
| :--- | :--- |
| PRD instance | — （本檔是源頭，下游派生 E-/US-/Q-/D-） |
| BDD `.feature` | `# 對應 PRD: PRD-NNNN` 或 `@US-NNNN` tag |
| ADR instance | `triggered_by: Q-NNNN / D-NNNN / CR-NNNN`（必填擇一） |
| Architecture instance | `traces: E-NNNN, ADR-NNNN` |
| API spec instance | `traces: US-NNNN, ADR-NNNN` |
| Module spec instance | `traces: US-NNNN, ADR-NNNN` |
| CR instance | `affects:` US/ADR/MOD/API list；需 CIA 則含 `cia: CIA-NNNN` |
| CIA instance | `triggered_by: CR-NNNN`（必填，無 CR 不開 CIA） |
| WBS instance | `traces: E-NNNN, US-NNNN`（每個任務） |

### 上游驗證流程

```text
For each ID 引用 in traces / triggered_by / affects:
  1. Search project for the upstream file (by ID pattern in filename or frontmatter)
  2. Confirm 該檔存在
  3. Confirm 該檔的 status != superseded / archived
  4. 若不存在 → 警告：「引用了不存在的 X-NNNN，請補建上游或修正引用」
  5. 若 superseded → 警告：「上游 X-NNNN 已被 Y-NNNN 取代，建議跟進更新本檔」
```

ID 規範詳見 `VibeCoding_Workflow_Templates/INDEX.md §ID 命名規範`，
檔名規則見同檔 `§檔名規範`。

## Check 3 — Bidirectional cross-references

針對本檔內任何「📎 與 X 的邊界」、「→ 詳見 X」、「relates to X」之類的互引：

```text
1. Identify X（被引用的對方檔案，僅針對 docs/** 內的專案文件）
2. Read X
3. Search X 內是否反向引用本檔
4. 若無 → 提議在 X 適當位置補一行反向引用：
   `> 📎 **與 <current> 的關係**: <一句話描述>`
5. 駕駛員裁決是否加入
```

**重要**：

- 反向引用的對象限**同專案的其他 instance 檔**
- **不需要**檢查與 VibeCoding 模板的雙向（模板是骨架，不在 instance 互引網內）
- ADR 之間常見的關係：`supersedes` / `superseded_by` / `relates_to` / `amends`
- CR / CIA / ADR 三者構成決策鏈，**鏈中每跳必須雙向可追溯**

## Required actions checklist（write 前自動檢查）

- [ ] 確認目標檔不在 skip scope（非模板、非 harness）
- [ ] 讀目標檔 frontmatter，記 `last_updated`、`status`、`id`
- [ ] 分類變更：typo / frontmatter-only / 實質內容
- [ ] 實質內容 → 更新 `last_updated` 為今日
- [ ] 實質內容 → 跑 Check 2 Traces：驗證所有上游 ID 仍 active
- [ ] 實質內容 → 跑 Check 3 雙向 ref：對每個外部引用檢查反向
- [ ] 若新增章節/欄位（結構性變動）→ 提示更新 `docs/INDEX.md` 或專案目錄索引
- [ ] 若狀態變更（draft → active / active → superseded）→ 提示通知下游

## Output format

當 skill 識別到問題時，回覆格式：

```text
[sunnydata-doc-freshness]
- 檔案: docs/adr/ADR-0007-use-postgres-for-orders.md
- 文件類型: ADR instance
- 發現問題:
  · last_updated 距今 142 天，未隨本次變更同步
  · triggered_by: CR-0015 — 該 CR 已標 superseded by CR-0024
  · body 中提到「relates to ADR-0003」，但 ADR-0003 內無反向引用
- 建議動作:
  · 將 last_updated 改為 2026-05-26
  · 更新 triggered_by 為 CR-0024
  · 在 docs/adr/ADR-0003-*.md 加一行 `> relates to ADR-0007`
- 是否繼續？(駕駛員裁決)
```

駕駛員可選：**go**（接受建議套用） / **fix manually**（先暫停） / **skip**（已知例外，記錄理由）。
本 skill 不阻擋寫入，僅讓決策可見。

## Relationship to other rules

| 規則 / Skill | 規範對象 | 關係 |
| :--- | :--- | :--- |
| `.claude/rules/template-formatter.md` | 模板與 instance 的 markdown 風格 | 正交（風格 vs 內容鮮度） |
| `.claude/rules/template-update-triggers.md` | 程式碼變更 → 應同步哪些 instance | 上游觸發；本 skill 補下游檢查 |
| `.claude/rules/change-governance.md` | instance 等級的變更需 CIA gate | 本 skill 是 CIA gate 之外的「日常編輯」鬆 gate |
| `.claude/rules/context-stability.md` | 6-tier 層級（本專案是扁平結構，僅參考） | 本 skill 對應 tier 4-5 instances |
| `VibeCoding_Workflow_Templates/INDEX.md §ID 命名規範` | ID 體系與檔名規則 | 本 skill 驗證實作 |
| `.claude/hooks/post-write.sh` | 寫檔後 markdown lint + trigger 提醒 | 本 skill 在 AI 寫檔**前**自動載入；hook 在**後**提醒 |

## Not in scope

- 模板骨架本身的更新（`VibeCoding_Workflow_Templates/*.md`）
- Markdown 格式 lint（由 `.markdownlint.json` + `.githooks/pre-commit` 負責）
- 程式碼 → 模板觸發提醒（由 `template-update-triggers.md` + `post-write.sh` 負責）
- 變更影響範圍分析（由 instance `CIA-NNNN-*.md` 模板負責）
- 模板版本演進（由 `INDEX.md §版本記錄` 負責）

## Edge cases

| 情境 | 處置 |
| :--- | :--- |
| 編輯新建中的草稿 instance（`status: draft`） | 跳過 Check 2 嚴格驗證，允許上游 ID 暫缺；提示「draft → active 前必須補完」 |
| 編輯歷史 ADR（已 active，現在補 typo） | 不更新 last_updated；不阻擋 |
| 純 frontmatter 改 owner / approver | 更新 last_updated，跳過 Check 3 雙向 |
| 大規模重組（一次動 ≥ 5 個 instance） | 建議改用 CIA-NNNN 走變更治理流程，本 skill 退讓 |
| 引用了已外部消失的舊系統 ID（migration 殘留） | 建議改為 `> 已遷移自 legacy: X` 註記，不報錯 |
