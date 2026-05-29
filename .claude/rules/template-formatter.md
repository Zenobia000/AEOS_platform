# Template Formatter Rule

> 為什麼存在：v3.1 → v3.2 的審視發現「每份 .md 風格不一」是 AI slop 的溫床
> ── 表格對齊隨機、blockquote 多寡不一、列表標記 `-`/`*` 混用、code block 不
> 標 lang。本規則把所有 `VibeCoding_Workflow_Templates/*.md` 與 `docs/**/*.md`
> 收斂到單一 source-of-truth，並由 `.markdownlint.json` + `.githooks/pre-commit`
> 強制執行。

## 0. 適用範圍

| 路徑 | 套用 |
| :--- | :---: |
| `VibeCoding_Workflow_Templates/**/*.md` | 強制 |
| `docs/**/*.md` | 強制 |
| `README.md`（專案根） | 強制 |
| `.claude/**/*.md`（rules / skills / agents） | 強制 |
| `CLAUDE.md`、`AGENTS.md` 等 entry file | 強制 |
| 第三方依賴目錄、`node_modules/`、`.git/` | 排除 |

## 1. 檔案結構

每個模板/規範檔案必須遵守：

```text
# <H1 title>                           ← 第 1 行：唯一 H1
                                       ← 第 2 行：空行
> **版本:** vX.Y | **更新:** YYYY-MM-DD | **狀態:** <enum>
> **負責人:** <role> | **審核:** <role> | **追蹤:** <ID list 或 —>
                                       ← 空行
---                                    ← 唯一分隔線（在 metadata 之後）
                                       ← 空行
## 1. <Section>                        ← 從 ## 1. 開始編號
```

### 1.1 Header 規則

- 唯一 H1：每個檔案開頭一個 `# Title`，全文不再出現 H1
- Title 用法：模板用 `# <模板名稱> - [專案名稱]`；指南用 `# <指南名稱>`
- Metadata 兩行：**第一行**狀態類，**第二行**責任歸屬類
- 第一行欄位順序：`版本 → 更新 → 狀態`（ADR 特殊例外：`狀態 → 日期 → 決策者`）
- 第二行欄位順序：`負責人 → 審核 (或適用範圍) → 追蹤`

### 1.2 章節編號

- 一級節用阿拉伯數字 `## 1. <Name>`、`## 2. <Name>`
- 二級節用 `### 1.1 <Name>`、`### 1.2 <Name>`
- 不超過 4 層（H4 上限）；超過視為複雜度過高，重構成獨立檔
- 章節名稱不加標點符號結尾（除問句外）

## 2. 表格

### 2.1 對齊

| 欄位類型 | 對齊 |
| :--- | :---: |
| 文字、ID、檔名 | 左對齊 `:---` |
| 數字、百分比、計數 | 右對齊 `---:` |
| 短旗標、emoji、yes/no | 置中 `:---:` |
| 表頭分隔列 | 必填，與表格欄數一致 |

### 2.2 風格

```markdown
| 欄 1 | 欄 2 | 欄 3 |
| :--- | :--- | :---: |
| 內容 | 內容 | ✓ |
```

- 每欄左右各保留 1 個空格
- 分隔列各 cell 至少 3 個 `-`（即 `:---`、`:---:`、`---:`）
- **禁止** IDE/linter 自動將 `:---` 改為 `---` 而失去對齊資訊
- 寬鬆對齊風格（cell 內容不需 padding 對齊整體欄寬）

### 2.3 反例

```markdown
❌ 表頭分隔列無對齊（IDE auto-format 結果）
| 欄 1 | 欄 2 |
| --- | --- |

❌ cell 過度 padding
| 欄 1             | 欄 2             |
| :--------------- | :--------------- |

❌ 多餘的 leading/trailing pipe
|欄 1|欄 2|
```

## 3. 列表

- 無序列表只用 `-`（不用 `*` 或 `+`）
- 有序列表用 `1.`、`2.` 從 1 開始；不用 `1.` 全部相同的 lazy 模式
- 巢狀縮排 2 個空格
- 列表項目間不留空行（除非含多段內容）

## 4. Code Block

- 強制標 language tag：` ```python `、` ```bash `、` ```yaml `、` ```mermaid `
- 無語言時用 ` ```text `（不留空）
- 行內 code 用單反引號 `` `like_this` ``
- 不用縮排 code（4-space indent block 已棄用）

## 5. Blockquote

| 用途 | 寫法 |
| :--- | :--- |
| Header metadata | 每行 `>` 開頭，多行內容用 `>` 連接 |
| Cross-ref 邊界註記 | `> 📎 **與 <file> 的邊界**: <說明>` |
| Tier-banner 提示 | `> **<tier-name>**: <說明>` |
| 警告/重要 | `> ⚠️ **警告**: <說明>`、`> 🛑 **停止**: <說明>` |
| 引用 | `> <被引用內容> — <出處>` |

連續 blockquote 區塊用空行 `>` 分隔內部段落，不留純空白行。

## 6. 強調

- **粗體** 用於關鍵字、欄位名、責任點
- *斜體* 用於外文、書名、輕量強調
- ~~刪除線~~ 用於已棄用條目
- 不疊加 (`***bold italic***`) — 重要性高就拆兩句

## 7. 連結

- 內部連結用相對路徑：`[15 §1](./15_documentation_and_maintenance_guide.md#1-文檔類型)`
- 外部連結附 title：`[OWASP](https://owasp.org "OWASP 官網")`
- 圖片用 `![alt](path "title")` —— alt 必填
- 不用 raw URL，外露時加 `<>`：`<https://example.com>`

## 8. YAML / JSON 內嵌

當示例需要 YAML 或 JSON，**必須**完整可解析：

```yaml
id: TC-0023
traces:
  user_story: US-0007
  scenario: SC-0012
```

不接受省略號 `...` 或 `[填入]` 字串混入 YAML key/value 結構，會破壞 lint。
若需 placeholder，包在引號內：`owner: "[填入 PM 姓名]"`。

## 9. 日期、版本、ID

| 類型 | 格式 | 範例 |
| :--- | :--- | :--- |
| 日期 | `YYYY-MM-DD` | `2026-05-26` |
| 版本 | `vX.Y` 或 `vX.Y.Z` | `v3.2` |
| ID（4 位流水） | `<PREFIX>-NNNN` | `ADR-0007`、`TC-0023` |
| ID（佔位）| `<PREFIX>-NNNN` | 模板用 NNNN，實例填數字 |
| 時間（含時分） | `YYYY-MM-DD HH:MM` (24h) | `2026-05-26 14:30` |

### 9.1 落成獨立檔案的 ID 檔名規則

`ADR-/CR-/CIA-` 三種 prefix 會建立獨立 `.md` 檔；其餘 ID 只出現在 body / frontmatter，不獨立成檔。

**檔名格式**：`<PREFIX>-<NNNN>-<short-kebab-slug>.md`

| 規則 | 說明 |
| :--- | :--- |
| Slug 長度 | 整檔名 ≤ 50 字元 |
| Slug 字元 | 小寫 ASCII + 連字符；禁用中文/空格/底線/駝峰 |
| Slug 內容 | 動詞 + 名詞，描述「做什麼」而非「為什麼」 |
| 內部引用 | body / `traces:` 一律寫 bare ID（`ADR-0007`），改檔名零連動 |

範例：

```text
✅ ADR-0007-use-postgres-for-orders.md
✅ CR-0023-deprecate-v1-api.md
✅ CIA-0005-upgrade-stripe-v2-to-v3.md
❌ ADR-0007.md                                  → 無 slug，初學者難辨識
❌ ADR-0007-使用-postgres.md                    → 中文，跨平台風險
❌ ADR-0007-postgres-because-mature.md          → slug 寫「為什麼」（屬 body）
```

詳見 `VibeCoding_Workflow_Templates/INDEX.md §檔名規範`。

## 10. Emoji 與符號

- 允許固定語意 emoji（提升 AI / 駕駛員辨識）：
  - 📎 cross-ref / 邊界註記
  - ⚠️ 警告
  - 🛑 硬 gate / 停止
  - ✅ 通過
  - ❌ 不通過 / 反例
  - 🟢🟡🔴 評分燈號（綠/黃/紅）
- **禁止**裝飾性 emoji（無意義的笑臉、星星）
- 不在標題首位放 emoji（影響 lint 與 ToC 生成）

## 11. 行寬與空行

- 行寬無硬性上限，但建議段落內每行 ≤ 120 字元
- 連續空行最多 1 行（不允許多個空行）
- 檔案結尾必須有單一 newline，無 trailing whitespace

## 12. 強制機制

| 層級 | 機制 | 阻擋 commit |
| :--- | :--- | :---: |
| IDE 即時 | `.markdownlint.json` + markdownlint extension | ❌ |
| Post-write hook | `.claude/hooks/post-write.sh` 跑 lint，AI 看見警告 | ❌ |
| Pre-commit gate | `.githooks/pre-commit` 跑 `npx markdownlint-cli2` | **✅** |

違反規則的修法：

1. 對著 `.markdownlint.json` 跑 `npx markdownlint-cli2 --fix <file>` 自動修
2. 仍有報錯 → 對照本規則手改
3. 真有合理例外 → 在違反處上方加 `<!-- markdownlint-disable-next-line MD0XX -->` 並補註理由

## 13. 與既有規則的關係

- `output-styles/` 是 **session 人格切換**，不規範文件 markdown 格式
- `context-stability.md` 規範 **tier 分層**，本檔規範 **格式**
- `change-governance.md` 規範 **變更流程**，與本檔正交
- `git-workflow.md` 規範 **commit message**，本檔規範**檔案內容**
