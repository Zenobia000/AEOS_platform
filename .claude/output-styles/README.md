# Claude Code Output Styles

> **版本:** v2.0 | **更新:** 2026-05-26 | **狀態:** 活躍
> **負責人:** 維護者 | **適用範圍:** Claude Code session-wide 人格切換

## What output-styles 真正該用來做

`/output-style <name>` 是 Claude Code 唯一**整個 session 都生效的人格切換機制**。它應該**只**用在「我想要 Claude 接下來所有回覆都改變表達方式」的情境，例如：

- 整段對話都偏好以視覺/diagram 為主而非長文
- 整段對話切換到蘇格拉底式提問模式
- 整段對話採用初學者友善口吻

**不**應該用 output-style 來：

- 裝載任務模板（PRD、ADR、API spec、code review 清單）—— 這些一次性、任務範圍的程序性知識屬於 **skill**
- 改變回應的具體章節結構 —— 同上，skill 更合適
- 為了「快捷鍵」效果包裝一個 skill —— 多餘的間接層

詳細設計理由見 `.claude/rules/primitive-selection.md`。

## 本目錄現存

只保留**真正符合上述定義**的 output-style：

| 檔案 | 用途 |
| :--- | :--- |
| `15-Vision-output.md` | 整段 session 偏好 ASCII 圖示 / diagram 優先於程式碼或長文 |

## 歷史

2025-10 階段曾有 14 個 task-template 形式的 output-styles（PRD / ADR / API / DDD / TDD / code review / security 等），後依 `primitive-selection.md` 規範**遷移為 skills**。剩餘的 task-template 知識請改用：

| 原 output-style | 對應位置 |
| :--- | :--- |
| 01 PRD product spec | `VibeCoding_Workflow_Templates/02_project_brief_and_prd.md` |
| 02 BDD scenario spec | `VibeCoding_Workflow_Templates/03_behavior_driven_development_guide.md` |
| 03 Architecture design doc | `VibeCoding_Workflow_Templates/05_architecture_and_design_document.md` |
| 04 DDD aggregate spec | `VibeCoding_Workflow_Templates/05_*.md` §1.2 DDD 戰術層 |
| 05 API contract spec | `VibeCoding_Workflow_Templates/06_api_design_specification.md` |
| 06 TDD unit spec | `VibeCoding_Workflow_Templates/07_module_specification_and_tests.md` |
| 07 Code review checklist | `VibeCoding_Workflow_Templates/11_code_review_and_refactoring_guide.md` |
| 08 Security checklist | `VibeCoding_Workflow_Templates/13_security_and_readiness_checklists.md` |
| 09 Database schema spec | `VibeCoding_Workflow_Templates/05_*.md` 資料層段 |
| 10-14 其餘任務模板 | 已整合進對應 VibeCoding 模板或拆解到 `.claude/skills/sunnydata-*` |

## 使用方式

```bash
# 切到 Vision 模式
/output-style 15-Vision-output

# 取消（回到預設）
/output-style default

# 查看當前模式
cat .claude/settings.local.json | grep outputStyle
```

切換後**整個 session** 都會以該風格回應，直到再次切換或重啟。

## 新增自訂 output-style 的判斷

回答以下任一才**真正需要** output-style：

- [ ] 我希望 Claude 在這整個 session 都改變**回應方式**（不是輸出格式）
- [ ] 即便話題切換，這個切換仍應保留
- [ ] 內容不可被「啟動時載入的單一 skill」取代

若以上皆否，請改用 `.claude/skills/<name>/SKILL.md` 撰寫 skill。skill 的觸發是任務範圍、按需載入，更不會干擾其他無關回應。
