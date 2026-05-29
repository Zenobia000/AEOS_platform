# 專案結構總覽

> **版本:** v6.0 | **更新:** 2026-05-26 | **狀態:** 活躍
> **負責人:** 維護者 | **適用範圍:** 全域（駕駛員與貢獻者必讀）

---

## 目錄總覽

```text
claude-Godzilla-z/
├── README.md                              # 入門指南、價值主張、快速開始
├── PROJECT_STRUCTURE.md                   # 本檔案 — 完整檔案樹
├── CLAUDE_TEMPLATE.md                     # 新專案初始化範本（被 hook 偵測）
├── MCP_SETUP_GUIDE.md                     # MCP Server 設定指南
├── LICENSE                                # MIT
│
├── package.json                           # markdownlint-cli2 devDependency pin
├── package-lock.json                      # 鎖定依賴版本
├── .markdownlint.json                     # markdown lint 規則 (27 條)
├── .markdownlint-cli2.jsonc               # lint runner config (globs / ignores)
├── .editorconfig                          # 跨 IDE 空白與換行規範
├── .gitignore                             # session state / binary / node_modules
├── .gitattributes                         # 行尾規範
│
├── .mcp.json.linux.example                # MCP 範本（Linux/WSL2）
├── .mcp.json.windows.example              # MCP 範本（Windows）
│
├── .githooks/                             # 版控的 git hooks（一次性啟用）
│   ├── pre-commit                         # commit-time markdown lint gate
│   └── README.md                          # 啟用方式：git config core.hooksPath .githooks
│
├── scripts/
│   └── v3.2-self-test.sh                  # 40 個觸發鏈與功能斷層自動化檢查
│
├── assets/
│   └── hero.png                           # README 品牌 logo
│
├── .claude/                               # Claude Code 核心配置
│   ├── settings.json                      # 權限、StatusLine、Model、Hooks
│   ├── CLAUDE.md                          # 專案級指令（自動載入）
│   ├── WORKFLOW.md                        # 開發流程指南
│   ├── README.md                          # 內部 onboarding
│   ├── STATUSLINE_GUIDE.md                # StatusLine 客製指南
│   ├── statusline.sh                      # StatusLine（Windows）
│   ├── statusline-linux.sh                # StatusLine（Linux/WSL2/macOS）
│   │
│   ├── rules/                  (10 條，自動載入)
│   │   ├── coding-style.md                # 編碼風格
│   │   ├── development-workflow.md        # 先開分支再動 code、TDD 流程
│   │   ├── git-workflow.md                # WHY/WHAT/IMPACT commit、分支策略
│   │   ├── patterns.md                    # Repository / API 信封 / 骨架專案
│   │   ├── performance.md                 # 模型選擇、Context Window、平行任務
│   │   ├── security.md                    # commit 前 checklist、秘密管理
│   │   ├── subagent-context.md            # 子代理產出持久化規則
│   │   ├── testing.md                     # 80%+ 覆蓋率、TDD 強制
│   │   ├── template-formatter.md          # markdown 風格規範 (v6.0 新增)
│   │   └── template-update-triggers.md    # code → template 對應 (v6.0 新增)
│   │
│   ├── skills/                 (23 個，按需載入)
│   │   ├── INDEX.md                       # 索引
│   │   │
│   │   ├── sunnydata-design                       # 設計流程
│   │   ├── sunnydata-api-design                   # REST API 規範
│   │   ├── sunnydata-testing                      # TDD + Unit/Integration/E2E
│   │   ├── sunnydata-security                     # OWASP + checklist
│   │   ├── sunnydata-code-review                  # PR review 流程
│   │   ├── sunnydata-architecture-review          # 架構級審查（smells/principles/fixes）
│   │   ├── sunnydata-debugging                    # 四階段結構化除錯
│   │   ├── sunnydata-infrastructure               # Docker + CI/CD + 部署
│   │   ├── sunnydata-branch-lifecycle             # worktree + PR/merge 收尾
│   │   ├── sunnydata-deep-research                # 多來源研究
│   │   ├── sunnydata-parallel-agents              # 獨立任務平行派發
│   │   ├── sunnydata-shadcn-ui                    # shadcn/ui 元件
│   │   ├── sunnydata-doc-freshness                # instance 文件鮮度 (v6.0 新增)
│   │   ├── sunnydata-skill-authoring              # SKILL.md 撰寫
│   │   │
│   │   ├── community-a11y-audit                   # WCAG 2.2
│   │   ├── community-frontend-design              # 高品質前端
│   │   ├── community-react-composition            # React 組合模式
│   │   ├── community-react-native                 # RN/Expo
│   │   ├── community-react-performance            # React/Next 效能
│   │   ├── community-ui-design-system             # UI/UX 設計系統
│   │   ├── community-ux-bencium-controlled        # UX (controlled)
│   │   ├── community-ux-bencium-innovative        # UX (innovative)
│   │   └── community-web-guidelines               # Web 介面指南
│   │
│   ├── agents/                 (13 個)
│   │   ├── architect.md                   # 系統架構
│   │   ├── build-error-resolver.md        # 建置錯誤修復
│   │   ├── code-quality-specialist.md     # 程式碼審查
│   │   ├── deployment-expert.md           # 部署運維
│   │   ├── documentation-specialist.md    # 文檔與 codemap
│   │   ├── e2e-validation-specialist.md   # E2E 測試
│   │   ├── general-purpose.md             # 通用解題
│   │   ├── planner.md                     # 功能規劃
│   │   ├── refactor-cleaner.md            # 死碼清理
│   │   ├── security-infrastructure-auditor.md  # 安全稽核
│   │   ├── tdd-guide.md                   # TDD 引導
│   │   ├── test-automation-engineer.md    # 測試自動化
│   │   └── workflow-template-manager.md   # 模板管理
│   │
│   ├── commands/               (17 個)
│   │   ├── task-init.md / task-next.md / task-status.md / time-log.md
│   │   ├── plan.md / tdd.md / e2e.md / verify.md
│   │   ├── build-fix.md / refactor-clean.md
│   │   ├── review-code.md / check-quality.md
│   │   ├── hub-delegate.md / suggest-mode.md
│   │   ├── learn.md / save-session.md
│   │   └── template-check.md
│   │
│   ├── hooks/
│   │   ├── README.md
│   │   ├── hook-utils.sh                  # 共用工具
│   │   ├── session-start.sh               # 偵測 CLAUDE_TEMPLATE.md
│   │   ├── user-prompt-submit.sh          # /task-* 指令偵測
│   │   ├── pre-tool-use.sh                # 工具使用前 context
│   │   ├── post-write.sh                  # 寫檔後 lint + trigger 提醒 (v6.0 增強)
│   │   ├── agent-monitor.sh               # Agent 派發監控
│   │   └── watch-agents.sh
│   │
│   ├── output-styles/          (僅 1 個 — 其餘已遷移為 skills)
│   │   ├── 15-Vision-output.md            # 唯一保留：ASCII 圖示優先的 session 人格
│   │   ├── README.md                      # 用法 + legacy 對應表
│   │   └── scripts/
│   │
│   ├── mcp-configs/
│   │   └── README.md                      # MCP 推薦清單
│   │
│   ├── context/                # 子代理產出持久化（per-clone）
│   │   ├── README.md
│   │   ├── decisions/                     # 技術決策
│   │   ├── deployment/ docs/ e2e/ quality/ security/ testing/ workflow/
│   │
│   ├── coordination/
│   │   ├── README.md
│   │   └── human_ai_collaboration_config.md
│   │
│   ├── taskmaster-data/        # TaskMaster 持久化（per-clone，session 檔已 gitignore）
│   │   └── (.session-*、timelog.jsonl、wbs.md 等 hook 自動產生)
│   │
│   └── logs/                              # hook 日誌 (gitignore)
│
└── VibeCoding_Workflow_Templates/         # 工作流模板庫 (v3.2，21 個檔)
    ├── INDEX.md                           # 含 ID 命名規範 + 檔名規範 + 版本記錄
    ├── 01_workflow_manual.md              # 含 QG-G0~G4 量化關卡
    ├── 02_project_brief_and_prd.md        # PRD（E-/US-/Q-/D- inline ID）
    ├── 03_behavior_driven_development_guide.md   # BDD Gherkin
    ├── 04_architecture_decision_record_template.md   # ADR (File ID)
    ├── 05_architecture_and_design_document.md    # C4 + DDD 雙層
    ├── 06_api_design_specification.md     # REST + 自訂業務錯誤碼
    ├── 07_module_specification_and_tests.md      # DbC + TC
    ├── 08_project_structure_guide.md      # 專案結構
    ├── 09_file_dependencies_template.md   # 依賴分析
    ├── 10_class_relationships_template.md # 類別關係 (UML)
    ├── 11_code_review_and_refactoring_guide.md   # PR 前 checklist
    ├── 12_frontend_architecture_specification.md # 前端技術視角
    ├── 13_security_and_readiness_checklists.md   # 量化 §F 上線判準
    ├── 14_deployment_and_operations_guide.md     # §6 Rollback 8 子段
    ├── 15_documentation_and_maintenance_guide.md # 文檔維護
    ├── 16_wbs_development_plan_template.md       # WBS 含對應 US 欄
    ├── 17_frontend_information_architecture_template.md  # 前端 IA 視角
    ├── 19_change_request_template.md      # CR (File ID, v3.2 新增)
    ├── 20_change_impact_analysis.md       # CIA 硬 gate (File ID, v3.2 新增)
    └── output_style.md                    # Output Style 參考（不入 lint scope）
```

---

## 配置層次

| 層級 | 檔案 | 用途 |
| :--- | :--- | :--- |
| **專案共用** | `.claude/settings.json` | 權限、StatusLine、Hooks 註冊 |
| **個人設定** | `.claude/settings.local.json`（gitignore） | MCP 啟用清單、個人權限 |
| **MCP 定義** | `.mcp.json`（gitignore） | MCP Server 設定（含 API keys） |
| **規則** | `.claude/rules/*.md` | 自動載入，每次對話生效 |
| **技能** | `.claude/skills/*/SKILL.md` | 按需載入（依 description match） |
| **Hook** | `.claude/hooks/*.sh` | 由 settings.json 註冊觸發點 |
| **Commit gate** | `.githooks/pre-commit` | 一次性 `git config core.hooksPath .githooks` 啟用 |

---

## 三層收斂機制（v6.0 核心）

```text
規範層                  套用層                       觸發層
────                    ────                         ────
template-formatter.md   20 模板已 lint clean         post-write.sh
.markdownlint.json      ID 體系 + frontmatter 統一   pre-commit gate
.editorconfig           Quality Gates 量化           sunnydata-doc-freshness
.githooks/pre-commit    Rollback Plan 8 子段         template-update-triggers
                                                     scripts/v3.2-self-test.sh
```

詳見 [README §為什麼有這個專案](README.md)。

---

## 不入 repo 的檔案（已 gitignore）

| 路徑 | 原因 |
| :--- | :--- |
| `.claude/settings.local.json` | 個人偏好 |
| `.claude/taskmaster-data/.session-*` | per-session 暫存 |
| `.claude/taskmaster-data/timelog.jsonl` | 個人時間日誌 |
| `.claude/taskmaster-data/wbs-history.log` | per-clone 審計日誌 |
| `.claude/taskmaster-data/project.json` | per-project 自動產生 |
| `.claude/logs/*.log` | hook 日誌 |
| `.mcp.json` | 含 API keys |
| `*.exe / *.dll / *.dylib / *.so` | 跨平台不安全 |
| `node_modules/` | 透過 `package-lock.json` 重建 |

---

## 擴充指南

| 想做什麼 | 看哪裡 |
| :--- | :--- |
| 新增 MCP Server | [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md) |
| 新增 skill | `.claude/skills/sunnydata-skill-authoring/SKILL.md` |
| 新增模板 | 在 `VibeCoding_Workflow_Templates/` 加檔，更新 INDEX |
| 改 lint 規則 | `.markdownlint.json` + 同步 `template-formatter.md` |
| 改 post-write 觸發 | `.claude/rules/template-update-triggers.md` + `.claude/hooks/post-write.sh` |
| 改 commit gate | `.githooks/pre-commit` |
| 跑全套自我檢查 | `bash scripts/v3.2-self-test.sh` |

---

## 維護承諾

本檔案是 `tier 5 view`（cache，非 source-of-truth）。當 v3.2 後續迭代新增檔案類別時：

1. 在對應目錄區段補一行（按字母序）
2. bump 本檔頂部 `版本` 與 `更新` 日期
3. 跑 `bash scripts/v3.2-self-test.sh` 確認無迴歸

未來考慮自動化：由 `sunnydata-doc-freshness` 配套腳本從 `find` 結果 regen 本檔。
