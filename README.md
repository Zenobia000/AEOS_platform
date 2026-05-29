<!-- markdownlint-disable MD041 MD042 -->
<div align="center">

<img src="assets/hero.png" alt="Claude Code Godzilla" width="720" />

# Claude Code Godzilla

**進倉。啟動。征服混沌的程式碼戰場。**

[![Version](https://img.shields.io/badge/version-v6.0-blue)](#版本記錄)
[![Templates](https://img.shields.io/badge/VibeCoding-v3.2-green)](VibeCoding_Workflow_Templates/INDEX.md)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20(WSL2)-lightgrey)](#快速開始)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>
<!-- markdownlint-enable MD041 MD042 -->

> 一套對抗 AI slop 的 Claude Code 完整工具箱 —— 21 個 VibeCoding 工作流模板（v3.2）、強制式 Markdown lint gate、三層觸發鏈、23 個按需技能。
> 不是又一套 prompt 集合：是讓 AI 寫文件**寫得像人**、寫程式碼**改得到位**的治理框架。

---

## 為什麼有這個專案

AI 加速時代真正要治理的不是「程式碼產出速度」，而是**「需求變更如何被吸收、追蹤、驗證、同步」**。沒有這層治理，AI 會把矛盾文件腦補成「合理版本」，把「看起來合理」的錯誤訊息產出量產化 —— 這就是 AI slop 的根源。

本專案三層收斂：

| 層 | 機制 | 範圍 |
| :--- | :--- | :--- |
| **規範層** | `template-formatter.md` + `.markdownlint.json` + `.editorconfig` | 21 個模板 + 駕駛員產出的 instance 文件統一格式 |
| **套用層** | 20 個 VibeCoding 模板已 lint clean、frontmatter 統一、ID 體系一致 | 直接複製即用，零格式債 |
| **觸發層** | `post-write.sh` + `pre-commit` gate + `sunnydata-doc-freshness` skill + 21 條 code→template 對應 | 寫程式碼即提醒同步文件；commit 違規即阻擋 |

---

## 快速開始

```bash
# 1. clone
git clone https://github.com/your-org/claude-Godzilla-z.git my-project
cd my-project

# 2. 安裝 markdownlint（pre-commit gate 用）
npm install

# 3. 啟用 pre-commit lint gate（一次性）
git config core.hooksPath .githooks

# 4. 設定 MCP（填入 API keys）
cp .mcp.json.linux.example .mcp.json   # Linux/WSL2
# cp .mcp.json.windows.example .mcp.json   # Windows

# 5. 啟動 Claude Code
claude

# 6. 驗證 self-test
bash scripts/v3.2-self-test.sh
```

預期 self-test 輸出 `39 PASS / 0 FAIL / 1 SKIP`。

---

## 主要內容

### 📚 VibeCoding 工作流模板（21 個，[INDEX](VibeCoding_Workflow_Templates/INDEX.md)）

從 PRD 到上線後變更治理的完整模板鏈，每個都有 lint clean 的 frontmatter + 統一 ID 體系：

| 階段 | 模板 |
| :--- | :--- |
| **總覽** | 01 workflow manual（含 QG-G0~G4 量化關卡） |
| **規劃** | 02 PRD、03 BDD |
| **架構** | 04 ADR、05 Architecture（C4 + DDD）、06 API |
| **設計** | 07 Module spec + DbC、08 Structure、09 Dependencies、10 Class relations |
| **品質** | 11 Code review、12 Frontend arch、13 Security、17 Frontend IA |
| **部署** | 14 Deploy + Rollback（8 子段）、15 Doc maintenance、16 WBS |
| **變更治理** | **19 CR**（變更請求）、**20 CIA**（變更影響分析硬 gate） |

### 🛡️ 規範與強制機制

- `.claude/rules/template-formatter.md` —— 13 段 markdown 風格規範
- `.markdownlint.json` + `.markdownlint-cli2.jsonc` —— 27 條 lint 規則
- `.githooks/pre-commit` —— commit 級 hard gate（違規阻擋）
- `.editorconfig` —— 跨 IDE 統一空白與換行

### 🔁 觸發鏈（駕駛員不用手動拖文件）

```text
寫 src/api/*       → post-write.sh 提醒同步 06 API spec（🔴 STRICT）
寫 migrations/*    → 提醒 14 §6.4 反向 migration（🔴 STRICT）
寫 docs/adr/ADR-*  → 提醒載入 sunnydata-doc-freshness skill
寫 docs/*.md       → skill 檢查 last_updated / traces / 雙向 ref
commit 違規 .md    → pre-commit gate 阻擋並指引 --fix
```

完整對應表：[`template-update-triggers.md`](.claude/rules/template-update-triggers.md)（21 條 code → template 規則）。

### 🎯 ID 命名體系

兩種 ID 嚴格區分（[INDEX §ID 命名規範](VibeCoding_Workflow_Templates/INDEX.md)）：

| 類型 | 範例 | 說明 |
| :--- | :--- | :--- |
| **Inline ID** | `E-0001`、`US-0007`、`API-0023`、`TC-0042` | 多個 ID 共存於同一檔 body |
| **File ID** | `ADR-0007-use-postgres-for-orders.md` | 每個 ID = 一個獨立 `.md` 檔 |

升級路徑：`Q-` → `D-` → `ADR-` → `CR-` → `CIA-` → 新 ADR。

### 🤖 Skills（23 個，按需載入）

| 類別 | 內容 |
| :--- | :--- |
| **sunnydata-** (14) | design / api-design / testing / security / code-review / architecture-review / debugging / infrastructure / branch-lifecycle / parallel-agents / deep-research / shadcn-ui / **doc-freshness** / skill-authoring |
| **community-** (9) | a11y-audit / frontend-design / react-{native,performance,composition} / ui-design-system / ux-bencium-{controlled,innovative} / web-guidelines |

### 📋 Rules（10 個，自動載入）

```text
coding-style              development-workflow      git-workflow
patterns                  performance               security
subagent-context          testing
template-formatter        template-update-triggers
```

---

## Quality Gates（QG-G0 ~ QG-G4）

[01_workflow_manual.md §6](VibeCoding_Workflow_Templates/01_workflow_manual.md) 定義 5 個量化關卡，每個含必備產出、可量化判準、RACI 簽核：

| Gate | 名稱 | 關鍵判準 |
| :--- | :--- | :--- |
| G0 | Ready to Design | Q-001~ ≤ 3、KPI 100% 有量測管道 |
| G1 | Ready to Code | 契約穩定 ≥ 2 sprint、NFR 100% 有測試 |
| G2 | Ready to Test | 覆蓋率 ≥ 80%（核心 ≥ 90%）、靜態檢查零 error |
| G3 | Ready to Deploy | critical = 0 且 high ≤ 2、回滾演練 ≥ 1 次 |
| G4 | Ready to Operate | Runbook ≥ 3 情境、SLO 達標、On-call 就緒 |

---

## 變更治理

任何上線後變更走 [`19 CR`](VibeCoding_Workflow_Templates/19_change_request_template.md)；觸碰 flow / contract / data / architecture 必須先跑 [`20 CIA`](VibeCoding_Workflow_Templates/20_change_impact_analysis.md) 並完成 §8 Human Decisions，才能動 code。詳見 [`change-governance.md`](.claude/rules/change-governance.md) *（即將補上）*。

---

## 結構

```text
.
├── README.md                         # 你正在讀
├── PROJECT_STRUCTURE.md              # 完整檔案樹
├── CLAUDE_TEMPLATE.md                # 新專案初始化範本
├── MCP_SETUP_GUIDE.md                # MCP 設定
├── LICENSE                           # MIT
├── package.json + package-lock.json  # markdownlint-cli2 pin
├── .markdownlint.json                # lint 規則
├── .markdownlint-cli2.jsonc          # lint runner config
├── .editorconfig                     # 跨 IDE 空白規範
├── .githooks/
│   ├── pre-commit                    # commit gate（git config core.hooksPath .githooks 啟用）
│   └── README.md
├── scripts/
│   └── v3.2-self-test.sh             # 40 個觸發鏈檢查
├── VibeCoding_Workflow_Templates/    # 21 個模板（核心產出）
└── .claude/
    ├── rules/             (10)       # 自動載入規則
    ├── skills/            (23)       # 按需技能
    ├── agents/            (13)       # 專業 agent
    ├── commands/          (17)       # /command
    ├── hooks/                        # post-write / pre-tool-use / session-start
    ├── output-styles/                # 僅 Vision-output（其餘已遷移為 skills）
    └── settings.json
```

完整檔案樹見 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。

---

## 驗證

```bash
# 一次性 self-test（檢查 40 個觸發點）
bash scripts/v3.2-self-test.sh

# 跑 markdown lint
npm run lint:md

# 自動修
npm run lint:md:fix
```

---

## 設計哲學

- **內部引用永遠寫 bare ID**（`ADR-0007` 不寫全檔名）—— 改檔名零連動風險
- **規則不能只是宣告**（rules）—— 必須有 lint config + hook + skill 三層強制
- **AI 加速 → 治理加倍**（不是更多文件，是更穩固的契約）
- **駕駛員心智**（你按下啟動鍵，框架替你抓邊界）

---

## 全域共用 Skills（選用）

讓所有專案共用某個 skill：

```bash
ln -s "$(pwd)/.claude/skills/sunnydata-doc-freshness" \
      ~/.claude/skills/sunnydata-doc-freshness
```

檔案實體在專案內（git 版控）、全域目錄只放捷徑 —— 改一處兩邊同步。

---

## 版本記錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| **v6.0** | 2026-05-26 | 規範+觸發+強制三層收斂；VibeCoding v3.2（ID 體系、QG 量化、CR/CIA、Rollback 擴寫）；markdownlint + pre-commit gate；sunnydata-doc-freshness skill；scripts/v3.2-self-test.sh；移除 19 個 legacy / personal 檔；倉庫減重 ~3.5 MB |
| v5.1 | 2026-05-10 | `sunnydata-architecture-review` skill；全域 symlink 共用 |
| v5.0 | 2026-04-06 | MECE skills 重構 (23→12, sunnydata-)；5-gate git；WHY/WHAT/IMPACT |
| v4.3 | 2026-03-24 | 時間追蹤、`/time-log`、StatusLine 持久化 |
| v4.2 | 2026-03-16 | 跨平台、Agent 全 opus |
| v4.1 | 2026-03-16 | rules(7)、skills(8)、MCP(+2) |
| v4.0 | 2026-03-16 | 13 Agent、16 Commands、StatusLine |

---

## License

[MIT](LICENSE)
