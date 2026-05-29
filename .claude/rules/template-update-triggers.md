# Template Update Triggers

> 為什麼存在：v3.1 → v3.2 審視結論的核心痛點之一是「文件的觸發更新靠駕駛員手動」。
> 程式碼改了 API 但忘了同步 06、加了 migration 但忘了寫 14 §6.4 反向 script、
> 上 ADR 但忘了補 INDEX 索引 —— 都會造成文件腐化。本規則把「改 X 程式碼 → 應同步 Y 模板」
> 編碼成機器可讀的對應表，由 `post-write.sh` 在每次寫檔後查表給提醒。

## 0. 觸發層次

| 層次 | 嚴重度 | 處置 |
| :--- | :---: | :--- |
| **STRICT**（契約變動） | 🔴 高 | 寫檔後立即在對話顯示「應同步 X」，AI 必須提及；觸發 CIA gate 候選 |
| **REMIND**（一般功能變動） | 🟡 中 | 寫檔後 log + 對話末端附帶提示 |
| **TRACE**（追蹤性更新） | 🟢 低 | log only；CI 級 doc-freshness 掃描時呈現 |

## 1. 觸發對應表

### 1.1 Code → Templates（程式碼變更觸發模板更新）

| 程式碼 glob | 應同步模板 | 層次 | 理由 |
| :--- | :--- | :---: | :--- |
| `src/api/**`、`src/controllers/**`、`src/handlers/**` | 06 API spec | 🔴 STRICT | 對外契約必須一致 |
| `**/migrations/**/*.sql`、`prisma/schema.prisma`、`alembic/versions/**` | 14 §6.4 反向 migration、05 §1.1 資料層 | 🔴 STRICT | 不可逆變更需預先記錄反向 script |
| `src/auth/**`、`src/middleware/auth*` | 06 §4 安全性、13 §C 認證/授權 | 🔴 STRICT | 認證機制變動為高風險 |
| `src/domain/**`、`src/entities/**`、`src/models/**` | 07 模組規格、05 §1.2 DDD 戰術層 | 🟡 REMIND | Domain 結構是 source-of-truth |
| `src/modules/**/index.*`、新 service 目錄 | 07、09 file dependencies、10 class relations | 🟡 REMIND | 新模組需登記三份結構文件 |
| `**/*.feature`（Gherkin） | 03 BDD、07 §TC 對應 | 🟡 REMIND | Scenario 與 TC 應雙向對齊 |
| `package.json`、`requirements.txt`、`pyproject.toml`、`go.mod`、`Cargo.toml` | 13 §C 依賴安全 | 🟡 REMIND | 新依賴需通過安全評估 |
| `Dockerfile`、`docker-compose*.yml`、`k8s/**` | 14 §1 基礎設施、05 §1.1.2 Container | 🟡 REMIND | Infra 變動影響部署與架構 |
| `.github/workflows/**`、`.gitlab-ci.yml`、`Jenkinsfile` | 14 §2 CI/CD | 🟢 TRACE | Pipeline 變動需與 §2 流程同步 |
| `src/routes/**`、`pages/**`、`app/**`（前端） | 17 IA、12 §技術視角 | 🟡 REMIND | 路由變動 = IA 變動 |
| `src/components/**`（前端 UI） | 12 §技術視角 | 🟢 TRACE | 元件結構演進需呼應規範 |
| `.env.example`、`config/**`、`settings.*` | 14 §4 配置、13 §D Secrets | 🟡 REMIND | 環境變數變動影響部署 |
| `docs/adr/ADR-*.md` 新增 | INDEX ADR 索引、04 範本 frontmatter 範例 | 🔴 STRICT | ADR 必須登記到中央索引 |
| `src/observability/**`、`metrics/**`、`tracing/**` | 13 §G 可觀測性、14 §5 監控 | 🟡 REMIND | SLI/SLO 一致性 |
| `tests/integration/**`、`e2e/**` | 11 §審查 / 14 §3 部署檢查（測試通過判準） | 🟢 TRACE | E2E 覆蓋率影響 G2/G3 |

### 1.2 Templates → Code（模板變更觸發程式碼/測試更新）

| 模板變更 | 應同步程式碼 | 層次 |
| :--- | :--- | :---: |
| 06 API 端點修改 | `src/api/**` 對應 handler、`tests/contract/**` | 🔴 STRICT |
| 04 新 ADR `proposed → accepted` | 對應實作 / 設定變更 | 🔴 STRICT |
| 04 ADR `accepted → superseded` | 反向實作或 migration | 🔴 STRICT |
| 13 §C 新增安全要求 | 對應 middleware、SAST 規則、依賴升級 | 🟡 REMIND |
| 14 §5 監控閾值變動 | Prometheus rules / Alertmanager 設定 | 🟡 REMIND |
| 19 CR 狀態 `已批准` | 進入實作週期（PR 必須引用此 CR） | 🟡 REMIND |
| 20 CIA `已批准` | §9 implementation order 開始執行 | 🔴 STRICT |

## 2. 偵測機制

`post-write.sh` 在 `PostToolUse:Write` 時被觸發，流程：

1. 取得 `tool_input.file_path`
2. 與本檔 §1.1 / §1.2 的 glob 比對
3. Hit → 在 stderr 輸出醒目提示，AI 在對話中可看見並轉述給駕駛員
4. STRICT 層級 → 額外提示「觸發 CIA gate 候選，請評估」

提示格式範例：

```text
🔔 [TEMPLATE-TRIGGER 🔴 STRICT]
   寫入: src/api/orders/controller.py
   應同步: VibeCoding_Workflow_Templates/06_api_design_specification.md
   理由: 對外契約必須一致
   建議: 比對 endpoint 是否仍與 06 §5 一致；變動需走 CR-NNNN 或直接更新 06
```

## 3. 升級為硬 gate 的條件

當 STRICT 層級觸發**且**：

- 變更涉及 `flow / contract / data / architecture / external`（見 `change-governance.md`）

→ 必須先跑 `20_change_impact_analysis.md`（CIA-NNNN），未完成 §8 Human Decisions 不可動 code。

`post-write.sh` 僅提醒，不自動阻擋；阻擋責任由 `.githooks/pre-commit` + AI 判斷承擔。

## 4. 例外與抑制

| 情境 | 處置 |
| :--- | :--- |
| 重構但無 contract 變動（純內部 rename） | 在 commit message 標 `refactor(no-spec-change)`；hook 仍提示但可忽略 |
| 緊急 hotfix | 允許先改 code、後補 ADR/CR；hook 提示「請於 24 小時內補單據」 |
| 第三方產生檔案（如 OpenAPI 自動 generate） | 加入 `post-write.sh` 的 IGNORE_GLOBS |
| 文檔本身的內部 typo | 不觸發（modification < N bytes 直接 pass） |

## 5. 維護本表

本表是「契約」，不是「絕對清單」。新增專案類別（如 ML pipeline、邊緣裝置）時：

1. 駕駛員或 ARCH 提 CR-NNNN 描述新對應
2. 評估歸入 STRICT / REMIND / TRACE
3. 更新本檔 §1.1 / §1.2
4. 同步 `post-write.sh` 的 glob 比對邏輯
5. 在 INDEX 版本記錄補一行
